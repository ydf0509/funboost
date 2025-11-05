# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/9/19 0019 9:48
import datetime
import json
from pprint import pprint
import time
import copy
import traceback
from funboost import nb_print
from funboost.constant import RedisKeys
from funboost.core.booster import BoostersManager
from funboost.core.func_params_model import PriorityConsumingControlConfig, PublisherParams
from funboost.core.msg_result_getter import AsyncResult
from funboost.core.serialization import Serialization
from funboost.utils import time_util, decorators, LoggerMixin
from funboost.utils.mongo_util import MongoMixin
from funboost.utils.redis_manager import RedisMixin

# from test_frame.my_patch_frame_config import do_patch_frame_config
#
# do_patch_frame_config()




# print(db)
# print(type(db))
# print(db.list_collection_names())

def get_cols(col_name_search: str):
    db = MongoMixin().mongo_db_task_status
    if not col_name_search:
        collection_name_list = db.list_collection_names()
    else:
        collection_name_list = [collection_name for collection_name in db.list_collection_names() if col_name_search in collection_name]
    # return [{'collection_name': collection_name, 'count': db.get_collection(collection_name).find().count()} for collection_name in collection_name_list]
    return [{'collection_name': collection_name, 'count': db.get_collection(collection_name).count_documents({})} for collection_name in collection_name_list]
    # for collection_name in collection_list:
    #     if col_name_search in collection_name:
    #     print (collection,db[collection].find().count())


def query_result(col_name, start_time, end_time, is_success, function_params: str, page, ):
    query_kw = copy.copy(locals())
    t0 = time.time()
    if not col_name:
        return []
    db = MongoMixin().mongo_db_task_status
    condition = {
        'insert_time': {'$gt': time_util.DatetimeConverter(start_time).datetime_obj,
                        '$lt': time_util.DatetimeConverter(end_time).datetime_obj},
    }
    # condition = {
    #     'insert_time_str': {'$gt': start_time,
    #                     '$lt': end_time},
    # }
    if is_success in ('2', 2, True):
        condition.update({"success": True})
    elif is_success in ('3', 3, False):
        condition.update({"success": False})
    if function_params.strip():
        condition.update({'params_str': {'$regex': function_params.strip()}})
    # nb_print(col_name)
    # nb_print(condition)
    # results = list(db.get_collection(col_name).find(condition, ).sort([('insert_time', -1)]).skip(int(page) * 100).limit(100))
    # with decorators.TimerContextManager():
    results = list(db.get_collection(col_name).find(condition, {'insert_time': 0, 'utime': 0}).skip(int(page) * 100).limit(100))
    # nb_print(results)
    nb_print(time.time() -t0, query_kw,len(results))
    return results


def get_speed(col_name, start_time, end_time):
    db = MongoMixin().mongo_db_task_status
    condition = {
        'insert_time': {'$gt': time_util.DatetimeConverter(start_time).datetime_obj,
                        '$lt': time_util.DatetimeConverter(end_time).datetime_obj},
    }
    # condition = {
    #     'insert_time_str': {'$gt': time_util.DatetimeConverter(time.time() - 60).datetime_str},
    # }
    # nb_print(condition)
    with decorators.TimerContextManager():
        # success_num = db.get_collection(col_name).count({**{'success': True}, **condition})
        # fail_num = db.get_collection(col_name).count({**{'success': False}, **condition})
        success_num = db.get_collection(col_name).count_documents({**{'success': True,'run_status':'finish'}, **condition})
        fail_num = db.get_collection(col_name).count_documents({**{'success': False,'run_status':'finish'}, **condition})
        qps = (success_num + fail_num) / (time_util.DatetimeConverter(end_time).timestamp - time_util.DatetimeConverter(start_time).timestamp)
        return {'success_num': success_num, 'fail_num': fail_num, 'qps': round(qps, 1)}


class Statistic(LoggerMixin):
    def __init__(self, col_name):
        db = MongoMixin().mongo_db_task_status
        self.col = db.get_collection(col_name)
        self.result = {'recent_10_days': {'time_arr': [], 'count_arr': []},
                       'recent_24_hours': {'time_arr': [], 'count_arr': []},
                       'recent_60_minutes': {'time_arr': [], 'count_arr': []},
                       'recent_60_seconds': {'time_arr': [], 'count_arr': []}}

    def statistic_by_period(self, t_start: str, t_end: str):
        condition = {'insert_time': {'$gt': time_util.DatetimeConverter(t_start).datetime_obj,
                                                         '$lt': time_util.DatetimeConverter(t_end).datetime_obj}}
        
        # now = datetime.datetime.now()
        # start_time = now - datetime.timedelta(hours=1)
        # end_time = now
        # condition = {
        #     'insert_time': {
        #         '$gt': start_time,
        #         '$lt': end_time
        #     }
        # }
        count =  self.col.count_documents(condition)
        print(count,t_start,t_end,time_util.DatetimeConverter(t_start).datetime_obj.timestamp(),condition)
        return count

    def build_result(self):
        with decorators.TimerContextManager():
            for i in range(10):
                t1 = datetime.datetime.now() + datetime.timedelta(days=-(9 - i))
                t2 = datetime.datetime.now() + datetime.timedelta(days=-(8 - i))
                self.result['recent_10_days']['time_arr'].append(time_util.DatetimeConverter(t1).date_str)
                count = self.statistic_by_period(time_util.DatetimeConverter(t1).date_str + ' 00:00:00',
                                                 time_util.DatetimeConverter(t2).date_str + ' 00:00:00')
                self.result['recent_10_days']['count_arr'].append(count)

            for i in range(0, 24):
                t1 = datetime.datetime.now() + datetime.timedelta(hours=-(23 - i))
                t2 = datetime.datetime.now() + datetime.timedelta(hours=-(22 - i))
                self.result['recent_24_hours']['time_arr'].append(t1.strftime('%Y-%m-%d %H:00:00'))
                # hour1_str = f'0{i}' if i < 10 else i
                count = self.statistic_by_period(t1.strftime('%Y-%m-%d %H:00:00'),
                                                 t2.strftime('%Y-%m-%d %H:00:00'))
                self.result['recent_24_hours']['count_arr'].append(count)

            for i in range(0, 60):
                t1 = datetime.datetime.now() + datetime.timedelta(minutes=-(59 - i))
                t2 = datetime.datetime.now() + datetime.timedelta(minutes=-(58 - i))
                self.result['recent_60_minutes']['time_arr'].append(t1.strftime('%Y-%m-%d %H:%M:00'))
                count = self.statistic_by_period(t1.strftime('%Y-%m-%d %H:%M:00'),
                                                 t2.strftime('%Y-%m-%d %H:%M:00'))
                self.result['recent_60_minutes']['count_arr'].append(count)

            for i in range(0, 60):
                t1 = datetime.datetime.now() + datetime.timedelta(seconds=-(59 - i))
                t2 = datetime.datetime.now() + datetime.timedelta(seconds=-(58 - i))
                self.result['recent_60_seconds']['time_arr'].append(t1.strftime('%Y-%m-%d %H:%M:%S'))
                count = self.statistic_by_period(t1.strftime('%Y-%m-%d %H:%M:%S'),
                                                 t2.strftime('%Y-%m-%d %H:%M:%S'))
                self.result['recent_60_seconds']['count_arr'].append(count)

def rpc_call(queue_name, msg_body, need_result, timeout):
  
    status_and_result = None
    task_id = None
    try:
        boost_params_json = RedisMixin().redis_db_frame.hget(RedisKeys.FUNBOOST_QUEUE__CONSUMER_PARAMS,queue_name)
        boost_params_dict = Serialization.to_dict(boost_params_json)
        broker_kind = boost_params_dict['broker_kind']
        publisher = BoostersManager.get_cross_project_publisher(PublisherParams(queue_name=queue_name,
                                                                            broker_kind=broker_kind, 
                                                                            publish_msg_log_use_full_msg=True))
    
        if need_result:
            # if booster.boost_params.is_using_rpc_mode is False:
            #     raise ValueError(f' need_result 为true,{booster.queue_name} 队列消费者 需要@boost设置支持rpc模式')
            
            async_result: AsyncResult =  publisher.publish(msg_body,priority_control_config=PriorityConsumingControlConfig(is_using_rpc_mode=True))
            async_result.set_timeout(timeout)
            status_and_result = async_result.status_and_result
            # print(status_and_result)
            task_id = async_result.task_id
        else:
            async_result =publisher.publish(msg_body)
            task_id = async_result.task_id
        if status_and_result['success'] is False:
            return dict(succ=False, msg=f'{queue_name} 队列,消息发布成功,但是函数执行失败', 
                            status_and_result=status_and_result,task_id=task_id)
        return dict(succ=True, msg=f'{queue_name} 队列,消息发布成功', 
                            status_and_result=status_and_result,task_id=task_id)
    except Exception as e:
        return dict(succ=False, msg=f'{queue_name} 队列,消息发布失败 {type(e)} {e} {traceback.format_exc()}',
                               status_and_result=status_and_result,task_id=task_id)
    

def get_result_by_task_id(task_id,timeout):
    async_result = AsyncResult(task_id)
    async_result.set_timeout(timeout)
    status_and_result = async_result.status_and_result
    if status_and_result is None:
        return dict(succ=False, msg=f'{task_id} 不存在 或 超时 或 结果已过期', 
                        status_and_result=status_and_result,task_id=task_id)
    if status_and_result['success'] is False:
        return dict(succ=False, msg=f'{task_id} 执行失败', 
                        status_and_result=status_and_result,task_id=task_id)
    return dict(succ=True, msg=f'task_id:{task_id} 获取结果成功', 
                            status_and_result=status_and_result,task_id=task_id)
        
    
     

if __name__ == '__main__':
    # print(get_cols('4'))
    # pprint(query_result('queue_test54_task_status', '2019-09-15 00:00:00', '2019-09-25 00:00:00', True, '999', 0))
    # print(json.dumps(query_result(**{'col_name': 'queue_test56', 'start_time': '2019-09-18 16:03:29', 'end_time': '2019-09-21 16:03:29', 'is_success': '1', 'function_params': '', 'page': '0'}))[:1000])
    # nb_print(get_speed_last_minute('queue_test54'))

    # nb_print(get_speed('queue_test56', '2019-09-18 16:03:29', '2019-09-23 16:03:29'))
    # stat = Statistic('queue_test_f01t')
    # stat.build_result()
    # nb_print(stat.result)
    
    # res = rpc_call('queue_test_g02t',{'x':1,'y':2},True,60)
    
    res = get_result_by_task_id('3232',60)
    print(res)
    
    

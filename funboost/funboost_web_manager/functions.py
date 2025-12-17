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

from funboost.core.func_params_model import PriorityConsumingControlConfig, PublisherParams
from funboost.core.msg_result_getter import AsyncResult
from funboost.core.serialization import Serialization
from funboost.utils import time_util, decorators  # LoggerMixin 已废弃，Statistic类不再使用
from funboost.utils.mongo_util import MongoMixin
from funboost.utils.redis_manager import RedisMixin
from funboost.core.active_cousumer_info_getter import QueuesConusmerParamsGetter, SingleQueueConusmerParamsGetter

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
    collection_name_set_filter = set(collection_name_list).intersection(QueuesConusmerParamsGetter().all_queue_names)
    return [{'collection_name': collection_name, 'count': db.get_collection(collection_name).count_documents({})} for collection_name in collection_name_set_filter]
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


# 以下 Statistic 类已废弃，功能已迁移到 get_consume_speed_curve，前端不再使用 speed_statistic_for_echarts 路由
# class Statistic(LoggerMixin):
#     def __init__(self, col_name):
#         db = MongoMixin().mongo_db_task_status
#         self.col = db.get_collection(col_name)
#         self.result = {'recent_10_days': {'time_arr': [], 'count_arr': []},
#                        'recent_24_hours': {'time_arr': [], 'count_arr': []},
#                        'recent_60_minutes': {'time_arr': [], 'count_arr': []},
#                        'recent_60_seconds': {'time_arr': [], 'count_arr': []}}
#
#     def statistic_by_period(self, t_start: str, t_end: str):
#         condition = {'insert_time': {'$gt': time_util.DatetimeConverter(t_start).datetime_obj,
#                                                          '$lt': time_util.DatetimeConverter(t_end).datetime_obj}}
#         count =  self.col.count_documents(condition)
#         print(count,t_start,t_end,time_util.DatetimeConverter(t_start).datetime_obj.timestamp(),condition)
#         return count
#
#     def build_result(self):
#         with decorators.TimerContextManager():
#             for i in range(10):
#                 t1 = datetime.datetime.now() + datetime.timedelta(days=-(9 - i))
#                 t2 = datetime.datetime.now() + datetime.timedelta(days=-(8 - i))
#                 self.result['recent_10_days']['time_arr'].append(time_util.DatetimeConverter(t1).date_str)
#                 count = self.statistic_by_period(time_util.DatetimeConverter(t1).date_str + ' 00:00:00',
#                                                  time_util.DatetimeConverter(t2).date_str + ' 00:00:00')
#                 self.result['recent_10_days']['count_arr'].append(count)
#
#             for i in range(0, 24):
#                 t1 = datetime.datetime.now() + datetime.timedelta(hours=-(23 - i))
#                 t2 = datetime.datetime.now() + datetime.timedelta(hours=-(22 - i))
#                 self.result['recent_24_hours']['time_arr'].append(t1.strftime('%Y-%m-%d %H:00:00'))
#                 count = self.statistic_by_period(t1.strftime('%Y-%m-%d %H:00:00'),
#                                                  t2.strftime('%Y-%m-%d %H:00:00'))
#                 self.result['recent_24_hours']['count_arr'].append(count)
#
#             for i in range(0, 60):
#                 t1 = datetime.datetime.now() + datetime.timedelta(minutes=-(59 - i))
#                 t2 = datetime.datetime.now() + datetime.timedelta(minutes=-(58 - i))
#                 self.result['recent_60_minutes']['time_arr'].append(t1.strftime('%Y-%m-%d %H:%M:00'))
#                 count = self.statistic_by_period(t1.strftime('%Y-%m-%d %H:%M:00'),
#                                                  t2.strftime('%Y-%m-%d %H:%M:00'))
#                 self.result['recent_60_minutes']['count_arr'].append(count)
#
#             for i in range(0, 60):
#                 t1 = datetime.datetime.now() + datetime.timedelta(seconds=-(59 - i))
#                 t2 = datetime.datetime.now() + datetime.timedelta(seconds=-(58 - i))
#                 self.result['recent_60_seconds']['time_arr'].append(t1.strftime('%Y-%m-%d %H:%M:%S'))
#                 count = self.statistic_by_period(t1.strftime('%Y-%m-%d %H:%M:%S'),
#                                                  t2.strftime('%Y-%m-%d %H:%M:%S'))
#                 self.result['recent_60_seconds']['count_arr'].append(count)



    
     

def get_consume_speed_curve(col_name: str, start_time: str, end_time: str, granularity: str = 'auto'):
    """
    获取消费速率曲线数据
    
    Args:
        col_name: 集合名称（队列名）
        start_time: 开始时间，格式 'YYYY-MM-DD HH:MM:SS'
        end_time: 结束时间，格式 'YYYY-MM-DD HH:MM:SS'
        granularity: 时间粒度，'second', 'minute', 'hour', 'day' 或 'auto'
    
    Returns:
        {
            'time_arr': [...],
            'success_arr': [...],
            'fail_arr': [...],
            'total_success': int,
            'total_fail': int,
            'granularity': str
        }
    """
    db = MongoMixin().mongo_db_task_status
    
    start_dt = time_util.DatetimeConverter(start_time).datetime_obj
    end_dt = time_util.DatetimeConverter(end_time).datetime_obj
    
    # 计算时间跨度（秒）
    time_span = (end_dt - start_dt).total_seconds()
    
    # 自动选择粒度
    if granularity == 'auto':
        if time_span <= 120:  # <= 2分钟
            granularity = 'second'
        elif time_span <= 3600:  # <= 1小时
            granularity = 'minute'
        elif time_span <= 86400 * 2:  # <= 2天
            granularity = 'hour'
        else:
            granularity = 'day'
    
    # 根据粒度设置时间格式和步长
    if granularity == 'second':
        time_format = '%Y-%m-%d %H:%M:%S'
        step = datetime.timedelta(seconds=1)
        max_points = 120
    elif granularity == 'minute':
        time_format = '%Y-%m-%d %H:%M'
        step = datetime.timedelta(minutes=1)
        max_points = 120
    elif granularity == 'hour':
        time_format = '%Y-%m-%d %H:00'
        step = datetime.timedelta(hours=1)
        max_points = 168  # 7天
    else:  # day
        time_format = '%Y-%m-%d'
        step = datetime.timedelta(days=1)
        max_points = 60
    
    # 限制数据点数量，避免太多
    actual_points = int(time_span / step.total_seconds()) + 1
    if actual_points > max_points:
        # 调整步长
        step = datetime.timedelta(seconds=time_span / max_points)
        actual_points = max_points
    
    time_arr = []
    success_arr = []
    fail_arr = []
    total_success = 0
    total_fail = 0
    
    current = start_dt
    while current < end_dt:
        next_time = current + step
        if next_time > end_dt:
            next_time = end_dt
        
        condition_base = {
            'insert_time': {'$gte': current, '$lt': next_time}
        }
        
        try:
            success_count = db.get_collection(col_name).count_documents({**condition_base, 'success': True, 'run_status': 'finish'})
            fail_count = db.get_collection(col_name).count_documents({**condition_base, 'success': False, 'run_status': 'finish'})
        except Exception as e:
            success_count = 0
            fail_count = 0
        
        time_arr.append(current.strftime(time_format))
        success_arr.append(success_count)
        fail_arr.append(fail_count)
        total_success += success_count
        total_fail += fail_count
        
        current = next_time
    
    return {
        'time_arr': time_arr,
        'success_arr': success_arr,
        'fail_arr': fail_arr,
        'total_success': total_success,
        'total_fail': total_fail,
        'granularity': granularity,
        'start_time': start_time,
        'end_time': end_time
    }


if __name__ == '__main__':
    pass
    # print(get_cols('4'))
    # pprint(query_result('queue_test54_task_status', '2019-09-15 00:00:00', '2019-09-25 00:00:00', True, '999', 0))
    # print(json.dumps(query_result(**{'col_name': 'queue_test56', 'start_time': '2019-09-18 16:03:29', 'end_time': '2019-09-21 16:03:29', 'is_success': '1', 'function_params': '', 'page': '0'}))[:1000])
    # nb_print(get_speed_last_minute('queue_test54'))

    # nb_print(get_speed('queue_test56', '2019-09-18 16:03:29', '2019-09-23 16:03:29'))
    # stat = Statistic('queue_test_f01t')
    # stat.build_result()
    # nb_print(stat.result)
    
    # res = rpc_call('queue_test_g02t',{'x':1,'y':2},True,60)
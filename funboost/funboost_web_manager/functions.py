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

from funboost.core.func_params_model import TaskOptions, PublisherParams
from funboost.core.msg_result_getter import AsyncResult
from funboost.core.serialization import Serialization
from funboost.utils import time_util, decorators  # LoggerMixin 已废弃，Statistic类不再使用
from funboost.utils.mongo_util import MongoMixin
from funboost.utils.redis_manager import RedisMixin
from funboost.core.active_cousumer_info_getter import QueuesConusmerParamsGetter, SingleQueueConusmerParamsGetter

# from test_frame.my_patch_frame_config import do_patch_frame_config
#
# do_patch_frame_config()


def get_mongo_table_name_by_queue_name(queue_name: str) -> str:
    """
    根据 queue_name 获取对应的 MongoDB 表名
    
    从队列配置的 function_result_status_persistance_conf.table_name 获取，
    如果没有配置 table_name，则使用 queue_name 作为表名
    
    Args:
        queue_name: 队列名称
        
    Returns:
        MongoDB 表名
    """
    try:
        queue_params = SingleQueueConusmerParamsGetter(queue_name).get_one_queue_params_use_cache()
        if queue_params:
            persistance_conf = queue_params.get('function_result_status_persistance_conf', {})
            table_name = persistance_conf.get('table_name')
            if table_name:
                return table_name
    except Exception as e:
        nb_print(f'获取队列 {queue_name} 的表名失败: {e}')
    # 默认使用 queue_name 作为表名
    return queue_name


def get_all_queue_table_info() -> dict:
    """
    获取所有队列及其对应的 MongoDB 表名映射
    
    Returns:
        {queue_name: table_name, ...}
    """
    result = {}
    try:
        queues_config = QueuesConusmerParamsGetter().get_queues_params()
        for queue_name, params in queues_config.items():
            persistance_conf = params.get('function_result_status_persistance_conf', {})
            table_name = persistance_conf.get('table_name') or queue_name
            result[queue_name] = table_name
    except Exception as e:
        nb_print(f'获取所有队列表名映射失败: {e}')
    return result


def get_cols(col_name_search: str):
    """
    获取队列列表，并返回每个队列对应的 MongoDB 表的记录数
    
    不再使用 db.list_collection_names()，而是从队列配置中获取表名
    注意：因为多个队列可能共享同一个表，所以查询时必须加上 queue_name 条件
    """
    db = MongoMixin().mongo_db_task_status
    
    # 从队列配置获取所有队列及其对应的表名
    queue_table_map = get_all_queue_table_info()
    
    result = []
    for queue_name, table_name in queue_table_map.items():
        # 根据搜索条件过滤
        if col_name_search and col_name_search not in queue_name:
            continue
        
        try:
            # 必须加上 queue_name 条件，因为多个队列可能共享同一个表
            count = db.get_collection(table_name).count_documents({'queue_name': queue_name})
        except Exception:
            count = 0
        
        result.append({
            'collection_name': queue_name,  # 返回队列名（用于前端显示和后续查询）
            'table_name': table_name,       # 实际的 MongoDB 表名
            'count': count
        })
    
    return result


def query_result(col_name, start_time, end_time, is_success, function_params: str, page, task_id: str = ''):
    """
    查询函数执行结果
    
    Args:
        col_name: 队列名称（不是表名，会自动转换为对应的 MongoDB 表名）
    
    注意：因为多个队列可能共享同一个表，所以查询时必须加上 queue_name 条件
    """
    query_kw = copy.copy(locals())
    t0 = time.time()
    if not col_name:
        return []
    db = MongoMixin().mongo_db_task_status
    
    # 根据队列名获取实际的 MongoDB 表名
    table_name = get_mongo_table_name_by_queue_name(col_name)
    
    # 基础条件：必须加上 queue_name，因为多个队列可能共享同一个表
    condition = {'queue_name': col_name}
    
    # 如果传了 task_id，忽略其他条件（时间、运行状态等），直接根据 task_id 查询
    if task_id and task_id.strip():
        condition.update({'task_id': {'$regex': f'^{task_id.strip()}'}})
    else:
        # 正常查询：使用时间范围和其他条件
        condition.update({
            'insert_time': {'$gt': time_util.DatetimeConverter(start_time).datetime_obj,
                            '$lt': time_util.DatetimeConverter(end_time).datetime_obj},
        })
        if is_success in ('2', 2, True):
            condition.update({"success": True})
        elif is_success in ('3', 3, False):
            condition.update({"success": False})
        if function_params.strip():
            condition.update({'params_str': {'$regex': function_params.strip()}})
    
    # nb_print(col_name)
    # nb_print(condition)
    # with decorators.TimerContextManager():
    # 按时间逆序排序，最新的在前面
    results = list(db.get_collection(table_name).find(condition, {'insert_time': 0, 'utime': 0}).sort([('time_start', -1)]).skip(int(page) * 100).limit(100))
    # nb_print(results)
    nb_print(time.time() -t0, query_kw, len(results), f'table: {table_name}')
    return results


def get_speed(col_name, start_time, end_time):
    """
    获取指定时间范围内的消费速率统计
    
    Args:
        col_name: 队列名称（不是表名，会自动转换为对应的 MongoDB 表名）
    
    注意：因为多个队列可能共享同一个表，所以查询时必须加上 queue_name 条件
    """
    db = MongoMixin().mongo_db_task_status
    
    # 根据队列名获取实际的 MongoDB 表名
    table_name = get_mongo_table_name_by_queue_name(col_name)
    
    # 基础条件：必须加上 queue_name，因为多个队列可能共享同一个表
    condition = {
        'queue_name': col_name,
        'insert_time': {'$gt': time_util.DatetimeConverter(start_time).datetime_obj,
                        '$lt': time_util.DatetimeConverter(end_time).datetime_obj},
    }
    # condition = {
    #     'insert_time_str': {'$gt': time_util.DatetimeConverter(time.time() - 60).datetime_str},
    # }
    # nb_print(condition)
    with decorators.TimerContextManager():
        # success_num = db.get_collection(table_name).count({**{'success': True}, **condition})
        # fail_num = db.get_collection(table_name).count({**{'success': False}, **condition})
        success_num = db.get_collection(table_name).count_documents({**{'success': True,'run_status':'finish'}, **condition})
        fail_num = db.get_collection(table_name).count_documents({**{'success': False,'run_status':'finish'}, **condition})
        qps = (success_num + fail_num) / (time_util.DatetimeConverter(end_time).timestamp - time_util.DatetimeConverter(start_time).timestamp)
        return {'success_num': success_num, 'fail_num': fail_num, 'qps': round(qps, 1)}




def get_consume_speed_curve(col_name: str, start_time: str, end_time: str, granularity: str = 'auto'):
    """
    获取消费速率曲线数据
    
    Args:
        col_name: 队列名称（不是表名，会自动转换为对应的 MongoDB 表名）
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
    
    # 根据队列名获取实际的 MongoDB 表名
    table_name = get_mongo_table_name_by_queue_name(col_name)
    
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
        
        # 基础条件：必须加上 queue_name，因为多个队列可能共享同一个表
        condition_base = {
            'queue_name': col_name,
            'insert_time': {'$gte': current, '$lt': next_time}
        }
        
        try:
            success_count = db.get_collection(table_name).count_documents({**condition_base, 'success': True, 'run_status': 'finish'})
            fail_count = db.get_collection(table_name).count_documents({**condition_base, 'success': False, 'run_status': 'finish'})
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
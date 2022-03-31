# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/9/19 0019 9:48
import datetime
import json
from pprint import pprint
import time
from flask import jsonify

from funboost import nb_print
from funboost.utils import time_util, decorators, LoggerMixin
from funboost.utils.mongo_util import MongoMixin

# from test_frame.my_patch_frame_config import do_patch_frame_config
#
# do_patch_frame_config()

db = MongoMixin().mongo_db_task_status


# print(db)
# print(type(db))
# print(db.list_collection_names())

def get_cols(col_name_search: str):
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
    # nb_print(result)
    return results


def get_speed(col_name, start_time, end_time):
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
        success_num = db.get_collection(col_name).count_documents({**{'success': True}, **condition})
        fail_num = db.get_collection(col_name).count_documents({**{'success': False}, **condition})
        qps = (success_num + fail_num) / (time_util.DatetimeConverter(end_time).timestamp - time_util.DatetimeConverter(start_time).timestamp)
        return {'success_num': success_num, 'fail_num': fail_num, 'qps': round(qps, 1)}


class Statistic(LoggerMixin):
    def __init__(self, col_name):
        self.col = db.get_collection(col_name)
        self.result = {'recent_10_days': {'time_arr': [], 'count_arr': []},
                       'recent_24_hours': {'time_arr': [], 'count_arr': []},
                       'recent_60_minutes': {'time_arr': [], 'count_arr': []},
                       'recent_60_seconds': {'time_arr': [], 'count_arr': []}}

    def statistic_by_period(self, t_start: str, t_end: str):
        return self.col.count_documents({'insert_time': {'$gt': time_util.DatetimeConverter(t_start).datetime_obj,
                                                         '$lt': time_util.DatetimeConverter(t_end).datetime_obj}})

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


if __name__ == '__main__':
    print(get_cols('4'))
    # pprint(query_result('queue_test54_task_status', '2019-09-15 00:00:00', '2019-09-25 00:00:00', True, '999', 0))
    # print(json.dumps(query_result(**{'col_name': 'queue_test56', 'start_time': '2019-09-18 16:03:29', 'end_time': '2019-09-21 16:03:29', 'is_success': '1', 'function_params': '', 'page': '0'}))[:1000])
    # nb_print(get_speed_last_minute('queue_test54'))

    # nb_print(get_speed('queue_test56', '2019-09-18 16:03:29', '2019-09-23 16:03:29'))
    stat = Statistic('queue_test56')
    stat.build_result()
    nb_print(stat.result)

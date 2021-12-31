# coding=utf8
"""
@author:Administrator
@file: bulk_operation.py
@time: 2018/08/27

三大数据库的更简单的批次操作，自动聚合一定时间内的离散任务为批次任务。免除手工数组切片的烦恼。
"""
import atexit
import re
import os
from elasticsearch import helpers
from threading import Thread
from typing import Union
import abc
import time
from queue import Queue, Empty
import unittest
# noinspection PyUnresolvedReferences
from pymongo import UpdateOne, InsertOne, UpdateMany, collection, MongoClient
import redis

from funboost.utils.time_util import DatetimeConverter
from funboost.utils import LoggerMixin, decorators, RedisMixin


class RedisOperation:
    """redis的操作，此类作用主要是规范下格式而已"""

    def __init__(self, operation_name: str, key: str, value: str):
        """
        :param operation_name: redis操作名字，例如 sadd lpush等
        :param key: redis的键
        :param value: reids键的值
        """
        self.operation_name = operation_name
        self.key = key
        self.value = value


class BaseBulkHelper(LoggerMixin, metaclass=abc.ABCMeta):
    """批量操纵抽象基类"""
    bulk_helper_map = {}

    def __new__(cls, base_object, *args, **kwargs):
        cls_key = f'{str(base_object)}-{os.getpid()}'
        if cls_key not in cls.bulk_helper_map:  # 加str是由于有一些类型的实例不能被hash作为字典的键
            self = super().__new__(cls)
            return self
        else:
            return cls.bulk_helper_map[cls_key]

    def __init__(self, base_object: Union[collection.Collection, redis.Redis], threshold: int = 100, max_time_interval=10, is_print_log: bool = True):
        cls_key = f'{str(base_object)}-{os.getpid()}'
        if cls_key not in self.bulk_helper_map:
            self._custom_init(base_object, threshold, max_time_interval, is_print_log)
            self.bulk_helper_map[cls_key] = self

    def _custom_init(self, base_object, threshold, max_time_interval, is_print_log):
        self.base_object = base_object
        self._threshold = threshold
        self._max_time_interval = max_time_interval
        self._is_print_log = is_print_log
        self._to_be_request_queue = Queue(threshold * 2)
        self._current_time = time.time()
        self._last_has_task_time = time.time()
        atexit.register(self.__do_something_before_exit)  # 程序自动结束前执行注册的函数
        self._main_thread_has_exit = False
        # Thread(target=self.__excute_bulk_operation_in_other_thread).start()
        # Thread(target=self.__check_queue_size).start()
        self.__excute_bulk_operation_in_other_thread()
        self.__check_queue_size()
        self.logger.debug(f'{self.__class__}被实例化')

    def add_task(self, base_operation: Union[UpdateOne, InsertOne, RedisOperation, tuple, dict]):
        """添加单个需要执行的操作，程序自动聚合陈批次操作"""
        self._to_be_request_queue.put(base_operation)
        # self.logger.debug(base_operation)

    # @decorators.tomorrow_threads(100)
    @decorators.keep_circulating(1, block=False, daemon=True)  # redis异常或网络异常，使其自动恢复。
    def __excute_bulk_operation_in_other_thread(self):
        while True:
            if self._to_be_request_queue.qsize() >= self._threshold or time.time() > self._current_time + self._max_time_interval:
                self._do_bulk_operation()
            if self._main_thread_has_exit and self._to_be_request_queue.qsize() == 0:
                pass
                # break
            time.sleep(10 ** -1)

    @decorators.keep_circulating(60, block=False, daemon=True)
    def __check_queue_size(self):
        if self._to_be_request_queue.qsize() > 0:
            self._last_has_task_time = time.time()
        if time.time() - self._last_has_task_time > 60:
            self.logger.info(f'{self.base_object} 最近一次有任务的时间是 ： {DatetimeConverter(self._last_has_task_time)}')

    @abc.abstractmethod
    def _do_bulk_operation(self):
        raise NotImplementedError

    def __do_something_before_exit(self):
        self._main_thread_has_exit = True
        self.logger.critical(f'程序自动结束前执行  [{str(self.base_object)}]  执行剩余的任务')


class MongoBulkWriteHelper(BaseBulkHelper):
    """
    一个更简单的批量插入,可以直接提交一个操作，自动聚合多个操作为一个批次再插入，速度快了n倍。
    """

    def _do_bulk_operation(self):
        if self._to_be_request_queue.qsize() > 0:
            t_start = time.time()
            count = 0
            request_list = []
            for _ in range(0, self._threshold):
                try:
                    request = self._to_be_request_queue.get_nowait()
                    # print(request)
                    count += 1
                    request_list.append(request)
                except Empty:
                    pass
                    break
            if request_list:
                # print(request_list)
                self.base_object.bulk_write(request_list, ordered=False)
            if self._is_print_log:
                mongo_col_str = re.sub(r"document_class=dict, tz_aware=False, connect=True\),", "", str(self.base_object))
                self.logger.info(f'【{mongo_col_str}】  批量插入的任务数量是 {count} 消耗的时间是 {round(time.time() - t_start, 6)}')
            self._current_time = time.time()


class ElasticBulkHelper(BaseBulkHelper):
    """
    elastic批量插入。
    """

    def _do_bulk_operation(self):
        if self._to_be_request_queue.qsize() > 0:
            t_start = time.time()
            count = 0
            request_list = []
            for _ in range(self._threshold):
                try:
                    request = self._to_be_request_queue.get_nowait()
                    count += 1
                    request_list.append(request)
                except Empty:
                    pass
                    break
            if request_list:
                # self.base_object.bulk_write(request_list, ordered=False)
                helpers.bulk(self.base_object, request_list)
            if self._is_print_log:
                self.logger.info(f'【{self.base_object}】  批量插入的任务数量是 {count} 消耗的时间是 {round(time.time() - t_start, 6)}')
            self._current_time = time.time()


class RedisBulkWriteHelper(BaseBulkHelper):
    """redis批量插入，比自带的更方便操作非整除批次"""

    def _do_bulk_operation(self):
        if self._to_be_request_queue.qsize() > 0:
            t_start = time.time()
            count = 0
            pipeline = self.base_object.pipeline()  # type: redis.client.Pipeline
            for _ in range(self._threshold):
                try:
                    request = self._to_be_request_queue.get_nowait()
                    count += 1
                except Empty:
                    break
                    pass
                else:
                    getattr(pipeline, request.operation_name)(request.key, request.value)
            pipeline.execute()
            pipeline.reset()
            if self._is_print_log:
                self.logger.info(f'[{str(self.base_object)}]  批量插入的任务数量是 {count} 消耗的时间是 {round(time.time() - t_start, 6)}')
            self._current_time = time.time()

    def _do_bulk_operation2(self):
        if self._to_be_request_queue.qsize() > 0:
            t_start = time.time()
            count = 0
            with self.base_object.pipeline() as pipeline:  # type: redis.client.Pipeline
                for _ in range(self._threshold):
                    try:
                        request = self._to_be_request_queue.get_nowait()
                        count += 1
                    except Empty:
                        pass
                    else:
                        getattr(pipeline, request.operation_name)(request.key, request.value)
                pipeline.execute()
            if self._is_print_log:
                self.logger.info(f'[{str(self.base_object)}]  批量插入的任务数量是 {count} 消耗的时间是 {round(time.time() - t_start, 6)}')
            self._current_time = time.time()


# noinspection SpellCheckingInspection,PyMethodMayBeStatic
class _Test(unittest.TestCase, LoggerMixin):
    # @unittest.skip
    def test_mongo_bulk_write(self):
        # col = MongoMixin().mongo_16_client.get_database('test').get_collection('ydf_test2')
        col = MongoClient('mongodb://myUserAdmin:8mwTdy1klnSYepNo@192.168.199.202:27016/admin').get_database('test').get_collection('ydf_test3')
        with decorators.TimerContextManager():
            for i in range(5000 + 13):
                # time.sleep(0.01)
                item = {'_id': i, 'field1': i * 2}
                mongo_helper = MongoBulkWriteHelper(col, 100, is_print_log=True)
                # mongo_helper.add_task(UpdateOne({'_id': item['_id']}, {'$set': item}, upsert=True))
                mongo_helper.add_task(InsertOne({'_id': item['_id']}))

    @unittest.skip
    def test_redis_bulk_write(self):

        with decorators.TimerContextManager():
            # r = redis.Redis(password='123456')
            r = RedisMixin().redis_db0
            redis_helper = RedisBulkWriteHelper(r, 200)
            # redis_helper = RedisBulkWriteHelper(r, 100)  # 放在外面可以
            for i in range(1003):
                # time.sleep(0.2)
                # 也可以在这里无限实例化
                redis_helper.add_task(RedisOperation('sadd', 'key1', str(i)))


if __name__ == '__main__':
    unittest.main()

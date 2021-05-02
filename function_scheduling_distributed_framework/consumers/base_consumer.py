# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:11
"""
所有中间件类型消费者的抽象基类。使实现不同中间件的消费者尽可能代码少。
整个流程最难的都在这里面。因为要实现多种并发模型，和对函数施加20运行种控制方式，所以代码非常长。
"""

import abc
import copy
# from multiprocessing import Process
import datetime
import json
import logging
import sys
import atexit
import socket
import os
import uuid
import time
import traceback
from collections import Callable
from functools import wraps
import threading
from threading import Lock, Thread
import eventlet
import gevent
import asyncio
import pymongo
from pymongo import IndexModel
from pymongo.errors import PyMongoError

# noinspection PyUnresolvedReferences
from nb_log import LoggerLevelSetterMixin, LogManager, nb_print, LoggerMixin, LoggerMixinDefaultWithFileHandler, stdout_write, stderr_write
# noinspection PyUnresolvedReferences
from function_scheduling_distributed_framework.concurrent_pool.async_helper import simple_run_in_executor
from function_scheduling_distributed_framework.concurrent_pool.async_pool_executor import AsyncPoolExecutor
# noinspection PyUnresolvedReferences
from function_scheduling_distributed_framework.concurrent_pool.bounded_threadpoolexcutor import \
    BoundedThreadPoolExecutor
from function_scheduling_distributed_framework.concurrent_pool.custom_evenlet_pool_executor import evenlet_timeout_deco, \
    check_evenlet_monkey_patch, CustomEventletPoolExecutor
from function_scheduling_distributed_framework.concurrent_pool.custom_gevent_pool_executor import gevent_timeout_deco, \
    GeventPoolExecutor, check_gevent_monkey_patch
from function_scheduling_distributed_framework.concurrent_pool.custom_threadpool_executor import \
    CustomThreadPoolExecutor, check_not_monkey
# from function_scheduling_distributed_framework.concurrent_pool.concurrent_pool_with_multi_process import ConcurrentPoolWithProcess
from function_scheduling_distributed_framework.consumers.redis_filter import RedisFilter, RedisImpermanencyFilter
from function_scheduling_distributed_framework.factories.publisher_factotry import get_publisher
from function_scheduling_distributed_framework.utils import decorators, time_util, RedisMixin
from function_scheduling_distributed_framework.utils.bulk_operation import MongoBulkWriteHelper, InsertOne
from function_scheduling_distributed_framework.utils.mongo_util import MongoMixin
from function_scheduling_distributed_framework import frame_config


def _delete_keys_and_return_new_dict(dictx: dict, keys: list = None):
    dict_new = copy.copy(dictx)  # 主要是去掉一级键 publish_time，浅拷贝即可。
    keys = ['publish_time', 'publish_time_format', 'extra'] if keys is None else keys
    for dict_key in keys:
        try:
            dict_new.pop(dict_key)
        except KeyError:
            pass
    return dict_new


class ExceptionForRetry(Exception):
    """为了重试的，抛出错误。只是定义了一个子类，用不用都可以"""


class ExceptionForRequeue(Exception):
    """框架检测到此错误，重新放回队列中"""


def _get_publish_time(paramsx: dict):
    """
    原来存放控制参数的位置没想好，建议所有控制参数放到extra键的字典值里面。
    :param paramsx:
    :return:
    """
    return paramsx.get('extra', {}).get('publish_time', None) or paramsx.get('publish_time', None)


class FunctionResultStatus(LoggerMixin, LoggerLevelSetterMixin):
    host_name = socket.gethostname()
    host_process = f'{host_name} - {os.getpid()}'
    script_name_long = sys.argv[0]
    script_name = script_name_long.split('/')[-1].split('\\')[-1]

    def __init__(self, queue_name, fucntion_name, params):
        self.queue_name = queue_name
        self.function = fucntion_name
        publish_time = _get_publish_time(params)
        if publish_time:
            self.publish_time_str = time_util.DatetimeConverter(publish_time).datetime_str
        function_params = _delete_keys_and_return_new_dict(params, )
        self.params = function_params
        self.params_str = json.dumps(function_params, ensure_ascii=False)
        self.result = ''
        self.run_times = 0
        self.exception = ''
        self.time_start = time.time()
        self.time_cost = None
        self.success = False
        self.total_thread = threading.active_count()
        self.set_log_level(20)

    def get_status_dict(self, without_datetime_obj=False):
        self.time_cost = round(time.time() - self.time_start, 3)
        item = self.__dict__
        item['host_name'] = self.host_name
        item['host_process'] = self.host_process
        item['script_name'] = self.script_name
        item['script_name_long'] = self.script_name_long
        # item.pop('time_start')
        datetime_str = time_util.DatetimeConverter().datetime_str
        try:
            json.dumps(item['result'])  # 不希望存不可json序列化的复杂类型。麻烦。存这种类型的结果是伪需求。
        except TypeError:
            item['result'] = str(item['result'])[:1000]
        item.update({'insert_time_str': datetime_str,
                     'insert_minutes': datetime_str[:-3],
                     })
        if not without_datetime_obj:
            item.update({'insert_time': datetime.datetime.now(),
                         'utime': datetime.datetime.utcnow(),
                         })
        else:
            item = _delete_keys_and_return_new_dict(item, ['insert_time', 'utime'])
        item['_id'] = str(uuid.uuid4())
        # self.logger.warning(item['_id'])
        # self.logger.warning(item)
        return item


class ResultPersistenceHelper(MongoMixin):
    def __init__(self, function_result_status_persistance_conf, queue_name):
        self.function_result_status_persistance_conf = function_result_status_persistance_conf
        if self.function_result_status_persistance_conf.is_save_status:
            task_status_col = self.mongo_db_task_status.get_collection(queue_name)
            # params_str 如果很长，必须使用TEXt或HASHED索引。
            task_status_col.create_indexes([IndexModel([("insert_time_str", -1)]), IndexModel([("insert_time", -1)]),
                                            IndexModel([("params_str", pymongo.TEXT)]), IndexModel([("success", 1)])
                                            ], )
            task_status_col.create_index([("utime", 1)],
                                         expireAfterSeconds=function_result_status_persistance_conf.expire_seconds)  # 只保留7天。
            self._mongo_bulk_write_helper = MongoBulkWriteHelper(task_status_col, 100, 2)
            self.task_status_col = task_status_col

    def save_function_result_to_mongo(self, function_result_status: FunctionResultStatus):
        if self.function_result_status_persistance_conf.is_save_status:
            item = function_result_status.get_status_dict()
            item2 = copy.copy(item)
            if not self.function_result_status_persistance_conf.is_save_result:
                item2['result'] = '不保存结果'
            self._mongo_bulk_write_helper.add_task(InsertOne(item2))  # 自动离散批量聚合方式。
            # self.task_status_col.insert_one(item2)


class ConsumersManager:
    schedulal_thread_to_be_join = []
    consumers_queue__info_map = dict()
    global_concurrent_mode = None
    schedual_task_always_use_thread = False
    _has_show_conusmers_info = False

    @classmethod
    def join_all_consumer_shedual_task_thread(cls):
        # nb_print((cls.schedulal_thread_to_be_join, len(cls.schedulal_thread_to_be_join), '模式：', cls.global_concurrent_mode))
        if cls.schedual_task_always_use_thread:
            for t in cls.schedulal_thread_to_be_join:
                nb_print(t)
                t.join()
        else:
            if cls.global_concurrent_mode in [1, 4]:
                for t in cls.schedulal_thread_to_be_join:
                    # nb_print(t)
                    t.join()
            elif cls.global_concurrent_mode == 2:
                # cls.logger.info()
                # nb_print(cls.schedulal_thread_to_be_join)
                gevent.joinall(cls.schedulal_thread_to_be_join, raise_error=True, )
            elif cls.global_concurrent_mode == 3:
                for g in cls.schedulal_thread_to_be_join:
                    # eventlet.greenthread.GreenThread.
                    # nb_print(g)
                    g.wait()

    @classmethod
    def show_all_consumer_info(cls):
        # nb_print(f'当前解释器内，所有消费者的信息是：\n  {cls.consumers_queue__info_map}')
        if not cls._has_show_conusmers_info:
            nb_print(f'当前解释器内，所有消费者的信息是：\n  {json.dumps(cls.consumers_queue__info_map, indent=4, ensure_ascii=False)}')
            for _, consumer_info in cls.consumers_queue__info_map.items():
                stdout_write(f'{time.strftime("%H:%M:%S")} "{consumer_info["where_to_instantiate"]}" '
                             f' \033[0;30;44m{consumer_info["queue_name"]} 的消费者\033[0m\n')
            cls._has_show_conusmers_info = True

    @staticmethod
    def get_concurrent_name_by_concurrent_mode(concurrent_mode):
        if concurrent_mode == 1:
            return 'thread'
        elif concurrent_mode == 2:
            return 'gevent'
        elif concurrent_mode == 3:
            return 'evenlet'
        elif concurrent_mode == 4:
            return 'async'


class FunctionResultStatusPersistanceConfig(LoggerMixin):
    def __init__(self, is_save_status: bool, is_save_result: bool, expire_seconds: int):
        """
        :param is_save_status:
        :param is_save_result:
        :param expire_seconds: 设置统计的过期时间，在mongo里面自动会移除这些过期的执行记录。
        """

        if not is_save_status and is_save_result:
            raise ValueError(f'你设置的是不保存函数运行状态但保存函数运行结果。不允许你这么设置')
        self.is_save_status = is_save_status
        self.is_save_result = is_save_result
        if expire_seconds > 10 * 24 * 3600:
            self.logger.warning(f'你设置的过期时间为 {expire_seconds} ,设置的时间过长。 ')
        self.expire_seconds = expire_seconds

    def to_dict(self):
        return {"is_save_status": self.is_save_status,
                'is_save_result': self.is_save_result, 'expire_seconds': self.expire_seconds}


# noinspection DuplicatedCode
class AbstractConsumer(LoggerLevelSetterMixin, metaclass=abc.ABCMeta, ):
    time_interval_for_check_do_not_run_time = 60
    BROKER_KIND = None

    @property
    @decorators.synchronized
    def publisher_of_same_queue(self):
        if not self._publisher_of_same_queue:
            self._publisher_of_same_queue = get_publisher(self._queue_name, consuming_function=self.consuming_function,
                                                          broker_kind=self.BROKER_KIND, log_level_int=self._log_level,
                                                          is_add_file_handler=self._create_logger_file)
            if self._msg_expire_senconds:
                self._publisher_of_same_queue.set_is_add_publish_time()
        return self._publisher_of_same_queue

    def bulid_a_new_publisher_of_same_queue(self):
        return get_publisher(self._queue_name, broker_kind=self.BROKER_KIND)

    @classmethod
    def join_shedual_task_thread(cls):
        """

        :return:
        """
        """
        def ff():
            RabbitmqConsumer('queue_test', consuming_function=f3, concurrent_num=20, msg_schedule_time_intercal=2, log_level=10, logger_prefix='yy平台消费', is_consuming_function_use_multi_params=True).start_consuming_message()
            RabbitmqConsumer('queue_test2', consuming_function=f4, concurrent_num=20, msg_schedule_time_intercal=4, log_level=10, logger_prefix='zz平台消费', is_consuming_function_use_multi_params=True).start_consuming_message()
            AbstractConsumer.join_shedual_task_thread()            # 如果开多进程启动消费者，在linux上需要这样写下这一行。


        if __name__ == '__main__':
            [Process(target=ff).start() for _ in range(4)]

        """
        ConsumersManager.join_all_consumer_shedual_task_thread()

    # noinspection PyProtectedMember,PyUnresolvedReferences
    def __init__(self, queue_name, *, consuming_function: Callable = None, function_timeout=0, concurrent_num=50,
                 specify_concurrent_pool=None, specify_async_loop=None, concurrent_mode=1,
                 max_retry_times=3, log_level=10, is_print_detail_exception=True,
                 msg_schedule_time_intercal=0.0, qps: float = 0, is_using_distributed_frequency_control=False,
                 msg_expire_senconds=0, is_send_consumer_hearbeat_to_redis=False,
                 logger_prefix='', create_logger_file=True, do_task_filtering=False,
                 task_filtering_expire_seconds=0, is_consuming_function_use_multi_params=True,
                 is_do_not_run_by_specify_time_effect=False,
                 do_not_run_by_specify_time=('10:00:00', '22:00:00'),
                 schedule_tasks_on_main_thread=False,
                 function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
                     False, False, 7 * 24 * 3600),
                 is_using_rpc_mode=False):
        """
        :param queue_name:
        :param consuming_function: 处理消息的函数。
        :param function_timeout : 超时秒数，函数运行超过这个时间，则自动杀死函数。为0是不限制。
         # 如果设置了qps，并且cocurrent_num是默认的50，会自动开了500并发，由于是采用的智能线程池任务少时候不会真开那么多线程而且会自动缩小线程数量。具体看ThreadPoolExecutorShrinkAble的说明
         # 由于有很好用的qps控制运行频率和智能扩大缩小的线程池，此框架建议不需要理会和设置并发数量只需要关心qps就行了，框架的并发是自适应并发数量，这一点很强很好用。
        :param concurrent_num:并发数量，并发种类由concurrent_mode决定
        :param specify_concurrent_pool:使用指定的线程池/携程池，可以多个消费者共使用一个线程池，不为None时候。threads_num失效
        :param specify_async_loop:指定的async的loop循环，设置并发模式为async才能起作用。
        :param concurrent_mode:并发模式，1线程 2gevent 3eventlet 4 asyncio
        :param max_retry_times:
        :param log_level: # 这里是设置消费者 发布者日志级别的，如果不想看到很多的细节显示信息，可以设置为 20 (logging.INFO)。
        :param is_print_detail_exception:
        :param msg_schedule_time_intercal:消息调度的时间间隔，用于控频
        :param qps:指定1秒内的函数执行次数，qps会覆盖msg_schedule_time_intercal，一会废弃msg_schedule_time_intercal这个参数。
        :param is_using_distributed_frequency_control: 是否使用分布式空频（依赖redis计数），默认只对当前实例化的消费者空频有效。假如实例化了2个qps为10的使用同一队列名的消费者，
               并且都启动，则每秒运行次数会达到20。如果使用分布式空频则所有消费者加起来的总运行次数是10。
        :param is_send_consumer_hearbeat_to_redis   时候将发布者的心跳发送到redis，有些功能的实现需要统计活跃消费者。因为有的中间件不是真mq。
        :param logger_prefix: 日志前缀，可使不同的消费者生成不同的日志
        :param create_logger_file : 是否创建文件日志
        :param do_task_filtering :是否执行基于函数参数的任务过滤
        :param task_filtering_expire_seconds:任务过滤的失效期，为0则永久性过滤任务。例如设置过滤过期时间是1800秒 ，
               30分钟前发布过1 + 2 的任务，现在仍然执行，
               如果是30分钟以内发布过这个任务，则不执行1 + 2，现在把这个逻辑集成到框架，一般用于接口价格缓存。
        :is_consuming_function_use_multi_params  函数的参数是否是传统的多参数，不为单个body字典表示多个参数。
        :param is_do_not_run_by_specify_time_effect :是否使不运行的时间段生效
        :param do_not_run_by_specify_time   :不运行的时间段
        :param schedule_tasks_on_main_thread :直接在主线程调度任务，意味着不能直接在当前主线程同时开启两个消费者。
        :param function_result_status_persistance_conf   :配置。是否保存函数的入参，运行结果和运行状态到mongodb。
               这一步用于后续的参数追溯，任务统计和web展示，需要安装mongo。
        :param is_using_rpc_mode 是否使用rpc模式，可以在发布端获取消费端的结果回调，但消耗一定性能，使用async_result.result时候会等待阻塞住当前线程。


        执行流程为
        1、 实例化消费者类，设置各种控制属性
        2、启动 start_consuming_message 启动消费
        3、start_consuming_message 中 调用 _shedual_task 从中间件循环取消息
        4、 _shedual_task 中调用 _submit_task，将 任务 添加到并发池中并发运行。
        5、 函数执行完成后，运行 _confirm_consume , 确认消费。
        各种中间件的 取消息、确认消费 单独实现，其他逻辑由于采用了模板模式，自动复用代码。

        """
        self.init_params = copy.copy(locals())
        self.init_params.pop('self')
        self.init_params['broker_kind'] = self.__class__.BROKER_KIND
        self.init_params['consuming_function'] = consuming_function

        ConsumersManager.consumers_queue__info_map[queue_name] = current_queue__info_dict = copy.copy(self.init_params)
        current_queue__info_dict['consuming_function'] = str(consuming_function)  # consuming_function.__name__
        current_queue__info_dict['specify_async_loop'] = str(specify_async_loop)
        current_queue__info_dict[
            'function_result_status_persistance_conf'] = function_result_status_persistance_conf.to_dict()
        current_queue__info_dict['class_name'] = self.__class__.__name__
        concurrent_name = ConsumersManager.get_concurrent_name_by_concurrent_mode(concurrent_mode)
        current_queue__info_dict['concurrent_mode_name'] = concurrent_name

        # 方便点击跳转定位到当前解释器下所有实例化消费者的文件行，点击可跳转到该处。
        # 获取被调用函数在被调用时所处代码行数
        # 直接实例化相应的类和使用工厂模式来实例化相应的类，得到的消费者实际实例化的行是不一样的，希望定位到用户的代码处，而不是定位到工厂模式处。也不要是task_deco装饰器本身处。
        line = sys._getframe(0).f_back.f_lineno
        # 获取被调用函数所在模块文件名
        file_name = sys._getframe(1).f_code.co_filename
        if 'consumer_factory.py' in file_name:
            line = sys._getframe(1).f_back.f_lineno
            file_name = sys._getframe(2).f_code.co_filename
        if r'function_scheduling_distributed_framework\__init__.py' in file_name or 'function_scheduling_distributed_framework/__init__.py' in file_name:
            line = sys._getframe(2).f_back.f_lineno
            file_name = sys._getframe(3).f_code.co_filename
        current_queue__info_dict['where_to_instantiate'] = f'{file_name}:{line}'

        self._queue_name = queue_name
        self.queue_name = queue_name  # 可以换成公有的，免得外部访问有警告。
        if consuming_function is None:
            raise ValueError('必须传 consuming_function 参数')
        self.consuming_function = consuming_function
        self._function_timeout = function_timeout

        # 如果设置了qps，并且cocurrent_num是默认的50，会自动开了500并发，由于是采用的智能线程池任务少时候不会真开那么多线程而且会自动缩小线程数量。具体看ThreadPoolExecutorShrinkAble的说明
        # 由于有很好用的qps控制运行频率和智能扩大缩小的线程池，此框架建议不需要理会和设置并发数量只需要关心qps就行了，框架的并发是自适应并发数量，这一点很强很好用。
        if qps != 0 and concurrent_num == 50:
            self._concurrent_num = 500
        else:
            self._concurrent_num = concurrent_num

        self._specify_concurrent_pool = specify_concurrent_pool
        self._specify_async_loop = specify_async_loop
        self._concurrent_pool = None
        self._concurrent_mode = concurrent_mode

        self._max_retry_times = max_retry_times
        self._is_print_detail_exception = is_print_detail_exception
        self._qps = qps
        if qps != 0:
            msg_schedule_time_intercal = 1.0 / qps  # 使用qps覆盖消息调度间隔，以qps为准，以后废弃msg_schedule_time_intercal这个参数。
        self._msg_schedule_time_intercal = msg_schedule_time_intercal if msg_schedule_time_intercal > 0.001 else 0.001
        self._is_using_distributed_frequency_control = is_using_distributed_frequency_control
        self._is_send_consumer_hearbeat_to_redis = is_send_consumer_hearbeat_to_redis or is_using_distributed_frequency_control
        self._msg_expire_senconds = msg_expire_senconds

        if self._concurrent_mode not in (1, 2, 3, 4, 5):
            raise ValueError('设置的并发模式不正确')
        self._concurrent_mode_dispatcher = ConcurrentModeDispatcher(self)
        if self._concurrent_mode == 4:
            self._run = self._async_run  # 这里做了自动转化，使用async_run代替run
        self.__check_monkey_patch()
        self._logger_prefix = logger_prefix
        self._log_level = log_level
        if logger_prefix != '':
            logger_prefix += '--'

        # logger_name = f'{logger_prefix}{self.__class__.__name__}--{concurrent_name}--{queue_name}--{self.consuming_function.__name__}'
        logger_name = f'{logger_prefix}{self.__class__.__name__}--{queue_name}'
        # nb_print(logger_name)
        self._create_logger_file = create_logger_file
        self._log_level = log_level
        self.logger = LogManager(logger_name).get_logger_and_add_handlers(log_level,
                                                                          log_filename=f'{logger_name}.log' if create_logger_file else None,
                                                                          formatter_template=frame_config.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER, )
        # self.logger.info(f'{self.__class__} 在 {current_queue__info_dict["where_to_instantiate"]}  被实例化')
        stdout_write(f'{time.strftime("%H:%M:%S")} "{current_queue__info_dict["where_to_instantiate"]}"  \033[0;30;44m此行 '
                     f'实例化队列名 {current_queue__info_dict["queue_name"]} 的消费者, 类型为 {self.__class__}\033[0m\n')

        self._do_task_filtering = do_task_filtering
        self._redis_filter_key_name = f'filter_zset:{queue_name}' if task_filtering_expire_seconds else f'filter_set:{queue_name}'
        filter_class = RedisFilter if task_filtering_expire_seconds == 0 else RedisImpermanencyFilter
        self._redis_filter = filter_class(self._redis_filter_key_name, task_filtering_expire_seconds)

        self._is_consuming_function_use_multi_params = is_consuming_function_use_multi_params

        self._unit_time_for_count = 10  # 每隔多少秒计数，显示单位时间内执行多少次，暂时固定为10秒。
        self._execute_task_times_every_unit_time = 0  # 每单位时间执行了多少次任务。
        self._lock_for_count_execute_task_times_every_unit_time = Lock()
        self._current_time_for_execute_task_times_every_unit_time = time.time()
        self._consuming_function_cost_time_total_every_unit_time = 0

        self._msg_num_in_broker = 0
        self._last_timestamp_when_has_task_in_queue = 0
        self._last_timestamp_print_msg_num = 0

        self._is_do_not_run_by_specify_time_effect = is_do_not_run_by_specify_time_effect
        self._do_not_run_by_specify_time = do_not_run_by_specify_time  # 可以设置在指定的时间段不运行。
        self._schedule_tasks_on_main_thread = schedule_tasks_on_main_thread

        self._result_persistence_helper = ResultPersistenceHelper(function_result_status_persistance_conf, queue_name)

        self._is_using_rpc_mode = is_using_rpc_mode

        self.stop_flag = False

        # 控频要用到的成员变量
        self._last_submit_task_timestamp = 0
        self._last_start_count_qps_timestamp = time.time()
        self._has_execute_times_in_recent_second = 0

        self._publisher_of_same_queue = None

        self.consumer_identification = f'{socket.gethostname()}_{time_util.DatetimeConverter().datetime_str.replace(":", "-")}_{os.getpid()}_{id(self)}'

        self.custom_init()

        atexit.register(self.join_shedual_task_thread)

    def __check_monkey_patch(self):
        if self._concurrent_mode == 2:
            check_gevent_monkey_patch()
        elif self._concurrent_mode == 3:
            check_evenlet_monkey_patch()
        else:
            check_not_monkey()

    @property
    @decorators.synchronized
    def concurrent_pool(self):
        return self._concurrent_mode_dispatcher.build_pool()

    def custom_init(self):
        pass

    def keep_circulating(self, time_sleep=0.001, exit_if_function_run_sucsess=False, is_display_detail_exception=True,
                         block=True):
        """间隔一段时间，一直循环运行某个方法的装饰器
        :param time_sleep :循环的间隔时间
        :param is_display_detail_exception
        :param exit_if_function_run_sucsess :如果成功了就退出循环
        :param block:是否阻塞在当前主线程运行。
        """

        def _keep_circulating(func):
            @wraps(func)
            def __keep_circulating(*args, **kwargs):

                # noinspection PyBroadException
                def ___keep_circulating():
                    while 1:
                        try:
                            result = func(*args, **kwargs)
                            if exit_if_function_run_sucsess:
                                return result
                        except Exception as e:
                            msg = func.__name__ + '   运行出错\n ' + traceback.format_exc(
                                limit=10) if is_display_detail_exception else str(e)
                            self.logger.exception(msg)
                        finally:
                            time.sleep(time_sleep)

                if block:
                    return ___keep_circulating()
                else:
                    threading.Thread(target=___keep_circulating, ).start()

            return __keep_circulating

        return _keep_circulating

    # noinspection PyAttributeOutsideInit
    def start_consuming_message(self):
        ConsumersManager.show_all_consumer_info()
        self.logger.warning(f'开始消费 {self._queue_name} 中的消息')
        if self._is_send_consumer_hearbeat_to_redis:
            self._distributed_consumer_statistics = DistributedConsumerStatistics(self._queue_name, self.consumer_identification)
            self._distributed_consumer_statistics.run()
            self.logger.warning(f'启动了分布式环境 使用 redis 的键 hearbeat:{self._queue_name} 统计活跃消费者 ，当前消费者唯一标识为 {self.consumer_identification}')
        self.keep_circulating(10, block=False)(self.check_heartbeat_and_message_count)()  # 间隔时间最好比self._unit_time_for_count小整数倍，不然日志不准。
        self._redis_filter.delete_expire_filter_task_cycle()
        if self._schedule_tasks_on_main_thread:
            self.keep_circulating(1)(self._shedual_task)()
        else:
            self._concurrent_mode_dispatcher.schedulal_task_with_no_block()
        setattr(frame_config, 'has_start_a_consumer_flag', 1)

    @abc.abstractmethod
    def _shedual_task(self):
        """
        每个子类必须实现这个的方法，完成如何从中间件取出消息，并将函数和运行参数添加到工作池。
        :return:
        """
        raise NotImplementedError

    def __get_priority_conf(self, kw: dict, broker_task_config_key: str):
        broker_task_config = kw['body'].get('extra', {}).get(broker_task_config_key, None)
        if broker_task_config is None:
            return getattr(self, f'_{broker_task_config_key}')
        else:
            return broker_task_config

    def _get_concurrent_info(self):
        concurrent_info = ''
        if self._concurrent_mode == 1:
            concurrent_info = f'[{threading.current_thread()}  {threading.active_count()}]'
        elif self._concurrent_mode == 2:
            concurrent_info = f'[{gevent.getcurrent()}  {threading.active_count()}]'
        elif self._concurrent_mode == 3:
            # noinspection PyArgumentList
            concurrent_info = f'[{eventlet.getcurrent()}  {threading.active_count()}]'
        return concurrent_info

    def _run(self, kw: dict, ):
        function_only_params = _delete_keys_and_return_new_dict(kw['body'], )
        if self.__get_priority_conf(kw, 'do_task_filtering') and self._redis_filter.check_value_exists(
                function_only_params):  # 对函数的参数进行检查，过滤已经执行过并且成功的任务。
            self.logger.warning(f'redis的 [{self._redis_filter_key_name}] 键 中 过滤任务 {kw["body"]}')
            self._confirm_consume(kw)
            return

        t_start_run_fun = time.time()
        self._run_consuming_function_with_confirm_and_retry(kw, current_retry_times=0,
                                                            function_result_status=FunctionResultStatus(
                                                                self.queue_name, self.consuming_function.__name__,
                                                                kw['body']),
                                                            )
        with self._lock_for_count_execute_task_times_every_unit_time:
            self._execute_task_times_every_unit_time += 1
            self._consuming_function_cost_time_total_every_unit_time += time.time() - t_start_run_fun
            if time.time() - self._current_time_for_execute_task_times_every_unit_time > self._unit_time_for_count:
                msg = f'{self._unit_time_for_count} 秒内执行了 {self._execute_task_times_every_unit_time} 次函数 [ {self.consuming_function.__name__} ] ,' \
                      f'函数平均运行耗时 {round(self._consuming_function_cost_time_total_every_unit_time / self._execute_task_times_every_unit_time, 4)} 秒'
                if self._msg_num_in_broker != -1:
                    msg += f''' ，预计还需要 {time_util.seconds_to_hour_minute_second(self._msg_num_in_broker / self._execute_task_times_every_unit_time * self._unit_time_for_count)} 时间 才能执行完成 {self._msg_num_in_broker}个剩余的任务'''
                self.logger.info(msg)
                self._current_time_for_execute_task_times_every_unit_time = time.time()
                self._consuming_function_cost_time_total_every_unit_time = 0
                self._execute_task_times_every_unit_time = 0

    def _run_consuming_function_with_confirm_and_retry(self, kw: dict, current_retry_times,
                                                       function_result_status: FunctionResultStatus, ):
        function_only_params = _delete_keys_and_return_new_dict(kw['body'])
        if current_retry_times < self.__get_priority_conf(kw, 'max_retry_times'):
            function_result_status.run_times += 1
            # noinspection PyBroadException
            t_start = time.time()
            try:
                function_run = self.consuming_function if self._function_timeout == 0 else self._concurrent_mode_dispatcher.timeout_deco(
                    self.__get_priority_conf(kw, 'function_timeout'))(self.consuming_function)
                if self._is_consuming_function_use_multi_params:  # 消费函数使用传统的多参数形式
                    function_result_status.result = function_run(**function_only_params)
                else:
                    function_result_status.result = function_run(
                        function_only_params)  # 消费函数使用单个参数，参数自身是一个字典，由键值对表示各个参数。
                if asyncio.iscoroutine(function_result_status.result):
                    self.logger.critical(f'异步的协程消费函数必须使用 async 并发模式并发,请设置 '
                                         f'消费函数 {self.consuming_function.__name__} 的concurrent_mode 为4')
                    # noinspection PyProtectedMember,PyUnresolvedReferences
                    os._exit(4)
                function_result_status.success = True
                self._confirm_consume(kw)
                if self.__get_priority_conf(kw, 'do_task_filtering'):
                    self._redis_filter.add_a_value(function_only_params)  # 函数执行成功后，添加函数的参数排序后的键值对字符串到set中。
                if self._log_level <= logging.DEBUG:
                    result_str_to_be_print = str(function_result_status.result)[:100] if len(str(function_result_status.result)) < 100 else str(function_result_status.result)[:100] + '  。。。。。  '
                    self.logger.debug(f' 函数 {self.consuming_function.__name__}  '
                                      f'第{current_retry_times + 1}次 运行, 正确了，函数运行时间是 {round(time.time() - t_start, 4)} 秒,入参是 【 {function_only_params} 】。 '
                                      f' 结果是  {result_str_to_be_print} ，  {self._get_concurrent_info()}  ')
            except Exception as e:
                if isinstance(e, (PyMongoError,
                                  ExceptionForRequeue)):  # mongo经常维护备份时候插入不了或挂了，或者自己主动抛出一个ExceptionForRequeue类型的错误会重新入队，不受指定重试次数逇约束。
                    self.logger.critical(f'函数 [{self.consuming_function.__name__}] 中发生错误 {type(e)}  {e}，消息重新入队')
                    time.sleep(1)  # 防止快速无限出错入队出队，导致cpu和中间件忙
                    return self._requeue(kw)
                self.logger.error(f'函数 {self.consuming_function.__name__}  第{current_retry_times + 1}次发生错误，'
                                  f'函数运行时间是 {round(time.time() - t_start, 4)} 秒,\n  入参是 【 {function_only_params} 】   \n 原因是 {type(e)} {e} ',
                                  exc_info=self.__get_priority_conf(kw, 'is_print_detail_exception'))
                function_result_status.exception = f'{e.__class__.__name__}    {str(e)}'
                return self._run_consuming_function_with_confirm_and_retry(kw, current_retry_times + 1, function_result_status, )
        else:
            self.logger.critical(
                f'函数 {self.consuming_function.__name__} 达到最大重试次数 {self.__get_priority_conf(kw, "max_retry_times")} 后,仍然失败， 入参是 【 {function_only_params} 】')
            self._confirm_consume(kw)  # 错得超过指定的次数了，就确认消费了。
            if self.__get_priority_conf(kw, 'do_task_filtering'):
                self._redis_filter.add_a_value(function_only_params)  # 函数执行成功后，添加函数的参数排序后的键值对字符串到set中。

        if self.__get_priority_conf(kw, 'is_using_rpc_mode'):
            # print(function_result_status.get_status_dict(without_datetime_obj=
            with RedisMixin().redis_db_frame.pipeline() as p:
                # RedisMixin().redis_db_frame.lpush(kw['body']['extra']['task_id'], json.dumps(function_result_status.get_status_dict(without_datetime_obj=True)))
                # RedisMixin().redis_db_frame.expire(kw['body']['extra']['task_id'], 600)
                p.lpush(kw['body']['extra']['task_id'],
                        json.dumps(function_result_status.get_status_dict(without_datetime_obj=True)))
                p.expire(kw['body']['extra']['task_id'], 600)
                p.execute()
        self._result_persistence_helper.save_function_result_to_mongo(function_result_status)

    async def _async_run(self, kw: dict, ):
        """虽然和上面有点大面积重复相似，这个是为了asyncio模式的，asyncio模式真的和普通同步模式的代码思维和形式区别太大，
        框架实现兼容async的消费函数很麻烦复杂，连并发池都要单独写"""
        function_only_params = _delete_keys_and_return_new_dict(kw['body'], )
        # if self.__get_priority_conf(kw, 'do_task_filtering') and self._redis_filter.check_value_exists(
        #         function_only_params):  # 对函数的参数进行检查，过滤已经执行过并且成功的任务。
        if self.__get_priority_conf(kw, 'do_task_filtering'):
            is_exists = await simple_run_in_executor(self._redis_filter.check_value_exists,
                                                     function_only_params)
            if is_exists:
                self.logger.warning(f'redis的 [{self._redis_filter_key_name}] 键 中 过滤任务 {kw["body"]}')
                # self._confirm_consume(kw)
                await simple_run_in_executor(self._confirm_consume, kw)
                return
        t_start_run_fun = time.time()
        await self._async_run_consuming_function_with_confirm_and_retry(kw, current_retry_times=0,
                                                                        function_result_status=FunctionResultStatus(
                                                                            self.queue_name, self.consuming_function.__name__,
                                                                            kw['body']), )
        # 异步调度不存在线程并发，不需要加锁。
        self._execute_task_times_every_unit_time += 1
        self._consuming_function_cost_time_total_every_unit_time += time.time() - t_start_run_fun
        if time.time() - self._current_time_for_execute_task_times_every_unit_time > self._unit_time_for_count:
            msg = f'''{self._unit_time_for_count} 秒内执行了 {self._execute_task_times_every_unit_time} 次函数 [ {self.consuming_function.__name__} ] ,''' + \
                  f'''函数平均运行耗时 {round(self._consuming_function_cost_time_total_every_unit_time / self._execute_task_times_every_unit_time, 4)} 秒'''
            if self._msg_num_in_broker != -1:
                msg += f''' ，预计还需要 {time_util.seconds_to_hour_minute_second(self._msg_num_in_broker / self._execute_task_times_every_unit_time * self._unit_time_for_count)} 时间 才能执行完成 {self._msg_num_in_broker}个剩余的任务'''
            self.logger.info(msg)
            self._current_time_for_execute_task_times_every_unit_time = time.time()
            self._consuming_function_cost_time_total_every_unit_time = 0
            self._execute_task_times_every_unit_time = 0

    async def _async_run_consuming_function_with_confirm_and_retry(self, kw: dict, current_retry_times,
                                                                   function_result_status: FunctionResultStatus, ):
        """虽然和上面有点大面积重复相似，这个是为了asyncio模式的，asyncio模式真的和普通同步模式的代码思维和形式区别太大，
        框架实现兼容async的消费函数很麻烦复杂，连并发池都要单独写"""
        function_only_params = _delete_keys_and_return_new_dict(kw['body'])
        if current_retry_times < self.__get_priority_conf(kw, 'max_retry_times'):
            function_result_status.run_times += 1
            # noinspection PyBroadException
            t_start = time.time()
            try:
                corotinue_obj = self.consuming_function(**function_only_params)
                if not asyncio.iscoroutine(corotinue_obj):
                    self.logger.critical(f'当前设置的并发模式为 async 并发模式，但消费函数不是异步协程函数，'
                                         f'请不要把消费函数 {self.consuming_function.__name__} 的 concurrent_mode 设置为 4')
                    # noinspection PyProtectedMember,PyUnresolvedReferences
                    os._exit(444)
                if self._function_timeout == 0:
                    rs = await corotinue_obj
                    # rs = await asyncio.wait_for(corotinue_obj, timeout=4)
                else:
                    rs = await asyncio.wait_for(corotinue_obj, timeout=self._function_timeout)
                function_result_status.result = rs
                function_result_status.success = True
                # self._confirm_consume(kw)
                await simple_run_in_executor(self._confirm_consume, kw)
                if self.__get_priority_conf(kw, 'do_task_filtering'):
                    # self._redis_filter.add_a_value(function_only_params)  # 函数执行成功后，添加函数的参数排序后的键值对字符串到set中。
                    await simple_run_in_executor(self._redis_filter.add_a_value, function_only_params)
                if self._log_level <= logging.DEBUG:
                    result_str_to_be_print = str(rs)[:100] if len(str(rs)) < 100 else str(rs)[:100] + '  。。。。。  '
                    self.logger.debug(f' 函数 {self.consuming_function.__name__}  '
                                      f'第{current_retry_times + 1}次 运行, 正确了，函数运行时间是 {round(time.time() - t_start, 4)} 秒,'
                                      f'入参是 【 {function_only_params} 】 ,结果是 {result_str_to_be_print}  。 {corotinue_obj} ')
            except Exception as e:
                if isinstance(e, (PyMongoError,
                                  ExceptionForRequeue)):  # mongo经常维护备份时候插入不了或挂了，或者自己主动抛出一个ExceptionForRequeue类型的错误会重新入队，不受指定重试次数逇约束。
                    self.logger.critical(f'函数 [{self.consuming_function.__name__}] 中发生错误 {type(e)}  {e}，消息重新入队')
                    # time.sleep(1)  # 防止快速无限出错入队出队，导致cpu和中间件忙
                    await asyncio.sleep(1)
                    # return self._requeue(kw)
                    return await simple_run_in_executor(self._requeue, kw)
                self.logger.error(f'函数 {self.consuming_function.__name__}  第{current_retry_times + 1}次发生错误，'
                                  f'函数运行时间是 {round(time.time() - t_start, 4)} 秒,\n  入参是 【 {function_only_params} 】   \n 原因是 {type(e)} {e} ',
                                  exc_info=self.__get_priority_conf(kw, 'is_print_detail_exception'))
                function_result_status.exception = f'{e.__class__.__name__}    {str(e)}'
                return await self._async_run_consuming_function_with_confirm_and_retry(kw, current_retry_times + 1, function_result_status, )
        else:
            self.logger.critical(
                f'函数 {self.consuming_function.__name__} 达到最大重试次数 {self.__get_priority_conf(kw, "max_retry_times")} 后,仍然失败， 入参是 【 {function_only_params} 】')
            # self._confirm_consume(kw)  # 错得超过指定的次数了，就确认消费了。
            await simple_run_in_executor(self._confirm_consume, kw)
            if self.__get_priority_conf(kw, 'do_task_filtering'):
                # self._redis_filter.add_a_value(function_only_params)  # 函数执行成功后，添加函数的参数排序后的键值对字符串到set中。
                await simple_run_in_executor(self._redis_filter.add_a_value, function_only_params)

        if self.__get_priority_conf(kw, 'is_using_rpc_mode'):
            def push_result():
                with RedisMixin().redis_db_frame.pipeline() as p:
                    p.lpush(kw['body']['extra']['task_id'],
                            json.dumps(function_result_status.get_status_dict(without_datetime_obj=True)))
                    p.expire(kw['body']['extra']['task_id'], 600)
                    p.execute()

            await simple_run_in_executor(push_result)
        # self._result_persistence_helper.save_function_result_to_mongo(function_result_status)
        await simple_run_in_executor(self._result_persistence_helper.save_function_result_to_mongo, function_result_status)

    @abc.abstractmethod
    def _confirm_consume(self, kw):
        """确认消费"""
        raise NotImplementedError

    def check_heartbeat_and_message_count(self):
        self._msg_num_in_broker = self.publisher_of_same_queue.get_message_count()
        if time.time() - self._last_timestamp_print_msg_num > 60:
            if self._msg_num_in_broker != -1:
                self.logger.info(f'[{self._queue_name}] 队列中还有 [{self._msg_num_in_broker}] 个任务')
            self._last_timestamp_print_msg_num = time.time()
        if self._msg_num_in_broker != 0:
            self._last_timestamp_when_has_task_in_queue = time.time()
        return self._msg_num_in_broker

    @abc.abstractmethod
    def _requeue(self, kw):
        """重新入队"""
        raise NotImplementedError

    def _submit_task(self, kw):
        if self._judge_is_daylight():
            self._requeue(kw)
            time.sleep(self.time_interval_for_check_do_not_run_time)
            return
        publish_time = _get_publish_time(kw['body'])
        msg_expire_senconds_priority = self.__get_priority_conf(kw, 'msg_expire_senconds')
        if msg_expire_senconds_priority != 0 and time.time() - msg_expire_senconds_priority > publish_time:
            self.logger.warning(
                f'消息发布时戳是 {publish_time} {kw["body"].get("publish_time_format", "")},距离现在 {round(time.time() - publish_time, 4)} 秒 ,'
                f'超过了指定的 {msg_expire_senconds_priority} 秒，丢弃任务')
            self._confirm_consume(kw)
            return 0
        if self._is_using_distributed_frequency_control:  # 如果是需要分布式控频。
            active_num = self._distributed_consumer_statistics.active_consumer_num
            self.__frequency_control(self._qps / active_num, self._msg_schedule_time_intercal * active_num)
        else:
            self.__frequency_control(self._qps, self._msg_schedule_time_intercal)
        if self._concurrent_mode == 5:  # 单线程
            self._run(kw)
        else:
            self.concurrent_pool.submit(self._run, kw)

    def __frequency_control(self, qpsx, msg_schedule_time_intercalx):
        # 以下是消费函数qps控制代码。无论是单个消费者空频还是分布式消费控频，都是基于直接计算的，没有依赖redis inrc计数，使得控频性能好。
        if qpsx == 0:
            return
        if qpsx <= 5:
            """ 原来的简单版 """
            time.sleep(msg_schedule_time_intercalx)
        elif 5 < qpsx <= 20:
            """ 改进的控频版,防止网络波动"""
            time_sleep_for_qps_control = max((msg_schedule_time_intercalx - (time.time() - self._last_submit_task_timestamp)) * 0.99, 10 ** -3)
            # print(time.time() - self._last_submit_task_timestamp)
            # print(time_sleep_for_qps_control)
            time.sleep(time_sleep_for_qps_control)
            self._last_submit_task_timestamp = time.time()
        else:
            """基于当前消费者计数的控频"""
            if time.time() - self._last_start_count_qps_timestamp > 1:
                self._has_execute_times_in_recent_second = 1
                self._last_start_count_qps_timestamp = time.time()
            else:
                self._has_execute_times_in_recent_second += 1
            # print(self._has_execute_times_in_recent_second)
            if self._has_execute_times_in_recent_second >= qpsx:
                time.sleep((1 - (time.time() - self._last_start_count_qps_timestamp)) * 1)

    @decorators.FunctionResultCacher.cached_function_result_for_a_time(120)
    def _judge_is_daylight(self):
        if self._is_do_not_run_by_specify_time_effect and (
                self._do_not_run_by_specify_time[0] < time_util.DatetimeConverter().time_str < self._do_not_run_by_specify_time[1]):
            self.logger.warning(
                f'现在时间是 {time_util.DatetimeConverter()} ，现在时间是在 {self._do_not_run_by_specify_time} 之间，不运行')
            return True

    def __str__(self):
        return f'队列为 {self.queue_name} 函数为 {self.consuming_function} 的消费者'


# noinspection PyProtectedMember
class ConcurrentModeDispatcher(LoggerMixin):

    def __init__(self, consumerx: AbstractConsumer):
        self.consumer = consumerx
        if ConsumersManager.global_concurrent_mode is not None and self.consumer._concurrent_mode != ConsumersManager.global_concurrent_mode:
            ConsumersManager.show_all_consumer_info()
            # print({self.consumer._concurrent_mode, ConsumersManager.global_concurrent_mode})
            if not {self.consumer._concurrent_mode, ConsumersManager.global_concurrent_mode}.issubset({1, 4}):
                raise ValueError('由于猴子补丁的原因，同一解释器中不可以设置两种并发类型,请查看显示的所有消费者的信息，'
                                 '搜索 concurrent_mode 关键字，确保当前解释器内的所有消费者的并发模式只有一种')
        self._concurrent_mode = ConsumersManager.global_concurrent_mode = self.consumer._concurrent_mode
        self.timeout_deco = None
        if self._concurrent_mode == 1:
            self.timeout_deco = decorators.timeout
        elif self._concurrent_mode == 2:
            self.timeout_deco = gevent_timeout_deco
        elif self._concurrent_mode == 3:
            self.timeout_deco = evenlet_timeout_deco
        self.logger.warning(f'{self.consumer} 设置并发模式'
                            f'为{ConsumersManager.get_concurrent_name_by_concurrent_mode(self._concurrent_mode)}')

    def build_pool(self):
        if self.consumer._concurrent_pool is not None:
            return self.consumer._concurrent_pool

        pool_type = None  # 是按照ThreadpoolExecutor写的三个鸭子类，公有方法名和功能写成完全一致，可以互相替换。
        if self._concurrent_mode == 1:
            pool_type = CustomThreadPoolExecutor
            # pool_type = BoundedThreadPoolExecutor
        elif self._concurrent_mode == 2:
            pool_type = GeventPoolExecutor
        elif self._concurrent_mode == 3:
            pool_type = CustomEventletPoolExecutor
        elif self._concurrent_mode == 4:
            pool_type = AsyncPoolExecutor
            check_not_monkey()
        if self._concurrent_mode == 4:
            self.consumer._concurrent_pool = self.consumer._specify_concurrent_pool if self.consumer._specify_concurrent_pool is not None else pool_type(
                self.consumer._concurrent_num, loop=self.consumer._specify_async_loop)
        else:
            self.consumer._concurrent_pool = self.consumer._specify_concurrent_pool if self.consumer._specify_concurrent_pool is not None else pool_type(
                self.consumer._concurrent_num)
        # print(self._concurrent_mode,self.consumer._concurrent_pool)
        return self.consumer._concurrent_pool

    def schedulal_task_with_no_block(self):
        if ConsumersManager.schedual_task_always_use_thread:
            t = Thread(target=self.consumer.keep_circulating(1)(self.consumer._shedual_task))
            ConsumersManager.schedulal_thread_to_be_join.append(t)
            t.start()
        else:
            if self._concurrent_mode in [1, 4, 5]:
                t = Thread(target=self.consumer.keep_circulating(1)(self.consumer._shedual_task))
                ConsumersManager.schedulal_thread_to_be_join.append(t)
                t.start()
            elif self._concurrent_mode == 2:
                g = gevent.spawn(self.consumer.keep_circulating(1)(self.consumer._shedual_task), )
                ConsumersManager.schedulal_thread_to_be_join.append(g)
            elif self._concurrent_mode == 3:
                g = eventlet.spawn(self.consumer.keep_circulating(1)(self.consumer._shedual_task), )
                ConsumersManager.schedulal_thread_to_be_join.append(g)
            # elif self._concurrent_mode == 4:
            #     t = Thread(target=self.consumer.keep_circulating(1)(self.consumer._shedual_task))
            #     ConsumersManager.schedulal_thread_to_be_join.append(t)
            #     t.start()
            # elif self._concurrent_mode ==5:


# noinspection DuplicatedCode
def wait_for_possible_has_finish_all_tasks(queue_name: str, minutes: int, send_stop_to_broker=0,
                                           broker_kind: int = 0, ):
    """
      由于是异步消费，和存在队列一边被消费，一边在推送，或者还有结尾少量任务还在确认消费者实际还没彻底运行完成。  但有时候需要判断 所有任务，务是否完成，提供一个不精确的判断，要搞清楚原因和场景后再慎用。
    :param queue_name: 队列名字
    :param minutes: 连续多少分钟没任务就判断为消费已完成
    :param send_stop_to_broker :发送停止标志到中间件，这回导致消费退出循环调度。
    :param broker_kind: 中间件种类
    :return:
    """
    if minutes <= 1:
        raise ValueError('疑似完成任务，判断时间最少需要设置为2分钟内,最好是是10分钟')
    pb = get_publisher(queue_name, broker_kind=broker_kind)
    no_task_time = 0
    while 1:
        # noinspection PyBroadException
        try:
            message_count = pb.get_message_count()
        except Exception as e:
            nb_print(e)
            message_count = -1
        if message_count == 0:
            no_task_time += 30
        else:
            no_task_time = 0
        time.sleep(30)
        if no_task_time > minutes * 60:
            break
    if send_stop_to_broker:
        pb.publish({'stop': 1})
    pb.close()


class DistributedConsumerStatistics(RedisMixin, LoggerMixinDefaultWithFileHandler):
    """
    为了兼容模拟mq的中间件（例如redis，他没有实现amqp协议，redis的list结构和真mq差远了），获取一个队列有几个连接活跃消费者数量。
    分布式环境中的消费者统计。主要目的有两点

    1、统计活跃消费者数量用于分布式控频。
        获取分布式的消费者数量后，用于分布式qps控频。如果不获取全环境中的消费者数量，则只能用于当前进程中的消费控频。
        即使只有一台机器，例如把xx.py启动3次，xx.py的consumer设置qps为10，如果不使用分布式控频，会1秒钟最终运行30次函数而不是10次。

    2、记录分布式环境中的活跃消费者的所有消费者 id，如果消费者id不在此里面说明已掉线或关闭，消息可以重新分发，用于不支持服务端天然消费确认的中间件。
    """

    def __init__(self, queue_name: str, consumer_identification: str):
        self._consumer_identification = consumer_identification
        self._queue_name = queue_name
        self._redis_key_name = f'hearbeat:{queue_name}'
        self.active_consumer_num = 1
        self._last_show_consumer_num_timestamp = 0

    def run(self):
        self.send_heartbeat()
        decorators.keep_circulating(10, block=False)(self.send_heartbeat)()
        decorators.keep_circulating(5, block=False)(self._show_active_consumer_num)()

    def send_heartbeat(self):
        results = self.redis_db_frame.smembers(self._redis_key_name)
        with self.redis_db_frame.pipeline() as p:
            for result in results:
                if time.time() - float(result.decode().split('&&')[-1]) > 15 or \
                        self._consumer_identification == result.decode().split('&&')[0]:
                    p.srem(self._redis_key_name, result)
            p.sadd(self._redis_key_name, f'{self._consumer_identification}&&{time.time()}')
            p.execute()

    def _show_active_consumer_num(self):
        self.active_consumer_num = self.redis_db_frame.scard(self._redis_key_name) or 1
        if time.time() - self._last_show_consumer_num_timestamp > 60:
            self.logger.info(f'分布式所有环境中使用 {self._queue_name} 队列的，一共有 {self.active_consumer_num} 个消费者')
            self._last_show_consumer_num_timestamp = time.time()

    def get_queue_heartbeat_ids(self, without_time: bool):
        if without_time:
            return [idx.decode().split('&&')[0] for idx in self.redis_db_frame.smembers(self._redis_key_name)]
        else:
            return [idx.decode() for idx in self.redis_db_frame.smembers(self._redis_key_name)]

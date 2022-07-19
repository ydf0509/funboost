# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:11
"""
所有中间件类型消费者的抽象基类。使实现不同中间件的消费者尽可能代码少。
整个流程最难的都在这里面。因为要实现多种并发模型，和对函数施加20运行种控制方式，所以代码非常长。
"""
import typing
import abc
import copy
from pathlib import Path
# from multiprocessing import Process
import datetime
# noinspection PyUnresolvedReferences,PyPackageRequirements
import pytz
import json
import logging
import sys
import atexit
import socket
import os
import uuid
import time
import traceback
# from collections import Callable
from typing import Callable
from functools import wraps
import threading
from threading import Lock, Thread
import eventlet
import gevent
import asyncio

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor as ApschedulerThreadPoolExecutor
from apscheduler.events import EVENT_JOB_MISSED

from funboost.concurrent_pool.single_thread_executor import SoloExecutor
from funboost.helpers import FunctionResultStatusPersistanceConfig
from funboost.utils.apscheduler_monkey import patch_run_job as patch_apscheduler_run_job

import pymongo
from pymongo import IndexModel
from pymongo.errors import PyMongoError

# noinspection PyUnresolvedReferences
from nb_log import get_logger, LoggerLevelSetterMixin, LogManager, nb_print, LoggerMixin, \
    LoggerMixinDefaultWithFileHandler, stdout_write, stderr_write, is_main_process, \
    only_print_on_main_process, nb_log_config_default
# noinspection PyUnresolvedReferences
from funboost.concurrent_pool.async_helper import simple_run_in_executor
from funboost.concurrent_pool.async_pool_executor import AsyncPoolExecutor
# noinspection PyUnresolvedReferences
from funboost.concurrent_pool.bounded_threadpoolexcutor import \
    BoundedThreadPoolExecutor
from funboost.concurrent_pool.custom_evenlet_pool_executor import evenlet_timeout_deco, \
    check_evenlet_monkey_patch, CustomEventletPoolExecutor
from funboost.concurrent_pool.custom_gevent_pool_executor import gevent_timeout_deco, \
    GeventPoolExecutor, check_gevent_monkey_patch
from funboost.concurrent_pool.custom_threadpool_executor import \
    CustomThreadPoolExecutor, check_not_monkey
# from funboost.concurrent_pool.concurrent_pool_with_multi_process import ConcurrentPoolWithProcess
from funboost.consumers.redis_filter import RedisFilter, RedisImpermanencyFilter
from funboost.factories.publisher_factotry import get_publisher
from funboost.utils import decorators, time_util, RedisMixin, un_strict_json_dumps
# noinspection PyUnresolvedReferences
from funboost.utils.bulk_operation import MongoBulkWriteHelper, InsertOne
from funboost.utils.mongo_util import MongoMixin
from funboost import funboost_config_deafult
# noinspection PyUnresolvedReferences
from funboost.constant import ConcurrentModeEnum, BrokerEnum

patch_apscheduler_run_job()


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
    """为了重试的，抛出错误。只是定义了一个子类，用不用都可以，函数出任何类型错误了框架都会自动重试"""


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

    def __init__(self, queue_name: str, fucntion_name: str, msg_dict: dict):
        # print(params)
        self.queue_name = queue_name
        self.function = fucntion_name
        self.msg_dict = msg_dict
        self.task_id = self.msg_dict.get('extra', {}).get('task_id', '')
        self.process_id = os.getpid()
        self.thread_id = threading.get_ident()
        self.publish_time = publish_time = _get_publish_time(msg_dict)
        if publish_time:
            self.publish_time_str = time_util.DatetimeConverter(publish_time).datetime_str
        function_params = _delete_keys_and_return_new_dict(msg_dict, )
        self.params = function_params
        self.params_str = json.dumps(function_params, ensure_ascii=False)
        self.result = None
        self.run_times = 0
        self.exception = None
        self.time_start = time.time()
        self.time_cost = None
        self.time_end = None
        self.success = False
        self.total_thread = threading.active_count()
        self.has_requeue = False
        self.set_log_level(20)

    def get_status_dict(self, without_datetime_obj=False):
        self.time_end = time.time()
        self.time_cost = round(self.time_end - self.time_start, 3)
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
        # kw['body']['extra']['task_id']
        # item['_id'] = self.task_id.split(':')[-1] or str(uuid.uuid4())
        item['_id'] = self.task_id or str(uuid.uuid4())
        # self.logger.warning(item['_id'])
        # self.logger.warning(item)
        return item


class ResultPersistenceHelper(MongoMixin, LoggerMixin):
    def __init__(self, function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig, queue_name):
        self.function_result_status_persistance_conf = function_result_status_persistance_conf
        self._bulk_list = []
        self._bulk_list_lock = Lock()
        self._last_bulk_insert_time = 0
        if self.function_result_status_persistance_conf.is_save_status:
            task_status_col = self.mongo_db_task_status.get_collection(queue_name)
            try:
                # params_str 如果很长，必须使用TEXt或HASHED索引。
                task_status_col.create_indexes([IndexModel([("insert_time_str", -1)]), IndexModel([("insert_time", -1)]),
                                                IndexModel([("params_str", pymongo.TEXT)]), IndexModel([("success", 1)])
                                                ], )
                task_status_col.create_index([("utime", 1)],
                                             expireAfterSeconds=function_result_status_persistance_conf.expire_seconds)  # 只保留7天(用户自定义的)。
            except pymongo.errors.OperationFailure as e:  # 新的mongo服务端，每次启动重复创建已存在索引会报错，try一下。
                self.logger.warning(e)
            # self._mongo_bulk_write_helper = MongoBulkWriteHelper(task_status_col, 100, 2)
            self.task_status_col = task_status_col
            self.logger.info(f"函数运行状态结果将保存至mongo的 task_status 库的 {queue_name} 集合中，请确认 funboost.py文件中配置的 MONGO_CONNECT_URL")

    def save_function_result_to_mongo(self, function_result_status: FunctionResultStatus):
        if self.function_result_status_persistance_conf.is_save_status:
            item = function_result_status.get_status_dict()
            item2 = copy.copy(item)
            if not self.function_result_status_persistance_conf.is_save_result:
                item2['result'] = '不保存结果'
            if item2['result'] is None:
                item2['result'] = ''
            if item2['exception'] is None:
                item2['exception'] = ''
            if self.function_result_status_persistance_conf.is_use_bulk_insert:
                # self._mongo_bulk_write_helper.add_task(InsertOne(item2))  # 自动离散批量聚合方式。
                with self._bulk_list_lock:
                    self._bulk_list.append(InsertOne(item2))
                    if time.time() - self._last_bulk_insert_time > 0.5:
                        self.task_status_col.bulk_write(self._bulk_list, ordered=False)
                        self._bulk_list.clear()
                        self._last_bulk_insert_time = time.time()
            else:
                self.task_status_col.insert_one(item2)  # 立即实时插入。


class ConsumersManager:
    schedulal_thread_to_be_join = []
    consumers_queue__info_map = dict()
    consumers_queue__consumer_obj_map = dict()
    global_concurrent_mode = None
    schedual_task_always_use_thread = False
    _has_show_conusmers_info = False

    @classmethod
    def join_all_consumer_shedual_task_thread(cls):
        """实现这个主要是为了兼容linux和win，在开启多进程时候兼容。在linux下如果子进程中即使有在一个非守护线程里面运行while 1的逻辑，代码也会很快结束。所以必须把所有循环拉取消息的线程join
        否则如果只是为了兼容win，压根不需要这里多此一举
        """
        # nb_print((cls.schedulal_thread_to_be_join, len(cls.schedulal_thread_to_be_join), '模式：', cls.global_concurrent_mode))
        if cls.schedual_task_always_use_thread:
            for t in cls.schedulal_thread_to_be_join:
                nb_print(t)
                t.join()
        else:
            if cls.global_concurrent_mode in [ConcurrentModeEnum.THREADING, ConcurrentModeEnum.ASYNC, ]:
                for t in cls.schedulal_thread_to_be_join:
                    # nb_print(t)
                    t.join()
            elif cls.global_concurrent_mode == ConcurrentModeEnum.GEVENT:
                # cls.logger.info()
                # nb_print(cls.schedulal_thread_to_be_join)
                gevent.joinall(cls.schedulal_thread_to_be_join, raise_error=True, )
            elif cls.global_concurrent_mode == ConcurrentModeEnum.EVENTLET:
                for g in cls.schedulal_thread_to_be_join:
                    # eventlet.greenthread.GreenThread.
                    # nb_print(g)
                    g.wait()

    @classmethod
    def show_all_consumer_info(cls):
        # nb_print(f'当前解释器内，所有消费者的信息是：\n  {cls.consumers_queue__info_map}')
        # if only_print_on_main_process(f'当前解释器内，所有消费者的信息是：\n  {json.dumps(cls.consumers_queue__info_map, indent=4, ensure_ascii=False)}'):
        if not cls._has_show_conusmers_info:
            for _, consumer_info in cls.consumers_queue__info_map.items():
                stdout_write(f'{time.strftime("%H:%M:%S")} "{consumer_info["where_to_instantiate"]}" '
                             f' \033[0;30;44m{consumer_info["queue_name"]} 的消费者\033[0m\n')
        cls._has_show_conusmers_info = True

    @staticmethod
    def get_concurrent_name_by_concurrent_mode(concurrent_mode):
        if concurrent_mode == ConcurrentModeEnum.THREADING:
            return 'thread'
        elif concurrent_mode == ConcurrentModeEnum.GEVENT:
            return 'gevent'
        elif concurrent_mode == ConcurrentModeEnum.EVENTLET:
            return 'evenlet'
        elif concurrent_mode == ConcurrentModeEnum.ASYNC:
            return 'async'
        elif concurrent_mode == ConcurrentModeEnum.SINGLE_THREAD:
            return 'single_thread'
        # elif concurrent_mode == ConcurrentModeEnum.LINUX_FORK:
        #     return 'linux_fork'


# noinspection DuplicatedCode
class AbstractConsumer(LoggerLevelSetterMixin, metaclass=abc.ABCMeta, ):
    time_interval_for_check_do_not_run_time = 60
    BROKER_KIND = None
    BROKER_EXCLUSIVE_CONFIG_KEYS = []  # 中间件能支持的独自的配置参数，例如kafka支持消费者组， 从最早还是最晚消费。因为支持30种中间件，

    # 每种中间件的概念有所不同，用户可以从 broker_exclusive_config 中传递该种中间件特有的配置意义参数。

    @property
    @decorators.synchronized
    def publisher_of_same_queue(self):
        if not self._publisher_of_same_queue:
            self._publisher_of_same_queue = get_publisher(self._queue_name, consuming_function=self.consuming_function,
                                                          broker_kind=self.BROKER_KIND, log_level_int=self._log_level,
                                                          is_add_file_handler=self._create_logger_file, broker_exclusive_config=self.broker_exclusive_config)
            if self._msg_expire_senconds:
                self._publisher_of_same_queue.set_is_add_publish_time()
        return self._publisher_of_same_queue

    def bulid_a_new_publisher_of_same_queue(self):
        return get_publisher(self._queue_name, consuming_function=self.consuming_function,
                             broker_kind=self.BROKER_KIND, log_level_int=self._log_level,
                             is_add_file_handler=self._create_logger_file, broker_exclusive_config=self.broker_exclusive_config)

    @classmethod
    def join_shedual_task_thread(cls):
        """

        :return:
        """
        ConsumersManager.join_all_consumer_shedual_task_thread()

    # noinspection PyProtectedMember,PyUnresolvedReferences
    def __init__(self, queue_name, *, consuming_function: Callable = None,
                 consumin_function_decorator: typing.Callable = None, function_timeout=0, concurrent_num=50,
                 specify_concurrent_pool=None, specify_async_loop=None, concurrent_mode=ConcurrentModeEnum.THREADING,
                 max_retry_times=3, log_level=10, is_print_detail_exception=True, is_show_message_get_from_broker=False,
                 qps: float = 0, is_using_distributed_frequency_control=False,
                 msg_expire_senconds=0, is_send_consumer_hearbeat_to_redis=False,
                 logger_prefix='', create_logger_file=True, do_task_filtering=False,
                 task_filtering_expire_seconds=0,
                 is_do_not_run_by_specify_time_effect=False,
                 do_not_run_by_specify_time=('10:00:00', '22:00:00'),
                 schedule_tasks_on_main_thread=False,
                 function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
                     False, False, 7 * 24 * 3600),
                 user_custom_record_process_info_func: typing.Callable = None,
                 is_using_rpc_mode=False,
                 broker_exclusive_config: dict = None,
                 ):

        """
        :param queue_name:
        :param consuming_function: 处理消息的函数。
        :param consumin_function_decorator : 函数的装饰器。因为此框架做参数自动转指点，需要获取精准的入参名称，不支持在消费函数上叠加 @ *args  **kwargs的装饰器，如果想用装饰器可以这里指定。
        :param function_timeout : 超时秒数，函数运行超过这个时间，则自动杀死函数。为0是不限制。
         # 如果设置了qps，并且cocurrent_num是默认的50，会自动开了500并发，由于是采用的智能线程池任务少时候不会真开那么多线程而且会自动缩小线程数量。具体看ThreadPoolExecutorShrinkAble的说明
         # 由于有很好用的qps控制运行频率和智能扩大缩小的线程池，此框架建议不需要理会和设置并发数量只需要关心qps就行了，框架的并发是自适应并发数量，这一点很强很好用。
        :param concurrent_num:并发数量，并发种类由concurrent_mode决定
        :param specify_concurrent_pool:使用指定的线程池/携程池，可以多个消费者共使用一个线程池，不为None时候。threads_num失效
        :param specify_async_loop:指定的async的loop循环，设置并发模式为async才能起作用。
        :param concurrent_mode:并发模式，1线程(ConcurrentModeEnum.THREADING) 2gevent(ConcurrentModeEnum.GEVENT)
                              3eventlet(ConcurrentModeEnum.EVENTLET) 4 asyncio(ConcurrentModeEnum.ASYNC) 5单线程(ConcurrentModeEnum.SINGLE_THREAD)
        :param max_retry_times:
        :param log_level: # 这里是设置消费者 发布者日志级别的，如果不想看到很多的细节显示信息，可以设置为 20 (logging.INFO)。
        :param is_print_detail_exception:函数出错时候时候显示详细的错误堆栈，占用屏幕太多
        :param is_show_message_get_from_broker: 从中间件取出消息时候时候打印显示出来
        :param qps:指定1秒内的函数执行次数，例如可以是小数0.01代表每100秒执行一次，也可以是50代表1秒执行50次.为0则不控频。
        :param is_using_distributed_frequency_control: 是否使用分布式空频（依赖redis统计消费者数量，然后频率平分），默认只对当前实例化的消费者空频有效。
            假如实例化了2个qps为10的使用同一队列名的消费者，并且都启动，则每秒运行次数会达到20。如果使用分布式空频则所有消费者加起来的总运行次数是10。
        :param is_send_consumer_hearbeat_to_redis   时候将发布者的心跳发送到redis，有些功能的实现需要统计活跃消费者。因为有的中间件不是真mq。
        :param logger_prefix: 日志前缀，可使不同的消费者生成不同的日志
        :param create_logger_file : 是否创建文件日志
        :param do_task_filtering :是否执行基于函数参数的任务过滤
        :param task_filtering_expire_seconds:任务过滤的失效期，为0则永久性过滤任务。例如设置过滤过期时间是1800秒 ，
               30分钟前发布过1 + 2 的任务，现在仍然执行，
               如果是30分钟以内发布过这个任务，则不执行1 + 2，现在把这个逻辑集成到框架，一般用于接口价格缓存。
        :param is_do_not_run_by_specify_time_effect :是否使不运行的时间段生效
        :param do_not_run_by_specify_time   :不运行的时间段
        :param schedule_tasks_on_main_thread :直接在主线程调度任务，意味着不能直接在当前主线程同时开启两个消费者。
        :param function_result_status_persistance_conf   :配置。是否保存函数的入参，运行结果和运行状态到mongodb。
               这一步用于后续的参数追溯，任务统计和web展示，需要安装mongo。
        :param user_custom_record_process_info_func  提供一个用户自定义的保存消息处理记录到某个地方例如mysql数据库的函数，函数仅仅接受一个入参，入参类型是 FunctionResultStatus，用户可以打印参数
        :param is_using_rpc_mode 是否使用rpc模式，可以在发布端获取消费端的结果回调，但消耗一定性能，使用async_result.result时候会等待阻塞住当前线程。
        :param broker_exclusive_config 加上一个不同种类中间件非通用的配置,不同中间件自身独有的配置，不是所有中间件都兼容的配置，因为框架支持30种消息队列，消息队列不仅仅是一般的先进先出queue这么简单的概念，
            例如kafka支持消费者组，rabbitmq也支持各种独特概念例如各种ack机制 复杂路由机制，每一种消息队列都有独特的配置参数意义，可以通过这里传递。

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
        ConsumersManager.consumers_queue__consumer_obj_map[queue_name] = self
        current_queue__info_dict['consuming_function'] = str(consuming_function)  # consuming_function.__name__
        current_queue__info_dict['specify_async_loop'] = str(specify_async_loop)
        current_queue__info_dict[
            'function_result_status_persistance_conf'] = function_result_status_persistance_conf.to_dict()
        current_queue__info_dict['class_name'] = self.__class__.__name__
        concurrent_name = ConsumersManager.get_concurrent_name_by_concurrent_mode(concurrent_mode)
        current_queue__info_dict['concurrent_mode_name'] = concurrent_name

        # 方便点击跳转定位到当前解释器下所有实例化消费者的文件行，点击可跳转到该处。
        # 获取被调用函数在被调用时所处代码行数
        # 直接实例化相应的类和使用工厂模式来实例化相应的类，得到的消费者实际实例化的行是不一样的，希望定位到用户的代码处，而不是定位到工厂模式处。也不要是boost装饰器本身处。
        line = sys._getframe(0).f_back.f_lineno
        # 获取被调用函数所在模块文件名
        file_name = sys._getframe(1).f_code.co_filename
        if 'consumer_factory.py' in file_name:
            line = sys._getframe(1).f_back.f_lineno
            file_name = sys._getframe(2).f_code.co_filename
        if r'funboost\__init__.py' in file_name or 'funboost/__init__.py' in file_name:
            line = sys._getframe(2).f_back.f_lineno
            file_name = sys._getframe(3).f_code.co_filename
        if r'funboost\helpers.py' in file_name or 'funboost/helpers.py' in file_name:
            line = sys._getframe(3).f_back.f_lineno
            file_name = sys._getframe(4).f_code.co_filename
        current_queue__info_dict['where_to_instantiate'] = f'{file_name}:{line}'

        self._queue_name = queue_name
        self.queue_name = queue_name  # 可以换成公有的，免得外部访问有警告。
        if consuming_function is None:
            raise ValueError('必须传 consuming_function 参数')
        self.consuming_function = consuming_function
        self._consumin_function_decorator = consumin_function_decorator
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
        self._is_show_message_get_from_broker = is_show_message_get_from_broker

        self._qps = qps
        self._msg_schedule_time_intercal = 0 if qps == 0 else 1.0 / qps

        self._is_using_distributed_frequency_control = is_using_distributed_frequency_control
        self._is_send_consumer_hearbeat_to_redis = is_send_consumer_hearbeat_to_redis or is_using_distributed_frequency_control
        self._msg_expire_senconds = msg_expire_senconds

        if self._concurrent_mode not in (1, 2, 3, 4, 5, 6):
            raise ValueError('设置的并发模式不正确')
        self._concurrent_mode_dispatcher = ConcurrentModeDispatcher(self)
        if self._concurrent_mode == ConcurrentModeEnum.ASYNC:
            self._run = self._async_run  # 这里做了自动转化，使用async_run代替run

        self._logger_prefix = logger_prefix
        self._log_level = log_level
        if logger_prefix != '':
            logger_prefix += '--'
        # logger_name = f'{logger_prefix}{self.__class__.__name__}--{concurrent_name}--{queue_name}--{self.consuming_function.__name__}'
        logger_name = f'{logger_prefix}{self.__class__.__name__}--{queue_name}'
        # nb_print(logger_name)
        self._create_logger_file = create_logger_file
        self._log_level = log_level
        log_file_handler_type = 1
        if int(os.getenv('is_fsdf_remote_run', 0)) == 1:  # 这个是远程部署的自动的环境变量，用户不需要亲自自己设置这个值。
            log_file_handler_type = 5  # 如果是fabric_deploy 自动化远程部署函数时候，python -c 启动的使用第一个filehandler没记录文件，现在使用第5种filehandler。
        self.logger = get_logger(logger_name, log_level_int=log_level, log_filename=f'{logger_name}.log' if create_logger_file else None,
                                 # log_file_handler_type=log_file_handler_type,
                                 formatter_template=funboost_config_deafult.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER, )
        # self.logger.info(f'{self.__class__} 在 {current_queue__info_dict["where_to_instantiate"]}  被实例化')

        stdout_write(f'{time.strftime("%H:%M:%S")} "{current_queue__info_dict["where_to_instantiate"]}"  \033[0;37;44m此行 '
                     f'实例化队列名 {current_queue__info_dict["queue_name"]} 的消费者, 类型为 {self.__class__}\033[0m\n')
        # only_print_on_main_process(f'{current_queue__info_dict["queue_name"]} 的消费者配置:\n', un_strict_json_dumps.dict2json(current_queue__info_dict))
        if is_main_process:
            self.logger.debug(f'{current_queue__info_dict["queue_name"]} 的消费者配置:\n {un_strict_json_dumps.dict2json(current_queue__info_dict)}')

        self._do_task_filtering = do_task_filtering
        self._redis_filter_key_name = f'filter_zset:{queue_name}' if task_filtering_expire_seconds else f'filter_set:{queue_name}'
        filter_class = RedisFilter if task_filtering_expire_seconds == 0 else RedisImpermanencyFilter
        self._redis_filter = filter_class(self._redis_filter_key_name, task_filtering_expire_seconds)

        self._unit_time_for_count = 10  # 每隔多少秒计数，显示单位时间内执行多少次，暂时固定为10秒。
        self._execute_task_times_every_unit_time = 0  # 每单位时间执行了多少次任务。
        self._lock_for_count_execute_task_times_every_unit_time = Lock()
        self._current_time_for_execute_task_times_every_unit_time = time.time()
        self._consuming_function_cost_time_total_every_unit_time = 0
        self._last_execute_task_time = time.time()  # 最近一次执行任务的时间。

        self._msg_num_in_broker = 0
        self._last_timestamp_when_has_task_in_queue = 0
        self._last_timestamp_print_msg_num = 0

        self._is_do_not_run_by_specify_time_effect = is_do_not_run_by_specify_time_effect
        self._do_not_run_by_specify_time = do_not_run_by_specify_time  # 可以设置在指定的时间段不运行。
        self._schedule_tasks_on_main_thread = schedule_tasks_on_main_thread

        self._result_persistence_helper = ResultPersistenceHelper(function_result_status_persistance_conf, queue_name)

        self._user_custom_record_process_info_func = user_custom_record_process_info_func

        self._is_using_rpc_mode = is_using_rpc_mode

        if broker_exclusive_config is None:
            broker_exclusive_config = {}
        self.broker_exclusive_config = broker_exclusive_config

        self._stop_flag = None
        self._pause_flag = None  # 暂停消费标志，从reids读取
        self._last_show_pause_log_time = 0
        self._redis_key_stop_flag = f'funboost_stop_flag:{self.queue_name}'
        self._redis_key_pause_flag = f'funboost_pause_flag:{self.queue_name}'

        # 控频要用到的成员变量
        self._last_submit_task_timestamp = 0
        self._last_start_count_qps_timestamp = time.time()
        self._has_execute_times_in_recent_second = 0

        self._publisher_of_same_queue = None

        self.consumer_identification = f'{nb_log_config_default.computer_name}_{nb_log_config_default.computer_ip}_' \
                                       f'{time_util.DatetimeConverter().datetime_str.replace(":", "-")}_{os.getpid()}_{id(self)}'
        self.consumer_identification_map = {'queue_name': self.queue_name,
                                            'computer_name': nb_log_config_default.computer_name,
                                            'computer_ip': nb_log_config_default.computer_ip,
                                            'process_id': os.getpid(),
                                            'consumer_id': id(self),
                                            'consumer_uuid': str(uuid.uuid4()),
                                            'start_datetime_str': time_util.DatetimeConverter().datetime_str,
                                            'start_timestamp': time.time(),
                                            'hearbeat_datetime_str': time_util.DatetimeConverter().datetime_str,
                                            'hearbeat_timestamp': time.time(),
                                            'consuming_function': self.consuming_function.__name__,
                                            'code_filename': Path(self.consuming_function.__code__.co_filename).as_posix()
                                            }

        self._delay_task_scheduler = BackgroundScheduler(timezone=funboost_config_deafult.TIMEZONE)
        self._delay_task_scheduler.add_executor(ApschedulerThreadPoolExecutor(2))  # 只是运行submit任务到并发池，不需要很多线程。
        self._delay_task_scheduler.add_listener(self._apscheduler_job_miss, EVENT_JOB_MISSED)
        self._delay_task_scheduler.start()

        self._check_broker_exclusive_config()

        self.custom_init()

        atexit.register(self.join_shedual_task_thread)

    def _check_broker_exclusive_config(self):
        if self.broker_exclusive_config:
            if set(self.broker_exclusive_config.keys()).issubset(self.BROKER_EXCLUSIVE_CONFIG_KEYS):
                self.logger.info(f'当前消息队列中间件能支持特殊独有配置 {self.broker_exclusive_config.keys()}')
            else:
                self.logger.warning(f'当前消息队列中间件含有不支持的特殊配置 {self.broker_exclusive_config.keys()}，能支持的特殊独有配置包括 {self.BROKER_EXCLUSIVE_CONFIG_KEYS}')

    def _check_monkey_patch(self):
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
                        if self._stop_flag == 1:
                            break
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
        # noinspection PyBroadException
        try:
            self._concurrent_mode_dispatcher.check_all_concurrent_mode()
            self._check_monkey_patch()
        except Exception:
            traceback.print_exc()
            os._exit(4444)  # noqa
        self.logger.warning(f'开始消费 {self._queue_name} 中的消息')

        self._distributed_consumer_statistics = DistributedConsumerStatistics(self)
        if self._is_send_consumer_hearbeat_to_redis:
            self._distributed_consumer_statistics.run()
            self.logger.warning(f'启动了分布式环境 使用 redis 的键 hearbeat:{self._queue_name} 统计活跃消费者 ，当前消费者唯一标识为 {self.consumer_identification}')

        self.keep_circulating(10, block=False)(self.check_heartbeat_and_message_count)()  # 间隔时间最好比self._unit_time_for_count小整数倍，不然日志不准。
        if self._do_task_filtering:
            self._redis_filter.delete_expire_filter_task_cycle()  # 这个默认是RedisFilter类，是个pass不运行。所以用别的消息中间件模式，不需要安装和配置redis。
        if self._schedule_tasks_on_main_thread:
            self.keep_circulating(1)(self._shedual_task)()
        else:
            self._concurrent_mode_dispatcher.schedulal_task_with_no_block()
        setattr(funboost_config_deafult, 'has_start_a_consumer_flag', 1)

    @abc.abstractmethod
    def _shedual_task(self):
        """
        每个子类必须实现这个的方法，完成如何从中间件取出消息，并将函数和运行参数添加到工作池。
        :return:
        """
        raise NotImplementedError

    def _print_message_get_from_broker(self, broker_name, msg):
        if isinstance(msg, (dict, list)):
            msg = json.dumps(msg, ensure_ascii=False)
        # print(999)
        if self._is_show_message_get_from_broker:
            self.logger.debug(f'从 {broker_name} 中间件 的 {self._queue_name} 中取出的消息是 {msg}')

    def _get_priority_conf(self, kw: dict, broker_task_config_key: str):
        broker_task_config = kw['body'].get('extra', {}).get(broker_task_config_key, None)
        if broker_task_config is None:
            return getattr(self, f'_{broker_task_config_key}', None)
        else:
            return broker_task_config

    # noinspection PyMethodMayBeStatic
    def _get_concurrent_info(self):
        concurrent_info = ''
        '''  影响了日志长度和一丝丝性能。
        if self._concurrent_mode == 1:
            concurrent_info = f'[{threading.current_thread()}  {threading.active_count()}]'
        elif self._concurrent_mode == 2:
            concurrent_info = f'[{gevent.getcurrent()}  {threading.active_count()}]'
        elif self._concurrent_mode == 3:
            # noinspection PyArgumentList
            concurrent_info = f'[{eventlet.getcurrent()}  {threading.active_count()}]'
        '''
        return concurrent_info

    def _run(self, kw: dict, ):
        # print(kw)
        t_start_run_fun = time.time()
        max_retry_times = self._get_priority_conf(kw, 'max_retry_times')
        current_function_result_status = FunctionResultStatus(self.queue_name, self.consuming_function.__name__, kw['body'], )
        current_retry_times = 0
        function_only_params = _delete_keys_and_return_new_dict(kw['body'])
        for current_retry_times in range(max_retry_times + 1):
            current_function_result_status = self._run_consuming_function_with_confirm_and_retry(kw, current_retry_times=current_retry_times,
                                                                                                 function_result_status=FunctionResultStatus(
                                                                                                     self.queue_name, self.consuming_function.__name__,
                                                                                                     kw['body']),
                                                                                                 )
            if current_function_result_status.success is True or current_retry_times == max_retry_times or current_function_result_status.has_requeue:
                break

        self._result_persistence_helper.save_function_result_to_mongo(current_function_result_status)
        self._confirm_consume(kw)
        if self._get_priority_conf(kw, 'do_task_filtering'):
            self._redis_filter.add_a_value(function_only_params)  # 函数执行成功后，添加函数的参数排序后的键值对字符串到set中。
        if current_function_result_status.success is False and current_retry_times == max_retry_times:
            self.logger.critical(
                f'函数 {self.consuming_function.__name__} 达到最大重试次数 {self._get_priority_conf(kw, "max_retry_times")} 后,仍然失败， 入参是  {function_only_params} ')
        if self._get_priority_conf(kw, 'is_using_rpc_mode'):
            # print(function_result_status.get_status_dict(without_datetime_obj=
            with RedisMixin().redis_db_filter_and_rpc_result.pipeline() as p:
                # RedisMixin().redis_db_frame.lpush(kw['body']['extra']['task_id'], json.dumps(function_result_status.get_status_dict(without_datetime_obj=True)))
                # RedisMixin().redis_db_frame.expire(kw['body']['extra']['task_id'], 600)
                p.lpush(kw['body']['extra']['task_id'],
                        json.dumps(current_function_result_status.get_status_dict(without_datetime_obj=True)))
                p.expire(kw['body']['extra']['task_id'], 600)
                p.execute()

        with self._lock_for_count_execute_task_times_every_unit_time:
            self._execute_task_times_every_unit_time += 1
            self._consuming_function_cost_time_total_every_unit_time += time.time() - t_start_run_fun
            self._last_execute_task_time = time.time()
            if time.time() - self._current_time_for_execute_task_times_every_unit_time > self._unit_time_for_count:
                avarage_function_spend_time = round(self._consuming_function_cost_time_total_every_unit_time / self._execute_task_times_every_unit_time, 4)
                msg = f'{self._unit_time_for_count} 秒内执行了 {self._execute_task_times_every_unit_time} 次函数 [ {self.consuming_function.__name__} ] ,' \
                      f'函数平均运行耗时 {avarage_function_spend_time} 秒'
                if self._msg_num_in_broker != -1:  # 有的中间件无法统计或没实现统计队列剩余数量的，统一返回的是-1，不显示这句话。
                    # msg += f''' ，预计还需要 {time_util.seconds_to_hour_minute_second(self._msg_num_in_broker * avarage_function_spend_time / active_consumer_num)} 时间 才能执行完成 {self._msg_num_in_broker}个剩余的任务'''
                    need_time = time_util.seconds_to_hour_minute_second(self._msg_num_in_broker / (self._execute_task_times_every_unit_time / self._unit_time_for_count) /
                                                                        self._distributed_consumer_statistics.active_consumer_num)
                    msg += f''' ，预计还需要 {need_time}''' + \
                           f''' 时间 才能执行完成 {self._msg_num_in_broker}个剩余的任务'''
                self.logger.info(msg)
                self._current_time_for_execute_task_times_every_unit_time = time.time()
                self._consuming_function_cost_time_total_every_unit_time = 0
                self._execute_task_times_every_unit_time = 0
        if self._user_custom_record_process_info_func:
            self._user_custom_record_process_info_func(current_function_result_status)

    def _run_consuming_function_with_confirm_and_retry(self, kw: dict, current_retry_times,
                                                       function_result_status: FunctionResultStatus, ):
        function_only_params = _delete_keys_and_return_new_dict(kw['body'])
        t_start = time.time()
        function_result_status.run_times = current_retry_times + 1
        try:
            function_timeout = self._get_priority_conf(kw, 'function_timeout')
            function_run0 = self.consuming_function if self._consumin_function_decorator is None else self._consumin_function_decorator(self.consuming_function)
            function_run = function_run0 if not function_timeout else self._concurrent_mode_dispatcher.timeout_deco(
                function_timeout)(function_run0)
            function_result_status.result = function_run(**function_only_params)
            if asyncio.iscoroutine(function_result_status.result):
                self.logger.critical(f'异步的协程消费函数必须使用 async 并发模式并发,请设置 '
                                     f'消费函数 {self.consuming_function.__name__} 的concurrent_mode 为 ConcurrentModeEnum.ASYNC 或 4')
                # noinspection PyProtectedMember,PyUnresolvedReferences
                os._exit(4)
            function_result_status.success = True
            if self._log_level <= logging.DEBUG:
                result_str_to_be_print = str(function_result_status.result)[:100] if len(str(function_result_status.result)) < 100 else str(function_result_status.result)[:100] + '  。。。。。  '
                self.logger.debug(f' 函数 {self.consuming_function.__name__}  '
                                  f'第{current_retry_times + 1}次 运行, 正确了，函数运行时间是 {round(time.time() - t_start, 4)} 秒,入参是 {function_only_params}  '
                                  f' 结果是  {result_str_to_be_print} ，  {self._get_concurrent_info()}  ')
        except Exception as e:
            if isinstance(e, (PyMongoError,
                              ExceptionForRequeue)):  # mongo经常维护备份时候插入不了或挂了，或者自己主动抛出一个ExceptionForRequeue类型的错误会重新入队，不受指定重试次数逇约束。
                self.logger.critical(f'函数 [{self.consuming_function.__name__}] 中发生错误 {type(e)}  {e}，消息重新入队')
                time.sleep(1)  # 防止快速无限出错入队出队，导致cpu和中间件忙
                self._requeue(kw)
                function_result_status.has_requeue = True
                return function_result_status
            self.logger.error(f'函数 {self.consuming_function.__name__}  第{current_retry_times + 1}次运行发生错误，'
                              f'函数运行时间是 {round(time.time() - t_start, 4)} 秒,\n  入参是  {function_only_params}    \n 原因是 {type(e)} {e} ',
                              exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            # traceback.print_exc()
            function_result_status.exception = f'{e.__class__.__name__}    {str(e)}'
        return function_result_status

    async def _async_run(self, kw: dict, ):
        # """虽然和上面有点大面积重复相似，这个是为了asyncio模式的，asyncio模式真的和普通同步模式的代码思维和形式区别太大，
        # 框架实现兼容async的消费函数很麻烦复杂，连并发池都要单独写"""
        t_start_run_fun = time.time()
        max_retry_times = self._get_priority_conf(kw, 'max_retry_times')
        current_function_result_status = FunctionResultStatus(self.queue_name, self.consuming_function.__name__, kw['body'], )
        current_retry_times = 0
        function_only_params = _delete_keys_and_return_new_dict(kw['body'])
        for current_retry_times in range(max_retry_times + 1):
            current_function_result_status = await self._async_run_consuming_function_with_confirm_and_retry(kw, current_retry_times=current_retry_times,
                                                                                                             function_result_status=FunctionResultStatus(
                                                                                                                 self.queue_name, self.consuming_function.__name__,
                                                                                                                 kw['body'], ),
                                                                                                             )
            if current_function_result_status.success is True or current_retry_times == max_retry_times or current_function_result_status.has_requeue:
                break

        # self._result_persistence_helper.save_function_result_to_mongo(function_result_status)
        await simple_run_in_executor(self._result_persistence_helper.save_function_result_to_mongo, current_function_result_status)
        await simple_run_in_executor(self._confirm_consume, kw)
        if self._get_priority_conf(kw, 'do_task_filtering'):
            # self._redis_filter.add_a_value(function_only_params)  # 函数执行成功后，添加函数的参数排序后的键值对字符串到set中。
            await simple_run_in_executor(self._redis_filter.add_a_value, function_only_params)
        if current_function_result_status.success is False and current_retry_times == max_retry_times:
            self.logger.critical(
                f'函数 {self.consuming_function.__name__} 达到最大重试次数 {self._get_priority_conf(kw, "max_retry_times")} 后,仍然失败， 入参是  {function_only_params} ')
            # self._confirm_consume(kw)  # 错得超过指定的次数了，就确认消费了。

        if self._get_priority_conf(kw, 'is_using_rpc_mode'):
            def push_result():
                with RedisMixin().redis_db_filter_and_rpc_result.pipeline() as p:
                    p.lpush(kw['body']['extra']['task_id'],
                            json.dumps(current_function_result_status.get_status_dict(without_datetime_obj=True)))
                    p.expire(kw['body']['extra']['task_id'], 600)
                    p.execute()

            await simple_run_in_executor(push_result)

        # 异步执行不存在线程并发，不需要加锁。
        self._execute_task_times_every_unit_time += 1
        self._consuming_function_cost_time_total_every_unit_time += time.time() - t_start_run_fun
        self._last_execute_task_time = time.time()
        if time.time() - self._current_time_for_execute_task_times_every_unit_time > self._unit_time_for_count:
            avarage_function_spend_time = round(self._consuming_function_cost_time_total_every_unit_time / self._execute_task_times_every_unit_time, 4)
            msg = f'{self._unit_time_for_count} 秒内执行了 {self._execute_task_times_every_unit_time} 次函数 [ {self.consuming_function.__name__} ] ,' \
                  f'函数平均运行耗时 {avarage_function_spend_time} 秒'
            if self._msg_num_in_broker != -1:
                if self._msg_num_in_broker != -1:  # 有的中间件无法统计或没实现统计队列剩余数量的，统一返回的是-1，不显示这句话。
                    # msg += f''' ，预计还需要 {time_util.seconds_to_hour_minute_second(self._msg_num_in_broker * avarage_function_spend_time / active_consumer_num)} 时间 才能执行完成 {self._msg_num_in_broker}个剩余的任务'''
                    need_time = time_util.seconds_to_hour_minute_second(self._msg_num_in_broker / (self._execute_task_times_every_unit_time / self._unit_time_for_count) /
                                                                        self._distributed_consumer_statistics.active_consumer_num)
                    msg += f''' ，预计还需要 {need_time}''' + \
                           f''' 时间 才能执行完成 {self._msg_num_in_broker}个剩余的任务'''
            self.logger.info(msg)
            self._current_time_for_execute_task_times_every_unit_time = time.time()
            self._consuming_function_cost_time_total_every_unit_time = 0
            self._execute_task_times_every_unit_time = 0
        if self._user_custom_record_process_info_func:
            await self._user_custom_record_process_info_func(current_function_result_status)

    async def _async_run_consuming_function_with_confirm_and_retry(self, kw: dict, current_retry_times,
                                                                   function_result_status: FunctionResultStatus, ):
        """虽然和上面有点大面积重复相似，这个是为了asyncio模式的，asyncio模式真的和普通同步模式的代码思维和形式区别太大，
        框架实现兼容async的消费函数很麻烦复杂，连并发池都要单独写"""
        function_only_params = _delete_keys_and_return_new_dict(kw['body'])
        function_result_status.run_times = current_retry_times + 1
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
                await simple_run_in_executor(self._requeue, kw)
                function_result_status.has_requeue = True
                return function_result_status
            self.logger.error(f'函数 {self.consuming_function.__name__}  第{current_retry_times + 1}次运行发生错误，'
                              f'函数运行时间是 {round(time.time() - t_start, 4)} 秒,\n  入参是  {function_only_params}    \n 原因是 {type(e)} {e} ',
                              exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            function_result_status.exception = f'{e.__class__.__name__}    {str(e)}'
        return function_result_status

    @abc.abstractmethod
    def _confirm_consume(self, kw):
        """确认消费"""
        raise NotImplementedError

    def check_heartbeat_and_message_count(self):
        self._msg_num_in_broker = self.publisher_of_same_queue.get_message_count()
        if time.time() - self._last_timestamp_print_msg_num > 60:
            if self._msg_num_in_broker != -1:
                self.logger.info(f'队列 [{self._queue_name}] 中还有 [{self._msg_num_in_broker}] 个任务')
            self._last_timestamp_print_msg_num = time.time()
        if self._msg_num_in_broker != 0:
            self._last_timestamp_when_has_task_in_queue = time.time()
        return self._msg_num_in_broker

    @abc.abstractmethod
    def _requeue(self, kw):
        """重新入队"""
        raise NotImplementedError

    def _apscheduler_job_miss(self, event):
        """
        这是 apscheduler 包的事件钩子。
        ev.function_args = job.args
        ev.function_kwargs = job.kwargs
        ev.function = job.func
        :return:
        """
        # print(event.scheduled_run_time)
        misfire_grace_time = self._get_priority_conf(event.function_kwargs["kw"], 'misfire_grace_time')
        self.logger.critical(f'现在时间是 {time_util.DatetimeConverter().datetime_str} ,'
                             f'比此任务规定的本应该的运行时间 {event.scheduled_run_time} 相比 超过了指定的 {misfire_grace_time} 秒,放弃执行此任务 \n'
                             f'{event.function_kwargs["kw"]["body"]} ')
        self._confirm_consume(event.function_kwargs["kw"])

        '''
        if self._get_priority_conf(event.function_kwargs["kw"], 'execute_delay_task_even_if_when_task_is_expired') is False:
            self.logger.critical(f'现在时间是 {time_util.DatetimeConverter().datetime_str} ,此任务设置的延时运行已过期 \n'
                                 f'{event.function_kwargs["kw"]["body"]} ， 此任务放弃执行')
            self._confirm_consume(event.function_kwargs["kw"])
        else:
            self.logger.warning(f'现在时间是 {time_util.DatetimeConverter().datetime_str} ,此任务设置的延时运行已过期 \n'
                                f'{event.function_kwargs["kw"]["body"]} ，'
                                f'但框架为了防止是任务积压导致消费延后，所以仍然使其运行一次')
            event.function(*event.function_args, **event.function_kwargs)
        '''

    def pause_consume(self):
        """设置队列为暂停消费状态"""
        RedisMixin().redis_db_frame.set(self._redis_key_pause_flag, 1)

    def continue_consume(self):
        """设置队列为继续消费状态"""
        RedisMixin().redis_db_frame.set(self._redis_key_pause_flag, 0)

    def _submit_task(self, kw):
        while 1:  # 这一块的代码为支持暂停消费。
            # print(self._pause_flag)
            if self._pause_flag == 1:
                time.sleep(1)
                if time.time() - self._last_show_pause_log_time > 60:
                    self.logger.warning(f'已设置 {self.queue_name} 队列中的任务为暂停消费')
                    self._last_show_pause_log_time = time.time()
            else:
                break

        if self._judge_is_daylight():
            self._requeue(kw)
            time.sleep(self.time_interval_for_check_do_not_run_time)
            return

        function_only_params = _delete_keys_and_return_new_dict(kw['body'], )
        if self._get_priority_conf(kw, 'do_task_filtering') and self._redis_filter.check_value_exists(
                function_only_params):  # 对函数的参数进行检查，过滤已经执行过并且成功的任务。
            self.logger.warning(f'redis的 [{self._redis_filter_key_name}] 键 中 过滤任务 {kw["body"]}')
            self._confirm_consume(kw)
            return
        publish_time = _get_publish_time(kw['body'])
        msg_expire_senconds_priority = self._get_priority_conf(kw, 'msg_expire_senconds')
        if msg_expire_senconds_priority and time.time() - msg_expire_senconds_priority > publish_time:
            self.logger.warning(
                f'消息发布时戳是 {publish_time} {kw["body"].get("publish_time_format", "")},距离现在 {round(time.time() - publish_time, 4)} 秒 ,'
                f'超过了指定的 {msg_expire_senconds_priority} 秒，丢弃任务')
            self._confirm_consume(kw)
            return 0

        msg_eta = self._get_priority_conf(kw, 'eta')
        msg_countdown = self._get_priority_conf(kw, 'countdown')
        misfire_grace_time = self._get_priority_conf(kw, 'misfire_grace_time')
        run_date = None
        # print(kw)
        if msg_countdown:
            run_date = time_util.DatetimeConverter(kw['body']['extra']['publish_time']).datetime_obj + datetime.timedelta(seconds=msg_countdown)
        if msg_eta:
            run_date = time_util.DatetimeConverter(msg_eta).datetime_obj
        # print(run_date,time_util.DatetimeConverter().datetime_obj)
        # print(run_date.timestamp(),time_util.DatetimeConverter().datetime_obj.timestamp())
        # print(self.concurrent_pool)
        if run_date:
            # print(repr(run_date),repr(datetime.datetime.now(tz=pytz.timezone(frame_config.TIMEZONE))))
            self._delay_task_scheduler.add_job(self.concurrent_pool.submit, 'date', run_date=run_date, args=(self._run,), kwargs={'kw': kw},
                                               misfire_grace_time=misfire_grace_time)
        else:
            self.concurrent_pool.submit(self._run, kw)

        if self._is_using_distributed_frequency_control:  # 如果是需要分布式控频。
            active_num = self._distributed_consumer_statistics.active_consumer_num
            self._frequency_control(self._qps / active_num, self._msg_schedule_time_intercal * active_num)
        else:
            self._frequency_control(self._qps, self._msg_schedule_time_intercal)

    def _frequency_control(self, qpsx, msg_schedule_time_intercalx):
        # 以下是消费函数qps控制代码。无论是单个消费者空频还是分布式消费控频，都是基于直接计算的，没有依赖redis inrc计数，使得控频性能好。
        if qpsx == 0:  # 不需要控频的时候，就不需要休眠。
            return
        if qpsx <= 5:
            """ 原来的简单版 """
            time.sleep(msg_schedule_time_intercalx)
        elif 5 < qpsx <= 20:
            """ 改进的控频版,防止消息队列中间件网络波动，例如1000qps使用redis,不能每次间隔1毫秒取下一条消息，
            如果取某条消息有消息超过了1毫秒，后面不能匀速间隔1毫秒获取，time.sleep不能休眠一个负数来让时光倒流"""
            time_sleep_for_qps_control = max((msg_schedule_time_intercalx - (time.time() - self._last_submit_task_timestamp)) * 0.99, 10 ** -3)
            # print(time.time() - self._last_submit_task_timestamp)
            # print(time_sleep_for_qps_control)
            time.sleep(time_sleep_for_qps_control)
            self._last_submit_task_timestamp = time.time()
        else:
            """基于当前消费者计数的控频，qps很大时候需要使用这种"""
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

    def wait_for_possible_has_finish_all_tasks(self, minutes: int = 3):
        """
        判断队列所有任务是否消费完成了。
        由于是异步消费，和存在队列一边被消费，一边在推送，或者还有结尾少量任务还在确认消费者实际还没彻底运行完成。  但有时候需要判断 所有任务，务是否完成，提供一个不精确的判断，要搞清楚原因和场景后再慎用。
        一般是和celery一样，是永久运行的后台任务，永远无限死循环去任务执行任务，但有的人有判断是否执行完成的需求。
        :param minutes: 消费者连续多少分钟没执行任务任务 并且 消息队列中间件中没有，就判断为消费完成，为了防止是长耗时任务，一般判断完成是真正提供的minutes的2个周期时间。
        :return:

        """
        if minutes <= 1:
            raise ValueError('疑似完成任务，判断时间最少需要设置为3分钟内,最好是是10分钟')
        no_task_time = 0
        while 1:
            # noinspection PyBroadException
            message_count = self._msg_num_in_broker
            # print(message_count,self._last_execute_task_time,time.time() - self._last_execute_task_time)
            if message_count == 0 and self._last_execute_task_time != 0 and (time.time() - self._last_execute_task_time) > minutes * 60:
                no_task_time += 30
            else:
                no_task_time = 0
            time.sleep(30)
            if no_task_time > minutes * 60:
                break

    def clear_filter_tasks(self):
        RedisMixin().redis_db_frame.delete(self._redis_filter_key_name)
        self.logger.warning(f'清空 {self._redis_filter_key_name} 键的任务过滤')

    def __str__(self):
        return f'队列为 {self.queue_name} 函数为 {self.consuming_function} 的消费者'


# noinspection PyProtectedMember
class ConcurrentModeDispatcher(LoggerMixin):

    def __init__(self, consumerx: AbstractConsumer):
        self.consumer = consumerx
        self._concurrent_mode = self.consumer._concurrent_mode
        self.timeout_deco = None
        if self._concurrent_mode in (ConcurrentModeEnum.THREADING, ConcurrentModeEnum.SINGLE_THREAD):
            self.timeout_deco = decorators.timeout
        elif self._concurrent_mode == ConcurrentModeEnum.GEVENT:
            self.timeout_deco = gevent_timeout_deco
        elif self._concurrent_mode == ConcurrentModeEnum.EVENTLET:
            self.timeout_deco = evenlet_timeout_deco
        self.logger.warning(f'{self.consumer} 设置并发模式'
                            f'为{ConsumersManager.get_concurrent_name_by_concurrent_mode(self._concurrent_mode)}')

    def check_all_concurrent_mode(self):
        if ConsumersManager.global_concurrent_mode is not None and self.consumer._concurrent_mode != ConsumersManager.global_concurrent_mode:
            ConsumersManager.show_all_consumer_info()
            # print({self.consumer._concurrent_mode, ConsumersManager.global_concurrent_mode})
            if not {self.consumer._concurrent_mode, ConsumersManager.global_concurrent_mode}.issubset({ConcurrentModeEnum.THREADING,
                                                                                                       ConcurrentModeEnum.ASYNC,
                                                                                                       ConcurrentModeEnum.SINGLE_THREAD}):
                # threding、asyncio、solo 这几种模式可以共存。但同一个解释器不能同时选择 gevent + 其它并发模式，也不能 eventlet + 其它并发模式。
                raise ValueError('''由于猴子补丁的原因，同一解释器中不可以设置两种并发类型,请查看显示的所有消费者的信息，
                                 搜索 concurrent_mode 关键字，确保当前解释器内的所有消费者的并发模式只有一种(或可以共存),
                                 asyncio threading single_thread 并发模式可以共存，但gevent和threading不可以共存，
                                 gevent和eventlet不可以共存''')

        ConsumersManager.global_concurrent_mode = self.consumer._concurrent_mode

    def build_pool(self):
        if self.consumer._concurrent_pool is not None:
            return self.consumer._concurrent_pool

        pool_type = None  # 是按照ThreadpoolExecutor写的三个鸭子类，公有方法名和功能写成完全一致，可以互相替换。
        if self._concurrent_mode == ConcurrentModeEnum.THREADING:
            pool_type = CustomThreadPoolExecutor
            # pool_type = BoundedThreadPoolExecutor
        elif self._concurrent_mode == ConcurrentModeEnum.GEVENT:
            pool_type = GeventPoolExecutor
        elif self._concurrent_mode == ConcurrentModeEnum.EVENTLET:
            pool_type = CustomEventletPoolExecutor
        elif self._concurrent_mode == ConcurrentModeEnum.ASYNC:
            pool_type = AsyncPoolExecutor
        elif self._concurrent_mode == ConcurrentModeEnum.SINGLE_THREAD:
            pool_type = SoloExecutor
        # elif self._concurrent_mode == ConcurrentModeEnum.LINUX_FORK:
        #     pool_type = SimpleProcessPool
        # pool_type = BoundedProcessPoolExecutor
        # from concurrent.futures import ProcessPoolExecutor
        # pool_type = ProcessPoolExecutor
        if self._concurrent_mode == ConcurrentModeEnum.ASYNC:
            self.consumer._concurrent_pool = self.consumer._specify_concurrent_pool if self.consumer._specify_concurrent_pool is not None else pool_type(
                self.consumer._concurrent_num, loop=self.consumer._specify_async_loop)
        else:
            # print(pool_type)
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
            if self._concurrent_mode in [ConcurrentModeEnum.THREADING, ConcurrentModeEnum.ASYNC,
                                         ConcurrentModeEnum.SINGLE_THREAD, ]:
                t = Thread(target=self.consumer.keep_circulating(1)(self.consumer._shedual_task))
                ConsumersManager.schedulal_thread_to_be_join.append(t)
                t.start()
            elif self._concurrent_mode == ConcurrentModeEnum.GEVENT:
                g = gevent.spawn(self.consumer.keep_circulating(1)(self.consumer._shedual_task), )
                ConsumersManager.schedulal_thread_to_be_join.append(g)
            elif self._concurrent_mode == ConcurrentModeEnum.GEVENT:
                g = eventlet.spawn(self.consumer.keep_circulating(1)(self.consumer._shedual_task), )
                ConsumersManager.schedulal_thread_to_be_join.append(g)


def wait_for_possible_has_finish_all_tasks_by_conusmer_list(consumer_list: typing.List[AbstractConsumer], minutes: int = 3):
    """
   判断多个消费者是否消费完成了。
   由于是异步消费，和存在队列一边被消费，一边在推送，或者还有结尾少量任务还在确认消费者实际还没彻底运行完成。  但有时候需要判断 所有任务，务是否完成，提供一个不精确的判断，要搞清楚原因和场景后再慎用。
   一般是和celery一样，是永久运行的后台任务，永远无限死循环去任务执行任务，但有的人有判断是否执行完成的需求。
   :param consumer_list: 多个消费者列表
   :param minutes: 消费者连续多少分钟没执行任务任务 并且 消息队列中间件中没有，就判断为消费完成。为了防止是长耗时任务，一般判断完成是真正提供的minutes的2个周期时间。
   :return:

    """
    with BoundedThreadPoolExecutor(len(consumer_list)) as pool:
        for consumer in consumer_list:
            pool.submit(consumer.wait_for_possible_has_finish_all_tasks(minutes))


class DistributedConsumerStatistics(RedisMixin, LoggerMixinDefaultWithFileHandler):
    """
    为了兼容模拟mq的中间件（例如redis，他没有实现amqp协议，redis的list结构和真mq差远了），获取一个队列有几个连接活跃消费者数量。
    分布式环境中的消费者统计。主要目的有3点

    1、统计活跃消费者数量用于分布式控频。
        获取分布式的消费者数量后，用于分布式qps控频。如果不获取全环境中的消费者数量，则只能用于当前进程中的消费控频。
        即使只有一台机器，例如把xx.py启动3次，xx.py的consumer设置qps为10，如果不使用分布式控频，会1秒钟最终运行30次函数而不是10次。

    2、记录分布式环境中的活跃消费者的所有消费者 id，如果消费者id不在此里面说明已掉线或关闭，消息可以重新分发，用于不支持服务端天然消费确认的中间件。

    3、从redis中获取停止和暂停状态，以便支持在别的地方发送命令停止或者暂停消费。
    """

    def __init__(self, consumer: AbstractConsumer):
        # self._consumer_identification = consumer_identification
        # self._consumer_identification_map = consumer_identification_map
        # self._queue_name = queue_name
        self._consumer_identification = consumer.consumer_identification
        self._consumer_identification_map = consumer.consumer_identification_map
        self._queue_name = consumer.queue_name
        self._consumer = consumer
        self._redis_key_name = f'funboost_hearbeat_queue__str:{self._queue_name}'
        self.active_consumer_num = 1
        self._last_show_consumer_num_timestamp = 0

        self._queue__consumer_identification_map_key_name = f'funboost_hearbeat_queue__dict:{self._queue_name}'
        self._server__consumer_identification_map_key_name = f'funboost_hearbeat_server__dict:{nb_log_config_default.computer_ip}'

    def run(self):
        self.send_heartbeat()
        self._consumer.keep_circulating(10, block=False)(self.send_heartbeat)()
        # decorators.keep_circulating(5, block=False)(self._show_active_consumer_num)()  # 主要是为快速频繁统计分布式消费者个数，快速调整分布式qps控频率。

    def _send_heartbeat_with_dict_value(self, redis_key, ):
        # 发送当前消费者进程心跳的，值是字典，按一个机器或者一个队列运行了哪些进程。

        results = self.redis_db_frame.smembers(redis_key)
        with self.redis_db_frame.pipeline() as p:
            for result in results:
                result_dict = json.loads(result)
                if self.timestamp() - result_dict['hearbeat_timestamp'] > 15 \
                        or self._consumer_identification_map['consumer_uuid'] == result_dict['consumer_uuid']:
                    # 因为这个是10秒钟运行一次，15秒还没更新，那肯定是掉线了。如果消费者本身是自己也先删除。
                    p.srem(redis_key, result)
            self._consumer_identification_map['hearbeat_datetime_str'] = time_util.DatetimeConverter().datetime_str
            self._consumer_identification_map['hearbeat_timestamp'] = self.timestamp()
            value = json.dumps(self._consumer_identification_map, sort_keys=True)
            p.sadd(redis_key, value)
            p.execute()

    def send_heartbeat(self):
        # 根据队列名心跳的，值是字符串，方便值作为其他redis的键名
        results = self.redis_db_frame.smembers(self._redis_key_name)
        with self.redis_db_frame.pipeline() as p:
            for result in results:
                if self.timestamp() - float(result.decode().split('&&')[-1]) > 15 or \
                        self._consumer_identification == result.decode().split('&&')[0]:  # 因为这个是10秒钟运行一次，15秒还没更新，那肯定是掉线了。如果消费者本身是自己也先删除。
                    p.srem(self._redis_key_name, result)
            p.sadd(self._redis_key_name, f'{self._consumer_identification}&&{self.timestamp()}')
            p.execute()

        self._send_heartbeat_with_dict_value(self._queue__consumer_identification_map_key_name)
        self._send_heartbeat_with_dict_value(self._server__consumer_identification_map_key_name)
        self._show_active_consumer_num()
        self._get_stop_and_pause_flag_from_redis()

    def _show_active_consumer_num(self):
        self.active_consumer_num = self.redis_db_frame.scard(self._redis_key_name) or 1
        if time.time() - self._last_show_consumer_num_timestamp > 600:
            self.logger.info(f'分布式所有环境中使用 {self._queue_name} 队列的，一共有 {self.active_consumer_num} 个消费者')
            self._last_show_consumer_num_timestamp = time.time()

    def get_queue_heartbeat_ids(self, without_time: bool):
        if without_time:
            return [idx.decode().split('&&')[0] for idx in self.redis_db_frame.smembers(self._redis_key_name)]
        else:
            return [idx.decode() for idx in self.redis_db_frame.smembers(self._redis_key_name)]

    # noinspection PyProtectedMember
    def _get_stop_and_pause_flag_from_redis(self):
        stop_flag = self.redis_db_frame.get(self._consumer._redis_key_stop_flag)
        if stop_flag is not None and int(stop_flag) == 1:
            self._consumer._stop_flag = 1
        else:
            self._consumer._stop_flag = 0

        pause_flag = self.redis_db_frame.get(self._consumer._redis_key_pause_flag)
        if pause_flag is not None and int(pause_flag) == 1:
            self._consumer._pause_flag = 1
        else:
            self._consumer._pause_flag = 0


class ActiveCousumerProcessInfoGetter(RedisMixin, LoggerMixinDefaultWithFileHandler):
    """

    获取分布式环境中的消费进程信息。
    使用这里面的4个方法需要相应函数的@boost装饰器设置 is_send_consumer_hearbeat_to_redis=True，这样会自动发送活跃心跳到redis。否则查询不到该函数的消费者进程信息。
    要想使用消费者进程信息统计功能，用户无论使用何种消息队列中间件类型，用户都必须安装redis，并在 funboost_config.py 中配置好redis链接信息
    """

    def _get_all_hearbeat_info_by_redis_key_name(self, redis_key):
        results = self.redis_db_frame.smembers(redis_key)
        # print(type(results))
        # print(results)
        # 如果所有机器所有进程都全部关掉了，就没办法还剩一个线程执行删除了，这里还需要判断一次15秒。
        active_consumers_processor_info_list = []
        for result in results:
            result_dict = json.loads(result)
            if self.timestamp() - result_dict['hearbeat_timestamp'] < 15:
                active_consumers_processor_info_list.append(result_dict)
        return active_consumers_processor_info_list

    def get_all_hearbeat_info_by_queue_name(self, queue_name) -> typing.List[typing.Dict]:
        """
        根据队列名查询有哪些活跃的消费者进程
        返回结果例子：
        [{
                "code_filename": "/codes/funboost/test_frame/my/test_consume.py",
                "computer_ip": "172.16.0.9",
                "computer_name": "VM_0_9_centos",
                "consumer_id": 140477437684048,
                "consumer_uuid": "79473629-b417-4115-b516-4365b3cdf383",
                "consuming_function": "f2",
                "hearbeat_datetime_str": "2021-12-27 19:22:04",
                "hearbeat_timestamp": 1640604124.4643965,
                "process_id": 9665,
                "queue_name": "test_queue72c",
                "start_datetime_str": "2021-12-27 19:21:24",
                "start_timestamp": 1640604084.0780013
            }, ...............]
        """
        redis_key = f'funboost_hearbeat_queue__dict:{queue_name}'
        return self._get_all_hearbeat_info_by_redis_key_name(redis_key)

    def get_all_hearbeat_info_by_ip(self, ip=None) -> typing.List[typing.Dict]:
        """
        根据机器的ip查询有哪些活跃的消费者进程，ip不传参就查本机ip使用funboost框架运行了哪些消费进程，传参则查询任意机器的消费者进程信息。
        返回结果的格式和上面的 get_all_hearbeat_dict_by_queue_name 方法相同。
        """
        ip = ip or nb_log_config_default.computer_ip
        redis_key = f'funboost_hearbeat_server__dict:{ip}'
        return self._get_all_hearbeat_info_by_redis_key_name(redis_key)

    def _get_all_hearbeat_info_partition_by_redis_key_prefix(self, redis_key_prefix):
        keys = self.redis_db_frame.scan(0, f'{redis_key_prefix}*', 10000)[1]
        infos_map = {}
        for key in keys:
            key = key.decode()
            infos = self.redis_db_frame.smembers(key)
            dict_key = key.replace(redis_key_prefix, '')
            infos_map[dict_key] = []
            for info_str in infos:
                info_dict = json.loads(info_str)
                if self.timestamp() - info_dict['hearbeat_timestamp'] < 15:
                    infos_map[dict_key].append(info_dict)
        return infos_map

    def get_all_hearbeat_info_partition_by_queue_name(self) -> typing.Dict[typing.AnyStr, typing.List[typing.Dict]]:
        """获取所有队列对应的活跃消费者进程信息，按队列名划分,不需要传入队列名，自动扫描redis键。请不要在 funboost_config.py 的redis 指定的db中放太多其他业务的缓存键值对"""
        infos_map = self._get_all_hearbeat_info_partition_by_redis_key_prefix('funboost_hearbeat_queue__dict:')
        self.logger.info(f'获取所有队列对应的活跃消费者进程信息，按队列名划分，结果是 {json.dumps(infos_map, indent=4)}')
        return infos_map

    def get_all_hearbeat_info_partition_by_ip(self) -> typing.Dict[typing.AnyStr, typing.List[typing.Dict]]:
        """获取所有机器ip对应的活跃消费者进程信息，按机器ip划分,不需要传入机器ip，自动扫描redis键。请不要在 funboost_config.py 的redis 指定的db中放太多其他业务的缓存键值对 """
        infos_map = self._get_all_hearbeat_info_partition_by_redis_key_prefix('funboost_hearbeat_server__dict:')
        self.logger.info(f'获取所有机器ip对应的活跃消费者进程信息，按机器ip划分，结果是 {json.dumps(infos_map, indent=4)}')
        return infos_map

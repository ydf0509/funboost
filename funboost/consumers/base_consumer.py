# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:11
"""
所有中间件类型消费者的抽象基类。使实现不同中间件的消费者尽可能代码少。
整个流程最难的都在这里面。因为要实现多种并发模型，和对函数施加20多种运行控制方式，所以代码非常长。

框架做主要的功能都是在这个文件里面实现的.
"""
import functools
import sys
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
import atexit
import os
import uuid
import time
import traceback
import inspect
from functools import wraps
import threading
from threading import Lock
import asyncio

import nb_log
from funboost.core.current_task import funboost_current_task, FctContext
from funboost.core.loggers import develop_logger

from funboost.core.func_params_model import BoosterParams, PublisherParams, BaseJsonAbleModel
from funboost.core.serialization import Serialization
from funboost.core.task_id_logger import TaskIdLogger
from funboost.constant import FunctionKind

from nb_libs.path_helper import PathHelper
from nb_log import (get_logger, LoggerLevelSetterMixin, LogManager, is_main_process,
                    nb_log_config_default)
from funboost.core.loggers import FunboostFileLoggerMixin, logger_prompt

from apscheduler.jobstores.redis import RedisJobStore

from apscheduler.executors.pool import ThreadPoolExecutor as ApschedulerThreadPoolExecutor

from funboost.funboost_config_deafult import FunboostCommonConfig
from funboost.concurrent_pool.single_thread_executor import SoloExecutor

from funboost.core.function_result_status_saver import ResultPersistenceHelper, FunctionResultStatus, RunStatus

from funboost.core.helper_funs import delete_keys_and_return_new_dict, get_publish_time, MsgGenerater

from funboost.concurrent_pool.async_helper import simple_run_in_executor
from funboost.concurrent_pool.async_pool_executor import AsyncPoolExecutor
# noinspection PyUnresolvedReferences
from funboost.concurrent_pool.bounded_threadpoolexcutor import \
    BoundedThreadPoolExecutor
from funboost.utils.redis_manager import RedisMixin
from func_timeout import func_set_timeout  # noqa

from funboost.concurrent_pool.custom_threadpool_executor import check_not_monkey
from funboost.concurrent_pool.flexible_thread_pool import FlexibleThreadPool, sync_or_async_fun_deco
# from funboost.concurrent_pool.concurrent_pool_with_multi_process import ConcurrentPoolWithProcess
from funboost.consumers.redis_filter import RedisFilter, RedisImpermanencyFilter
from funboost.factories.publisher_factotry import get_publisher

from funboost.utils import decorators, time_util, redis_manager
from funboost.constant import ConcurrentModeEnum, BrokerEnum, ConstStrForClassMethod
from funboost.core import kill_remote_task
from funboost.core.exceptions import ExceptionForRequeue, ExceptionForPushToDlxqueue

# from funboost.core.booster import BoostersManager  互相导入
from funboost.core.lazy_impoter import funboost_lazy_impoter


# patch_apscheduler_run_job()

class GlobalVars:
    global_concurrent_mode = None
    has_start_a_consumer_flag = False


# noinspection DuplicatedCode
class AbstractConsumer(LoggerLevelSetterMixin, metaclass=abc.ABCMeta, ):
    time_interval_for_check_do_not_run_time = 60
    BROKER_KIND = None
    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {}  # 每种中间件的概念有所不同，用户可以从 broker_exclusive_config 中传递该种中间件特有的配置意义参数。

    @property
    @decorators.synchronized
    def publisher_of_same_queue(self):
        if not self._publisher_of_same_queue:
            self._publisher_of_same_queue = get_publisher(publisher_params=self.publisher_params)
        return self._publisher_of_same_queue

    def bulid_a_new_publisher_of_same_queue(self):
        return get_publisher(publisher_params=self.publisher_params)

    @property
    @decorators.synchronized
    def publisher_of_dlx_queue(self):
        """ 死信队列发布者 """
        if not self._publisher_of_dlx_queue:
            publisher_params_dlx = copy.copy(self.publisher_params)
            publisher_params_dlx.queue_name = self._dlx_queue_name
            publisher_params_dlx.consuming_function = None
            self._publisher_of_dlx_queue = get_publisher(publisher_params=publisher_params_dlx)
        return self._publisher_of_dlx_queue

    @classmethod
    def join_shedual_task_thread(cls):
        """

        :return:
        """
        # ConsumersManager.join_all_consumer_shedual_task_thread()
        if GlobalVars.has_start_a_consumer_flag:
            # self.keep_circulating(10,block=True,)(time.sleep)()
            while 1:
                time.sleep(10)

    def __init__(self, consumer_params: BoosterParams):

        """
        """
        self.raw_consumer_params = copy.copy(consumer_params)
        self.consumer_params = copy.copy(consumer_params)
        # noinspection PyUnresolvedReferences
        file_name = self.consumer_params.consuming_function.__code__.co_filename
        # noinspection PyUnresolvedReferences
        line = self.consumer_params.consuming_function.__code__.co_firstlineno
        self.consumer_params.auto_generate_info['where_to_instantiate'] = f'{file_name}:{line}'

        self.queue_name = self._queue_name = consumer_params.queue_name
        self.consuming_function = consumer_params.consuming_function
        if consumer_params.consuming_function is None:
            raise ValueError('必须传 consuming_function 参数')

        self._msg_schedule_time_intercal = 0 if consumer_params.qps in (None, 0) else 1.0 / consumer_params.qps

        self._concurrent_mode_dispatcher = ConcurrentModeDispatcher(self)
        if consumer_params.concurrent_mode == ConcurrentModeEnum.ASYNC:
            self._run = self._async_run  # 这里做了自动转化，使用async_run代替run
        self.logger: logging.Logger
        self._build_logger()
        # stdout_write(f'''{time.strftime("%H:%M:%S")} "{self.consumer_params.auto_generate_info['where_to_instantiate']}"  \033[0;37;44m此行 实例化队列名 {self.queue_name} 的消费者, 类型为 {self.__class__}\033[0m\n''')
        print(f'''\033[0m
         "{self.consumer_params.auto_generate_info['where_to_instantiate']}" \033[0m此行 实例化队列名 {self.queue_name} 的消费者, 类型为 {self.__class__} ''')

        # only_print_on_main_process(f'{current_queue__info_dict["queue_name"]} 的消费者配置:\n', un_strict_json_dumps.dict2json(current_queue__info_dict))

        # self._do_task_filtering = consumer_params.do_task_filtering
        # self.consumer_params.is_show_message_get_from_broker = consumer_params.is_show_message_get_from_broker
        self._redis_filter_key_name = f'filter_zset:{consumer_params.queue_name}' if consumer_params.task_filtering_expire_seconds else f'filter_set:{consumer_params.queue_name}'
        filter_class = RedisFilter if consumer_params.task_filtering_expire_seconds == 0 else RedisImpermanencyFilter
        self._redis_filter = filter_class(self._redis_filter_key_name, consumer_params.task_filtering_expire_seconds)

        self._unit_time_for_count = 10  # 每隔多少秒计数，显示单位时间内执行多少次，暂时固定为10秒。
        self._execute_task_times_every_unit_time = 0  # 每单位时间执行了多少次任务。
        self._lock_for_count_execute_task_times_every_unit_time = Lock()
        self._current_time_for_execute_task_times_every_unit_time = time.time()
        self._consuming_function_cost_time_total_every_unit_time = 0
        self._last_execute_task_time = time.time()  # 最近一次执行任务的时间。

        self._last_show_remaining_execution_time = 0
        self._show_remaining_execution_time_interval = 300

        self._msg_num_in_broker = 0
        self._last_timestamp_when_has_task_in_queue = 0
        self._last_timestamp_print_msg_num = 0

        self._result_persistence_helper: ResultPersistenceHelper
        self._check_broker_exclusive_config()
        broker_exclusive_config_merge = dict()
        broker_exclusive_config_merge.update(self.BROKER_EXCLUSIVE_CONFIG_DEFAULT)
        broker_exclusive_config_merge.update(self.consumer_params.broker_exclusive_config)
        # print(broker_exclusive_config_merge)
        self.consumer_params.broker_exclusive_config = broker_exclusive_config_merge

        self._stop_flag = None
        self._pause_flag = None  # 暂停消费标志，从reids读取
        self._last_show_pause_log_time = 0
        self._redis_key_stop_flag = f'funboost_stop_flag:{self.queue_name}'
        self._redis_key_pause_flag = f'funboost_pause_flag:{self.queue_name}'

        # 控频要用到的成员变量
        self._last_submit_task_timestamp = 0
        self._last_start_count_qps_timestamp = time.time()
        self._has_execute_times_in_recent_second = 0

        self._publisher_of_same_queue = None  #
        self._dlx_queue_name = f'{self.queue_name}_dlx'
        self._publisher_of_dlx_queue = None  # 死信队列发布者

        self._do_not_delete_extra_from_msg = False
        self._concurrent_pool = None

        self.consumer_identification = f'{nb_log_config_default.computer_name}_{nb_log_config_default.computer_ip}_' \
                                       f'{time_util.DatetimeConverter().datetime_str.replace(":", "-")}_{os.getpid()}_{id(self)}'
        # noinspection PyUnresolvedReferences
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

        self._has_start_delay_task_scheduler = False
        self._consuming_function_is_asyncio = inspect.iscoroutinefunction(self.consuming_function)
        self.custom_init()
        # develop_logger.warning(consumer_params._log_filename)
        # self.publisher_params = PublisherParams(queue_name=consumer_params.queue_name, consuming_function=consumer_params.consuming_function,
        #                                         broker_kind=self.BROKER_KIND, log_level=consumer_params.log_level,
        #                                         logger_prefix=consumer_params.logger_prefix,
        #                                         create_logger_file=consumer_params.create_logger_file,
        #                                         log_filename=consumer_params.log_filename,
        #                                         logger_name=consumer_params.logger_name,
        #                                         broker_exclusive_config=self.consumer_params.broker_exclusive_config)
        self.publisher_params = BaseJsonAbleModel.init_by_another_model(PublisherParams, self.consumer_params)
        # print(self.publisher_params)
        if is_main_process:
            self.logger.info(f'{self.queue_name} consumer 的消费者配置:\n {self.consumer_params.json_str_value()}')
        atexit.register(self.join_shedual_task_thread)

        if self.consumer_params.is_auto_start_consuming_message:
            _ = self.publisher_of_same_queue
            self.start_consuming_message()

    def _build_logger(self):
        logger_prefix = self.consumer_params.logger_prefix
        if logger_prefix != '':
            logger_prefix += '--'
            # logger_name = f'{logger_prefix}{self.__class__.__name__}--{concurrent_name}--{queue_name}--{self.consuming_function.__name__}'
        logger_name = self.consumer_params.logger_name or f'funboost.{logger_prefix}{self.__class__.__name__}--{self.queue_name}'
        self.logger_name = logger_name
        log_filename = self.consumer_params.log_filename or f'funboost.{self.queue_name}.log'
        self.logger = LogManager(logger_name, logger_cls=TaskIdLogger).get_logger_and_add_handlers(
            log_level_int=self.consumer_params.log_level,
            log_filename=log_filename if self.consumer_params.create_logger_file else None,
            error_log_filename=nb_log.generate_error_file_name(log_filename),
            formatter_template=FunboostCommonConfig.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER, )
        self.logger.info(f'队列 {self.queue_name} 的日志写入到 {nb_log_config_default.LOG_PATH} 文件夹的 {log_filename} 和 {nb_log.generate_error_file_name(log_filename)} 文件中')

    def _check_broker_exclusive_config(self):
        broker_exclusive_config_keys = self.BROKER_EXCLUSIVE_CONFIG_DEFAULT.keys()
        if self.consumer_params.broker_exclusive_config:
            if set(self.consumer_params.broker_exclusive_config.keys()).issubset(broker_exclusive_config_keys):
                self.logger.info(f'当前消息队列中间件能支持特殊独有配置 {self.consumer_params.broker_exclusive_config.keys()}')
            else:
                self.logger.warning(f'当前消息队列中间件含有不支持的特殊配置 {self.consumer_params.broker_exclusive_config.keys()}，能支持的特殊独有配置包括 {broker_exclusive_config_keys}')

    def _check_monkey_patch(self):
        if self.consumer_params.concurrent_mode == ConcurrentModeEnum.GEVENT:
            from funboost.concurrent_pool.custom_gevent_pool_executor import check_gevent_monkey_patch
            check_gevent_monkey_patch()
        elif self.consumer_params.concurrent_mode == ConcurrentModeEnum.EVENTLET:
            from funboost.concurrent_pool.custom_evenlet_pool_executor import check_evenlet_monkey_patch
            check_evenlet_monkey_patch()
        else:
            check_not_monkey()

    # def _log_error(self, msg, exc_info=None):
    #     self.logger.error(msg=f'{msg} \n', exc_info=exc_info, extra={'sys_getframe_n': 3})  # 这是改变日志栈层级
    #     self.error_file_logger.error(msg=f'{msg} \n', exc_info=exc_info, extra={'sys_getframe_n': 3})
    #
    # def _log_critical(self, msg, exc_info=None):
    #     self.logger.critical(msg=f'{msg} \n', exc_info=exc_info, extra={'sys_getframe_n': 3})
    #     self.error_file_logger.critical(msg=f'{msg} \n', exc_info=exc_info, extra={'sys_getframe_n': 3})

    @property
    @decorators.synchronized
    def concurrent_pool(self):
        return self._concurrent_mode_dispatcher.build_pool()

    def custom_init(self):
        pass

    def keep_circulating(self, time_sleep=0.001, exit_if_function_run_sucsess=False, is_display_detail_exception=True,
                         block=True, daemon=False):
        """间隔一段时间，一直循环运行某个方法的装饰器
        :param time_sleep :循环的间隔时间
        :param is_display_detail_exception
        :param exit_if_function_run_sucsess :如果成功了就退出循环
        :param block:是否阻塞在当前主线程运行。
        :param daemon:是否守护线程
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
                        except BaseException as e:
                            log_msg = func.__name__ + '   运行出错\n ' + traceback.format_exc(
                                limit=10) if is_display_detail_exception else str(e)
                            # self.logger.error(msg=f'{log_msg} \n', exc_info=True)
                            # self.error_file_logger.error(msg=f'{log_msg} \n', exc_info=True)
                            self.logger.error(msg=log_msg, exc_info=True)
                        finally:
                            time.sleep(time_sleep)
                            # print(func,time_sleep)

                if block:
                    return ___keep_circulating()
                else:
                    threading.Thread(target=___keep_circulating, daemon=daemon).start()

            return __keep_circulating

        return _keep_circulating

    # noinspection PyAttributeOutsideInit
    def start_consuming_message(self):
        # ConsumersManager.show_all_consumer_info()
        # noinspection PyBroadException
        pid_queue_name_tuple = (os.getpid(), self.queue_name)
        if pid_queue_name_tuple in funboost_lazy_impoter.BoostersManager.pid_queue_name__has_start_consume_set:
            self.logger.warning(f'{pid_queue_name_tuple} 已启动消费,不要一直去启动消费,funboost框架自动阻止.')  # 有的人乱写代码,无数次在函数内部或for循环里面执行 f.consume(),一个队列只需要启动一次消费,不然每启动一次性能消耗很大,直到程序崩溃
            return
        else:
            funboost_lazy_impoter.BoostersManager.pid_queue_name__has_start_consume_set.add(pid_queue_name_tuple)
        GlobalVars.has_start_a_consumer_flag = True
        try:
            self._concurrent_mode_dispatcher.check_all_concurrent_mode()
            self._check_monkey_patch()
        except BaseException:  # noqa
            traceback.print_exc()
            os._exit(4444)  # noqa
        self.logger.info(f'开始消费 {self._queue_name} 中的消息')
        self._result_persistence_helper = ResultPersistenceHelper(self.consumer_params.function_result_status_persistance_conf, self.queue_name)

        self._distributed_consumer_statistics = DistributedConsumerStatistics(self)
        if self.consumer_params.is_send_consumer_hearbeat_to_redis:
            self._distributed_consumer_statistics.run()
            self.logger.warning(f'启动了分布式环境 使用 redis 的键 hearbeat:{self._queue_name} 统计活跃消费者 ，当前消费者唯一标识为 {self.consumer_identification}')

        self.keep_circulating(60, block=False, daemon=False)(self.check_heartbeat_and_message_count)()  # 间隔时间最好比self._unit_time_for_count小整数倍，不然日志不准。
        if self.consumer_params.is_support_remote_kill_task:
            kill_remote_task.RemoteTaskKiller(self.queue_name, None).start_cycle_kill_task()
            self.consumer_params.is_show_message_get_from_broker = True  # 方便用户看到从消息队列取出来的消息的task_id,然后使用task_id杀死运行中的消息。
        if self.consumer_params.do_task_filtering:
            self._redis_filter.delete_expire_filter_task_cycle()  # 这个默认是RedisFilter类，是个pass不运行。所以用别的消息中间件模式，不需要安装和配置redis。
        if self.consumer_params.schedule_tasks_on_main_thread:
            self.keep_circulating(1, daemon=False)(self._shedual_task)()
        else:
            self._concurrent_mode_dispatcher.schedulal_task_with_no_block()

    def _start_delay_task_scheduler(self):
        from funboost.timing_job import FsdfBackgroundScheduler
        jobstores = {
            "default": RedisJobStore(**redis_manager.get_redis_conn_kwargs(),
            jobs_key=f'funboost.apscheduler.{self.queue_name}.jobs')
        }
        self._delay_task_scheduler = FsdfBackgroundScheduler(timezone=FunboostCommonConfig.TIMEZONE, daemon=False,
                                                             jobstores=jobstores  # push 方法的序列化带thredignn.lock
                                                             )
        self._delay_task_scheduler.add_executor(ApschedulerThreadPoolExecutor(2))  # 只是运行submit任务到并发池，不需要很多线程。
        # self._delay_task_scheduler.add_listener(self._apscheduler_job_miss, EVENT_JOB_MISSED)
        self._delay_task_scheduler.start()
        self.logger.warning('启动延时任务sheduler')

    logger_apscheduler = get_logger('push_for_apscheduler_use_database_store', log_filename='push_for_apscheduler_use_database_store.log')

    @classmethod
    def _push_for_apscheduler_use_database_store(cls, queue_name, msg, runonce_uuid):
        key = 'apscheduler.redisjobstore_runonce'
        if RedisMixin().redis_db_frame.sadd(key, runonce_uuid):  # 这样可以阻止多次启动同队列名消费者 redis jobstore多次运行函数.
            cls.logger_apscheduler.debug(f'延时任务用普通消息重新发布到普通队列 {msg}')
            funboost_lazy_impoter.BoostersManager.get_or_create_booster_by_queue_name(queue_name).publish(msg)

    @abc.abstractmethod
    def _shedual_task(self):
        """
        每个子类必须实现这个的方法，完成如何从中间件取出消息，并将函数和运行参数添加到工作池。
        :return:
        """
        raise NotImplementedError

    def convert_msg_before_run(self, msg: typing.Union[str, dict]) -> dict:
        """
        转换消息,消息没有使用funboost来发送,并且没有extra相关字段时候
        用户也可以按照4.21文档,继承任意Consumer类,并实现这个方法 convert_msg_before_run,先转换不规范的消息.
        """
        """ 一般消息至少包含这样
        {
          "a": 42,
          "b": 84,
          "extra": {
            "task_id": "queue_2_result:9b79a372-f765-4a33-8639-9d15d7a95f61",
            "publish_time": 1701687443.3596,
            "publish_time_format": "2023-12-04 18:57:23"
          }
        }
        """

        """
        extra_params = {'task_id': task_id, 'publish_time': round(time.time(), 4),
                        'publish_time_format': time.strftime('%Y-%m-%d %H:%M:%S')}
        """
        msg = Serialization.to_dict(msg)
        # 以下是清洗补全字段.
        if 'extra' not in msg:
            msg['extra'] = {'is_auto_fill_extra': True}
        extra = msg['extra']
        if 'task_id' not in extra:
            extra['task_id'] = MsgGenerater.generate_task_id(self._queue_name)
        if 'publish_time' not in extra:
            extra['publish_time'] = MsgGenerater.generate_publish_time()
        if 'publish_time_format':
            extra['publish_time_format'] = MsgGenerater.generate_publish_time_format()
        return msg

    def _submit_task(self, kw):
        while 1:  # 这一块的代码为支持暂停消费。
            # print(self._pause_flag)
            if self._pause_flag == 1:
                time.sleep(5)
                if time.time() - self._last_show_pause_log_time > 60:
                    self.logger.warning(f'已设置 {self.queue_name} 队列中的任务为暂停消费')
                    self._last_show_pause_log_time = time.time()
            else:
                break
        kw['body'] = self.convert_msg_before_run(kw['body'])
        self._print_message_get_from_broker(kw['body'])
        if self._judge_is_daylight():
            self._requeue(kw)
            time.sleep(self.time_interval_for_check_do_not_run_time)
            return
        function_only_params = delete_keys_and_return_new_dict(kw['body'], )
        if self._get_priority_conf(kw, 'do_task_filtering') and self._redis_filter.check_value_exists(
                function_only_params):  # 对函数的参数进行检查，过滤已经执行过并且成功的任务。
            self.logger.warning(f'redis的 [{self._redis_filter_key_name}] 键 中 过滤任务 {kw["body"]}')
            self._confirm_consume(kw)
            return
        publish_time = get_publish_time(kw['body'])
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
        if run_date:  # 延时任务
            # print(repr(run_date),repr(datetime.datetime.now(tz=pytz.timezone(frame_config.TIMEZONE))))
            if self._has_start_delay_task_scheduler is False:
                self._has_start_delay_task_scheduler = True
                self._start_delay_task_scheduler()

            # 这种方式是扔到线程池
            # self._delay_task_scheduler.add_job(self.concurrent_pool.submit, 'date', run_date=run_date, args=(self._run,), kwargs={'kw': kw},
            #                                    misfire_grace_time=misfire_grace_time)

            # 这种方式是延时任务重新以普通任务方式发送到消息队列
            msg_no_delay = copy.deepcopy(kw['body'])
            self.__delete_eta_countdown(msg_no_delay)
            # print(msg_no_delay)
            # 数据库作为apscheduler的jobstores时候， 不能用 self.pbulisher_of_same_queue.publish，self不能序列化
            self._delay_task_scheduler.add_job(self._push_for_apscheduler_use_database_store, 'date', run_date=run_date,
                                               kwargs={'queue_name': self.queue_name, 'msg': msg_no_delay, 'runonce_uuid': str(uuid.uuid4())},
                                               misfire_grace_time=misfire_grace_time)
            self._confirm_consume(kw)

        else:  # 普通任务
            self.concurrent_pool.submit(self._run, kw)

        if self.consumer_params.is_using_distributed_frequency_control:  # 如果是需要分布式控频。
            active_num = self._distributed_consumer_statistics.active_consumer_num
            self._frequency_control(self.consumer_params.qps / active_num, self._msg_schedule_time_intercal * active_num)
        else:
            self._frequency_control(self.consumer_params.qps, self._msg_schedule_time_intercal)

    def __delete_eta_countdown(self, msg_body: dict):
        self.__dict_pop(msg_body.get('extra', {}), 'eta')
        self.__dict_pop(msg_body.get('extra', {}), 'countdown')
        self.__dict_pop(msg_body.get('extra', {}), 'misfire_grace_time')

    @staticmethod
    def __dict_pop(dictx, key):
        try:
            dictx.pop(key)
        except KeyError:
            pass

    def _frequency_control(self, qpsx: float, msg_schedule_time_intercalx: float):
        # 以下是消费函数qps控制代码。无论是单个消费者空频还是分布式消费控频，都是基于直接计算的，没有依赖redis inrc计数，使得控频性能好。
        if qpsx is None:  # 不需要控频的时候，就不需要休眠。
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

    def _print_message_get_from_broker(self, msg, broker_name=None):
        # print(999)
        if self.consumer_params.is_show_message_get_from_broker:
            # self.logger.debug(f'从 {broker_name} 中间件 的 {self._queue_name} 中取出的消息是 {msg}')
            self.logger.debug(f'从 {broker_name or self.consumer_params.broker_kind} 中间件 的 {self._queue_name} 中取出的消息是 {Serialization.to_json_str(msg)}')

    def _get_priority_conf(self, kw: dict, broker_task_config_key: str):
        broker_task_config = kw['body'].get('extra', {}).get(broker_task_config_key, None)
        if not broker_task_config:
            return getattr(self.consumer_params, f'{broker_task_config_key}', None)
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

    def _set_do_not_delete_extra_from_msg(self):
        """例如从死信队列，把完整的包括extra的消息移到另一个正常队列，不要把extra中的参数去掉
        queue2queue.py 的 consume_and_push_to_another_queue 中操作了这个，普通用户无需调用这个方法。
        """
        self._do_not_delete_extra_from_msg = True

    def user_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus):  # 这个可以继承
        pass

    async def aio_user_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus):  # 这个可以继承
        pass

    def _convert_real_function_only_params_by_conusuming_function_kind(self, function_only_params: dict):
        """对于实例方法和classmethod 方法， 从消息队列的消息恢复第一个入参， self 和 cls"""
        if self.consumer_params.consuming_function_kind in [FunctionKind.CLASS_METHOD, FunctionKind.INSTANCE_METHOD]:
            real_function_only_params = copy.copy(function_only_params)
            method_first_param_name = None
            method_first_param_value = None
            for k, v in function_only_params.items():
                if isinstance(v, dict) and ConstStrForClassMethod.FIRST_PARAM_NAME in v:
                    method_first_param_name = k
                    method_first_param_value = v
                    break
            # method_cls = getattr(sys.modules[self.consumer_params.consuming_function_class_module],
            #                      self.consumer_params.consuming_function_class_name)
            if self.publisher_params.consuming_function_kind == FunctionKind.CLASS_METHOD:
                method_cls = getattr(PathHelper.import_module(method_first_param_value[ConstStrForClassMethod.CLS_MODULE]),
                                     method_first_param_value[ConstStrForClassMethod.CLS_NAME])
                real_function_only_params[method_first_param_name] = method_cls
            elif self.publisher_params.consuming_function_kind == FunctionKind.INSTANCE_METHOD:
                method_cls = getattr(PathHelper.import_module(method_first_param_value[ConstStrForClassMethod.CLS_MODULE]),
                                     method_first_param_value[ConstStrForClassMethod.CLS_NAME])
                obj = method_cls(**method_first_param_value[ConstStrForClassMethod.OBJ_INIT_PARAMS])
                real_function_only_params[method_first_param_name] = obj
            # print(real_function_only_params)
            return real_function_only_params
        else:
            return function_only_params

    # noinspection PyProtectedMember
    def _run(self, kw: dict, ):
        # print(kw)
        try:
            t_start_run_fun = time.time()
            max_retry_times = self._get_priority_conf(kw, 'max_retry_times')
            current_function_result_status = FunctionResultStatus(self.queue_name, self.consuming_function.__name__, kw['body'], )
            current_retry_times = 0
            function_only_params = delete_keys_and_return_new_dict(kw['body'])
            for current_retry_times in range(max_retry_times + 1):
                current_function_result_status.run_times = current_retry_times + 1
                current_function_result_status.run_status = RunStatus.running
                self._result_persistence_helper.save_function_result_to_mongo(current_function_result_status)
                current_function_result_status = self._run_consuming_function_with_confirm_and_retry(kw, current_retry_times=current_retry_times,
                                                                                                     function_result_status=current_function_result_status)
                if (current_function_result_status.success is True or current_retry_times == max_retry_times
                        or current_function_result_status._has_requeue
                        or current_function_result_status._has_to_dlx_queue
                        or current_function_result_status._has_kill_task):
                    break
                else:
                    if self.consumer_params.retry_interval:
                        time.sleep(self.consumer_params.retry_interval)
            if not (current_function_result_status._has_requeue and self.BROKER_KIND in [BrokerEnum.RABBITMQ_AMQPSTORM, BrokerEnum.RABBITMQ_PIKA, BrokerEnum.RABBITMQ_RABBITPY]):  # 已经nack了，不能ack，否则rabbitmq delevar tag 报错
                self._confirm_consume(kw)
            current_function_result_status.run_status = RunStatus.finish
            self._result_persistence_helper.save_function_result_to_mongo(current_function_result_status)
            if self._get_priority_conf(kw, 'do_task_filtering'):
                self._redis_filter.add_a_value(function_only_params)  # 函数执行成功后，添加函数的参数排序后的键值对字符串到set中。
            if current_function_result_status.success is False and current_retry_times == max_retry_times:
                log_msg = f'函数 {self.consuming_function.__name__} 达到最大重试次数 {self._get_priority_conf(kw, "max_retry_times")} 后,仍然失败， 入参是  {function_only_params} '
                if self.consumer_params.is_push_to_dlx_queue_when_retry_max_times:
                    log_msg += f'  。发送到死信队列 {self._dlx_queue_name} 中'
                    self.publisher_of_dlx_queue.publish(kw['body'])
                # self.logger.critical(msg=f'{log_msg} \n', )
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)

            if self._get_priority_conf(kw, 'is_using_rpc_mode'):
                # print(function_result_status.get_status_dict(without_datetime_obj=
                if (current_function_result_status.success is False and current_retry_times == max_retry_times) or current_function_result_status.success is True:
                    with RedisMixin().redis_db_filter_and_rpc_result.pipeline() as p:
                        # RedisMixin().redis_db_frame.lpush(kw['body']['extra']['task_id'], json.dumps(function_result_status.get_status_dict(without_datetime_obj=True)))
                        # RedisMixin().redis_db_frame.expire(kw['body']['extra']['task_id'], 600)
                        current_function_result_status.rpc_result_expire_seconds = self.consumer_params.rpc_result_expire_seconds
                        p.lpush(kw['body']['extra']['task_id'],
                                Serialization.to_json_str(current_function_result_status.get_status_dict(without_datetime_obj=True)))
                        p.expire(kw['body']['extra']['task_id'], self.consumer_params.rpc_result_expire_seconds)
                        p.execute()

            with self._lock_for_count_execute_task_times_every_unit_time:
                self._execute_task_times_every_unit_time += 1
                self._consuming_function_cost_time_total_every_unit_time += time.time() - t_start_run_fun
                self._last_execute_task_time = time.time()
                if time.time() - self._current_time_for_execute_task_times_every_unit_time > self._unit_time_for_count:
                    avarage_function_spend_time = round(self._consuming_function_cost_time_total_every_unit_time / self._execute_task_times_every_unit_time, 4)
                    msg = f'{self._unit_time_for_count} 秒内执行了 {self._execute_task_times_every_unit_time} 次函数 [ {self.consuming_function.__name__} ] ,' \
                          f'函数平均运行耗时 {avarage_function_spend_time} 秒。 '
                    self.logger.info(msg)
                    if time.time() - self._last_show_remaining_execution_time > self._show_remaining_execution_time_interval:
                        self._msg_num_in_broker = self.publisher_of_same_queue.get_message_count()
                        if self._msg_num_in_broker != -1:  # 有的中间件无法统计或没实现统计队列剩余数量的，统一返回的是-1，不显示这句话。
                            # msg += f''' ，预计还需要 {time_util.seconds_to_hour_minute_second(self._msg_num_in_broker * avarage_function_spend_time / active_consumer_num)} 时间 才能执行完成 {self._msg_num_in_broker}个剩余的任务'''
                            need_time = time_util.seconds_to_hour_minute_second(self._msg_num_in_broker / (self._execute_task_times_every_unit_time / self._unit_time_for_count) /
                                                                                self._distributed_consumer_statistics.active_consumer_num)
                            msg += f''' 预计还需要 {need_time} 时间 才能执行完成 队列 {self.queue_name} 中的 {self._msg_num_in_broker} 个剩余任务'''
                            self.logger.info(msg)
                            self._last_show_remaining_execution_time = time.time()
                    self._current_time_for_execute_task_times_every_unit_time = time.time()
                    self._consuming_function_cost_time_total_every_unit_time = 0
                    self._execute_task_times_every_unit_time = 0
            self.user_custom_record_process_info_func(current_function_result_status)  # 两种方式都可以自定义,记录结果,建议继承方式,不使用boost中指定 user_custom_record_process_info_func
            if self.consumer_params.user_custom_record_process_info_func:
                self.consumer_params.user_custom_record_process_info_func(current_function_result_status)
        except BaseException as e:
            log_msg = f' error 严重错误 {type(e)} {e} '
            # self.logger.critical(msg=f'{log_msg} \n', exc_info=True)
            # self.error_file_logger.critical(msg=f'{log_msg} \n', exc_info=True)
            self.logger.critical(msg=log_msg, exc_info=True)
        fct = funboost_current_task()
        fct.set_fct_context(None)

    # noinspection PyProtectedMember
    def _run_consuming_function_with_confirm_and_retry(self, kw: dict, current_retry_times,
                                                       function_result_status: FunctionResultStatus, ):
        function_only_params = delete_keys_and_return_new_dict(kw['body']) if self._do_not_delete_extra_from_msg is False else kw['body']
        task_id = kw['body']['extra']['task_id']
        t_start = time.time()
        # function_result_status.run_times = current_retry_times + 1
        fct = funboost_current_task()
        fct_context = FctContext(function_params=function_only_params,
                                 full_msg=kw['body'],
                                 function_result_status=function_result_status,
                                 logger=self.logger, )

        try:
            function_run = self.consuming_function
            if self._consuming_function_is_asyncio:
                fct_context.asyncio_use_thread_concurrent_mode = True
                function_run = sync_or_async_fun_deco(function_run)
            else:
                fct_context.asynco_use_thread_concurrent_mode = False
            fct.set_fct_context(fct_context)
            function_timeout = self._get_priority_conf(kw, 'function_timeout')
            function_run = function_run if self.consumer_params.consumin_function_decorator is None else self.consumer_params.consumin_function_decorator(function_run)
            function_run = function_run if not function_timeout else self._concurrent_mode_dispatcher.timeout_deco(
                function_timeout)(function_run)

            if self.consumer_params.is_support_remote_kill_task:
                if kill_remote_task.RemoteTaskKiller(self.queue_name, task_id).judge_need_revoke_run():  # 如果远程指令杀死任务，如果还没开始运行函数，就取消运行
                    function_result_status._has_kill_task = True
                    self.logger.warning(f'取消运行 {task_id} {function_only_params}')
                    return function_result_status
                function_run = kill_remote_task.kill_fun_deco(task_id)(function_run)  # 用杀死装饰器包装起来在另一个线程运行函数,以便等待远程杀死。
            function_result_status.result = function_run(**self._convert_real_function_only_params_by_conusuming_function_kind(function_only_params))
            # if asyncio.iscoroutine(function_result_status.result):
            #     log_msg = f'''异步的协程消费函数必须使用 async 并发模式并发,请设置消费函数 {self.consuming_function.__name__} 的concurrent_mode 为 ConcurrentModeEnum.ASYNC 或 4'''
            #     # self.logger.critical(msg=f'{log_msg} \n')
            #     # self.error_file_logger.critical(msg=f'{log_msg} \n')
            #     self._log_critical(msg=log_msg)
            #     # noinspection PyProtectedMember,PyUnresolvedReferences
            #
            #     os._exit(4)
            function_result_status.success = True
            if self.consumer_params.log_level <= logging.DEBUG:
                result_str_to_be_print = str(function_result_status.result)[:100] if len(str(function_result_status.result)) < 100 else str(function_result_status.result)[:100] + '  。。。。。  '
                # print(funboost_current_task().task_id)
                # print(fct.function_result_status.task_id)
                # print(get_current_taskid())
                self.logger.debug(f' 函数 {self.consuming_function.__name__}  '
                                  f'第{current_retry_times + 1}次 运行, 正确了，函数运行时间是 {round(time.time() - t_start, 4)} 秒,入参是 {function_only_params} , '
                                  f'结果是  {result_str_to_be_print}   {self._get_concurrent_info()}  ')
        except BaseException as e:
            if isinstance(e, (ExceptionForRequeue,)):  # mongo经常维护备份时候插入不了或挂了，或者自己主动抛出一个ExceptionForRequeue类型的错误会重新入队，不受指定重试次数逇约束。
                log_msg = f'函数 [{self.consuming_function.__name__}] 中发生错误 {type(e)}  {e} 。消息重新放入当前队列 {self._queue_name}'
                # self.logger.critical(msg=f'{log_msg} \n')
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)
                time.sleep(0.1)  # 防止快速无限出错入队出队，导致cpu和中间件忙
                # 重回队列如果不修改task_id,insert插入函数消费状态结果到mongo会主键重复。要么保存函数消费状态使用replace，要么需要修改taskikd
                # kw_new = copy.deepcopy(kw)
                # new_task_id =f'{self._queue_name}_result:{uuid.uuid4()}'
                # kw_new['body']['extra']['task_id'] = new_task_id
                # self._requeue(kw_new)
                self._requeue(kw)
                function_result_status._has_requeue = True
            if isinstance(e, ExceptionForPushToDlxqueue):
                log_msg = f'函数 [{self.consuming_function.__name__}] 中发生错误 {type(e)}  {e}，消息放入死信队列 {self._dlx_queue_name}'
                # self.logger.critical(msg=f'{log_msg} \n')
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)
                self.publisher_of_dlx_queue.publish(kw['body'])  # 发布到死信队列，不重回当前队列
                function_result_status._has_to_dlx_queue = True
            if isinstance(e, kill_remote_task.TaskHasKilledError):
                log_msg = f'task_id 为 {task_id} , 函数 [{self.consuming_function.__name__}] 运行入参 {function_only_params}   ，已被远程指令杀死 {type(e)}  {e}'
                # self.logger.critical(msg=f'{log_msg} ')
                # self.error_file_logger.critical(msg=f'{log_msg} ')
                self.logger.critical(msg=log_msg)
                function_result_status._has_kill_task = True
            if isinstance(e, (ExceptionForRequeue, ExceptionForPushToDlxqueue, kill_remote_task.TaskHasKilledError)):
                return function_result_status
            log_msg = f'''函数 {self.consuming_function.__name__}  第{current_retry_times + 1}次运行发生错误，
                          函数运行时间是 {round(time.time() - t_start, 4)} 秒,  入参是  {function_only_params}    
                          {type(e)} {e} '''
            # self.logger.error(msg=f'{log_msg} \n', exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            # self.error_file_logger.error(msg=f'{log_msg} \n', exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            self.logger.error(msg=log_msg, exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            # traceback.print_exc()
            function_result_status.exception = f'{e.__class__.__name__}    {str(e)}'
            function_result_status.result = FunctionResultStatus.FUNC_RUN_ERROR
        return function_result_status

    # noinspection PyProtectedMember
    async def _async_run(self, kw: dict, ):
        # """虽然和上面有点大面积重复相似，这个是为了asyncio模式的，asyncio模式真的和普通同步模式的代码思维和形式区别太大，
        # 框架实现兼容async的消费函数很麻烦复杂，连并发池都要单独写"""
        try:
            t_start_run_fun = time.time()
            max_retry_times = self._get_priority_conf(kw, 'max_retry_times')
            current_function_result_status = FunctionResultStatus(self.queue_name, self.consuming_function.__name__, kw['body'], )
            current_retry_times = 0
            function_only_params = delete_keys_and_return_new_dict(kw['body'])
            for current_retry_times in range(max_retry_times + 1):
                current_function_result_status.run_times = current_retry_times + 1
                current_function_result_status.run_status = RunStatus.running
                self._result_persistence_helper.save_function_result_to_mongo(current_function_result_status)
                current_function_result_status = await self._async_run_consuming_function_with_confirm_and_retry(kw, current_retry_times=current_retry_times,
                                                                                                                 function_result_status=current_function_result_status)
                if current_function_result_status.success is True or current_retry_times == max_retry_times or current_function_result_status._has_requeue:
                    break
                else:
                    if self.consumer_params.retry_interval:
                        await asyncio.sleep(self.consumer_params.retry_interval)

            if not (current_function_result_status._has_requeue and self.BROKER_KIND in [BrokerEnum.RABBITMQ_AMQPSTORM, BrokerEnum.RABBITMQ_PIKA, BrokerEnum.RABBITMQ_RABBITPY]):
                await simple_run_in_executor(self._confirm_consume, kw)
            current_function_result_status.run_status = RunStatus.finish
            await simple_run_in_executor(self._result_persistence_helper.save_function_result_to_mongo, current_function_result_status)
            if self._get_priority_conf(kw, 'do_task_filtering'):
                # self._redis_filter.add_a_value(function_only_params)  # 函数执行成功后，添加函数的参数排序后的键值对字符串到set中。
                await simple_run_in_executor(self._redis_filter.add_a_value, function_only_params)
            if current_function_result_status.success is False and current_retry_times == max_retry_times:
                log_msg = f'函数 {self.consuming_function.__name__} 达到最大重试次数 {self._get_priority_conf(kw, "max_retry_times")} 后,仍然失败， 入参是  {function_only_params} '
                if self.consumer_params.is_push_to_dlx_queue_when_retry_max_times:
                    log_msg += f'  。发送到死信队列 {self._dlx_queue_name} 中'
                    await simple_run_in_executor(self.publisher_of_dlx_queue.publish, kw['body'])
                # self.logger.critical(msg=f'{log_msg} \n', )
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)

                # self._confirm_consume(kw)  # 错得超过指定的次数了，就确认消费了。
            if self._get_priority_conf(kw, 'is_using_rpc_mode'):
                def push_result():
                    with RedisMixin().redis_db_filter_and_rpc_result.pipeline() as p:
                        current_function_result_status.rpc_result_expire_seconds = self.consumer_params.rpc_result_expire_seconds
                        p.lpush(kw['body']['extra']['task_id'],
                                Serialization.to_json_str(current_function_result_status.get_status_dict(without_datetime_obj=True)))
                        p.expire(kw['body']['extra']['task_id'], self.consumer_params.rpc_result_expire_seconds)
                        p.execute()

                if (current_function_result_status.success is False and current_retry_times == max_retry_times) or current_function_result_status.success is True:
                    await simple_run_in_executor(push_result)

            # 异步执行不存在线程并发，不需要加锁。
            self._execute_task_times_every_unit_time += 1
            self._consuming_function_cost_time_total_every_unit_time += time.time() - t_start_run_fun
            self._last_execute_task_time = time.time()
            if time.time() - self._current_time_for_execute_task_times_every_unit_time > self._unit_time_for_count:
                avarage_function_spend_time = round(self._consuming_function_cost_time_total_every_unit_time / self._execute_task_times_every_unit_time, 4)
                msg = f'{self._unit_time_for_count} 秒内执行了 {self._execute_task_times_every_unit_time} 次函数 [ {self.consuming_function.__name__} ] ,' \
                      f'函数平均运行耗时 {avarage_function_spend_time} 秒。 '
                self.logger.info(msg)
                if self._msg_num_in_broker != -1 and time.time() - self._last_show_remaining_execution_time > self._show_remaining_execution_time_interval:  # 有的中间件无法统计或没实现统计队列剩余数量的，统一返回的是-1，不显示这句话。
                    # msg += f''' ，预计还需要 {time_util.seconds_to_hour_minute_second(self._msg_num_in_broker * avarage_function_spend_time / active_consumer_num)} 时间 才能执行完成 {self._msg_num_in_broker}个剩余的任务'''
                    need_time = time_util.seconds_to_hour_minute_second(self._msg_num_in_broker / (self._execute_task_times_every_unit_time / self._unit_time_for_count) /
                                                                        self._distributed_consumer_statistics.active_consumer_num)
                    msg += f''' 预计还需要 {need_time} 时间 才能执行完成 队列 {self.queue_name} 中的 {self._msg_num_in_broker} 个剩余任务'''
                    self.logger.info(msg)
                    self._last_show_remaining_execution_time = time.time()
                self._current_time_for_execute_task_times_every_unit_time = time.time()
                self._consuming_function_cost_time_total_every_unit_time = 0
                self._execute_task_times_every_unit_time = 0

            self.user_custom_record_process_info_func(current_function_result_status)  # 两种方式都可以自定义,记录结果.建议使用文档4.21.b的方式继承来重写
            await self.aio_user_custom_record_process_info_func(current_function_result_status)
            if self.consumer_params.user_custom_record_process_info_func:
                self.consumer_params.user_custom_record_process_info_func(current_function_result_status)

        except BaseException as e:
            log_msg = f' error 严重错误 {type(e)} {e} '
            # self.logger.critical(msg=f'{log_msg} \n', exc_info=True)
            # self.error_file_logger.critical(msg=f'{log_msg} \n', exc_info=True)
            self.logger.critical(msg=log_msg, exc_info=True)
        fct = funboost_current_task()
        fct.set_fct_context(None)

    # noinspection PyProtectedMember
    async def _async_run_consuming_function_with_confirm_and_retry(self, kw: dict, current_retry_times,
                                                                   function_result_status: FunctionResultStatus, ):
        """虽然和上面有点大面积重复相似，这个是为了asyncio模式的，asyncio模式真的和普通同步模式的代码思维和形式区别太大，
        框架实现兼容async的消费函数很麻烦复杂，连并发池都要单独写"""
        function_only_params = delete_keys_and_return_new_dict(kw['body']) if self._do_not_delete_extra_from_msg is False else kw['body']
        function_result_status.run_times = current_retry_times + 1
        # noinspection PyBroadException
        t_start = time.time()
        fct = funboost_current_task()
        fct_context = FctContext(function_params=function_only_params,
                                 full_msg=kw['body'],
                                 function_result_status=function_result_status,
                                 logger=self.logger, )
        fct.set_fct_context(fct_context)
        try:
            corotinue_obj = self.consuming_function(**self._convert_real_function_only_params_by_conusuming_function_kind(function_only_params))
            if not asyncio.iscoroutine(corotinue_obj):
                log_msg = f'''当前设置的并发模式为 async 并发模式，但消费函数不是异步协程函数，请不要把消费函数 {self.consuming_function.__name__} 的 concurrent_mode 设置错误'''
                # self.logger.critical(msg=f'{log_msg} \n')
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)
                # noinspection PyProtectedMember,PyUnresolvedReferences
                os._exit(444)
            if not self.consumer_params.function_timeout:
                rs = await corotinue_obj
                # rs = await asyncio.wait_for(corotinue_obj, timeout=4)
            else:
                rs = await asyncio.wait_for(corotinue_obj, timeout=self.consumer_params.function_timeout)
            function_result_status.result = rs
            function_result_status.success = True
            if self.consumer_params.log_level <= logging.DEBUG:
                result_str_to_be_print = str(rs)[:100] if len(str(rs)) < 100 else str(rs)[:100] + '  。。。。。  '
                self.logger.debug(f' 函数 {self.consuming_function.__name__}  '
                                  f'第{current_retry_times + 1}次 运行, 正确了，函数运行时间是 {round(time.time() - t_start, 4)} 秒,'
                                  f'入参是 【 {function_only_params} 】 ,结果是 {result_str_to_be_print}  。 {corotinue_obj} ')
        except BaseException as e:
            if isinstance(e, (ExceptionForRequeue,)):  # mongo经常维护备份时候插入不了或挂了，或者自己主动抛出一个ExceptionForRequeue类型的错误会重新入队，不受指定重试次数逇约束。
                log_msg = f'函数 [{self.consuming_function.__name__}] 中发生错误 {type(e)}  {e} 。 消息重新放入当前队列 {self._queue_name}'
                # self.logger.critical(msg=f'{log_msg} \n')
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)
                # time.sleep(1)  # 防止快速无限出错入队出队，导致cpu和中间件忙
                await asyncio.sleep(0.1)
                # return self._requeue(kw)
                await simple_run_in_executor(self._requeue, kw)
                function_result_status._has_requeue = True
            if isinstance(e, ExceptionForPushToDlxqueue):
                log_msg = f'函数 [{self.consuming_function.__name__}] 中发生错误 {type(e)}  {e}，消息放入死信队列 {self._dlx_queue_name}'
                # self.logger.critical(msg=f'{log_msg} \n')
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)
                await simple_run_in_executor(self.publisher_of_dlx_queue.publish, kw['body'])  # 发布到死信队列，不重回当前队列
                function_result_status._has_to_dlx_queue = True
            if isinstance(e, (ExceptionForRequeue, ExceptionForPushToDlxqueue)):
                return function_result_status
            log_msg = f'''函数 {self.consuming_function.__name__}  第{current_retry_times + 1}次运行发生错误，
                          函数运行时间是 {round(time.time() - t_start, 4)} 秒,  入参是  {function_only_params}     
                          原因是 {type(e)} {e} '''
            # self.logger.error(msg=f'{log_msg} \n', exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            # self.error_file_logger.error(msg=f'{log_msg} \n', exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            self.logger.error(msg=log_msg, exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            function_result_status.exception = f'{e.__class__.__name__}    {str(e)}'
            function_result_status.result = FunctionResultStatus.FUNC_RUN_ERROR
        return function_result_status

    @abc.abstractmethod
    def _confirm_consume(self, kw):
        """确认消费"""
        raise NotImplementedError

    def check_heartbeat_and_message_count(self):
        self._msg_num_in_broker = self.publisher_of_same_queue.get_message_count()
        if time.time() - self._last_timestamp_print_msg_num > 600:
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
        log_msg = f''' 现在时间是 {time_util.DatetimeConverter().datetime_str} ,比此任务规定的本应该的运行时间 {event.scheduled_run_time} 相比 超过了指定的 {misfire_grace_time} 秒,放弃执行此任务 
                             {event.function_kwargs["kw"]["body"]} '''
        # self.logger.critical(msg=f'{log_msg} \n')
        # self.error_file_logger.critical(msg=f'{log_msg} \n')
        self.logger.critical(msg=log_msg)
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
        """从远程机器可以设置队列为暂停消费状态，funboost框架会自动停止消费，此功能需要配置好redis"""
        RedisMixin().redis_db_frame.set(self._redis_key_pause_flag, 1)

    def continue_consume(self):
        """从远程机器可以设置队列为暂停消费状态，funboost框架会自动继续消费，此功能需要配置好redis"""
        RedisMixin().redis_db_frame.set(self._redis_key_pause_flag, 0)

    @decorators.FunctionResultCacher.cached_function_result_for_a_time(120)
    def _judge_is_daylight(self):
        if self.consumer_params.is_do_not_run_by_specify_time_effect and (
                self.consumer_params.do_not_run_by_specify_time[0] < time_util.DatetimeConverter().time_str < self.consumer_params.do_not_run_by_specify_time[1]):
            self.logger.warning(
                f'现在时间是 {time_util.DatetimeConverter()} ，现在时间是在 {self.consumer_params.do_not_run_by_specify_time} 之间，不运行')
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
            # print(message_count,self._last_execute_task_time,time.time() - self._last_execute_task_time,no_task_time)
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
class ConcurrentModeDispatcher(FunboostFileLoggerMixin):

    def __init__(self, consumerx: AbstractConsumer):
        self.consumer = consumerx
        self._concurrent_mode = self.consumer.consumer_params.concurrent_mode
        self.timeout_deco = None
        if self._concurrent_mode in (ConcurrentModeEnum.THREADING, ConcurrentModeEnum.SINGLE_THREAD):
            # self.timeout_deco = decorators.timeout
            self.timeout_deco = func_set_timeout  # 这个超时装饰器性能好很多。
        elif self._concurrent_mode == ConcurrentModeEnum.GEVENT:
            from funboost.concurrent_pool.custom_gevent_pool_executor import gevent_timeout_deco
            self.timeout_deco = gevent_timeout_deco
        elif self._concurrent_mode == ConcurrentModeEnum.EVENTLET:
            from funboost.concurrent_pool.custom_evenlet_pool_executor import evenlet_timeout_deco
            self.timeout_deco = evenlet_timeout_deco
        # self.logger.info(f'{self.consumer} 设置并发模式 {self.consumer.consumer_params.concurrent_mode}')

    def check_all_concurrent_mode(self):
        if GlobalVars.global_concurrent_mode is not None and \
                self.consumer.consumer_params.concurrent_mode != GlobalVars.global_concurrent_mode:
            # print({self.consumer._concurrent_mode, ConsumersManager.global_concurrent_mode})
            if not {self.consumer.consumer_params.concurrent_mode, GlobalVars.global_concurrent_mode}.issubset({ConcurrentModeEnum.THREADING,
                                                                                                                ConcurrentModeEnum.ASYNC,
                                                                                                                ConcurrentModeEnum.SINGLE_THREAD}):
                # threding、asyncio、solo 这几种模式可以共存。但同一个解释器不能同时选择 gevent + 其它并发模式，也不能 eventlet + 其它并发模式。
                raise ValueError('''由于猴子补丁的原因，同一解释器中不可以设置两种并发类型,请查看显示的所有消费者的信息，
                                 搜索 concurrent_mode 关键字，确保当前解释器内的所有消费者的并发模式只有一种(或可以共存),
                                 asyncio threading single_thread 并发模式可以共存，但gevent和threading不可以共存，
                                 gevent和eventlet不可以共存''')

        GlobalVars.global_concurrent_mode = self.consumer.consumer_params.concurrent_mode

    def build_pool(self):
        if self.consumer._concurrent_pool is not None:
            return self.consumer._concurrent_pool

        pool_type = None  # 是按照ThreadpoolExecutor写的三个鸭子类，公有方法名和功能写成完全一致，可以互相替换。
        if self._concurrent_mode == ConcurrentModeEnum.THREADING:
            # pool_type = CustomThreadPoolExecutor
            # pool_type = BoundedThreadPoolExecutor
            pool_type = FlexibleThreadPool
        elif self._concurrent_mode == ConcurrentModeEnum.GEVENT:
            from funboost.concurrent_pool.custom_gevent_pool_executor import get_gevent_pool_executor
            pool_type = get_gevent_pool_executor
        elif self._concurrent_mode == ConcurrentModeEnum.EVENTLET:
            from funboost.concurrent_pool.custom_evenlet_pool_executor import get_eventlet_pool_executor
            pool_type = get_eventlet_pool_executor
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
            self.consumer._concurrent_pool = self.consumer.consumer_params.specify_concurrent_pool or pool_type(
                self.consumer.consumer_params.concurrent_num, loop=self.consumer.consumer_params.specify_async_loop)
        else:
            # print(pool_type)
            self.consumer._concurrent_pool = self.consumer.consumer_params.specify_concurrent_pool or pool_type(self.consumer.consumer_params.concurrent_num)
        # print(self._concurrent_mode,self.consumer._concurrent_pool)
        return self.consumer._concurrent_pool

    # def schedulal_task_with_no_block(self):
    #     if ConsumersManager.schedual_task_always_use_thread:
    #         t = Thread(target=self.consumer.keep_circulating(1)(self.consumer._shedual_task))
    #         ConsumersManager.schedulal_thread_to_be_join.append(t)
    #         t.start()
    #     else:
    #         if self._concurrent_mode in [ConcurrentModeEnum.THREADING, ConcurrentModeEnum.ASYNC,
    #                                      ConcurrentModeEnum.SINGLE_THREAD, ]:
    #             t = Thread(target=self.consumer.keep_circulating(1)(self.consumer._shedual_task))
    #             ConsumersManager.schedulal_thread_to_be_join.append(t)
    #             t.start()
    #         elif self._concurrent_mode == ConcurrentModeEnum.GEVENT:
    #             import gevent
    #             g = gevent.spawn(self.consumer.keep_circulating(1)(self.consumer._shedual_task), )
    #             ConsumersManager.schedulal_thread_to_be_join.append(g)
    #         elif self._concurrent_mode == ConcurrentModeEnum.EVENTLET:
    #             import eventlet
    #             g = eventlet.spawn(self.consumer.keep_circulating(1)(self.consumer._shedual_task), )
    #             ConsumersManager.schedulal_thread_to_be_join.append(g)

    def schedulal_task_with_no_block(self):
        self.consumer.keep_circulating(1, block=False, daemon=False)(self.consumer._shedual_task)()


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


class DistributedConsumerStatistics(RedisMixin, FunboostFileLoggerMixin):
    """
    为了兼容模拟mq的中间件（例如redis，他没有实现amqp协议，redis的list结构和真mq差远了），获取一个队列有几个连接活跃消费者数量。
    分布式环境中的消费者统计。主要目的有3点

    1、统计活跃消费者数量用于分布式控频。
        获取分布式的消费者数量后，用于分布式qps控频。如果不获取全环境中的消费者数量，则只能用于当前进程中的消费控频。
        即使只有一台机器，例如把xx.py启动3次，xx.py的consumer设置qps为10，如果不使用分布式控频，会1秒钟最终运行30次函数而不是10次。

    2、记录分布式环境中的活跃消费者的所有消费者 id，如果消费者id不在此里面说明已掉线或关闭，消息可以重新分发，用于不支持服务端天然消费确认的中间件。

    3、从redis中获取停止和暂停状态，以便支持在别的地方发送命令停止或者暂停消费。
    """
    SHOW_CONSUMER_NUM_INTERVAL = 600
    HEARBEAT_EXPIRE_SECOND = 25
    SEND_HEARTBEAT_INTERVAL = 10

    if HEARBEAT_EXPIRE_SECOND < SEND_HEARTBEAT_INTERVAL * 2:
        raise ValueError(f'HEARBEAT_EXPIRE_SECOND:{HEARBEAT_EXPIRE_SECOND} , SEND_HEARTBEAT_INTERVAL:{SEND_HEARTBEAT_INTERVAL} ')


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
        self._consumer.keep_circulating(self.SEND_HEARTBEAT_INTERVAL, block=False, daemon=False)(self.send_heartbeat)()

    def _send_heartbeat_with_dict_value(self, redis_key, ):
        # 发送当前消费者进程心跳的，值是字典，按一个机器或者一个队列运行了哪些进程。

        results = self.redis_db_frame.smembers(redis_key)
        with self.redis_db_frame.pipeline() as p:
            for result in results:
                result_dict = Serialization.to_dict(result)
                if self.timestamp() - result_dict['hearbeat_timestamp'] > self.HEARBEAT_EXPIRE_SECOND \
                        or self._consumer_identification_map['consumer_uuid'] == result_dict['consumer_uuid']:
                    # 因为这个是10秒钟运行一次，15秒还没更新，那肯定是掉线了。如果消费者本身是自己也先删除。
                    p.srem(redis_key, result)
            self._consumer_identification_map['hearbeat_datetime_str'] = time_util.DatetimeConverter().datetime_str
            self._consumer_identification_map['hearbeat_timestamp'] = self.timestamp()
            value = Serialization.to_json_str(self._consumer_identification_map, )
            p.sadd(redis_key, value)
            p.execute()

    def send_heartbeat(self):
        # 根据队列名心跳的，值是字符串，方便值作为其他redis的键名

        results = self.redis_db_frame.smembers(self._redis_key_name)
        with self.redis_db_frame.pipeline() as p:
            for result in results:
                if self.timestamp() - float(result.split('&&')[-1]) > self.HEARBEAT_EXPIRE_SECOND or \
                        self._consumer_identification == result.split('&&')[0]:  # 因为这个是10秒钟运行一次，15秒还没更新，那肯定是掉线了。如果消费者本身是自己也先删除。
                    p.srem(self._redis_key_name, result)
            p.sadd(self._redis_key_name, f'{self._consumer_identification}&&{self.timestamp()}')
            p.execute()

        self._send_heartbeat_with_dict_value(self._queue__consumer_identification_map_key_name)
        self._send_heartbeat_with_dict_value(self._server__consumer_identification_map_key_name)
        self._show_active_consumer_num()
        self._get_stop_and_pause_flag_from_redis()


    def _show_active_consumer_num(self):
        self.active_consumer_num = self.redis_db_frame.scard(self._redis_key_name) or 1
        if time.time() - self._last_show_consumer_num_timestamp > self.SHOW_CONSUMER_NUM_INTERVAL:
            self.logger.info(f'分布式所有环境中使用 {self._queue_name} 队列的，一共有 {self.active_consumer_num} 个消费者')
            self._last_show_consumer_num_timestamp = time.time()

    def get_queue_heartbeat_ids(self, without_time: bool):
        if without_time:
            return [idx.split('&&')[0] for idx in self.redis_db_frame.smembers(self._redis_key_name)]
        else:
            return [idx for idx in self.redis_db_frame.smembers(self._redis_key_name)]

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

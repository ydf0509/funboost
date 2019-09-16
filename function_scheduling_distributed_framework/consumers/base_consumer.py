# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:11
import abc
import atexit
import copy
import json

import time
import traceback
from collections import Callable
from functools import wraps
import threading
from threading import Lock, Thread
import eventlet
import gevent
from pymongo.errors import PyMongoError

from function_scheduling_distributed_framework.concurrent_pool.bounded_threadpoolexcutor import BoundedThreadPoolExecutor
from function_scheduling_distributed_framework.concurrent_pool.custom_evenlet_pool_executor import evenlet_timeout_deco, check_evenlet_monkey_patch, CustomEventletPoolExecutor
from function_scheduling_distributed_framework.concurrent_pool.custom_gevent_pool_executor import gevent_timeout_deco, GeventPoolExecutor, check_gevent_monkey_patch
from function_scheduling_distributed_framework.concurrent_pool.custom_threadpool_executor import CustomThreadPoolExecutor, check_not_monkey
from function_scheduling_distributed_framework.consumers.redis_filter import RedisFilter
from function_scheduling_distributed_framework.factories.publisher_factotry import get_publisher
from function_scheduling_distributed_framework.utils import LoggerLevelSetterMixin, LogManager, decorators, nb_print, LoggerMixin, time_util


def delete_keys_and_return_new_dict(dictx: dict, keys: list):
    dict_new = copy.copy(dictx)  # 主要是去掉一级键 publish_time，浅拷贝即可。
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


class AbstractConsumer(LoggerLevelSetterMixin, metaclass=abc.ABCMeta, ):
    consumers_queue__info_map = dict()
    time_interval_for_check_do_not_run_time = 60
    BROKER_KIND = None

    @property
    @decorators.synchronized
    def publisher_of_same_queue(self):
        if not self._publisher_of_same_queue:
            self._publisher_of_same_queue = get_publisher(self._queue_name, broker_kind=self.BROKER_KIND)
            if self._msg_expire_senconds:
                self._publisher_of_same_queue.set_is_add_publish_time()
        return self._publisher_of_same_queue

    @classmethod
    def join_shedual_task_thread(cls):
        """

        :return:
        """
        """
        def ff():
            RabbitmqConsumer('queue_test', consuming_function=f3, threads_num=20, msg_schedule_time_intercal=2, log_level=10, logger_prefix='yy平台消费', is_consuming_function_use_multi_params=True).start_consuming_message()
            RabbitmqConsumer('queue_test2', consuming_function=f4, threads_num=20, msg_schedule_time_intercal=4, log_level=10, logger_prefix='zz平台消费', is_consuming_function_use_multi_params=True).start_consuming_message()
            AbstractConsumer.join_shedual_task_thread()            # 如果开多进程启动消费者，在linux上需要这样写下这一行。


        if __name__ == '__main__':
            [Process(target=ff).start() for _ in range(4)]

        """
        ConcurrentModeDispatcher.join()

    @classmethod
    def show_all_consumer_info(cls):
        nb_print(f'当前解释器内，所有消费者的信息是：\n  {json.dumps(cls.consumers_queue__info_map, indent=4, ensure_ascii=False)}')

    def __init__(self, queue_name, *, consuming_function: Callable = None, function_timeout=0, threads_num=50, specify_threadpool=None, concurrent_mode=1,
                 max_retry_times=3, log_level=10, is_print_detail_exception=True, msg_schedule_time_intercal=0.0, msg_expire_senconds=0,
                 logger_prefix='', create_logger_file=True, do_task_filtering=False, is_consuming_function_use_multi_params=True,
                 is_do_not_run_by_specify_time_effect=False, do_not_run_by_specify_time=('10:00:00', '22:00:00'), schedule_tasks_on_main_thread=False):
        """
        :param queue_name:
        :param consuming_function: 处理消息的函数。
        :param function_timeout : 超时秒数，函数运行超过这个时间，则自动杀死函数。为0是不限制。
        :param threads_num:
        :param specify_threadpool:使用指定的线程池，可以多个消费者共使用一个线程池，不为None时候。threads_num失效
        :param concurrent_mode:并发模式，暂时支持 线程 、gevent、eventlet三种模式。  1线程  2 gevent 3 evenlet
        :param max_retry_times:
        :param log_level:
        :param is_print_detail_exception:
        :param msg_schedule_time_intercal:消息调度的时间间隔，用于控频
        :param logger_prefix: 日志前缀，可使不同的消费者生成不同的日志
        :param create_logger_file : 是否创建文件日志
        :param do_task_filtering :是否执行基于函数参数的任务过滤
        :is_consuming_function_use_multi_params  函数的参数是否是传统的多参数，不为单个body字典表示多个参数。
        :param is_do_not_run_by_specify_time_effect :是否使不运行的时间段生效
        :param do_not_run_by_specify_time   :不运行的时间段
        :param schedule_tasks_on_main_thread :直接在主线程调度任务，意味着不能直接在当前主线程同时开启两个消费者。
        """
        self.__class__.consumers_queue__info_map[queue_name] = current_queue__info_dict = copy.copy(locals())
        current_queue__info_dict['consuming_function'] = str(consuming_function)  # consuming_function.__name__
        current_queue__info_dict.pop('self')
        current_queue__info_dict['broker_kind'] = self.__class__.BROKER_KIND
        current_queue__info_dict['class_name'] = self.__class__.__name__
        if concurrent_mode == 1:
            current_queue__info_dict['concurrent_mode_name'] = 'threading'
        elif concurrent_mode == 2:
            current_queue__info_dict['concurrent_mode_name'] = 'gevent'
        elif concurrent_mode == 3:
            current_queue__info_dict['concurrent_mode_name'] = 'eventlet'

        self._queue_name = queue_name
        self.queue_name = queue_name  # 可以换成公有的，免得外部访问有警告。
        self.consuming_function = consuming_function
        self._function_timeout = function_timeout
        self._threads_num = threads_num
        self._specify_threadpool = specify_threadpool
        self._threadpool = None  # 单独加一个检测消息数量和心跳的线程
        self._concurrent_mode = concurrent_mode
        self._max_retry_times = max_retry_times
        self._is_print_detail_exception = is_print_detail_exception
        self._msg_schedule_time_intercal = msg_schedule_time_intercal if msg_schedule_time_intercal > 0.001 else 0.001
        self._msg_expire_senconds = msg_expire_senconds

        if self._concurrent_mode not in (1, 2, 3):
            raise ValueError('设置的并发模式不正确')
        self._concurrent_mode_dispatcher = ConcurrentModeDispatcher(self)

        self._logger_prefix = logger_prefix
        self._log_level = log_level
        if logger_prefix != '':
            logger_prefix += '--'
        logger_name = f'{logger_prefix}{self.__class__.__name__}--{self._concurrent_mode_dispatcher.concurrent_name}--{queue_name}'
        # nb_print(logger_name)
        self.logger = LogManager(logger_name).get_logger_and_add_handlers(log_level, log_filename=f'{logger_name}.log' if create_logger_file else None)
        self.logger.info(f'{self.__class__} 被实例化')

        self._do_task_filtering = do_task_filtering
        self._redis_filter_key_name = f'filter:{queue_name}'
        self._redis_filter = RedisFilter(self._redis_filter_key_name)

        self._is_consuming_function_use_multi_params = is_consuming_function_use_multi_params

        self._lock_for_pika = Lock()

        self._execute_task_times_every_minute = 0  # 每分钟执行了多少次任务。
        self._lock_for_count_execute_task_times_every_minute = Lock()
        self._current_time_for_execute_task_times_every_minute = time.time()

        self._msg_num_in_broker = 0
        self._last_timestamp_when_has_task_in_queue = 0
        self._last_timestamp_print_msg_num = 0

        self._is_do_not_run_by_specify_time_effect = is_do_not_run_by_specify_time_effect
        self._do_not_run_by_specify_time = do_not_run_by_specify_time  # 可以设置在指定的时间段不运行。
        self._schedule_tasks_on_main_thread = schedule_tasks_on_main_thread

        self.stop_flag = False

        self._publisher_of_same_queue = None

        self.custom_init()

    @property
    @decorators.synchronized
    def threadpool(self):
        return self._concurrent_mode_dispatcher.build_pool()

    def custom_init(self):
        pass

    def keep_circulating(self, time_sleep=0.001, exit_if_function_run_sucsess=False, is_display_detail_exception=True):
        """间隔一段时间，一直循环运行某个方法的装饰器
        :param time_sleep :循环的间隔时间
        :param is_display_detail_exception
        :param exit_if_function_run_sucsess :如果成功了就退出循环
        """

        def _keep_circulating(func):
            # noinspection PyBroadException
            @wraps(func)
            def __keep_circulating(*args, **kwargs):
                while 1:
                    if self.stop_flag:
                        break
                    try:
                        result = func(*args, **kwargs)
                        if exit_if_function_run_sucsess:
                            return result
                    except Exception as e:
                        msg = func.__name__ + '   运行出错\n ' + traceback.format_exc(limit=10) if is_display_detail_exception else str(e)
                        self.logger.error(msg)
                    finally:
                        time.sleep(time_sleep)

            return __keep_circulating

        return _keep_circulating

    def start_consuming_message(self):
        self.logger.warning(f'开始消费 {self._queue_name} 中的消息')
        # self.threadpool.submit(decorators.keep_circulating(20)(self.check_heartbeat_and_message_count))
        self.threadpool.submit(self.keep_circulating(20)(self.check_heartbeat_and_message_count))
        if self._schedule_tasks_on_main_thread:
            # decorators.keep_circulating(1)(self._shedual_task)()
            self.keep_circulating(1)(self._shedual_task)()
        else:
            # t = Thread(target=decorators.keep_circulating(1)(self._shedual_task))
            self._concurrent_mode_dispatcher.schedulal_task_with_no_block()

    @abc.abstractmethod
    def _shedual_task(self):
        raise NotImplementedError

    def _run_consuming_function_with_confirm_and_retry(self, kw: dict, current_retry_times=0, ):
        if self._do_task_filtering and self._redis_filter.check_value_exists(kw['body']):  # 对函数的参数进行检查，过滤已经执行过并且成功的任务。
            self.logger.info(f'redis的 [{self._redis_filter_key_name}] 键 中 过滤任务 {kw["body"]}')
            self._confirm_consume(kw)
            return
        with self._lock_for_count_execute_task_times_every_minute:
            self._execute_task_times_every_minute += 1
            if time.time() - self._current_time_for_execute_task_times_every_minute > 60:
                self.logger.info(
                    f'一分钟内执行了 {self._execute_task_times_every_minute} 次函数 [ {self.consuming_function.__name__} ] ,预计'
                    f'还需要 {time_util.seconds_to_hour_minute_second(self._msg_num_in_broker / self._execute_task_times_every_minute * 60)} 时间'
                    f'才能执行完成 {self._msg_num_in_broker}个剩余的任务 ')
                self._current_time_for_execute_task_times_every_minute = time.time()
                self._execute_task_times_every_minute = 0

        if current_retry_times < self._max_retry_times + 1:
            # noinspection PyBroadException
            t_start = time.time()
            try:
                function_run = self.consuming_function if self._function_timeout == 0 else self._concurrent_mode_dispatcher.timeout_deco(self._function_timeout)(self.consuming_function)
                if self._is_consuming_function_use_multi_params:  # 消费函数使用传统的多参数形式
                    function_run(**delete_keys_and_return_new_dict(kw['body'], ['publish_time', 'publish_time_format']))
                else:
                    function_run(delete_keys_and_return_new_dict(kw['body'], ['publish_time', 'publish_time_format']))  # 消费函数使用单个参数，参数自身是一个字典，由键值对表示各个参数。
                self._confirm_consume(kw)
                if self._do_task_filtering:
                    self._redis_filter.add_a_value(kw['body'])  # 函数执行成功后，添加函数的参数排序后的键值对字符串到set中。

                # self.logger.debug(f'{self._concurrent_mode_dispatcher.get_concurrent_info()}  函数 {self.consuming_function.__name__}  '
                #                   f'第{current_retry_times + 1}次 运行, 正确了，函数运行时间是 {round(time.time() - t_start, 4)} 秒,入参是 【 {kw["body"]} 】')
                self.logger.debug(f' 函数 {self.consuming_function.__name__}  '
                                  f'第{current_retry_times + 1}次 运行, 正确了，函数运行时间是 {round(time.time() - t_start, 4)} 秒,入参是 【 {kw["body"]} 】。  {self._concurrent_mode_dispatcher.get_concurrent_info()}')
            except Exception as e:
                if isinstance(e, (PyMongoError, ExceptionForRequeue)):  # mongo经常维护备份时候插入不了或挂了，或者自己主动抛出一个ExceptionForRequeue类型的错误会重新入队，不受指定重试次数逇约束。
                    self.logger.critical(f'函数 [{self.consuming_function.__name__}] 中发生错误 {type(e)}  {e}')
                    return self._requeue(kw)
                self.logger.error(f'函数 {self.consuming_function.__name__}  第{current_retry_times + 1}次发生错误，'
                                  f'函数运行时间是 {round(time.time() - t_start, 4)} 秒,\n  入参是 【 {kw["body"]} 】   \n 原因是 {type(e)} {e} ', exc_info=self._is_print_detail_exception)
                self._run_consuming_function_with_confirm_and_retry(kw, current_retry_times + 1)
        else:
            self.logger.critical(f'函数 {self.consuming_function.__name__} 达到最大重试次数 {self._max_retry_times} 后,仍然失败， 入参是 【 {kw["body"]} 】')
            self._confirm_consume(kw)  # 错得超过指定的次数了，就确认消费了。

    @abc.abstractmethod
    def _confirm_consume(self, kw):
        """确认消费"""
        raise NotImplementedError

        # noinspection PyUnusedLocal

    def check_heartbeat_and_message_count(self):
        self._msg_num_in_broker = self.publisher_of_same_queue.get_message_count()
        if time.time() - self._last_timestamp_print_msg_num > 60:
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
        if self._msg_expire_senconds != 0 and time.time() - self._msg_expire_senconds > kw['body']['publish_time']:
            self.logger.warning(f'消息发布时戳是 {kw["body"]["publish_time"]} {kw["body"].get("publish_time_format", "")},距离现在 {round(time.time() - kw["body"]["publish_time"], 4)} 秒 ,'
                                f'超过了指定的 {self._msg_expire_senconds} 秒，丢弃任务')
            self._confirm_consume(kw)
            return 0
        self.threadpool.submit(self._run_consuming_function_with_confirm_and_retry, kw)
        time.sleep(self._msg_schedule_time_intercal)

    @decorators.FunctionResultCacher.cached_function_result_for_a_time(120)
    def _judge_is_daylight(self):
        if self._is_do_not_run_by_specify_time_effect and self._do_not_run_by_specify_time[0] < time_util.DatetimeConverter().time_str < self._do_not_run_by_specify_time[1]:
            self.logger.warning(f'现在时间是 {time_util.DatetimeConverter()} ，现在时间是在 {self._do_not_run_by_specify_time} 之间，不运行')
            return True

    def __str__(self):
        return f'队列为 {self.queue_name} 函数为 {self.consuming_function} 的消费者'


# noinspection PyProtectedMember
class ConcurrentModeDispatcher(LoggerMixin):
    schedulal_thread_to_be_join = []
    concurrent_mode = None
    schedual_task_always_use_thread = False

    def __init__(self, consumerx: AbstractConsumer):
        self.consumer = consumerx
        if self.__class__.concurrent_mode is not None and self.consumer._concurrent_mode != self.__class__.concurrent_mode:
            AbstractConsumer.show_all_consumer_info()
            raise ValueError('由于猴子补丁的原因，同一解释器中不可以设置两种并发类型,请查看显示的所有消费者的信息，'
                             '搜索 concurrent_mode 关键字，确保当前解释器内的所有消费者的并发模式只有一种')
        self._concurrent_mode = self.__class__.concurrent_mode = self.consumer._concurrent_mode
        concurrent_name = ''
        self.timeout_deco = None
        if self._concurrent_mode == 1:
            concurrent_name = 'thread'
            self.timeout_deco = decorators.timeout
        elif self._concurrent_mode == 2:
            concurrent_name = 'gevent'
            self.timeout_deco = gevent_timeout_deco
        elif self._concurrent_mode == 3:
            concurrent_name = 'evenlet'
            self.timeout_deco = evenlet_timeout_deco
        self.concurrent_name = concurrent_name
        self.logger.warning(f'{self.consumer} 设置并发模式为 {self.concurrent_name}')

    def build_pool(self):
        if self.consumer._threadpool:
            return self.consumer._threadpool

        pool_type = None  # 是按照ThreadpoolExecutor写的三个鸭子类，公有方法名和功能写成完全一致，可以互相替换。
        if self._concurrent_mode == 1:
            pool_type = CustomThreadPoolExecutor
            # pool_type = BoundedThreadPoolExecutor
            check_not_monkey()
        elif self._concurrent_mode == 2:
            pool_type = GeventPoolExecutor
            check_gevent_monkey_patch()
        elif self._concurrent_mode == 3:
            pool_type = CustomEventletPoolExecutor
            check_evenlet_monkey_patch()
        self.consumer._threadpool = self.consumer._specify_threadpool if self.consumer._specify_threadpool else pool_type(self.consumer._threads_num + 1)  # 单独加一个检测消息数量和心跳的线程
        self.logger.warning(f'{self.concurrent_name} {self.consumer._threadpool}')
        return self.consumer._threadpool

    def schedulal_task_with_no_block(self):
        if self.schedual_task_always_use_thread:
            t = Thread(target=self.consumer.keep_circulating(1)(self.consumer._shedual_task))
            self.__class__.schedulal_thread_to_be_join.append(t)
            t.start()
        else:
            if self._concurrent_mode == 1:
                t = Thread(target=self.consumer.keep_circulating(1)(self.consumer._shedual_task))
                self.__class__.schedulal_thread_to_be_join.append(t)
                t.start()
            elif self._concurrent_mode == 2:
                g = gevent.spawn(self.consumer.keep_circulating(1)(self.consumer._shedual_task), )
                self.__class__.schedulal_thread_to_be_join.append(g)
            elif self._concurrent_mode == 3:
                g = eventlet.spawn(self.consumer.keep_circulating(1)(self.consumer._shedual_task), )
                self.__class__.schedulal_thread_to_be_join.append(g)
        atexit.register(self.join)

    @classmethod
    def join(cls):
        nb_print((cls.schedulal_thread_to_be_join, len(cls.schedulal_thread_to_be_join), '模式：', cls.concurrent_mode))
        if cls.schedual_task_always_use_thread:
            for t in cls.schedulal_thread_to_be_join:
                nb_print(t)
                t.join()
        else:
            if cls.concurrent_mode == 1:
                for t in cls.schedulal_thread_to_be_join:
                    nb_print(t)
                    t.join()
            elif cls.concurrent_mode == 2:
                # cls.logger.info()
                nb_print(cls.schedulal_thread_to_be_join)
                gevent.joinall(cls.schedulal_thread_to_be_join, raise_error=True, )
            elif cls.concurrent_mode == 3:
                for g in cls.schedulal_thread_to_be_join:
                    # eventlet.greenthread.GreenThread.
                    nb_print(g)
                    g.wait()

    def get_concurrent_info(self):
        concurrent_info = ''
        if self._concurrent_mode == 1:
            concurrent_info = f'[{threading.current_thread()}  {threading.active_count()}]'
        elif self._concurrent_mode == 2:
            concurrent_info = f'[{gevent.getcurrent()}  {threading.active_count()}]'
        elif self._concurrent_mode == 3:
            # noinspection PyArgumentList
            concurrent_info = f'[{eventlet.getcurrent()}  {threading.active_count()}]'
        return concurrent_info


def wait_for_possible_has_finish_all_tasks(queue_name: str, minutes: int, send_stop_to_broker=0, broker_kind: int = 0, ):
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

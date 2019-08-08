# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 11:57
import abc
import json
import time
import typing
from functools import wraps
from threading import Lock
import amqpstorm
from pika.exceptions import AMQPError as PikaAMQPError

from function_scheduling_distributed_framework.utils import LoggerLevelSetterMixin, LogManager, decorators


class AbstractPublisher(LoggerLevelSetterMixin, metaclass=abc.ABCMeta, ):
    has_init_broker = 0

    def __init__(self, queue_name, log_level_int=10, logger_prefix='', is_add_file_handler=True, clear_queue_within_init=False, is_add_publish_time=False, ):
        """
        :param queue_name:
        :param log_level_int:
        :param logger_prefix:
        :param is_add_file_handler:
        :param clear_queue_within_init:
        """
        self._queue_name = queue_name
        if logger_prefix != '':
            logger_prefix += '--'
        logger_name = f'{logger_prefix}{self.__class__.__name__}--{queue_name}'
        self.logger = LogManager(logger_name).get_logger_and_add_handlers(log_level_int, log_filename=f'{logger_name}.log' if is_add_file_handler else None)  #
        # self.rabbit_client = RabbitMqFactory(is_use_rabbitpy=is_use_rabbitpy).get_rabbit_cleint()
        # self.channel = self.rabbit_client.creat_a_channel()
        # self.queue = self.channel.queue_declare(queue=queue_name, durable=True)
        self._lock_for_pika = Lock()
        self._lock_for_count = Lock()
        self._current_time = None
        self.count_per_minute = None
        self._init_count()
        self.custom_init()
        self.logger.info(f'{self.__class__} 被实例化了')
        self.publish_msg_num_total = 0
        self._is_add_publish_time = is_add_publish_time
        # atexit.register(self.__at_exit)
        if clear_queue_within_init:
            self.clear()

    def set_is_add_publish_time(self, is_add_publish_time=True):
        self._is_add_publish_time = is_add_publish_time
        return self

    def _init_count(self):
        with self._lock_for_count:
            self._current_time = time.time()
            self.count_per_minute = 0

    def custom_init(self):
        pass

    def publish(self, msg: typing.Union[str, dict]):
        if isinstance(msg, str):
            msg = json.loads(msg)
        if self._is_add_publish_time:
            # msg.update({'publish_time': time.time(), 'publish_time_format': time_util.DatetimeConverter().datetime_str})
            msg.update({'publish_time': round(time.time(), 4), })
        t_start = time.time()
        decorators.handle_exception(retry_times=10, is_throw_error=True, time_sleep=0.1)(self.concrete_realization_of_publish)(json.dumps(msg))
        self.logger.debug(f'向{self._queue_name} 队列，推送消息 耗时{round(time.time() - t_start, 4)}秒  {msg}')
        with self._lock_for_count:
            self.count_per_minute += 1
            self.publish_msg_num_total += 1
        if time.time() - self._current_time > 10:
            self.logger.info(f'10秒内推送了 {self.count_per_minute} 条消息,累计推送了 {self.publish_msg_num_total} 条消息到 {self._queue_name} 中')
            self._init_count()

    @abc.abstractmethod
    def concrete_realization_of_publish(self, msg):
        raise NotImplementedError

    @abc.abstractmethod
    def clear(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_message_count(self):
        raise NotImplementedError

    @abc.abstractmethod
    def close(self):
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        self.logger.warning(f'with中自动关闭publisher连接，累计推送了 {self.publish_msg_num_total} 条消息 ')

    def __at_exit(self):
        self.logger.warning(f'程序关闭前，累计推送了 {self.publish_msg_num_total} 条消息 到 {self._queue_name} 中')


def deco_mq_conn_error(f):
    @wraps(f)
    def _deco_mq_conn_error(self, *args, **kwargs):
        if not self.has_init_broker:
            self.logger.warning(f'对象的方法 【{f.__name__}】 首次使用 rabbitmq channel,进行初始化执行 init_broker 方法')
            self.init_broker()
            self.has_init_broker = 1
            return f(self, *args, **kwargs)
        # noinspection PyBroadException
        try:
            return f(self, *args, **kwargs)
        except (PikaAMQPError, amqpstorm.AMQPError) as e:  # except Exception as e:   # 现在装饰器用到了绝大多出地方，单个异常类型不行。ex
            self.logger.error(f'rabbitmq链接出错   ,方法 {f.__name__}  出错 ，{e}')
            self.init_broker()
            return f(self, *args, **kwargs)

    return _deco_mq_conn_error

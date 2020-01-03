# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 11:57
import abc
import atexit
import json
import uuid
import time
import typing
from functools import wraps
from threading import Lock
import amqpstorm
from pika.exceptions import AMQPError as PikaAMQPError

from function_scheduling_distributed_framework.utils import LoggerLevelSetterMixin, LogManager, decorators, RedisMixin


class RedisAsyncResult(RedisMixin):
    def __init__(self, task_id, timeout=120):
        self.task_id = task_id
        self.timeout = timeout
        self._has_pop = False
        self._status_and_result = None

    def set_timeout(self, timeout=60):
        self.timeout = timeout
        return self

    @property
    def status_and_result(self):
        if not self._has_pop:
            self._status_and_result = json.loads(self.redis_db_frame.blpop(self.task_id, self.timeout)[1])
            self._has_pop = True
        return self._status_and_result

    def get(self):
        return self.status_and_result['result']

    @property
    def result(self):
        return self.get()

    def is_success(self):
        return self.status_and_result['success']


class PriorityConsumingControlConfig:
    """
    为每个独立的任务设置控制参数，和函数参数一起发布到中间件。可能有少数时候有这种需求。
    例如消费为add函数，可以每个独立的任务设置不同的超时时间，不同的重试次数，是否使用rpc模式。这里的配置优先，可以覆盖生成消费者时候的配置。
    """

    def __init__(self, function_timeout: float = None, max_retry_times: int = None,
                 is_print_detail_exception: bool = None,
                 msg_expire_senconds: int = None,
                 is_using_rpc_mode: bool = None):
        self.function_timeout = function_timeout
        self.max_retry_times = max_retry_times
        self.is_print_detail_exception = is_print_detail_exception
        self.msg_expire_senconds = msg_expire_senconds
        self.is_using_rpc_mode = is_using_rpc_mode

    def to_dict(self):
        return self.__dict__


class AbstractPublisher(LoggerLevelSetterMixin, metaclass=abc.ABCMeta, ):
    has_init_broker = 0

    def __init__(self, queue_name, log_level_int=10, logger_prefix='', is_add_file_handler=True, clear_queue_within_init=False, is_add_publish_time=True, ):
        """
        :param queue_name:
        :param log_level_int:
        :param logger_prefix:
        :param is_add_file_handler:
        :param clear_queue_within_init:
        :param is_add_publish_time:是否添加发布时间，以后废弃，都添加。
        """
        self._queue_name = queue_name
        if logger_prefix != '':
            logger_prefix += '--'
        logger_name = f'{logger_prefix}{self.__class__.__name__}--{queue_name}'
        self.logger = LogManager(logger_name).get_logger_and_add_handlers(log_level_int, log_filename=f'{logger_name}.log' if is_add_file_handler else None)  #
        # self.rabbit_client = RabbitMqFactory(is_use_rabbitpy=is_use_rabbitpy).get_rabbit_cleint()
        # self.channel = self.rabbit_client.creat_a_channel()
        # self.queue = self.channel.queue_declare(queue=queue_name, durable=True)
        self._lock_for_count = Lock()
        self._current_time = None
        self.count_per_minute = None
        self._init_count()
        self.custom_init()
        self.logger.info(f'{self.__class__} 被实例化了')
        self.publish_msg_num_total = 0
        self._is_add_publish_time = is_add_publish_time
        self.__init_time = time.time()
        atexit.register(self.__at_exit)
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

    def publish(self, msg: typing.Union[str, dict],
                priority_control_config: PriorityConsumingControlConfig = None):
        if isinstance(msg, str):
            msg = json.loads(msg)
        task_id = f'{self._queue_name}_result:{uuid.uuid4()}'
        msg['extra'] = extra_params = {'task_id': task_id, 'publish_time': round(time.time(), 4), 'publish_time_format': time.strftime('%Y-%m-%d %H:%M:%S')}
        if priority_control_config:
            extra_params.update(priority_control_config.to_dict())
        t_start = time.time()
        decorators.handle_exception(retry_times=10, is_throw_error=True, time_sleep=0.1)(self.concrete_realization_of_publish)(json.dumps(msg))
        self.logger.debug(f'向{self._queue_name} 队列，推送消息 耗时{round(time.time() - t_start, 4)}秒  {msg}')
        with self._lock_for_count:
            self.count_per_minute += 1
            self.publish_msg_num_total += 1
        if time.time() - self._current_time > 10:
            self.logger.info(f'10秒内推送了 {self.count_per_minute} 条消息,累计推送了 {self.publish_msg_num_total} 条消息到 {self._queue_name} 中')
            self._init_count()
        return RedisAsyncResult(task_id)

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
        self.logger.warning(f'程序关闭前，{round(time.time() - self.__init_time)} 秒内，累计推送了 {self.publish_msg_num_total} 条消息 到 {self._queue_name} 中')


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

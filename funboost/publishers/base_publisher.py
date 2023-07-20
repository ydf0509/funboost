# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 11:57
import abc
import copy
import inspect
import atexit
import json
import multiprocessing
import threading
import uuid
import time
import typing
from functools import wraps
from threading import Lock
import datetime
import amqpstorm

from pikav1.exceptions import AMQPError as PikaAMQPError

from nb_log import LoggerLevelSetterMixin, get_logger, LoggerMixin

from funboost.core.msg_result_getter import AsyncResult, AioAsyncResult
from funboost.utils import decorators, time_util
from funboost import funboost_config_deafult

RedisAsyncResult = AsyncResult  # 别名
RedisAioAsyncResult = AioAsyncResult  # 别名


class PriorityConsumingControlConfig:
    """
    为每个独立的任务设置控制参数，和函数参数一起发布到中间件。可能有少数时候有这种需求。
    例如消费为add函数，可以每个独立的任务设置不同的超时时间，不同的重试次数，是否使用rpc模式。这里的配置优先，可以覆盖生成消费者时候的配置。
    """

    def __init__(self, function_timeout: float = None, max_retry_times: int = None,
                 is_print_detail_exception: bool = None,
                 msg_expire_senconds: int = None,
                 is_using_rpc_mode: bool = None,

                 countdown: typing.Union[float, int] = None,
                 eta: datetime.datetime = None,
                 misfire_grace_time: typing.Union[int, None] = None,

                 other_extra_params: dict = None,

                 ):
        """

        :param function_timeout: 超时杀死
        :param max_retry_times:
        :param is_print_detail_exception:
        :param msg_expire_senconds:
        :param is_using_rpc_mode: rpc模式才能在发布端获取结果
        :param eta: 规定什么时候运行
        :param countdown: 规定多少秒后运行
        # execute_delay_task_even_if_when_task_is_expired
        :param misfire_grace_time: 单位为秒。这个参数是配合 eta 或 countdown 使用的。是延时任务专用配置.

               一个延时任务，例如规定发布10秒后才运行，但由于消费速度慢导致任务积压，导致任务还没轮到开始消费就已经过了30秒，
               如果 misfire_grace_time 配置的值是大于20则会依旧运行。如果配置的值是5，那么由于10 + 5 < 30,所以不会执行。

               例如规定18点运行，但由于消费速度慢导致任务积压，导致任务还没轮到开始消费就已经过了18点10分
               ，如果 misfire_grace_time设置为700，则这个任务会被执行，如果设置为300，忧郁18点10分超过了18点5分，就不会执行。

               misfire_grace_time 如果设置为None，则任务永远不会过期，一定会被执行。
               misfire_grace_time 的值要么是大于1的整数， 要么等于None

               此含义也可以百度 apscheduler包的 misfire_grace_time 参数的含义。

        """
        self.function_timeout = function_timeout
        self.max_retry_times = max_retry_times
        self.is_print_detail_exception = is_print_detail_exception
        self.msg_expire_senconds = msg_expire_senconds
        self.is_using_rpc_mode = is_using_rpc_mode

        if countdown and eta:
            raise ValueError('不能同时设置eta和countdown')
        self.eta = eta
        self.countdown = countdown
        self.misfire_grace_time = misfire_grace_time
        if misfire_grace_time is not None and misfire_grace_time < 1:
            raise ValueError(f'misfire_grace_time 的值要么是大于1的整数， 要么等于None')

        self.other_extra_params = other_extra_params

    def to_dict(self):
        if isinstance(self.countdown, datetime.datetime):
            self.countdown = time_util.DatetimeConverter(self.countdown).datetime_str
        priority_consuming_control_config_dict = {k: v for k, v in self.__dict__.items() if v is not None}  # 使中间件消息不要太长，框架默认的值不发到中间件。
        return priority_consuming_control_config_dict


class PublishParamsChecker(LoggerMixin):
    """
    发布的任务的函数参数检查，使发布的任务在消费时候不会出现低级错误。
    """

    def __init__(self, func: typing.Callable):
        # print(func)
        spec = inspect.getfullargspec(func)
        self.all_arg_name = spec.args
        self.all_arg_name_set = set(spec.args)
        # print(spec.args)
        if spec.defaults:
            len_deafult_args = len(spec.defaults)
            self.position_arg_name_list = spec.args[0: -len_deafult_args]
            self.position_arg_name_set = set(self.position_arg_name_list)
            self.keyword_arg_name_list = spec.args[-len_deafult_args:]
            self.keyword_arg_name_set = set(self.keyword_arg_name_list)
        else:
            self.position_arg_name_list = spec.args
            self.position_arg_name_set = set(self.position_arg_name_list)
            self.keyword_arg_name_list = []
            self.keyword_arg_name_set = set()
        self.logger.info(f'{func} 函数的入参要求是 全字段 {self.all_arg_name_set} ,必须字段为 {self.position_arg_name_set} ')

    def check_params(self, publish_params: dict):
        publish_params_keys_set = set(publish_params.keys())
        if publish_params_keys_set.issubset(self.all_arg_name_set) and publish_params_keys_set.issuperset(
                self.position_arg_name_set):
            return True
        else:
            raise ValueError(f'你发布的参数不正确，你发布的任务的所有键是 {publish_params_keys_set}， '
                             f'必须是 {self.all_arg_name_set} 的子集， 必须是 {self.position_arg_name_set} 的超集')


class AbstractPublisher(LoggerLevelSetterMixin, metaclass=abc.ABCMeta, ):

    def __init__(self, queue_name, log_level_int=10, logger_prefix='', is_add_file_handler=True,
                 clear_queue_within_init=False, is_add_publish_time=True, consuming_function: callable = None,
                 broker_exclusive_config: dict = None,
                 ):
        # noinspection GrazieInspection
        """
                :param queue_name:
                :param log_level_int:
                :param logger_prefix:
                :param is_add_file_handler:
                :param clear_queue_within_init:
                :param is_add_publish_time:是否添加发布时间，以后废弃，都添加。
                :param consuming_function:消费函数，为了做发布时候的函数入参校验用的，如果不传则不做发布任务的校验，
                       例如add 函数接收x，y入参，你推送{"x":1,"z":3}就是不正确的，函数不接受z参数。
                :param broker_exclusive_config 加上一个不同种类中间件非通用的配置,不同中间件自身独有的配置，不是所有中间件都兼容的配置，因为框架支持30种消息队列，消息队列不仅仅是一般的先进先出queue这么简单的概念，
                        例如kafka支持消费者组，rabbitmq也支持各种独特概念例如各种ack机制 复杂路由机制，每一种消息队列都有独特的配置参数意义，可以通过这里传递。
                """
        self.queue_name = self._queue_name = queue_name
        if logger_prefix != '':
            logger_prefix += '--'
        # consuming_function_name = f'--{consuming_function.__name__}' if consuming_function else ''
        # logger_name = f'{logger_prefix}{self.__class__.__name__}--{queue_name}{consuming_function_name}'
        self._is_add_file_handler = is_add_file_handler
        self._logger_prefix = logger_prefix
        self._log_level_int = log_level_int
        logger_name = f'{logger_prefix}{self.__class__.__name__}--{queue_name}'
        self.logger = get_logger(logger_name, log_level_int=log_level_int,
                                 log_filename=f'{logger_name}.log' if is_add_file_handler else None,
                                 formatter_template=funboost_config_deafult.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER,
                                 )  #
        self.publish_params_checker = PublishParamsChecker(consuming_function) if consuming_function else None
        if broker_exclusive_config is None:
            broker_exclusive_config = {}
        # print(broker_exclusive_config)
        self.broker_exclusive_config = broker_exclusive_config
        # self.rabbit_client = RabbitMqFactory(is_use_rabbitpy=is_use_rabbitpy).get_rabbit_cleint()
        # self.channel = self.rabbit_client.creat_a_channel()
        # self.queue = self.channel.queue_declare(queue=queue_name, durable=True)
        self.has_init_broker = 0
        self._lock_for_count = Lock()
        self._current_time = None
        self.count_per_minute = None
        self._init_count()
        self.custom_init()
        self.logger.info(f'{self.__class__} 被实例化了')
        self.publish_msg_num_total = 0
        self._is_add_publish_time = is_add_publish_time
        self.__init_time = time.time()
        atexit.register(self._at_exit)
        if clear_queue_within_init:
            self.clear()

    def set_is_add_publish_time(self, is_add_publish_time=True):
        self._is_add_publish_time = is_add_publish_time
        return self

    def _init_count(self):
        self._current_time = time.time()
        self.count_per_minute = 0

    def custom_init(self):
        pass

    @staticmethod
    def _get_from_other_extra_params(k: str, msg):
        msg_dict = json.loads(msg) if isinstance(msg, str) else msg
        return msg_dict['extra'].get('other_extra_params', {}).get(k, None)

    def _convert_msg(self, msg: typing.Union[str, dict], task_id=None,
                     priority_control_config: PriorityConsumingControlConfig = None) -> (typing.Dict, typing.Dict, typing.Dict):
        if isinstance(msg, (str, bytes)):
            msg = json.loads(msg)
        msg_function_kw = copy.deepcopy(msg)
        raw_extra = {}
        if 'extra' in msg:
            msg_function_kw.pop('extra')
            raw_extra = msg['extra']
        if self.publish_params_checker:
            self.publish_params_checker.check_params(msg_function_kw)
        task_id = task_id or f'{self._queue_name}_result:{uuid.uuid4()}'
        extra_params = {'task_id': task_id, 'publish_time': round(time.time(), 4),
                        'publish_time_format': time.strftime('%Y-%m-%d %H:%M:%S')}
        if priority_control_config:
            extra_params.update(priority_control_config.to_dict())
        extra_params.update(raw_extra)
        msg['extra'] = extra_params
        return msg, msg_function_kw, extra_params, task_id

    def publish(self, msg: typing.Union[str, dict], task_id=None,
                priority_control_config: PriorityConsumingControlConfig = None):
        """

        :param msg:函数的入参字典或者字典转json。,例如消费函数是 def add(x,y)，你就发布 {"x":1,"y":2}
        :param task_id:可以指定task_id,也可以不指定就随机生产uuid
        :param priority_control_config:优先级配置，消息可以携带优先级配置，覆盖boost的配置。
        :return:
        """
        msg, msg_function_kw, extra_params, task_id = self._convert_msg(msg, task_id, priority_control_config)
        t_start = time.time()
        decorators.handle_exception(retry_times=10, is_throw_error=True, time_sleep=0.1)(
            self.concrete_realization_of_publish)(json.dumps(msg, ensure_ascii=False))
        self.logger.debug(f'向{self._queue_name} 队列，推送消息 耗时{round(time.time() - t_start, 4)}秒  {msg_function_kw}')  # 显示msg太长了。
        with self._lock_for_count:
            self.count_per_minute += 1
            self.publish_msg_num_total += 1
            if time.time() - self._current_time > 10:
                self.logger.info(
                    f'10秒内推送了 {self.count_per_minute} 条消息,累计推送了 {self.publish_msg_num_total} 条消息到 {self._queue_name} 队列中')
                self._init_count()
        return AsyncResult(task_id)

    def push(self, *func_args, **func_kwargs):
        """
        简写，只支持传递消费函数的本身参数，不支持priority_control_config参数。
        类似于 publish和push的关系类似 apply_async 和 delay的关系。前者更强大，后者更简略。

        例如消费函数是
        def add(x,y):
            print(x+y)

        publish({"x":1,'y':2}) 和 push(1,2)是等效的。但前者可以传递priority_control_config参数。后者只能穿add函数所接受的入参。
        :param func_args:
        :param func_kwargs:
        :return:
        """
        # print(func_args,func_kwargs,self.publish_params_checker.all_arg_name)
        msg_dict = func_kwargs
        # print(msg_dict)
        # print(self.publish_params_checker.position_arg_name_list)
        # print(func_args)
        for index, arg in enumerate(func_args):
            # print(index,arg,self.publish_params_checker.position_arg_name_list)
            # msg_dict[self.publish_params_checker.position_arg_name_list[index]] = arg
            msg_dict[self.publish_params_checker.all_arg_name[index]] = arg
        # print(msg_dict)
        return self.publish(msg_dict)

    delay = push  # 那就来个别名吧，两者都可以。

    @abc.abstractmethod
    def concrete_realization_of_publish(self, msg: str):
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

    def _at_exit(self):
        if multiprocessing.current_process().name == 'MainProcess':
            self.logger.warning(
                f'程序关闭前，{round(time.time() - self.__init_time)} 秒内，累计推送了 {self.publish_msg_num_total} 条消息 到 {self._queue_name} 中')


has_init_broker_lock = threading.Lock()


def deco_mq_conn_error(f):
    @wraps(f)
    def _deco_mq_conn_error(self, *args, **kwargs):
        with has_init_broker_lock:
            if not self.has_init_broker:
                self.logger.warning(f'对象的方法 【{f.__name__}】 首次使用 进行初始化执行 init_broker 方法')
                self.init_broker()
                self.has_init_broker = 1
                return f(self, *args, **kwargs)
            # noinspection PyBroadException
            try:
                return f(self, *args, **kwargs)

            except (PikaAMQPError, amqpstorm.AMQPError, ) as e:  # except BaseException as e:   # 现在装饰器用到了绝大多出地方，单个异常类型不行。ex
                self.logger.error(f'中间件链接出错   ,方法 {f.__name__}  出错 ，{e}')
                self.init_broker()
                return f(self, *args, **kwargs)
            except BaseException as e:
                self.logger.critical(e, exc_info=True)

    return _deco_mq_conn_error

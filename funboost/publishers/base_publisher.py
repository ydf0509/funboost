# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 11:57
from pathlib import Path

import abc
import copy
import inspect
import atexit
import json
import logging
import multiprocessing
import sys
import threading
import time
import typing
from functools import wraps
from threading import Lock

import nb_log
from funboost.concurrent_pool.async_helper import simple_run_in_executor
from funboost.constant import ConstStrForClassMethod, FunctionKind
from funboost.core.broker_kind__exclusive_config_default_define import generate_broker_exclusive_config
from funboost.core.func_params_model import PublisherParams, TaskOptions
from funboost.core.function_result_status_saver import FunctionResultStatus
from funboost.core.helper_funs import MsgGenerater
from funboost.core.loggers import develop_logger

# from nb_log import LoggerLevelSetterMixin, LoggerMixin
from funboost.core.loggers import LoggerLevelSetterMixin, FunboostFileLoggerMixin, get_logger
from funboost.core.msg_result_getter import AsyncResult, AioAsyncResult
from funboost.core.serialization import PickleHelper, Serialization
from funboost.core.task_id_logger import TaskIdLogger
from funboost.utils import decorators
from funboost.funboost_config_deafult import BrokerConnConfig, FunboostCommonConfig
from nb_libs.path_helper import PathHelper
from funboost.core.consuming_func_iniput_params_check import ConsumingFuncInputParamsChecker

RedisAsyncResult = AsyncResult  # 别名
RedisAioAsyncResult = AioAsyncResult  # 别名


class AbstractPublisher(LoggerLevelSetterMixin, metaclass=abc.ABCMeta, ):
    """
    发布消息到消息队列
    同步编程，最重要的方法有 push publish，
    asyncio异步编程，最重要的方法有 aio_push aio_publish，
    
    用法是 booster.push(1,y=2)
    或者 booster.publish({"x":1,"y":2},task_options=TaskOptions(max_retry_times=3,...)) 
    总结就是push更简单更魔法，publish是更强大更灵活，因为publish除了发布函数入参自身，还可以传递task_options参数。
    """
    def __init__(self, publisher_params: PublisherParams, ):
        self.publisher_params = publisher_params
        
        self.queue_name = self._queue_name = publisher_params.queue_name
        self.logger: logging.Logger
        self._build_logger()
        
        self.publisher_params.broker_exclusive_config = generate_broker_exclusive_config(self.publisher_params.broker_kind,self.publisher_params.broker_exclusive_config,self.logger)
        self.has_init_broker = 0
        self._lock_for_count = Lock()
        self._current_time = None
        self.count_per_minute = None
        self._init_count()
        self.custom_init()
        self.logger.info(f'{self.__class__} 被实例化了')
        self.publish_msg_num_total = 0
        
        ConsumingFuncInputParamsChecker.gen_final_func_input_params_info(publisher_params)
        self.publish_params_checker = ConsumingFuncInputParamsChecker(self.final_func_input_params_info) if publisher_params.consuming_function else None

        self.__init_time = time.time()
        atexit.register(self._at_exit)
        if publisher_params.clear_queue_within_init:
            self.clear()
    
    @property
    def final_func_input_params_info(self):
        """
        {...
         "auto_generate_info": {
    "where_to_instantiate": "D:\\codes\\funboost\\examples\\example_faas\\task_funs_dir\\sub.py:5",
    "final_func_input_params_info": {
      "func_name": "sub",
      "func_position": "<function sub at 0x00000272649BBA60>",
      "is_manual_func_input_params": false,
      "all_arg_name_list": [
        "a",
        "b"
      ],
      "must_arg_name_list": [
        "a",
        "b"
      ],
      "optional_arg_name_list": []
    }
  }}
        """
        return self.publisher_params.auto_generate_info['final_func_input_params_info']

    def _build_logger(self):
        logger_prefix = self.publisher_params.logger_prefix
        if logger_prefix != '':
            logger_prefix += '--'
        self.logger_name = self.publisher_params.logger_name or f'funboost.{logger_prefix}{self.__class__.__name__}--{self.queue_name}'
        self.log_filename = self.publisher_params.log_filename or f'funboost.{self.queue_name}.log'
        self.logger = nb_log.LogManager(self.logger_name, logger_cls=TaskIdLogger).get_logger_and_add_handlers(
            log_level_int=self.publisher_params.log_level,
            log_filename=self.log_filename if self.publisher_params.create_logger_file else None,
            error_log_filename=nb_log.generate_error_file_name(self.log_filename),
            formatter_template=FunboostCommonConfig.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER, )

    def _init_count(self):
        self._current_time = time.time()
        self.count_per_minute = 0

    def custom_init(self):
        pass

    

    @staticmethod
    def _get_from_other_extra_params(k: str, msg):
        # msg_dict = json.loads(msg) if isinstance(msg, str) else msg
        msg_dict = Serialization.to_dict(msg)
        return msg_dict['extra'].get('other_extra_params', {}).get(k, None)

    def _convert_msg(self, msg: typing.Union[str, dict], task_id=None,
                     task_options: TaskOptions = None) -> (typing.Dict, typing.Dict, typing.Dict, str):
        """
        
        """
        msg = Serialization.to_dict(msg)
        msg_function_kw = copy.deepcopy(msg)
        raw_extra = {}
        if 'extra' in msg:
            msg_function_kw.pop('extra')
            raw_extra = msg['extra']
        self.check_func_msg_dict(msg_function_kw)

        if task_options:
            task_options_dict = Serialization.to_dict(task_options.to_json(exclude_unset=True))
        else:
            task_options_dict = {}
        task_id = task_id or task_options_dict.get('task_id') or raw_extra.get('task_id') or MsgGenerater.generate_task_id(self._queue_name)
        task_options_dict['task_id'] = task_id
        task_options_dict['publish_time'] = task_options_dict.get('publish_time') or raw_extra.get('publish_time') or MsgGenerater.generate_publish_time()
        task_options_dict['publish_time_format'] = task_options_dict.get('publish_time_format') or raw_extra.get('publish_time_format') or MsgGenerater.generate_publish_time_format()
    
        new_extra = {}
        new_extra.update(raw_extra)
        new_extra.update(task_options_dict) # task_options.json 是为了充分使用 pydantic的自定义时间格式化字符串
        msg['extra'] = new_extra
        extra_params = new_extra
        return msg, msg_function_kw, extra_params, task_id

    def publish(self, msg: typing.Union[str, dict], task_id=None,
                task_options: TaskOptions = None):
        """

        :param msg:函数的入参字典或者字典转json。,例如消费函数是 def add(x,y)，你就发布 {"x":1,"y":2}
        :param task_id:可以指定task_id,也可以不指定就随机生产uuid
        :param task_options:优先级配置，消息可以携带优先级配置，覆盖boost的配置。
        :return: AsyncResult 对象，可以用于等待结果。 例如 status_and_result =  async_result.status_and_result 来等待返回结果。

        funboost 消息体中的extra字典，包含的key就是 TaskOptions 中声明的字段。例如 task_id, publish_time, publish_time_format 等。
        如果用户传递了 task_options，则以 task_options 为准。
        如果用户没有传递 task_options，则以消息体中的extra字典为准。
        如果最终还是没有 task_id, publish_time, publish_time_format 等字段，则自动生成。

        意味着如果你想传递 task_options 中的值，你的msg字典，
        第一种：你可以有一个extra字段，里面存放 task_options的各种字段，（适合跨编程语言）
        第二种：你可以通过publish方法的 task_options指定一个 TaskOptions pydantic模型对象 （适合python语言，因为能章节用funboost）

        如果是跨业务跨编程语言，由于java不能调用python funboost的publish方法:
        java可以这样通过http接口或者funboost.faas  来发布消息 {"user_id":123,"name":"张三","extra": {"task_id":"1234567890","max_retry_times":3}} 

        """
        msg = copy.deepcopy(msg)  # 字典是可变对象,不要改变影响用户自身的传参字典. 用户可能继续使用这个传参字典.
        msg, msg_function_kw, extra_params, task_id = self._convert_msg(msg, task_id, task_options)
        t_start = time.time()

        try:
            msg_json = Serialization.to_json_str(msg)
        except Exception as e:
            can_not_json_serializable_keys = Serialization.find_can_not_json_serializable_keys(msg)
            self.logger.warning(f'msg 中包含不能序列化的键: {can_not_json_serializable_keys}')
            # raise ValueError(f'msg 中包含不能序列化的键: {can_not_json_serializable_keys}')
            new_msg = copy.deepcopy(Serialization.to_dict(msg))
            for key in can_not_json_serializable_keys:
                new_msg[key] = PickleHelper.to_str(new_msg[key])
            new_msg['extra']['can_not_json_serializable_keys'] = can_not_json_serializable_keys
            msg_json = Serialization.to_json_str(new_msg)
        # print(msg_json)
        decorators.handle_exception(retry_times=10, is_throw_error=True, time_sleep=0.1)(
            self._publish_impl)(msg_json)

        self.logger.debug(f'向{self._queue_name} 队列，推送消息 耗时{round(time.time() - t_start, 4)}秒  {msg_json if self.publisher_params.publish_msg_log_use_full_msg else msg_function_kw}',
                          extra={'task_id': task_id} # 发布日志中显示task_id，方便排查问题。
                          )  # 显示msg太长了。
        with self._lock_for_count:
            self.count_per_minute += 1
            self.publish_msg_num_total += 1
            if time.time() - self._current_time > 10:
                self.logger.info(
                    f'10秒内推送了 {self.count_per_minute} 条消息,累计推送了 {self.publish_msg_num_total} 条消息到 {self._queue_name} 队列中')
                self._init_count()
        self._after_publish(msg, msg_function_kw, task_id)
        return AsyncResult(task_id,timeout=self.publisher_params.rpc_timeout)
    
    def _after_publish(self, msg: dict, msg_function_kw: dict, task_id: str):
        """发布消息后的钩子方法，子类可以覆写此方法来实现自定义逻辑，例如记录指标"""
        pass

    def send_msg(self, msg: typing.Union[dict, str]):
        """直接发送任意原始的消息内容到消息队列,不生成辅助参数,无视函数入参名字,不校验入参个数和键名"""
        decorators.handle_exception(retry_times=10, is_throw_error=True, time_sleep=0.1)(
            self._publish_impl)(Serialization.to_json_str(msg))

    @staticmethod
    def __get_cls_file(cls: type):
        if cls.__module__ == '__main__':
            cls_file = Path(sys.argv[0]).resolve().as_posix()
        else:
            cls_file = Path(sys.modules[cls.__module__].__file__).resolve().as_posix()
        return cls_file

    def push(self, *func_args, **func_kwargs):
        """
        简写，只支持传递消费函数的本身参数，不支持task_options参数。
        类似于 publish和push的关系类似 apply_async 和 delay的关系。前者更强大，后者更简略。

        例如消费函数是
        def add(x,y):
            print(x+y)

        publish({"x":1,'y':2}) 和 push(1,2)是等效的。但前者可以传递task_options参数。后者只能穿add函数所接受的入参。
        :param func_args:
        :param func_kwargs:
        :return:
        """
        # print(func_args, func_kwargs, self.publish_params_checker.all_arg_name)
        msg_dict = func_kwargs
        # print(msg_dict)
        # print(self.publish_params_checker.position_arg_name_list)
        # print(func_args)
        func_args_list = list(func_args)

        # print(func_args_list)
        if self.publisher_params.consuming_function_kind == FunctionKind.CLASS_METHOD:
            # print(self.publish_params_checker.all_arg_name[0])
            # func_args_list.insert(0, {'first_param_name': self.publish_params_checker.all_arg_name[0],
            #        'cls_type': ClsHelper.get_classs_method_cls(self.publisher_params.consuming_function).__name__},
            #                       )
            cls = func_args_list[0]
            # print(cls,cls.__name__, sys.modules[cls.__module__].__file__)
            if not inspect.isclass(cls):
                raise ValueError(f'The consuming_function {self.publisher_params.consuming_function} is class_method,the first params of push must be a class')
            func_args_list[0] = {ConstStrForClassMethod.FIRST_PARAM_NAME: self.publish_params_checker.all_arg_name_list[0],
                                 ConstStrForClassMethod.CLS_NAME: cls.__name__,
                                 ConstStrForClassMethod.CLS_FILE: self.__get_cls_file(cls),
                                 ConstStrForClassMethod.CLS_MODULE: PathHelper(self.__get_cls_file(cls)).get_module_name(),
                                 }
        elif self.publisher_params.consuming_function_kind == FunctionKind.INSTANCE_METHOD:
            obj = func_args[0]

            cls = type(obj)
            if not hasattr(obj, ConstStrForClassMethod.OBJ_INIT_PARAMS):
                raise ValueError(f'''The consuming_function {self.publisher_params.consuming_function} is an instance method, and the instance must have the {ConstStrForClassMethod.OBJ_INIT_PARAMS} attribute.
The first argument of the push method must be the instance of the class.
                ''')
            func_args_list[0] = {ConstStrForClassMethod.FIRST_PARAM_NAME: self.publish_params_checker.all_arg_name_list[0],
                                 ConstStrForClassMethod.CLS_NAME: cls.__name__,
                                 ConstStrForClassMethod.CLS_FILE: self.__get_cls_file(cls),
                                 ConstStrForClassMethod.CLS_MODULE: PathHelper(self.__get_cls_file(cls)).get_module_name(),
                                 ConstStrForClassMethod.OBJ_INIT_PARAMS: getattr(obj, ConstStrForClassMethod.OBJ_INIT_PARAMS),

                                 }

        for index, arg in enumerate(func_args_list):
            # print(index,arg,self.publish_params_checker.position_arg_name_list)
            # msg_dict[self.publish_params_checker.position_arg_name_list[index]] = arg
            msg_dict[self.publish_params_checker.all_arg_name_list[index]] = arg

        # print(msg_dict)
        return self.publish(msg_dict)

    delay = push  # 那就来个别名吧，两者都可以。

    @abc.abstractmethod
    def _publish_impl(self, msg: str):
        raise NotImplementedError

    def sync_call(self, msg_dict: dict, is_return_rpc_data_obj=True) -> typing.Union[dict, FunctionResultStatus]:
        """仅有部分中间件支持同步调用并阻塞等待返回结果,不依赖AsyncResult + redis作为rpc，例如 http grpc 等"""
        raise NotImplementedError(f'broker  {self.publisher_params.broker_kind} not support sync_call method')

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

    async def aio_push(self, *func_args, **func_kwargs) -> AioAsyncResult:
        """asyncio 生态下发布消息,因为同步push只需要消耗不到1毫秒,所以基本上大概可以直接在asyncio异步生态中直接调用同步的push方法,
        但为了更好的防止网络波动(例如发布消息到外网的消息队列耗时达到10毫秒),可以使用aio_push"""
        async_result = await simple_run_in_executor(self.push, *func_args, **func_kwargs)
        return AioAsyncResult(async_result.task_id,timeout=async_result.timeout )

    async def aio_publish(self, msg: typing.Union[str, dict], task_id=None,
                          task_options: TaskOptions = None) -> AioAsyncResult:
        """asyncio 生态下发布消息,因为同步push只需要消耗不到1毫秒,所以基本上大概可以直接在asyncio异步生态中直接调用同步的push方法,
        但为了更好的防止网络波动(例如发布消息到外网的消息队列耗时达到10毫秒),可以使用aio_push"""
        async_result = await simple_run_in_executor(self.publish, msg, task_id, task_options)
        return AioAsyncResult(async_result.task_id, timeout=async_result.timeout)

    def check_func_msg_dict(self,msg_dict:dict):
        if self.publish_params_checker and self.publisher_params.should_check_publish_func_params:
            if not isinstance(msg_dict,dict):
                raise ValueError(f"check_func_msg_dict 入参必须是字典, 当前是: {type(msg_dict)}")
            if 'extra' in msg_dict:
                msg_function_kw = copy.deepcopy(msg_dict)
                msg_function_kw.pop('extra')
            else:
                msg_function_kw = msg_dict
            self.publish_params_checker.check_func_msg_dict(msg_function_kw)
        return True

    def check_func_input_params(self, *args, **kwargs):
        """
        校验 push 风格的参数: f.check_params(1, y=2)
        利用框架启动时已经解析好的 final_func_input_params_info 进行参数映射和校验。
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 校验通过返回 True，失败抛出异常
        """

        params_dict = dict(zip(self.publish_params_checker.all_arg_name_list, args))
        if kwargs:
            params_dict.update(kwargs)
        # print(4444,args,kwargs, params_dict)
        return self.check_func_msg_dict(params_dict)

        




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
            except Exception as e:
                # 通过异常类的模块名和类名判断，不需要导入包
                exc_module = type(e).__module__
                exc_name = type(e).__name__
                
                # 只要是这些包的 AMQP/Connection 相关异常都重连
                is_amqp_error = (
                    ('amqpstorm' in exc_module or 'pika' in exc_module or 'amqp' in exc_module)
                    and ('AMQP' in exc_name or 'Connection' in exc_name or 'Channel' in exc_name)
                )
                
                if is_amqp_error:
                    self.logger.error(f'中间件链接出错, 方法 {f.__name__} 出错, {e}')
                    self.init_broker()
                    return f(self, *args, **kwargs)
                raise  # 其他异常继续抛出
            except BaseException as e:
                self.logger.critical(e, exc_info=True)

    return _deco_mq_conn_error

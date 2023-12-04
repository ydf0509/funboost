import asyncio
import copy
import datetime
import json
import logging
import typing

from funboost.constant import ConcurrentModeEnum, BrokerEnum
from pydantic import BaseModel, validator, root_validator, PrivateAttr
from funboost.core.function_result_status_config import FunctionResultStatusPersistanceConfig


class PyDanticModelJsonMixin:
    def get_str_dict(self):
        model_dict: dict = self.dict()
        model_dict_copy = copy.deepcopy(model_dict)
        for k, v in model_dict.items():
            if isinstance(v, typing.Callable):
                model_dict_copy[k] = str(v)
        return model_dict_copy

    def json(self, **dumps_kwargs: typing.Any):
        # 创建一个字典表示模型字段和对应值
        # 使用 json.dumps() 方法进行序列化
        return json.dumps(self.get_str_dict(), **dumps_kwargs)

    def json_pre(self):
        return json.dumps(self.get_str_dict(), ensure_ascii=False, indent=4)


class BoosterParams(PyDanticModelJsonMixin, BaseModel, ):
    queue_name: str
    concurrent_mode: int = ConcurrentModeEnum.THREADING
    concurrent_num :int= 50
    specify_concurrent_pool: typing.Callable = None
    specify_async_loop: typing.Callable = None
    qps: float = 0
    is_using_distributed_frequency_control :bool= False
    is_send_consumer_hearbeat_to_redis:bool = False

    max_retry_times:int = 3
    is_push_to_dlx_queue_when_retry_max_times:bool = False

    consumin_function_decorator: typing.Callable = None
    function_timeout:float = 0

    log_level: int = logging.DEBUG
    logger_prefix :str= ''
    create_logger_file = True
    log_filename: str = None
    is_show_message_get_from_broker:bool = False
    is_print_detail_exception :bool= True

    msg_expire_senconds :float= 0

    do_task_filtering:bool = False
    task_filtering_expire_seconds:int = 0

    function_result_status_persistance_conf = FunctionResultStatusPersistanceConfig(is_save_result=False, is_save_status=False, expire_seconds=70 * 24 * 3600)
    user_custom_record_process_info_func: typing.Callable = None

    is_using_rpc_mode = False
    is_support_remote_kill_task = False

    is_do_not_run_by_specify_time_effect = False
    do_not_run_by_specify_time = ('10:00:00', '22:00:00')

    schedule_tasks_on_main_thread = False

    broker_exclusive_config = {}

    consuming_function: typing.Callable = None

    broker_kind: int = BrokerEnum.PERSISTQUEUE  # 中间件选型见3.1章节 https://funboost.readthedocs.io/zh/latest/articles/c3.html

    auto_generate_info: dict = {}  # 自动生成的信息,不需要用户主动传参.
    # class Config:
    #     json_encoders = {
    #         typing.Callable: lambda v: str(v)  # 自定义 函数 类型的序列化逻辑
    #     }
    #     underscore_attrs_are_private = True
    #
    # _where_to_instantiate: str = None
    # _lock = PrivateAttr(default_factory=Lock)


class PriorityConsumingControlConfig(BaseModel):
    """
    为每个独立的任务设置控制参数，和函数参数一起发布到中间件。可能有少数时候有这种需求。
    例如消费为add函数，可以每个独立的任务设置不同的超时时间，不同的重试次数，是否使用rpc模式。这里的配置优先，可以覆盖生成消费者时候的配置。
    """

    function_timeout: float = None
    max_retry_times: int = None
    is_print_detail_exception: bool = None
    msg_expire_senconds: int = None
    is_using_rpc_mode: bool = None
    countdown: typing.Union[float, int] = None
    eta: datetime.datetime = None
    misfire_grace_time: typing.Union[int, None] = None
    other_extra_params: dict = None

    @root_validator
    def cehck_values(cls, values: dict):
        if values['countdown'] and values['eta']:
            raise ValueError('不能同时设置eta和countdown')
        if values['misfire_grace_time'] is not None and values['misfire_grace_time'] < 1:
            raise ValueError(f'misfire_grace_time 的值要么是大于1的整数， 要么等于None')
        return values


class PublisherParams(PyDanticModelJsonMixin, BaseModel):
    queue_name: str
    log_level: int = logging.DEBUG
    logger_prefix = ''
    create_logger_file = True
    log_filename: str = None
    clear_queue_within_init = False
    consuming_function: typing.Callable = None
    broker_kind: int = None
    broker_exclusive_config: dict = None


if __name__ == '__main__':
    print(FunctionResultStatusPersistanceConfig(is_save_result=True, is_save_status=True, expire_seconds=70 * 24 * 3600))

    print(PriorityConsumingControlConfig().dict())

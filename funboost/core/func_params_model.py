import copy
import datetime
import json
import logging
import typing

from funboost.constant import ConcurrentModeEnum, BrokerEnum
from pydantic import BaseModel, validator, root_validator, PrivateAttr

from funboost.core.loggers import flogger


class BaseJsonAbleModel(BaseModel):
    def get_str_dict(self):
        """因为model字段包括了 函数,无法json序列化,需要自定义json序列化"""
        model_dict: dict = self.dict()  # noqa
        model_dict_copy = copy.deepcopy(model_dict)
        for k, v in model_dict.items():
            if isinstance(v, typing.Callable):
                model_dict_copy[k] = str(v)
        return model_dict_copy

    def json_str_value(self):
        return json.dumps(self.get_str_dict(), ensure_ascii=False, )

    def json_pre(self):
        return json.dumps(self.get_str_dict(), ensure_ascii=False, indent=4)

    def update_from_dict(self, dictx: dict):
        for k, v in dictx.items():
            setattr(self, k, v)
        return self

    def update_from_kwargs(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self

    def update_from_model(self, modelx: BaseModel):
        for k, v in modelx.dict().items():
            setattr(self, k, v)
        return self


class FunctionResultStatusPersistanceConfig(BaseJsonAbleModel):
    is_save_status: bool  # 是否保存函数的运行状态信息
    is_save_result: bool  # 是否保存函数的运行结果
    expire_seconds: int = 7 * 24 * 3600  # mongo中的函数运行状态保存多久时间,自动过期
    is_use_bulk_insert: bool = False  # 是否使用批量插入来保存结果，批量插入是每隔0.5秒钟保存一次最近0.5秒内的所有的函数消费状态结果，始终会出现最后0.5秒内的执行结果没及时插入mongo。为False则，每完成一次函数就实时写入一次到mongo。

    @validator('expire_seconds')
    def check_expire_seconds(cls, value):
        if value > 10 * 24 * 3600:
            flogger.warning(f'你设置的过期时间为 {value} ,设置的时间过长。 ')
        return value

    @root_validator(skip_on_failure=True)
    def cehck_values(cls, values: dict):
        if not values['is_save_status'] and values['is_save_result']:
            raise ValueError(f'你设置的是不保存函数运行状态但保存函数运行结果。不允许你这么设置')
        return values


class BoosterParams(BaseJsonAbleModel):
    """
    pydatinc pycharm编程代码补全,请安装 pydantic插件, 在pycharm的  file -> settings -> Plugins -> 输入 pydantic 搜索,点击安装 pydantic 插件.

    @boost的传参必须是此类或者继承此类,如果你不想每个装饰器入参都很多,你可以写一个子类继承BoosterParams, 传参这个子类,例如下面的 BoosterParamsComplete
    """
    queue_name: str

    concurrent_mode: str = ConcurrentModeEnum.THREADING
    concurrent_num: int = 50
    specify_concurrent_pool: typing.Callable = None
    specify_async_loop: typing.Callable = None

    qps: float = 0
    is_using_distributed_frequency_control: bool = False

    is_send_consumer_hearbeat_to_redis: bool = False

    max_retry_times: int = 3
    is_push_to_dlx_queue_when_retry_max_times: bool = False

    consumin_function_decorator: typing.Callable = None
    function_timeout: float = 0

    log_level: int = logging.DEBUG
    logger_prefix: str = ''
    create_logger_file: bool = True
    log_filename: typing.Union[str, None] = None
    is_show_message_get_from_broker: bool = False
    is_print_detail_exception: bool = True

    msg_expire_senconds: float = 0

    do_task_filtering: bool = False
    task_filtering_expire_seconds: int = 0

    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = FunctionResultStatusPersistanceConfig(
        is_save_result=False, is_save_status=False, expire_seconds=7 * 24 * 3600, is_use_bulk_insert=False)

    user_custom_record_process_info_func: typing.Callable = None

    is_using_rpc_mode: bool = False

    is_support_remote_kill_task: bool = False

    is_do_not_run_by_specify_time_effect: bool = False
    do_not_run_by_specify_time: tuple = ('10:00:00', '22:00:00')

    schedule_tasks_on_main_thread: bool = False

    consuming_function: typing.Callable = None

    broker_kind: str = BrokerEnum.PERSISTQUEUE  # 中间件选型见3.1章节 https://funboost.readthedocs.io/zh/latest/articles/c3.html

    broker_exclusive_config: dict = {}

    auto_generate_info: dict = {}  # 自动生成的信息,不需要用户主动传参.

    @root_validator(skip_on_failure=True)
    def check_values(cls, values: dict):

        # 如果设置了qps，并且cocurrent_num是默认的50，会自动开了500并发，由于是采用的智能线程池任务少时候不会真开那么多线程而且会自动缩小线程数量。具体看ThreadPoolExecutorShrinkAble的说明
        # 由于有很好用的qps控制运行频率和智能扩大缩小的线程池，此框架建议不需要理会和设置并发数量只需要关心qps就行了，框架的并发是自适应并发数量，这一点很强很好用。
        if values['qps'] and values['concurrent_num'] == 50:
            values['concurrent_num'] = 500
        if values['concurrent_mode'] == ConcurrentModeEnum.SINGLE_THREAD:
            values['concurrent_num'] = 1

        values['is_send_consumer_hearbeat_to_redis'] = values['is_send_consumer_hearbeat_to_redis'] or values['is_using_distributed_frequency_control']

        if values['concurrent_mode'] not in ConcurrentModeEnum.__dict__.values():
            raise ValueError('设置的并发模式不正确')
        return values


class BoosterParamsComplete(BoosterParams):
    """
    例如一个子类,这个子类可以作为@booot的传参,每个@boost可以少写一些这些重复的入参字段.

    支持函数消费状态 结果状态持久化
    支持发送消费者的心跳到redis,便于统计分布式环境的活跃消费者
    支持rpc模式
    永远是使用 amqpstorm包 操作 rabbbitmq作为消息队列.
    """

    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = FunctionResultStatusPersistanceConfig(
        is_save_result=True, is_save_status=True, expire_seconds=7 * 24 * 3600, is_use_bulk_insert=True)
    is_send_consumer_hearbeat_to_redis = True
    is_using_rpc_mode = True
    broker_kind = BrokerEnum.RABBITMQ_AMQPSTORM


class PriorityConsumingControlConfig(BaseJsonAbleModel):
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

    @root_validator(skip_on_failure=True)
    def cehck_values(cls, values: dict):
        if values['countdown'] and values['eta']:
            raise ValueError('不能同时设置eta和countdown')
        if values['misfire_grace_time'] is not None and values['misfire_grace_time'] < 1:
            raise ValueError(f'misfire_grace_time 的值要么是大于1的整数， 要么等于None')
        return values


class PublisherParams(BaseJsonAbleModel):
    queue_name: str
    log_level: int = logging.DEBUG
    logger_prefix: str = ''
    create_logger_file: bool = True
    log_filename: typing.Optional[str] = None
    clear_queue_within_init: bool = False
    consuming_function: typing.Callable = None
    broker_kind: str = None
    broker_exclusive_config: dict = None


if __name__ == '__main__':
    print(FunctionResultStatusPersistanceConfig(is_save_result=True, is_save_status=True, expire_seconds=70 * 24 * 3600).update_from_kwargs(expire_seconds=100).get_str_dict())

    print(PriorityConsumingControlConfig().get_str_dict())

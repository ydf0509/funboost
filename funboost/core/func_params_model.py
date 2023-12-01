import datetime
import typing

from funboost.constant import ConcurrentModeEnum, BrokerEnum
from pydantic import BaseModel, validator, root_validator
import nb_log


class FunctionResultStatusPersistanceConfig(BaseModel):
    _logger = nb_log.get_logger('FunctionResultStatusPersistanceConfig')
    is_save_status: bool
    is_save_result: bool
    expire_seconds: int = 7 * 24 * 3600
    is_use_bulk_insert: bool = False

    @validator('expire_seconds')
    def check_expire_seconds(cls, value):
        if value > 10 * 24 * 3600:
            cls._logger.warning(f'你设置的过期时间为 {value} ,设置的时间过长。 ')

    @root_validator
    def cehck_values(cls, values: dict):
        """
        :param is_save_status:
        :param is_save_result:
        :param expire_seconds: 设置统计的过期时间，在mongo里面自动会移除这些过期的执行记录。
        :param is_use_bulk_insert : 是否使用批量插入来保存结果，批量插入是每隔0.5秒钟保存一次最近0.5秒内的所有的函数消费状态结果，始终会出现最后0.5秒内的执行结果没及时插入mongo。为False则，每完成一次函数就实时写入一次到mongo。
        """
        if not values['is_save_status'] and values['is_save_result']:
            raise ValueError(f'你设置的是不保存函数运行状态但保存函数运行结果。不允许你这么设置')
        return values


class ConsumerParams:
    concurrent_mode = ConcurrentModeEnum.THREADING
    concurrent_num = 50
    specify_concurrent_pool = None
    specify_async_loop = None
    qps: float = 0
    is_using_distributed_frequency_control = False
    is_send_consumer_hearbeat_to_redis = False

    max_retry_times = 3
    is_push_to_dlx_queue_when_retry_max_times = False

    consumin_function_decorator = None
    function_timeout = 0

    log_level = 10
    logger_prefix = ''
    create_logger_file = True
    is_show_message_get_from_broker = False
    is_print_detail_exception = True

    msg_expire_senconds = 0

    do_task_filtering = False
    task_filtering_expire_seconds = 0

    function_result_status_persistance_conf = FunctionResultStatusPersistanceConfig(is_save_result=False, is_save_status=False, expire_seconds=70 * 24 * 3600)
    user_custom_record_process_info_func = None

    is_using_rpc_mode = False
    is_support_remote_kill_task = False

    is_do_not_run_by_specify_time_effect = False
    do_not_run_by_specify_time = ('10:00:00', '22:00:00')

    schedule_tasks_on_main_thread = False

    broker_exclusive_config = {}


class BoosterParams(ConsumerParams):
    broker_kind: int = BrokerEnum.PERSISTQUEUE  # 中间件选型见3.1章节 https://funboost.readthedocs.io/zh/latest/articles/c3.html


class BoosterParamsContainConsumingFunction(BoosterParams):
    consuming_function: typing.Callable


class PriorityConsumingControlConfig:
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


class PublisherParams(BaseModel):
    queue_name: str
    log_level_int: int = 10
    logger_prefix = ''
    is_add_file_handler = True
    clear_queue_within_init = False
    is_add_publish_time = True
    consuming_function: callable = None
    broker_exclusive_config: dict = None


if __name__ == '__main__':
    print(FunctionResultStatusPersistanceConfig(is_save_result=True, is_save_status=True, expire_seconds=70 * 24 * 3600))

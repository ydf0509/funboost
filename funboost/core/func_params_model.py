import asyncio
import datetime
import functools
import json
import logging
import typing
from collections import OrderedDict

from funboost.concurrent_pool import FunboostBaseConcurrentPool, FlexibleThreadPool, ConcurrentPoolBuilder
from funboost.constant import ConcurrentModeEnum, BrokerEnum
from pydantic import BaseModel, validator, root_validator, BaseConfig, Field

# noinspection PyUnresolvedReferences
from funboost.core.loggers import develop_logger
from funboost.core.loggers import flogger


def patch_for_pydantic_field_deepcopy():
    from concurrent.futures import ThreadPoolExecutor
    from asyncio import AbstractEventLoop

    # noinspection PyUnusedLocal,PyDefaultArgument
    def __deepcopy__(self, memodict={}):
        """
        pydantic 的默认值，需要deepcopy
        """
        return self

    # pydantic 的类型需要用到
    ThreadPoolExecutor.__deepcopy__ = __deepcopy__
    AbstractEventLoop.__deepcopy__ = __deepcopy__
    # BaseEventLoop.__deepcopy__ = __deepcopy__


patch_for_pydantic_field_deepcopy()


class NoExtraFieldsConfig(BaseConfig):
    allow_mutation = False
    extra = "forbid"


class BaseJsonAbleModel(BaseModel):
    """
    因为model字段包括了 函数对象,无法json序列化,需要自定义json序列化
    """

    def get_str_dict(self):
        model_dict: dict = self.dict()  # noqa
        model_dict_copy = OrderedDict()
        for k, v in model_dict.items():
            if isinstance(v, typing.Callable):
                model_dict_copy[k] = str(v)
            # elif k in ['specify_concurrent_pool', 'specify_async_loop'] and v is not None:
            elif type(v).__module__ != "builtins":  # 自定义类型的对象,json不可序列化,需要转化下.
                model_dict_copy[k] = str(v)
            else:
                model_dict_copy[k] = v
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

    class Config(BaseConfig):
        arbitrary_types_allowed = True
        # allow_mutation = False
        extra = "forbid"


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

    queue_name: str  # 队列名字,必传项,每个函数要使用不同的队列名字.

    """如果设置了qps，并且cocurrent_num是默认的50，会自动开了500并发，由于是采用的智能线程池任务少时候不会真开那么多线程而且会自动缩小线程数量。具体看ThreadPoolExecutorShrinkAble的说明
    由于有很好用的qps控制运行频率和智能扩大缩小的线程池，此框架建议不需要理会和设置并发数量只需要关心qps就行了，框架的并发是自适应并发数量，这一点很强很好用。"""
    concurrent_mode: str = ConcurrentModeEnum.THREADING  # 并发模式,支持THREADING,GEVENT,EVENTLET,ASYNC,SINGLE_THREAD并发,multi_process_consume 支持协程/线程 叠加多进程并发,性能炸裂.
    concurrent_num: int = 50  # 并发数量，并发种类由concurrent_mode决定
    specify_concurrent_pool: FunboostBaseConcurrentPool = None  # 使用指定的线程池/携程池，可以多个消费者共使用一个线程池,节约线程.不为None时候。threads_num失效
    specify_async_loop: asyncio.AbstractEventLoop = None  # 指定的async的loop循环，设置并发模式为async才能起作用。 有些包例如aiohttp,请求和httpclient的实例化不能处在两个不同的loop中,可以传过来.

    """qps:
    强悍的控制功能,指定1秒内的函数执行次数，例如可以是小数0.01代表每100秒执行一次，也可以是50代表1秒执行50次.为None则不控频。 设置qps时候,不需要指定并发数量,funboost的能够自适应智能动态调节并发池大小."""
    qps: typing.Union[float, int] = None
    """is_using_distributed_frequency_control:
    是否使用分布式空频（依赖redis统计消费者数量，然后频率平分），默认只对当前实例化的消费者空频有效。假如实例化了2个qps为10的使用同一队列名的消费者，并且都启动，则每秒运行次数会达到20。
    如果使用分布式空频则所有消费者加起来的总运行次数是10。"""
    is_using_distributed_frequency_control: bool = False

    is_send_consumer_hearbeat_to_redis: bool = False  # 是否将发布者的心跳发送到redis，有些功能的实现需要统计活跃消费者。因为有的中间件不是真mq。这个功能,需要安装redis.

    """max_retry_times:
    最大自动重试次数，当函数发生错误，立即自动重试运行n次，对一些特殊不稳定情况会有效果。
    可以在函数中主动抛出重试的异常ExceptionForRetry，框架也会立即自动重试。
    主动抛出ExceptionForRequeue异常，则当前 消息会重返中间件，
    主动抛出 ExceptionForPushToDlxqueue  异常，可以使消息发送到单独的死信队列中，死信队列的名字是 队列名字 + _dlx。"""
    max_retry_times: int = 3
    is_push_to_dlx_queue_when_retry_max_times: bool = False  # 函数达到最大重试次数仍然没成功，是否发送到死信队列,死信队列的名字是 队列名字 + _dlx。

    consumin_function_decorator: typing.Callable = None  # 函数的装饰器。因为此框架做参数自动转指点，需要获取精准的入参名称，不支持在消费函数上叠加 @ *args  **kwargs的装饰器，如果想用装饰器可以这里指定。
    function_timeout: typing.Union[int, float] = 0  # 超时秒数，函数运行超过这个时间，则自动杀死函数。为0是不限制。

    log_level: int = logging.DEBUG  # 消费者和发布者的日志级别,建议设置DEBUG级别,不然无法知道正在运行什么消息
    logger_prefix: str = ''  # 日志名字前缀,可以设置前缀
    create_logger_file: bool = True  # 发布者和消费者是否创建文件文件日志,为False则只打印控制台不写文件.
    log_filename: typing.Union[str, None] = None  # 消费者发布者的文件日志名字.如果为None,则自动使用 funboost.队列 名字作为文件日志名字.  日志文件夹是在nb_log_config.py的 LOG_PATH中决定的.
    is_show_message_get_from_broker: bool = False  # 运行时候,是否记录从消息队列获取出来的消息内容
    is_print_detail_exception: bool = True  # 消费函数出错时候,是否打印详细的报错堆栈,为False则只打印简略的报错信息不包含堆栈.

    msg_expire_senconds: typing.Union[float, int] = None  # 消息过期时间,可以设置消息是多久之前发布的就丢弃这条消息,不运行. 为None则永不丢弃

    do_task_filtering: bool = False  # 是否对函数入参进行过滤去重.
    task_filtering_expire_seconds: int = 0  # 任务过滤的失效期，为0则永久性过滤任务。例如设置过滤过期时间是1800秒 ， 30分钟前发布过1 + 2 的任务，现在仍然执行，如果是30分钟以内发布过这个任务，则不执行1 + 2

    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = FunctionResultStatusPersistanceConfig(
        is_save_result=False, is_save_status=False, expire_seconds=7 * 24 * 3600, is_use_bulk_insert=False)  # 是否保存函数的入参，运行结果和运行状态到mongodb。这一步用于后续的参数追溯，任务统计和web展示，需要安装mongo。

    user_custom_record_process_info_func: typing.Callable = None  # 提供一个用户自定义的保存消息处理记录到某个地方例如mysql数据库的函数，函数仅仅接受一个入参，入参类型是 FunctionResultStatus，用户可以打印参数

    is_using_rpc_mode: bool = False  # 是否使用rpc模式，可以在发布端获取消费端的结果回调，但消耗一定性能，使用async_result.result时候会等待阻塞住当前线程。

    is_support_remote_kill_task: bool = False  # 是否支持远程任务杀死功能，如果任务数量少，单个任务耗时长，确实需要远程发送命令来杀死正在运行的函数，才设置为true，否则不建议开启此功能。

    is_do_not_run_by_specify_time_effect: bool = False  # 是否使不运行的时间段生效
    do_not_run_by_specify_time: tuple = ('10:00:00', '22:00:00')  # 不运行的时间段,在这个时间段自动不运行函数.

    schedule_tasks_on_main_thread: bool = False  # 直接在主线程调度任务，意味着不能直接在当前主线程同时开启两个消费者。

    consuming_function: typing.Callable = None  # 消费函数,在@boost时候不用指定,因为装饰器知道下面的函数.

    broker_kind: str = BrokerEnum.PERSISTQUEUE  # 中间件选型见3.1章节 https://funboost.readthedocs.io/zh/latest/articles/c3.html

    broker_exclusive_config: dict = {}  # 加上一个不同种类中间件非通用的配置,不同中间件自身独有的配置，不是所有中间件都兼容的配置，因为框架支持30种消息队列，消息队列不仅仅是一般的先进先出queue这么简单的概念，
    # 例如kafka支持消费者组，rabbitmq也支持各种独特概念例如各种ack机制 复杂路由机制，每一种消息队列都有独特的配置参数意义，可以通过这里传递。

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
        # if not set(values.keys()).issubset(set(BoosterParams.__fields__.keys())):
        #     raise ValueError(f'{cls.__name__} 的字段包含了父类 BoosterParams 不存在的字段')
        for k in values.keys():
            if k not in BoosterParams.__fields__.keys():
                raise ValueError(f'{cls.__name__} 的字段新增了父类 BoosterParams 不存在的字段 "{k}"')  # 使 BoosterParams的子类,不能增加字段,只能覆盖字段.
        return values


class BoosterParamsComplete(BoosterParams):
    """
    例如一个子类,这个BoosterParams的子类可以作为@booot的传参,每个@boost可以少写一些这些重复的入参字段.

    function_result_status_persistance_conf 永远支持函数消费状态 结果状态持久化
    is_send_consumer_hearbeat_to_redis 永远支持发送消费者的心跳到redis,便于统计分布式环境的活跃消费者
    is_using_rpc_mode  永远支持rpc模式
    broker_kind 永远是使用 amqpstorm包 操作 rabbbitmq作为消息队列.
    specify_concurrent_pool 同一个进程的不同booster函数,共用一个线程池,线程资源利用更高.
    """

    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = FunctionResultStatusPersistanceConfig(
        is_save_result=True, is_save_status=True, expire_seconds=7 * 24 * 3600, is_use_bulk_insert=True)  # 开启函数消费状态 结果持久化到 mongo,为True用户必须要安装mongo和多浪费一丝丝性能.
    is_send_consumer_hearbeat_to_redis: bool = True  # 消费者心跳发到redis,为True那么用户必须安装reids
    is_using_rpc_mode: bool = True  # 固定支持rpc模式,不用每次指定 (不需要使用rpc模式的同学,就不要指定为True,必须安装redis和浪费一点性能)
    broker_kind: str = BrokerEnum.RABBITMQ_AMQPSTORM  # 固定使用rabbitmq,不用每次指定
    specify_concurrent_pool: FunboostBaseConcurrentPool = Field(default_factory=functools.partial(ConcurrentPoolBuilder.get_pool, FlexibleThreadPool, 500)) # 多个消费函数共享线程池


class PriorityConsumingControlConfig(BaseJsonAbleModel):
    """
    为每个独立的任务设置控制参数，和函数参数一起发布到中间件。可能有少数时候有这种需求。
    例如消费为add函数，可以每个独立的任务设置不同的超时时间，不同的重试次数，是否使用rpc模式。这里的配置优先，可以覆盖生成消费者时候的配置。
    """

    function_timeout: typing.Union[float, int] = None
    max_retry_times: int = None
    is_print_detail_exception: bool = None
    msg_expire_senconds: int = None
    is_using_rpc_mode: bool = None
    countdown: typing.Union[float, int] = None
    eta: datetime.datetime = None
    misfire_grace_time: typing.Union[int, None] = None
    other_extra_params: dict = None  # 其他参数, 例如消息优先级 , priority_control_config=PriorityConsumingControlConfig(other_extra_params={'priroty': priorityxx})，

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
    clear_queue_within_init: bool = False  # with 语法发布时候,先清空消息队列
    consuming_function: typing.Callable = None  # consuming_function 作用是 inspect 模块获取函数的入参信息
    broker_kind: str = None
    broker_exclusive_config: dict = {}


if __name__ == '__main__':
    from funboost.concurrent_pool import FlexibleThreadPool

    pass
    # print(FunctionResultStatusPersistanceConfig(is_save_result=True, is_save_status=True, expire_seconds=70 * 24 * 3600).update_from_kwargs(expire_seconds=100).get_str_dict())
    #
    # print(PriorityConsumingControlConfig().get_str_dict())

    print(BoosterParams(queue_name='3213', specify_concurrent_pool=FlexibleThreadPool(100)).json_pre())

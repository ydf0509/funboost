"""
pydantic 模型定义， funboost 使用pydantic 作为重要函数的入参，
方便函数入参太多在层层传递时候的麻烦，例如 BoosterParams 经常新增字段，如果funboost直接入参一大堆，需要每一层都去新增入参很麻烦

BoosterParams 是 funboost 最核心的入参模型，掌握了 BoosterParams 就是掌握了 funboost 的90% 用法。

"""

import functools
import typing
import asyncio
import logging
import datetime
from pydantic.fields import Field
from typing_extensions import Literal

from funboost.concurrent_pool.pool_commons import ConcurrentPoolBuilder
from funboost.concurrent_pool.flexible_thread_pool import FlexibleThreadPool
from funboost.core.lazy_impoter import funboost_lazy_impoter
from funboost.core.pydantic_compatible_base import compatible_root_validator
from funboost.core.pydantic_compatible_base import BaseJsonAbleModel
from funboost.constant import BrokerEnum, ConcurrentModeEnum, StrConst


from funboost.concurrent_pool import FunboostBaseConcurrentPool

class FunctionResultStatusPersistanceConfig(BaseJsonAbleModel):
    is_save_status: bool  # 是否保存函数的运行状态信息
    is_save_result: bool  # 是否保存函数的运行结果
    expire_seconds: int = 7 * 24 * 3600  # mongo中的函数运行状态保存多久时间,自动过期
    is_use_bulk_insert: bool = False  # 是否使用批量插入来保存结果，批量插入是每隔0.5秒钟保存一次最近0.5秒内的所有的函数消费状态结果，始终会出现最后0.5秒内的执行结果没及时插入mongo。为False则，每完成一次函数就实时写入一次到mongo。
    table_name:typing.Optional[str] = None # 表名，用于指定保存函数运行状态和结果的表名，默认使用队列名作为表名。   

    @compatible_root_validator(skip_on_failure=True)
    def check_values(self, ):
        expire_seconds = self.expire_seconds
        if expire_seconds > 10 * 24 * 3600:
            funboost_lazy_impoter.flogger.warning(f'你设置的过期时间为 {expire_seconds} 秒 ,设置的时间过长。 ')
        if not self.is_save_status and self.is_save_result:
            raise ValueError(f'你设置的是不保存函数运行状态但保存函数运行结果。不允许你这么设置')
        return self

class BoosterParams(BaseJsonAbleModel):
    """
    pydatinc pycharm编程代码补全,请安装 pydantic插件, 在pycharm的  file -> settings -> Plugins -> 输入 pydantic 搜索,点击安装 pydantic 插件.

    @boost的传参必须是此类或者继承此类,如果你不想每个装饰器入参都很多,你可以写一个子类继承BoosterParams, 传参这个子类,例如下面的 BoosterParamsComplete
    """

    queue_name: str  # 队列名字,必传项,每个函数要使用不同的队列名字.
    broker_kind: str = BrokerEnum.SQLITE_QUEUE  # 中间件选型见3.1章节 https://funboost.readthedocs.io/zh-cn/latest/articles/c3.html

    """ project_name是项目名，属于管理层面的标签, 默认为None, 给booster设置所属项目名, 用于对于在redis保存的funboost信息中，根据项目名字查看相关队列。
    # 如果不设置很难从redis保存的funboost信息中，区分哪些队列名属于哪个项目。 主要是给web接口查看用。
    # 一个项目的队列名字有哪些，是保存在redis的set中，key为 f'funboost.project_name:{project_name}'
    # 通常配合 CareProjectNameEnv.set($project_name) 使用 ，它可以让你在监控和管理时“只看自己的一亩三分地“，避免被其他人的队列刷屏干扰。"""
    project_name: typing.Optional[str] = None

    """如果设置了qps，并且cocurrent_num是默认的50，会自动开了500并发，由于是采用的智能线程池任务少时候不会真开那么多线程而且会自动缩小线程数量。
    具体看ThreadPoolExecutorShrinkAble的说明
    由于有很好用的qps控制运行频率和智能扩大缩小的线程池，此框架建议不需要理会和设置并发数量只需要关心qps就行了，框架的并发是自适应并发数量，这一点很强很好用。"""
    concurrent_mode: str = ConcurrentModeEnum.THREADING  # 并发模式,支持THREADING,GEVENT,EVENTLET,ASYNC,SINGLE_THREAD并发,multi_process_consume 支持协程/线程 叠加多进程并发,性能炸裂.
    concurrent_num: int = 50  # 并发数量，并发种类由concurrent_mode决定
    specify_concurrent_pool: typing.Optional[FunboostBaseConcurrentPool] = None  # 使用指定的线程池/携程池，可以多个消费者共使用一个线程池,节约线程.不为None时候。threads_num失效
    
    specify_async_loop: typing.Optional[asyncio.AbstractEventLoop] = None  # 指定的async的loop循环，设置并发模式为async才能起作用。 有些包例如aiohttp,发送请求和httpclient的实例化不能处在两个不同的loop中,可以传过来.
    is_auto_start_specify_async_loop_in_child_thread: bool = True  # 是否自动在funboost asyncio并发池的子线程中自动启动指定的async的loop循环，设置并发模式为async才能起作用。如果是False,用户自己在自己的代码中去手动启动自己的loop.run_forever() 
    
    """qps:
    强悍的控制功能,指定1秒内的函数执行次数，例如可以是小数0.01代表每100秒执行一次，也可以是50代表1秒执行50次.为None则不控频。 
    设置qps时候,不需要指定并发数量,funboost的能够自适应智能动态调节并发池大小."""
    qps: typing.Union[float, int, None] = None
    """is_using_distributed_frequency_control:
    是否使用分布式空频（依赖redis统计消费者数量，然后频率平分），默认只对当前实例化的消费者空频有效。
    假如实例化了2个qps为10的使用同一队列名的消费者，并且都启动，则每秒运行次数会达到20。
    如果使用分布式空频则所有消费者加起来的总运行次数是10。"""
    is_using_distributed_frequency_control: bool = False

    is_send_consumer_heartbeat_to_redis: bool = False  # 是否将发布者的心跳发送到redis，有些功能的实现需要统计活跃消费者。因为有的中间件不是真mq。这个功能,需要安装redis.

    """max_retry_times:
    最大自动重试次数，当函数发生错误，立即自动重试运行n次，对一些特殊不稳定情况会有效果。
    可以在函数中主动抛出重试的异常ExceptionForRetry，框架也会立即自动重试。
    主动抛出ExceptionForRequeue异常，则当前 消息会重返中间件，
    主动抛出 ExceptionForPushToDlxqueue  异常，可以使消息发送到单独的死信队列中，死信队列的名字是 队列名字 + _dlx。"""
    max_retry_times: int = 3
    retry_interval: typing.Union[float, int] = 0  # 函数出错后间隔多少秒再重试.
    is_push_to_dlx_queue_when_retry_max_times: bool = False  # 函数达到最大重试次数仍然没成功，是否发送到死信队列,死信队列的名字是 队列名字 + _dlx。


    consuming_function_decorator: typing.Optional[typing.Callable] = None  # 函数的装饰器。因为此框架做参数自动转指点，需要获取精准的入参名称，不支持在消费函数上叠加 @ *args  **kwargs的装饰器，如果想用装饰器可以这里指定。
    
    
    """
    function_timeout: 
    超时秒数，函数运行超过这个时间，则自动杀死函数。为0是不限制。 
    用户应该尽量使用各种三方包例如 aiohttp pymysql 自己的 socket timeout 设置来控制超时，而不是无脑使用funboost的function_timeout参数。
    谨慎使用,非必要别去设置超时时间,设置后性能会降低(因为需要把用户函数包装到另一个线单独的程中去运行),而且突然强制超时杀死运行中函数,可能会造成死锁.
    (例如用户函数在获得线程锁后突然杀死函数,别的线程再也无法获得锁了)
    """
    function_timeout: typing.Union[int, float,None] = None 
    """
    is_support_remote_kill_task:
    是否支持远程任务杀死功能，如果任务数量少，单个任务耗时长，确实需要远程发送命令来杀死正在运行的函数，才设置为true，否则不建议开启此功能。
    (是把函数放在单独的线程中实现的,随时准备线程被远程命令杀死,所以性能会降低)
    """
    is_support_remote_kill_task: bool = False  
   
    """
    log_level:
        logger_name 对应的 日志级别
        消费者和发布者的日志级别,建议设置DEBUG级别,不然无法知道正在运行什么消息.
        这个是funboost每个队列的单独命名空间的日志级别,丝毫不会影响改变用户其他日志以及root命名空间的日志级别,所以DEBUG级别就好,
        用户不要压根不懂什么是python logger 的name,还去手痒调高级别. 
        不懂python日志命名空间的小白去看nb_log文档,或者直接问 ai大模型 python logger name的作用是什么.
    """
    log_level: int = logging.DEBUG # 不需要改这个级别,请看上面原因
    logger_prefix: str = ''  # 日志名字前缀,可以设置前缀
    create_logger_file: bool = True  # 发布者和消费者是否创建文件文件日志,为False则只打印控制台不写文件.
    logger_name: typing.Union[str, None] = ''  # 队列消费者发布者的日志命名空间.
    log_filename: typing.Union[str, None] = None  # 消费者发布者的文件日志名字.如果为None,则自动使用 funboost.队列 名字作为文件日志名字.  日志文件夹是在nb_log_config.py的 LOG_PATH中决定的.
    is_show_message_get_from_broker: bool = False  # 运行时候,是否记录从消息队列获取出来的消息内容
    is_print_detail_exception: bool = True  # 消费函数出错时候,是否打印详细的报错堆栈,为False则只打印简略的报错信息不包含堆栈.
    publish_msg_log_use_full_msg: bool = False # 发布到消息队列的消息内容的日志，是否显示消息的完整体，还是只显示函数入参。

    msg_expire_seconds: typing.Union[float, int,None] = None  # 消息过期时间,可以设置消息是多久之前发布的就丢弃这条消息,不运行. 为None则永不丢弃

    do_task_filtering: bool = False  # 是否对函数入参进行过滤去重.
    task_filtering_expire_seconds: int = 0  # 任务过滤的失效期，为0则永久性过滤任务。例如设置过滤过期时间是1800秒 ， 30分钟前发布过1 + 2 的任务，现在仍然执行，如果是30分钟以内执行过这个任务，则不执行1 + 2

    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = FunctionResultStatusPersistanceConfig(
        is_save_result=False, is_save_status=False, expire_seconds=7 * 24 * 3600, is_use_bulk_insert=False)  # 是否保存函数的入参，运行结果和运行状态到mongodb。这一步用于后续的参数追溯，任务统计和web展示，需要安装mongo。

    user_custom_record_process_info_func: typing.Optional[typing.Callable] = None  # 提供一个用户自定义的保存消息处理记录到某个地方例如mysql数据库的函数，函数仅仅接受一个入参，入参类型是 FunctionResultStatus，用户可以打印参数

    is_using_rpc_mode: bool = False  # 是否使用rpc模式，可以在发布端获取消费端的结果回调，但消耗一定性能，使用async_result.result时候会等待阻塞住当前线程。
    rpc_result_expire_seconds: int = 1800  # redis保存rpc结果的过期时间.
    rpc_timeout:int = 1800 # rpc模式下，等待rpc结果返回的超时时间

    delay_task_apscheduler_jobstores_kind :Literal[ 'redis', 'memory'] = 'redis'  # 延时任务的aspcheduler对象使用哪种jobstores ，可以为 redis memory 两种作为jobstore

    
    is_do_not_run_by_specify_time_effect: bool = False  # 是否使不运行的时间段生效
    do_not_run_by_specify_time: list = ['10:00:00', '22:00:00']  # 不运行的时间段,在这个时间段自动不运行函数.

    schedule_tasks_on_main_thread: bool = False  # 直接在主线程调度任务，意味着不能直接在当前主线程同时开启两个消费者。

    is_auto_start_consuming_message: bool = False  # 是否在定义后就自动启动消费，无需用户手动写 .consume() 来启动消息消费。
    
    # booster_group :消费分组名字， BoostersManager.consume_group 时候根据 booster_group 启动多个消费函数,减少需要写 f1.consume() f2.consume() ...这种。
    # 不像BoostersManager.consume_all() 会启动所有不相关消费函数,也不像  f1.consume() f2.consume() 这样需要逐个启动消费函数。
    # 可以根据业务逻辑创建不同的分组，实现灵活的消费启动策略。
    # 用法见文档 4.2d.3 章节.   使用 BoostersManager ,通过 consume_group 启动一组消费函数
    booster_group:typing.Union[str, None] = None

    consuming_function: typing.Optional[typing.Callable] = None  # 消费函数,在@boost时候不用指定,因为装饰器知道下面的函数.
    consuming_function_raw: typing.Optional[typing.Callable] = None  # 不需要传递，自动生成
    consuming_function_name: str = '' # 不需要传递，自动生成

    
    """
    # 加上一个不同种类中间件非通用的配置,不同中间件自身独有的配置，不是所有中间件都兼容的配置，因为框架支持30种消息队列，消息队列不仅仅是一般的先进先出queue这么简单的概念，
    # 例如kafka支持消费者组，rabbitmq也支持各种独特概念例如各种ack机制 复杂路由机制，有的中间件原生能支持消息优先级有的中间件不支持,
    # 每一种消息队列都有独特的配置参数意义，可以通过这里传递。
    # 每种中间件能传递的键值对可以看 funboost/core/broker_kind__exclusive_config_default.py 的 BROKER_EXCLUSIVE_CONFIG_DEFAULT 属性。
    """
    broker_exclusive_config: dict = {} 
    


    should_check_publish_func_params: bool = True  # 消息发布时候是否校验消息发布内容,比如有的人发布消息,函数只接受a,b两个入参,他去传2个入参,或者传参不存在的参数名字; 如果消费函数加了装饰器 ，你非要写*args,**kwargs,那就需要关掉发布消息时候的函数入参检查
    manual_func_input_params :dict= {'is_manual_func_input_params': False,'must_arg_name_list':[],'optional_arg_name_list':[]} # 也可以手动指定函数入参字段，默认是根据消费函数def定义的入参来生成这个。


    consumer_override_cls: typing.Optional[typing.Type] = None  # 使用 consumer_override_cls 和 publisher_override_cls 来自定义重写或新增消费者 发布者,见文档4.21b介绍，
    publisher_override_cls: typing.Optional[typing.Type] = None

    # func_params_is_pydantic_model: bool = False  # funboost 兼容支持 函数娼还是 pydantic model类型，funboost在发布之前和取出来时候自己转化。

    consuming_function_kind: typing.Optional[str] = None  # 自动生成的信息,不需要用户主动传参,如果自动判断失误就传递。是判断消费函数是函数还是实例方法还是类方法。如果传递了，就不自动获取函数类型。
    """ consuming_function_kind 可以为以下类型，
    class FunctionKind:
        CLASS_METHOD = 'CLASS_METHOD'
        INSTANCE_METHOD = 'INSTANCE_METHOD'
        STATIC_METHOD = 'STATIC_METHOD'
        COMMON_FUNCTION = 'COMMON_FUNCTION'
    """

    """
    user_options:
    用户额外自定义的配置,高级用户或者奇葩需求可以用得到,用户可以自由发挥,存放任何设置.
    user_options 提供了一个统一的、用户自定义的命名空间，让用户可以为自己的“奇葩需求”或“高级定制”传递配置，而无需等待框架开发者添加官方支持。
    funboost 是自由框架不是奴役框架,不仅消费函数逻辑自由,目录层级结构自由,自定义奇葩扩展也要追求自由,用户不用改funboost BoosterParams 源码来加装饰器参数
    
    使用场景见文档 4b.6 章节.
    """
    user_options: dict = {} # 用户自定义的配置,高级用户或者奇葩需求可以用得到,用户可以自由发挥,存放任何设置,例如配合 consumer_override_cls中读取 或 register_custom_broker 使用
    
    
    auto_generate_info: dict = {}  # 自动生成的信息,不需要用户主动传参.例如包含 final_func_input_params_info 和 where_to_instantiate 等。
    
    """# is_fake_booster：是否是伪造的booster,
    # 用于faas模式下，因为跨项目的faas管理只拿到了redis的一些基本元数据，没有booster的函数逻辑，
    # 例如ApsJobAdder管理定时任务，需要booster，但没有真实的函数逻辑，
    # 你可以看 SingleQueueConusmerParamsGetter.gen_booster_for_faas 的用法，目前主要是控制不要执行 BoostersManager.regist_booster
    # 普通用户完全不用改这个参数。
    """
    is_fake_booster: bool = False
    booster_registry_name: str = StrConst.BOOSTER_REGISTRY_NAME_DEFAULT  # 普通用户不用管不用改，用于隔离boosters注册。例如faas的是虚假的跨服务跨项目的booster，没有具体函数逻辑，不可污染真正的注册。
    

    @compatible_root_validator(skip_on_failure=True, )
    def check_values(self):
       
        # 如果设置了qps，并且cocurrent_num是默认的50，会自动开了500并发，由于是采用的智能线程池任务少时候不会真开那么多线程而且会自动缩小线程数量。具体看ThreadPoolExecutorShrinkAble的说明
        # 由于有很好用的qps控制运行频率和智能扩大缩小的线程池，此框架建议不需要理会和设置并发数量只需要关心qps就行了，框架的并发是自适应并发数量，这一点很强很好用。
        if self.qps and self.concurrent_num == 50:
            self.concurrent_num = 500
        if self.concurrent_mode == ConcurrentModeEnum.SINGLE_THREAD:
            self.concurrent_num = 1

        self.is_send_consumer_heartbeat_to_redis = self.is_send_consumer_heartbeat_to_redis or self.is_using_distributed_frequency_control

        if self.concurrent_mode not in ConcurrentModeEnum.__dict__.values():
            raise ValueError('设置的并发模式不正确')
        if self.broker_kind in [BrokerEnum.REDIS_ACK_ABLE, BrokerEnum.REDIS_STREAM, BrokerEnum.REDIS_PRIORITY, 
                                     BrokerEnum.RedisBrpopLpush,BrokerEnum.REDIS,BrokerEnum.REDIS_PUBSUB]:
            self.is_send_consumer_heartbeat_to_redis = True  # 需要心跳进程来辅助判断消息是否属于掉线或关闭的进程，需要重回队列
       
        if self.function_result_status_persistance_conf.table_name is None:
            self.function_result_status_persistance_conf.table_name = self.queue_name
        
        # 禁止子类添加 BoosterParams 中不存在的字段，主要是担心用户继承的子类中拼写错误，本以为自己是覆盖父类字段默认值，实际却变成了新增了字段。
        # 兼容 Pydantic v1 和 v2 获取所有字段
        self_fields = self.model_fields.keys() if hasattr(self, 'model_fields') else self.__fields__.keys()
        parent_fields = BoosterParams.model_fields.keys() if hasattr(BoosterParams, 'model_fields') else BoosterParams.__fields__.keys()
        for k in self_fields:
            if k not in parent_fields:
                raise ValueError(f'{self.__class__.__name__} 的字段新增了父类 BoosterParams 不存在的字段 "{k}"')  # 使 BoosterParams的子类,不能增加字段,只能覆盖字段.
        
        return self

    def __call__(self, func):
        """
        新增加一种语法,
        一般是使用@boost(BoosterParams(queue_name='q1',qps=2))，你如果图方便可以使用 @BoosterParams(queue_name='q1',qps=2)这样的写法。

        @BoosterParams(queue_name='q1',qps=2) 这个和 @boost(BoosterParams(queue_name='q1',qps=2)) 写法等效,

        @BoosterParams(queue_name='q1',qps=2)
        def f(a,b):
            print(a,b)
        :param func:
        :return:
        """
        return funboost_lazy_impoter.boost(self)(func)


class BoosterParamsComplete(BoosterParams):
    """
    例如一个子类,这个BoosterParams的子类可以作为@booot的传参,每个@boost可以少写一些这些重复的入参字段.

    function_result_status_persistance_conf 永远支持函数消费状态 结果状态持久化
    is_send_consumer_heartbeat_to_redis 永远支持发送消费者的心跳到redis,便于统计分布式环境的活跃消费者
    is_using_rpc_mode  永远支持rpc模式
    broker_kind 永远是使用 amqpstorm包 操作 rabbbitmq作为消息队列.
    specify_concurrent_pool 同一个进程的不同booster函数,共用一个线程池,线程资源利用更高.
    """

    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = FunctionResultStatusPersistanceConfig(
        is_save_result=True, is_save_status=True, expire_seconds=7 * 24 * 3600, is_use_bulk_insert=True)  # 开启函数消费状态 结果持久化到 mongo,为True用户必须要安装mongo和多浪费一丝丝性能.
    is_send_consumer_heartbeat_to_redis: bool = True  # 消费者心跳发到redis,为True那么用户必须安装reids
    is_using_rpc_mode: bool = True  # 固定支持rpc模式,不用每次指定 (不需要使用rpc模式的同学,就不要指定为True,必须安装redis和浪费一点性能)
    rpc_result_expire_seconds: int = 3600
    broker_kind: str = BrokerEnum.RABBITMQ_AMQPSTORM  # 固定使用rabbitmq,不用每次指定
    specify_concurrent_pool: FunboostBaseConcurrentPool = Field(default_factory=functools.partial(ConcurrentPoolBuilder.get_pool, FlexibleThreadPool, 500))  # 多个消费函数共享线程池


class TaskOptions(BaseJsonAbleModel):
    """
    这个是 publish 支持的额外参数，和函数参数一起发布到中间件。
    可能有少数时候有这种需求。如果需要发布额外字段到消息队列，必须使用publish方法，push方法是类似celery的dalay只能发布函数入参自身。
    这里面的字段值如果非None，会放到消息队列的消息里面的 extra 字段中。
    """
    # task_id 和 publish_time 和 publish_time_format 这三个可以指定，如果不指定就自动生成
    task_id: str = None
    publish_time: float = None
    publish_time_format: str = None
    
    # function_timeout，max_retry_times，is_print_detail_exception，msg_expire_seconds，is_using_rpc_mode 这几个是 消费函数执行时候的控制参数，
    # 这个优先级比BoosterParams更高，例如 BoosterParams 设置重试3次，你可以通过 TaskOptions 设置重试10次，那么最终消费函数执行时候，会按照 TaskOptions 中的设置来执行。
    # task_options 中的设置，优先级 高于 @boost(BoosterParams(...)) 中的设置。
    function_timeout: typing.Union[float, int,None] = None
    max_retry_times: typing.Union[int,None] = None
    is_print_detail_exception: typing.Union[bool,None] = None
    msg_expire_seconds: typing.Union[float, int,None] = None
    is_using_rpc_mode: typing.Union[bool,None] = None

    # countdown，eta，misfire_grace_time 这三个是 发布延时任务
    countdown: typing.Union[float, int,None] = None
    eta: typing.Union[datetime.datetime, str,None] = None  # 时间对象， 或 %Y-%m-%d %H:%M:%S 字符串。
    misfire_grace_time: typing.Union[int, None] = None
    
    user_extra_info: typing.Optional[dict] = None # 用户自定义的额外信息，用户随意存放任何信息，但要保证可以json序列化。可以在消费端通过 fct.full_msg 获取。

    other_extra_params: typing.Optional[dict] = None  # 其他参数，某些中间件独有的, 例如消息优先级 , task_options=TaskOptions(other_extra_params={'priroty': priorityxx})，
    
    """filter_str:
    用户指定过滤字符串， 例如函数入参是 def fun(userid,username,sex，user_description),
    默认是所有入参一起组成json来过滤，但其实只把userid的值来过滤就好了。所以如果需要精准的按照什么过滤，用户来灵活指定一个字符串就好了
    
    用法见文档4.35 
    f3.publish(msg={'a':i,'b':i*2},task_options=TaskOptions(filter_str=str(i)))
    """
    filter_str :typing.Optional[str] = None 

    can_not_json_serializable_keys: typing.List[str] = None # 不能json序列化的入参名字，反序列化时候需要使用pickle来反序列化这些字段(这个是自动生成的，用户不需要手动指定此入参。)
    
    otel_context :typing.Optional[dict] = None # opentelemetry 的上下文，用于链路追踪

    @compatible_root_validator(skip_on_failure=True)
    def cehck_values(self):
        if self.countdown and self.eta:
            raise ValueError('不能同时设置eta和countdown')
        if self.misfire_grace_time is not None and self.misfire_grace_time < 1:
            raise ValueError(f'misfire_grace_time 的值要么是大于1的整数， 要么等于None')
        return self


# PriorityConsumingControlConfig = TaskOptions # 兼容老名字

class PublisherParams(BaseJsonAbleModel):
    queue_name: str
    broker_kind: typing.Optional[str] = None

    # 项目名, 默认为None, 给booster设置所属项目名, 用于在redis保存的funboost信息中，根据项目名字查看相关队列。
    # 如果不设置很难从redis保存的funboost信息中，区分哪些队列名属于哪个项目。 主要是给web接口查看用。
    project_name: typing.Optional[str] = None # 推荐去设置

    log_level: int = logging.DEBUG
    logger_prefix: str = ''
    create_logger_file: bool = True
    logger_name: str = ''  # 队列消费者发布者的日志命名空间.
    log_filename: typing.Optional[str] = None
    clear_queue_within_init: bool = False  # with 语法发布时候,先清空消息队列
    consuming_function: typing.Optional[typing.Callable] = None  # consuming_function 作用是 inspect 模块获取函数的入参信息

    broker_exclusive_config: dict = {}
    
    should_check_publish_func_params: bool = True  # 消息发布时候是否校验消息发布内容,比如有的人发布消息,函数只接受a,b两个入参,他去传2个入参,或者传参不存在的参数名字,  如果消费函数你非要写*args,**kwargs,那就需要关掉发布消息时候的函数入参检查
    manual_func_input_params :dict= {'is_manual_func_input_params': False,'must_arg_name_list':[],'optional_arg_name_list':[]}

    publisher_override_cls: typing.Optional[typing.Type] = None
    # func_params_is_pydantic_model: bool = False  # funboost 兼容支持 函数娼还是 pydantic model类型，funboost在发布之前和取出来时候自己转化。
    publish_msg_log_use_full_msg: bool = False # 发布到消息队列的消息内容的日志，是否显示消息的完整体，还是只显示函数入参。
    consuming_function_kind: typing.Optional[str] = None  # 自动生成的信息,不需要用户主动传参.
    rpc_timeout: int = 1800 # rpc模式下，等待rpc结果返回的超时时间
    user_options: dict = {}  # 用户自定义的配置,高级用户或者奇葩需求可以用得到,用户可以自由发挥,存放任何设置.
    auto_generate_info: dict = {}
    is_fake_booster: bool = False # 是否是伪造的booster, 不注册到BoostersManager
    booster_registry_name: str = StrConst.BOOSTER_REGISTRY_NAME_DEFAULT  # 普通用户不用管不用改，用于隔离boosters注册。例如faas的是虚假的跨服务跨项目的booster，没有具体函数逻辑，不可污染真正的注册。
    
    


if __name__ == '__main__':
    from funboost.concurrent_pool import FlexibleThreadPool

    pass
    # print(FunctionResultStatusPersistanceConfig(is_save_result=True, is_save_status=True, expire_seconds=70 * 24 * 3600).update_from_kwargs(expire_seconds=100).get_str_dict())
    #
    # print(TaskOptions().get_str_dict())

    print(BoosterParams(queue_name='3213', specify_concurrent_pool=FlexibleThreadPool(100)).json_pre())
    # print(PublisherParams.schema_json())  # 注释掉，因为 PublisherParams 包含 Callable 类型字段，无法生成 JSON Schema

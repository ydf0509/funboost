# -*- coding: utf-8 -*-

from pathlib import Path
from funboost.constant import BrokerEnum, ConcurrentModeEnum
from funboost.helpers import FunctionResultStatusPersistanceConfig
from funboost.utils.simple_data_class import DataClassBase

'''
此文件是第一次运行框架自动生成刀项目根目录的，不需要用由户手动创建。
'''

'''
你项目根目录下自动生成的 funboost_config.py 文件中修改配置，会被自动读取到。

此文件按需修改，例如你使用redis中间件作为消息队列，可以不用管rabbitmq mongodb kafka啥的配置。
但有3个功能例外，如果你需要使用rpc模式或者分布式控频或者任务过滤功能，无论设置使用何种消息队列中间件都需要把redis连接配置好，
如果@boost装饰器设置is_using_rpc_mode为True或者 is_using_distributed_frequency_control为True或do_task_filtering=True则需要把redis连接配置好，默认是False。


框架使用文档是 https://funboost.readthedocs.io/zh_CN/latest/

'''

# 如果@boost装饰器没有亲自指定broker_kind入参，则默认使用DEFAULT_BROKER_KIND这个中间件。
# 强烈推荐安装rabbitmq然后使用 BrokerEnum.RABBITMQ_AMQPSTORM 这个中间件,
# 次之 BrokerEnum.REDIS_ACK_ABLE中间件，kafka则推荐 BrokerEnum.CONFLUENT_KAFKA。
# BrokerEnum.PERSISTQUEUE 的优点是基于单机磁盘的消息持久化，不需要安装消息中间件软件就能使用，但不是跨机器的真分布式。
DEFAULT_BROKER_KIND = BrokerEnum.PERSISTQUEUE

MONGO_CONNECT_URL = f'mongodb://192.168.6.133:27017'  # 如果有密码连接 'mongodb://myUserAdmin:8mwTdy1klnSYepNo@192.168.199.202:27016/admin'

RABBITMQ_USER = 'rabbitmq_user'
RABBITMQ_PASS = 'rabbitmq_pass'
RABBITMQ_HOST = '127.0.0.1'
RABBITMQ_PORT = 5672
RABBITMQ_VIRTUAL_HOST = '/'  # my_host # 这个是rabbitmq的虚拟子host用户自己创建的，如果你想直接用rabbitmq的根host而不是使用虚拟子host，这里写 / 即可。

REDIS_HOST = '127.0.0.1'
REDIS_PASSWORD = ''
REDIS_PORT = 6379
REDIS_DB = 7

NSQD_TCP_ADDRESSES = ['127.0.0.1:4150']
NSQD_HTTP_CLIENT_HOST = '127.0.0.1'
NSQD_HTTP_CLIENT_PORT = 4151

KAFKA_BOOTSTRAP_SERVERS = ['127.0.0.1:9092']

SQLACHEMY_ENGINE_URL = 'sqlite:////sqlachemy_queues/queues.db'

# persist_quque中间件时候采用本机sqlite的方式，数据库文件生成的位置。如果linux账号在根目录没权限建文件夹，可以换文件夹。
SQLLITE_QUEUES_PATH = '/sqllite_queues'

TXT_FILE_PATH = Path(__file__).parent / 'txt_queues'  # 不建议使用这个txt模拟消息队列中间件，本地持久化优先选择 PERSIST_QUQUE 中间件。

ROCKETMQ_NAMESRV_ADDR = '192.168.199.202:9876'

MQTT_HOST = '127.0.0.1'
MQTT_TCP_PORT = 1883

HTTPSQS_HOST = '127.0.0.1'
HTTPSQS_PORT = '1218'
HTTPSQS_AUTH = '123456'

NATS_URL = 'nats://192.168.6.134:4222'

KOMBU_URL = 'redis://127.0.0.1:6379/0'
# KOMBU_URL =  'sqla+sqlite:////dssf_kombu_sqlite.sqlite'  # 4个//// 代表磁盘根目录下生成一个文件。推荐绝对路径。3个///是相对路径。


# nb_log包的第几个日志模板，内置了7个模板，可以在你当前项目根目录下的nb_log_config.py文件扩展模板。
NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER = 11  # 7是简短的不可跳转，5是可点击跳转的，11是可显示ip 进程 线程的模板。
FSDF_DEVELOP_LOG_LEVEL = 50  # 开发时候的日志，仅供我自己用，所以日志级别跳到最高，用户不需要管。

TIMEZONE = 'Asia/Shanghai'

"""
BoostDecoratorDefaultParams是
@boost装饰器默认的全局入参。如果boost没有亲自指定某个入参，就自动使用这里的配置。
这里的值不用配置，在boost装饰器中可以为每个消费者指定不同的入参，
除非你嫌弃每个 boost 装饰器相同入参太多了，可以设置这里的全局默认值。
"""


class BoostDecoratorDefaultParams(DataClassBase):
    '''
    这个concurrent_mode是并发模式,有5种细粒度并发模式，可以叠加多进程并发。
    1线程(ConcurrentModeEnum.THREADING) 2 gevent(ConcurrentModeEnum.GEVENT)
    3 eventlet(ConcurrentModeEnum.EVENTLET) 4 asyncio(ConcurrentModeEnum.ASYNC) 5单线程(ConcurrentModeEnum.SINGLE_THREAD)
    '''
    concurrent_mode = ConcurrentModeEnum.THREADING
    concurrent_num = 50  # 并发数量，值得是线程/协程数量
    specify_concurrent_pool = None  # 使用指定的线程池（协程池），可以多个消费者共使用一个线程池，不为None时候。threads_num失效，具体看文档
    specify_async_loop = None  # 指定的async的loop循环，设置并发模式为async才能起作用。
    qps: float = 0  # 指定1秒内的函数执行次数，例如可以是小数0.01代表每100秒执行一次，也可以是50代表1秒执行50次.为0则不控频。
    is_using_distributed_frequency_control = False  # 是否使用分布式空频（依赖redis统计消费者数量，然后频率平分），默认只对当前实例化的消费者空频有效。

    max_retry_times = 3  # 最大自动重试次数，当函数发生错误，立即自动重试运行n次，对一些特殊不稳定情况会有效果。

    function_timeout = 0  # 超时秒数，函数运行超过这个时间，则自动杀死函数。为0是不限制。设置后代码性能会变差，非必要不要轻易设置。


    log_level = 10  # 框架的日志级别。logging.DEBUG(10)  logging.DEBUG(10) logging.INFO(20) logging.WARNING(30) logging.ERROR(40) logging.CRITICAL(50)
    logger_prefix = ''  # 日志前缀，可使不同的消费者生成不同的日志前缀
    create_logger_file = True  # 是否创建文件日志，文件日志的文件夹位置由 nb_log_config 中的 LOG_PATH 决定
    is_show_message_get_from_broker = False  # 从中间件取出消息时候时候打印显示出来
    is_print_detail_exception = True  # 是否打印详细的堆栈错误。为0则打印简略的错误占用控制台屏幕行数少。

    msg_expire_senconds = 0  # 消息过期时间，为0永不过期，为10则代表，10秒之前发布的任务如果现在才轮到消费则丢弃任务。

    is_send_consumer_hearbeat_to_redis = False  # 是否将发布者的心跳发送到redis，有些功能的实现需要统计活跃消费者。因为有的中间件不是真mq。

    do_task_filtering = False  # 是否执行基于函数参数的任务过滤
    '''
    task_filtering_expire_seconds是任务过滤的失效期，为0则永久性过滤任务。例如设置过滤过期时间是1800秒 ，
    30分钟前发布过1 + 2 的任务，现在仍然执行，
    如果是30分钟以内发布过这个任务，则不执行1 + 2，现在把这个逻辑集成到框架，一般用于接口价格缓存。'''
    task_filtering_expire_seconds = 0

    function_result_status_persistance_conf = FunctionResultStatusPersistanceConfig(False, False, 7 * 24 * 3600)  # 配置。是否保存函数的入参，运行结果和运行状态到mongodb。

    is_using_rpc_mode = False  # 是否使用rpc模式，可以在发布端获取消费端的结果回调，但消耗一定性能，使用async_result.result时候会等待阻塞住当前线程。。

    is_do_not_run_by_specify_time_effect = False  # 是否使不运行的时间段生效
    do_not_run_by_specify_time = ('10:00:00', '22:00:00')  # 不运行的时间段

    schedule_tasks_on_main_thread = False  # 直接在主线程调度任务，意味着不能直接在当前主线程同时开启两个消费者。fun.consume()就阻塞了，这之后的代码不会运行

    broker_kind: int = None  # 中间件种类，支持30种消息队列。 入参见 BrokerEnum枚举类的属性。例如 BrokerEnum.REDIS

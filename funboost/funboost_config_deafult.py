# -*- coding: utf-8 -*-

from pathlib import Path
import pytz
from funboost.constant import BrokerEnum, ConcurrentModeEnum
from funboost.core.function_result_status_config import FunctionResultStatusPersistanceConfig
from funboost.utils.simple_data_class import DataClassBase

'''
此文件是第一次运行框架自动生成刀项目根目录的，不需要用由户手动创建。
此文件里面可以写任意python代码。例如 中间件 帐号 密码自己完全可以从apola配置中心获取或者从环境变量获取。
'''

'''
你项目根目录下自动生成的 funboost_config.py 文件中修改配置，会被自动读取到。
用户不要动修改框架的源码 funboost/funboost_config_deafult.py 中的代码，此模块的变量会自动被 funboost_config.py 覆盖。

框架使用文档是 https://funboost.readthedocs.io/zh_CN/latest/
'''


class BrokerConnConfig(DataClassBase):
    """
    中间件连接配置
    此文件按需修改，例如你使用redis中间件作为消息队列，可以不用管rabbitmq mongodb kafka啥的配置。
    但有3个功能例外，如果你需要使用rpc模式或者分布式控频或者任务过滤功能，无论设置使用何种消息队列中间件都需要把redis连接配置好，
    如果@boost装饰器设置is_using_rpc_mode为True或者 is_using_distributed_frequency_control为True或do_task_filtering=True则需要把redis连接配置好，默认是False不强迫用户安装redis。
    """

    MONGO_CONNECT_URL = f'mongodb://127.0.0.1:27017'  # 如果有密码连接 'mongodb://myUserAdmin:8mwTdy1klnSYepNo@192.168.199.202:27016/'   authSource 指定鉴权db，MONGO_CONNECT_URL = 'mongodb://root:123456@192.168.64.151:27017?authSource=admin'

    RABBITMQ_USER = 'rabbitmq_user'
    RABBITMQ_PASS = 'rabbitmq_pass'
    RABBITMQ_HOST = '127.0.0.1'
    RABBITMQ_PORT = 5672
    RABBITMQ_VIRTUAL_HOST = ''  # my_host # 这个是rabbitmq的虚拟子host用户自己创建的，如果你想直接用rabbitmq的根host而不是使用虚拟子host，这里写 空字符串 即可。
    RABBITMQ_URL = f'amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{RABBITMQ_VIRTUAL_HOST}'

    REDIS_HOST = '127.0.0.1'
    REDIS_USERNAME = ''
    REDIS_PASSWORD = ''
    REDIS_PORT = 6379
    REDIS_DB = 7  # redis消息队列所在db，请不要在这个db放太多其他键值对，框架里面有的功能会scan扫描unacked的键名，使用单独的db。
    REDIS_DB_FILTER_AND_RPC_RESULT = 8  # 如果函数做任务参数过滤 或者使用rpc获取结果，使用这个db，因为这个db的键值对多，和redis消息队列db分开
    REDIS_URL = f'redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

    NSQD_TCP_ADDRESSES = ['127.0.0.1:4150']
    NSQD_HTTP_CLIENT_HOST = '127.0.0.1'
    NSQD_HTTP_CLIENT_PORT = 4151

    KAFKA_BOOTSTRAP_SERVERS = ['127.0.0.1:9092']

    SQLACHEMY_ENGINE_URL = 'sqlite:////sqlachemy_queues/queues.db'

    # 如果broker_kind 使用 peewee 中间件模式会使用mysql配置
    MYSQL_HOST = '127.0.0.1'
    MYSQL_PORT = 3306
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = '123456'
    MYSQL_DATABASE = 'testdb6'

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

    KOMBU_URL = 'redis://127.0.0.1:6379/9'  # 这个就是celery依赖包kombu使用的消息队列格式，所以funboost支持一切celery支持的消息队列种类。
    # KOMBU_URL =  'sqla+sqlite:////dssf_kombu_sqlite.sqlite'  # 4个//// 代表磁盘根目录下生成一个文件。推荐绝对路径。3个///是相对路径。

    CELERY_BROKER_URL = 'redis://127.0.0.1:6379/12'  # 使用celery作为中间件。funboost新增支持celery框架来运行函数
    CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/13'  # celery结果存放，可以为None

    DRAMATIQ_URL = RABBITMQ_URL

    PULSAR_URL = 'pulsar://192.168.70.128:6650'


class FunboostCommonConfig(DataClassBase):
    """
    funboost运行的其它全局默认配置
    """
    # nb_log包的第几个日志模板，内置了7个模板，可以在你当前项目根目录下的nb_log_config.py文件扩展模板。
    NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER = 11  # 7是简短的不可跳转，5是可点击跳转的，11是可显示ip 进程 线程的模板。
    FSDF_DEVELOP_LOG_LEVEL = 50  # 作者开发时候的调试代码的日志，仅供我自己用，所以日志级别跳到最高，用户不需要管。

    TIMEZONE = 'Asia/Shanghai'


class BoostDecoratorDefaultParams(DataClassBase):
    """
     @boost装饰器的默认全局配置

    BoostDecoratorDefaultParams是@boost装饰器默认的全局入参。如果boost没有亲自指定某个入参，就自动使用这里的配置。
    这里的值不用配置，在boost装饰器中可以为每个消费者指定不同的入参，除非你嫌弃每个 boost 装饰器相同入参太多了，那么可以设置这里的全局默认值。

    例如用户不想每次在boost装饰器指定broker_kind为哪种消息队列，可以设置broker_kind为用户自己希望的默认消息队列类型

    boost入参可以ide跳转到boost函数的docstring查看
    boost入参也可以看文档3.3章节  https://funboost.readthedocs.io/zh/latest/articles/c3.html

    BoostDecoratorDefaultParams这个类的属性名字和boost装饰器的入参名字一模一样，只有 queue_name 必须每个装饰器是不同的名字，不能作为全局的。
    所以boost装饰器只有一个是必传参数。
    """

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

    function_result_status_persistance_conf = FunctionResultStatusPersistanceConfig(False, False, 7 * 24 * 3600)
    user_custom_record_process_info_func = None

    is_using_rpc_mode = False
    is_support_remote_kill_task = False

    is_do_not_run_by_specify_time_effect = False
    do_not_run_by_specify_time = ('10:00:00', '22:00:00')

    schedule_tasks_on_main_thread = False

    broker_exclusive_config = {}

    broker_kind: int = BrokerEnum.PERSISTQUEUE  # 中间件选型见3.1章节 https://funboost.readthedocs.io/zh/latest/articles/c3.html

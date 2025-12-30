# funboost 项目代码文件大全 

### 代码文件: funboost\.editorconfig
```python
root = true

[*]
max_line_length = 400
```

### 代码文件: funboost\constant.py
```python
# coding= utf-8



class BrokerEnum:
    """
    在funboost中万物皆可为消息队列broker,funboost内置了所有 知名的正经经典消息队列作为broker,
    也支持了基于 内存 各种数据库 文件系统 tcp/udp/http这些socket 模拟作为broker.
    funboost也内置支持了各种python三方包和消费框架作为broker,例如 sqlachemy kombu celery rq dramtiq huey nameko 等等

    用户也可以按照文档4.21章节,轻松扩展任何物质概念作为funboost的broker.
    """
    
    # funboost框架能轻松兼容消息队列各种工作模式, 拉模式/推模式/轮询模式，单条获取 批量获取
    """
    funboost 的 consumer的 _dispatch_task 非常灵活，用户实现把从消息队列取出的消息通过_submit_task方法
    丢到并发池，他不是强制用户重写实现怎么取一条消息，例如强制你实现一个 _get_one_message的法，
    那就不灵活和限制扩展任意东西作为broker了，而是用户完全自己来写灵活代码。
    所以无论获取消息是 拉模式 还是推模式 还是轮询模式，是单条获取 还是多条批量获取，
    不管你的新中间件和rabbitmq api用法差别有多么巨大，都能轻松扩展任意东西作为funboost的中间件。 
    所以你能看到funboost源码中能轻松实现任物质概念作为funboost的broker。
    """


    EMPTY = 'EMPTY'  # 空的实现，需要搭配 boost入参的 consumer_override_cls 和 publisher_override_cls使用，或者被继承。

    RABBITMQ_AMQPSTORM = 'RABBITMQ_AMQPSTORM'  # 使用 amqpstorm 包操作rabbitmq  作为 分布式消息队列，支持消费确认.强烈推荐这个作为funboost中间件。
    RABBITMQ = RABBITMQ_AMQPSTORM

    RABBITMQ_RABBITPY = 'RABBITMQ_RABBITPY'  # 使用 rabbitpy 包操作rabbitmq  作为 分布式消息队列，支持消费确认，不建议使用

    """
    以下是各种redis数据结构和各种方式来实现作为消息队列的,redis简直被作者玩出花来了.
    因为redis本身是缓存数据库,不是消息队列,redis没有实现经典AMQP协议,所以redis是模拟消息队列不是真消息队列.
    例如要实现消费确认,随意重启但消息万无一失,你搞个简单的 redis.blpop 弹出删除消息,那就压根不行.重启就丢失了,但消息可能还没开始运行或者正在运行中.
    
    redis做ack挑战难点不是怎么实现确认消费本身,而是何时应该把关闭或宕机进程的消费者的待确认消费的孤儿消息重回队列.  
    在 Redis 上实现 ACK 的真正难点，根本不在于“确认”这个动作本身，而在于建立一套可靠的、能够准确判断“何时可以安全地及时地进行任务恢复”的分布式故障检测机制。
    所以你以为只要使用 brpoplpush 或者 REDIS_STREAM 就能自动轻易解决ack问题,那就太天真了,因为redis服务端不能像rabbitmq服务端那样天生自带自动重回宕机消费者的消息机制,需要你在redis客户端来维护实现这套机制.
    """
    REDIS = 'REDIS'  # 使用 redis 的 list结构，brpop 作为分布式消息队列。随意重启和关闭会丢失大量消息，不支持消费确认。注重性能不在乎丢失消息可以选这个redis方案。
    REDIS_ACK_ABLE = 'REDIS_ACK_ABLE'  # 基于redis的 list + 临时unack的set队列，采用了 lua脚本操持了取任务和加到pengding为原子性，,基于进程心跳消失判断消息是否为掉线进程的，随意重启和掉线不会丢失任务。
    REIDS_ACK_USING_TIMEOUT = 'reids_ack_using_timeout'  # 基于redis的 list + 临时unack的set队列，使用超时多少秒没确认消费就自动重回队列，请注意 ack_timeout的设置值和函数耗时大小，否则会发生反复重回队列的后果,boost可以设置ack超时，broker_exclusive_config={'ack_timeout': 1800}.缺点是无法区分执行太慢还是真宕机
    REDIS_PRIORITY = 'REDIS_PRIORITY'  # # 基于redis的多 list + 临时unack的set队列，blpop监听多个key，和rabbitmq的x-max-priority属性一样，支持任务优先级。看文档4.29优先级队列说明。
    REDIS_STREAM = 'REDIS_STREAM'  # 基于redis 5.0 版本以后，使用 stream 数据结构作为分布式消息队列，支持消费确认和持久化和分组消费，是redis官方推荐的消息队列形式，比list结构更适合。
    RedisBrpopLpush = 'RedisBrpopLpush'  # 基于redis的list结构但是采用 brpoplpush 双队列形式，和 redis_ack_able的实现差不多，实现上采用了原生命令就不需要lua脚本来实现取出和加入unack了。
    REDIS_PUBSUB = 'REDIS_PUBSUB'  # 基于redis 发布订阅的，发布一个消息多个消费者都能收到同一条消息，但不支持持久化

    MEMORY_QUEUE = 'MEMORY_QUEUE'  # 使用python queue.Queue实现的基于当前python进程的消息队列，不支持跨进程 跨脚本 跨机器共享任务，不支持持久化，适合一次性短期简单任务。
    LOCAL_PYTHON_QUEUE = MEMORY_QUEUE  # 别名，python本地queue就是基于python自带的语言的queue.Queue，消息存在python程序的内存中，不支持重启断点接续。

    RABBITMQ_PIKA = 'RABBITMQ_PIKA'  # 使用pika包操作rabbitmq  作为 分布式消息队列。，不建议使用

    MONGOMQ = 'MONGOMQ'  # 使用mongo的表中的行模拟的 作为分布式消息队列，支持消费确认。

    SQLITE_QUEUE = 'sqlite3'  # 使用基于sqlite3模拟消息队列，支持消费确认和持久化，但不支持跨机器共享任务，可以基于本机单机跨脚本和跨进程共享任务，好处是不需要安装中间件。
    PERSISTQUEUE = SQLITE_QUEUE  # PERSISTQUEUE的别名

    NSQ = 'NSQ'  # 基于nsq作为分布式消息队列，支持消费确认。

    KAFKA = 'KAFKA'  # 基于kafka作为分布式消息队列，如果随意重启会丢失消息，建议使用BrokerEnum.CONFLUENT_KAFKA。

    """基于confluent-kafka包，包的性能比kafka-python提升10倍。同时应对反复随意重启部署消费代码的场景，此消费者实现至少消费一次，第8种BrokerEnum.KAFKA是最多消费一次。"""
    KAFKA_CONFLUENT = 'KAFKA_CONFLUENT'
    CONFLUENT_KAFKA = KAFKA_CONFLUENT

    KAFKA_CONFLUENT_SASlPlAIN = 'KAFKA_CONFLUENT_SASlPlAIN'  # 可以设置账号密码的kafka

    SQLACHEMY = 'SQLACHEMY'  # 基于SQLACHEMY 的连接作为分布式消息队列中间件支持持久化和消费确认。支持mysql oracle sqlserver等5种数据库。

    ROCKETMQ = 'ROCKETMQ'  # 基于 rocketmq 作为分布式消息队列，这个中间件必须在linux下运行，win不支持。

    ZEROMQ = 'ZEROMQ'  # 基于zeromq作为分布式消息队列，不需要安装中间件，可以支持跨机器但不支持持久化。


    """
    kombu 和 celery 都是 funboost中的神级别broker_kind。
    使得funboost以逸待劳，支持kombu的所有现有和未来的消息队列。
    通过直接支持 kombu，funboost 相当于一瞬间就继承了 `kombu` 支持的所有现有和未来的消息队列能力。无论 kombu 社区未来增加了对哪种新的云消息服务（如 Google
    Pub/Sub、Azure Service Bus）或小众 MQ 的支持，funboost 无需修改自身代码，就能自动获得这种能力。这
    是一种“以逸待劳”的策略，极大地扩展了 funboost 的适用范围。

    kombu 包可以作为funboost的broker，这个包也是celery的中间件依赖包，这个包可以操作10种中间件(例如rabbitmq redis)，但没包括分布式函数调度框架的kafka nsq zeromq 等。
    同时 kombu 包的性能非常差，可以用原生redis的lpush和kombu的publish测试发布，使用brpop 和 kombu 的 drain_events测试消费，对比差距相差了5到10倍。
    由于性能差，除非是分布式函数调度框架没实现的中间件才选kombu方式(例如kombu支持亚马逊队列  qpid pyro 队列)，否则强烈建议使用此框架的操作中间件方式而不是使用kombu。
    """
    KOMBU = 'KOMBU'

    """ 基于emq作为中间件的。这个和上面的中间件有很大不同，服务端不存储消息。所以不能先发布几十万个消息，然后再启动消费。mqtt优点是web前后端能交互，
    前端不能操作redis rabbitmq kafka，但很方便操作mqtt。这种使用场景是高实时的互联网接口。
    """
    MQTT = 'MQTT'

    HTTPSQS = 'HTTPSQS'  # httpsqs中间件实现的，基于http协议操作，dcoker安装此中间件简单。

    PULSAR = 'PULSAR'  # 最有潜力的下一代分布式消息系统。5年后会同时取代rabbitmq和kafka。

    UDP = 'UDP'  # 基于socket udp 实现的，需要先启动消费端再启动发布，支持分布式但不支持持久化，好处是不需要安装消息队列中间件软件。

    TCP = 'TCP'  # 基于socket tcp 实现的，需要先启动消费端再启动发布，支持分布式但不支持持久化，好处是不需要安装消息队列中间件软件。

    HTTP = 'HTTP'  # 基于http实现的，发布使用的urllib3，消费服务端使用的aiohttp.server实现的，支持分布式但不支持持久化，好处是不需要安装消息队列中间件软件。

    NATS = 'NATS'  # 高性能中间件nats,中间件服务端性能很好,。

    TXT_FILE = 'TXT_FILE'  # 磁盘txt文件作为消息队列，支持单机持久化，不支持多机分布式。不建议这个，用sqlite。

    PEEWEE = 'PEEWEE'  # peewee包操作mysql，使用表模拟消息队列

    CELERY = 'CELERY'  # funboost支持celery框架来发布和消费任务，由celery框架来调度执行任务，但是写法简单远远暴击用户亲自使用celery的麻烦程度，
    # 用户永无无需关心和操作Celery对象实例,无需关心celery的task_routes和includes配置,funboost来自动化设置这些celery配置。
    # funboost将Celery本身纳入了自己的Broker体系。能“吞下”另一个大型框架，简直太妙了。本身就证明了funboost架构的包容性和精妙性和复杂性。

    DRAMATIQ = 'DRAMATIQ'  # funboost使用 dramatiq 框架作为消息队列，dramatiq类似celery也是任务队列框架。用户使用funboost api来操作dramatiq核心调度。

    HUEY = 'HUEY'  # huey任务队列框架作为funboost调度核心

    RQ = 'RQ'  # rq任务队列框架作为funboost调度核心

    NAMEKO = 'NAMEKO'  # funboost支持python微服务框架nameko，用户无需掌握nameko api语法，就玩转python nameko微服务


class ConcurrentModeEnum:
    THREADING = 'threading'  # 线程方式运行，兼容支持 async def 的异步函数。
    GEVENT = 'gevent'
    EVENTLET = 'eventlet'
    ASYNC = 'async'  # asyncio并发，适用于async def定义的函数。
    SINGLE_THREAD = 'single_thread'  # 如果你不想并发，不想预先从消息队列中间件拉取消息到python程序的内存queue队列缓冲中，那么就适合使用此并发模式。
    SOLO = SINGLE_THREAD


# is_fsdf_remote_run = 0

class FunctionKind:
    CLASS_METHOD = 'CLASS_METHOD'
    INSTANCE_METHOD = 'INSTANCE_METHOD'
    STATIC_METHOD = 'STATIC_METHOD'
    COMMON_FUNCTION = 'COMMON_FUNCTION'


class ConstStrForClassMethod:
    FIRST_PARAM_NAME = 'first_param_name'
    CLS_NAME = 'cls_name'
    OBJ_INIT_PARAMS = 'obj_init_params'
    CLS_MODULE = 'cls_module'
    CLS_FILE = 'cls_file'


class RedisKeys:

    REDIS_KEY_PAUSE_FLAG  = 'funboost_pause_flag' 
    REDIS_KEY_STOP_FLAG = 'funboost_stop_flag'
    QUEUE__MSG_COUNT_MAP = 'funboost_queue__msg_count_map'
    FUNBOOST_QUEUE__CONSUMER_PARAMS= 'funboost_queue__consumer_parmas'
    FUNBOOST_QUEUE__RUN_COUNT_MAP = 'funboost_queue__run_count_map'
    FUNBOOST_QUEUE__RUN_FAIL_COUNT_MAP = 'funboost_queue__run_fail_count_map'
    FUNBOOST_ALL_QUEUE_NAMES = 'funboost_all_queue_names'
    FUNBOOST_ALL_IPS = 'funboost_all_ips'
    FUNBOOST_LAST_GET_QUEUE_PARAMS_AND_ACTIVE_CONSUMERS_AND_REPORT__UUID_TS = 'funboost_last_get_queue_params_and_active_consumers_and_report__uuid_ts'


    FUNBOOST_HEARTBEAT_QUEUE__DICT_PREFIX = 'funboost_hearbeat_queue__dict:'
    FUNBOOST_HEARTBEAT_SERVER__DICT_PREFIX = 'funboost_hearbeat_server__dict:'


    @staticmethod
    def gen_funboost_apscheduler_redis_lock_key_by_queue_name(queue_name):
        return f'funboost.BackgroundSchedulerProcessJobsWithinRedisLock:{queue_name}'

    @staticmethod
    def gen_funboost_hearbeat_queue__dict_key_by_queue_name(queue_name):
        return f'{RedisKeys.FUNBOOST_HEARTBEAT_QUEUE__DICT_PREFIX}{queue_name}'

    @staticmethod
    def gen_funboost_hearbeat_server__dict_key_by_ip(ip):
        return f'{RedisKeys.FUNBOOST_HEARTBEAT_SERVER__DICT_PREFIX}{ip}'
    
    @staticmethod
    def gen_funboost_queue_time_series_data_key_by_queue_name(queue_name):
        return f'funboost_queue_time_series_data:{queue_name}'
    
    @staticmethod
    def gen_funboost_redis_apscheduler_jobs_key_by_queue_name(queue_name):
        jobs_key=f'funboost.apscheduler.jobs:{queue_name}'
        return jobs_key
    
    @staticmethod
    def gen_funboost_redis_apscheduler_run_times_key_by_queue_name(queue_name):
        run_times_key=f'funboost.apscheduler.run_times:{queue_name}'
        return run_times_key

```

### 代码文件: funboost\funboost_config_deafult.py
```python
# -*- coding: utf-8 -*-
import logging
from pathlib import Path
import pytz
from funboost.constant import BrokerEnum, ConcurrentModeEnum
from funboost.core.func_params_model import FunctionResultStatusPersistanceConfig
from funboost.utils.simple_data_class import DataClassBase
from nb_log import nb_log_config_default

'''
funboost_config.py 文件是第一次运行框架自动生成到你的项目根目录的，不需要用由户手动创建。
此文件里面可以写任意python代码。例如 中间件 帐号 密码自己完全可以从apola配置中心获取或者从环境变量获取。
'''

'''
你项目根目录下自动生成的 funboost_config.py 文件中修改配置，会被自动读取到。
用户不要动修改框架的源码 funboost/funboost_config_deafult.py 中的代码，此模块的变量会自动被 funboost_config.py 覆盖。
funboost/funboost_config_deafult.py配置覆盖逻辑可看funboost/set_frame_config.py中的代码.

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
    REDIS_DB = 7  # redis消息队列所在db，请不要在这个db放太多其他键值对，以及方便你自己可视化查看你的redis db，框架里面有的功能会scan扫描unacked的键名，使用单独的db。
    REDIS_DB_FILTER_AND_RPC_RESULT = 8  # 如果函数做任务参数过滤 或者使用rpc获取结果，使用这个db，因为这个db的键值对多，和redis消息队列db分开
    REDIS_SSL = False # 是否使用ssl加密,默认是False
    REDIS_URL = f'{"rediss" if REDIS_SSL else "redis"}://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

    NSQD_TCP_ADDRESSES = ['127.0.0.1:4150']
    NSQD_HTTP_CLIENT_HOST = '127.0.0.1'
    NSQD_HTTP_CLIENT_PORT = 4151

    KAFKA_BOOTSTRAP_SERVERS = ['127.0.0.1:9092']
    KFFKA_SASL_CONFIG = {
        "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
        "sasl_plain_username": "",
        "sasl_plain_password": "",
        "sasl_mechanism": "SCRAM-SHA-256",
        "security_protocol": "SASL_PLAINTEXT",
    }

    SQLACHEMY_ENGINE_URL = 'sqlite:////sqlachemy_queues/queues.db'

    # 如果broker_kind 使用 peewee 中间件模式会使用mysql配置
    MYSQL_HOST = '127.0.0.1'
    MYSQL_PORT = 3306
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = '123456'
    MYSQL_DATABASE = 'testdb6'

    # persist_quque中间件时候采用本机sqlite的方式，数据库文件生成的位置,如果linux账号在根目录没权限建文件夹，可以换文件夹。
    SQLLITE_QUEUES_PATH = '/sqllite_queues'

    TXT_FILE_PATH = Path(__file__).parent / 'txt_queues'  # 不建议使用这个txt模拟消息队列中间件，本地持久化优先选择 PERSIST_QUQUE 中间件。

    ROCKETMQ_NAMESRV_ADDR = '192.168.199.202:9876'

    MQTT_HOST = '127.0.0.1'
    MQTT_TCP_PORT = 1883

    HTTPSQS_HOST = '127.0.0.1'
    HTTPSQS_PORT = 1218
    HTTPSQS_AUTH = '123456'

    NATS_URL = 'nats://192.168.6.134:4222'

    KOMBU_URL = 'redis://127.0.0.1:6379/9'  # 这个就是celery依赖包kombu使用的消息队列格式，所以funboost支持一切celery支持的消息队列种类。
    # KOMBU_URL =  'sqla+sqlite:////dssf_kombu_sqlite.sqlite'  # 4个//// 代表磁盘根目录下生成一个文件。推荐绝对路径。3个///是相对路径。

    CELERY_BROKER_URL = 'redis://127.0.0.1:6379/12'  # 使用celery作为中间件。funboost新增支持celery框架来运行函数,url内容就是celery的broker形式.
    CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/13'  # celery结果存放，可以为None

    DRAMATIQ_URL = RABBITMQ_URL

    PULSAR_URL = 'pulsar://192.168.70.128:6650'


class FunboostCommonConfig(DataClassBase):
    # nb_log包的第几个日志模板，内置了7个模板，可以在你当前项目根目录下的nb_log_config.py文件扩展模板。
    # NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER = 11  # 7是简短的不可跳转，5是可点击跳转的，11是可显示ip 进程 线程的模板,也可以亲自设置日志模板不传递数字。
    NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER = logging.Formatter(
        f'%(asctime)s-({nb_log_config_default.computer_ip},{nb_log_config_default.computer_name})-[p%(process)d_t%(thread)d] - %(name)s - "%(filename)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(task_id)s - %(message)s',
        "%Y-%m-%d %H:%M:%S",)   # 这个是带task_id的日志模板,日志可以显示task_id,方便用户串联起来排查某一个任务消息的所有日志.

    TIMEZONE = 'Asia/Shanghai'  # 时区

    # 以下配置是修改funboost的一些命名空间和启动时候的日志级别,新手不熟练就别去屏蔽日志了
    SHOW_HOW_FUNBOOST_CONFIG_SETTINGS = True  # 如果你单纯想屏蔽 "分布式函数调度框架会自动导入funboost_config模块当第一次运行脚本时候，函数调度框架会在你的python当前项目的根目录下 ...... "  这句话,
    FUNBOOST_PROMPT_LOG_LEVEL = logging.DEBUG  # funboost启动时候的相关提示语,用户可以设置这个命名空间的日志级别来调整
    KEEPALIVETIMETHREAD_LOG_LEVEL = logging.DEBUG  # funboost的作者发明的可缩小自适应线程池,用户对可变线程池的线程创建和销毁线程完全无兴趣,可以提高日志级别.

```

### 代码文件: funboost\README.md
```python
用法见README.md和test_frame的例子。
```

### 代码文件: funboost\set_frame_config.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/4/11 0011 0:56
"""

使用覆盖的方式，做配置。
"""
import sys
import time
import importlib
import json
from pathlib import Path
from shutil import copyfile

from funboost.core.funboost_config_getter import _try_get_user_funboost_common_config
from funboost.core.loggers import flogger, get_funboost_file_logger, logger_prompt
from nb_log import nb_print, stderr_write, stdout_write
from nb_log.monkey_print import is_main_process, only_print_on_main_process
from funboost import funboost_config_deafult


def show_funboost_flag():
    funboost_flag_str = '''


    FFFFFFFFFFFFFFFFFFFFFF     UUUUUUUU     UUUUUUUU     NNNNNNNN        NNNNNNNN     BBBBBBBBBBBBBBBBB             OOOOOOOOO               OOOOOOOOO             SSSSSSSSSSSSSSS      TTTTTTTTTTTTTTTTTTTTTTT
    F::::::::::::::::::::F     U::::::U     U::::::U     N:::::::N       N::::::N     B::::::::::::::::B          OO:::::::::OO           OO:::::::::OO         SS:::::::::::::::S     T:::::::::::::::::::::T
    F::::::::::::::::::::F     U::::::U     U::::::U     N::::::::N      N::::::N     B::::::BBBBBB:::::B       OO:::::::::::::OO       OO:::::::::::::OO      S:::::SSSSSS::::::S     T:::::::::::::::::::::T
    FF::::::FFFFFFFFF::::F     UU:::::U     U:::::UU     N:::::::::N     N::::::N     BB:::::B     B:::::B     O:::::::OOO:::::::O     O:::::::OOO:::::::O     S:::::S     SSSSSSS     T:::::TT:::::::TT:::::T
      F:::::F       FFFFFF      U:::::U     U:::::U      N::::::::::N    N::::::N       B::::B     B:::::B     O::::::O   O::::::O     O::::::O   O::::::O     S:::::S                 TTTTTT  T:::::T  TTTTTT
      F:::::F                   U:::::D     D:::::U      N:::::::::::N   N::::::N       B::::B     B:::::B     O:::::O     O:::::O     O:::::O     O:::::O     S:::::S                         T:::::T        
      F::::::FFFFFFFFFF         U:::::D     D:::::U      N:::::::N::::N  N::::::N       B::::BBBBBB:::::B      O:::::O     O:::::O     O:::::O     O:::::O      S::::SSSS                      T:::::T        
      F:::::::::::::::F         U:::::D     D:::::U      N::::::N N::::N N::::::N       B:::::::::::::BB       O:::::O     O:::::O     O:::::O     O:::::O       SS::::::SSSSS                 T:::::T        
      F:::::::::::::::F         U:::::D     D:::::U      N::::::N  N::::N:::::::N       B::::BBBBBB:::::B      O:::::O     O:::::O     O:::::O     O:::::O         SSS::::::::SS               T:::::T        
      F::::::FFFFFFFFFF         U:::::D     D:::::U      N::::::N   N:::::::::::N       B::::B     B:::::B     O:::::O     O:::::O     O:::::O     O:::::O            SSSSSS::::S              T:::::T        
      F:::::F                   U:::::D     D:::::U      N::::::N    N::::::::::N       B::::B     B:::::B     O:::::O     O:::::O     O:::::O     O:::::O                 S:::::S             T:::::T        
      F:::::F                   U::::::U   U::::::U      N::::::N     N:::::::::N       B::::B     B:::::B     O::::::O   O::::::O     O::::::O   O::::::O                 S:::::S             T:::::T        
    FF:::::::FF                 U:::::::UUU:::::::U      N::::::N      N::::::::N     BB:::::BBBBBB::::::B     O:::::::OOO:::::::O     O:::::::OOO:::::::O     SSSSSSS     S:::::S           TT:::::::TT      
    F::::::::FF                  UU:::::::::::::UU       N::::::N       N:::::::N     B:::::::::::::::::B       OO:::::::::::::OO       OO:::::::::::::OO      S::::::SSSSSS:::::S           T:::::::::T      
    F::::::::FF                    UU:::::::::UU         N::::::N        N::::::N     B::::::::::::::::B          OO:::::::::OO           OO:::::::::OO        S:::::::::::::::SS            T:::::::::T      
    FFFFFFFFFFF                      UUUUUUUUU           NNNNNNNN         NNNNNNN     BBBBBBBBBBBBBBBBB             OOOOOOOOO               OOOOOOOOO           SSSSSSSSSSSSSSS              TTTTTTTTTTT      


    '''

    funboost_flag_str2 = r'''

          ___                  ___                    ___                                           ___                    ___                    ___                          
         /  /\                /__/\                  /__/\                  _____                  /  /\                  /  /\                  /  /\                   ___   
        /  /:/_               \  \:\                 \  \:\                /  /::\                /  /::\                /  /::\                /  /:/_                 /  /\  
       /  /:/ /\               \  \:\                 \  \:\              /  /:/\:\              /  /:/\:\              /  /:/\:\              /  /:/ /\               /  /:/  
      /  /:/ /:/           ___  \  \:\            _____\__\:\            /  /:/~/::\            /  /:/  \:\            /  /:/  \:\            /  /:/ /::\             /  /:/   
     /__/:/ /:/           /__/\  \__\:\          /__/::::::::\          /__/:/ /:/\:|          /__/:/ \__\:\          /__/:/ \__\:\          /__/:/ /:/\:\           /  /::\   
     \  \:\/:/            \  \:\ /  /:/          \  \:\~~\~~\/          \  \:\/:/~/:/          \  \:\ /  /:/          \  \:\ /  /:/          \  \:\/:/~/:/          /__/:/\:\  
      \  \::/              \  \:\  /:/            \  \:\  ~~~            \  \::/ /:/            \  \:\  /:/            \  \:\  /:/            \  \::/ /:/           \__\/  \:\ 
       \  \:\               \  \:\/:/              \  \:\                 \  \:\/:/              \  \:\/:/              \  \:\/:/              \__\/ /:/                 \  \:\
        \  \:\               \  \::/                \  \:\                 \  \::/                \  \::/                \  \::/                 /__/:/                   \__\/
         \__\/                \__\/                  \__\/                  \__\/                  \__\/                  \__\/                  \__\/                         



    '''

    logger_prompt.debug('\033[0m' + funboost_flag_str2 + '\033[0m')

    logger_prompt.debug(f'''分布式函数调度框架funboost文档地址：  \033[0m https://funboost.readthedocs.io/zh-cn/latest/ \033[0m ''')


show_funboost_flag()


def dict2json(dictx: dict, indent=4):
    dict_new = {}
    for k, v in dictx.items():
        # only_print_on_main_process(f'{k} :  {v}')
        if isinstance(v, (bool, tuple, dict, float, int)):
            dict_new[k] = v
        else:
            dict_new[k] = str(v)
    return json.dumps(dict_new, ensure_ascii=False, indent=indent)


def show_frame_config():
    if is_main_process():
        logger_prompt.debug('显示当前的项目中间件配置参数')
        # for var_name in dir(funboost_config_deafult):
        #     if var_name.isupper():
        #         var_value = getattr(funboost_config_deafult, var_name)
        #         if var_name == 'MONGO_CONNECT_URL':
        #             if re.match('mongodb://.*?:.*?@.*?/.*', var_value):
        #                 mongo_pass = re.search('mongodb://.*?:(.*?)@', var_value).group(1)
        #                 mongo_pass_encryption = f'{"*" * (len(mongo_pass) - 2)}{mongo_pass[-1]}' if len(
        #                     mongo_pass) > 3 else mongo_pass
        #                 var_value_encryption = re.sub(r':(\w+)@', f':{mongo_pass_encryption}@', var_value)
        #                 only_print_on_main_process(f'{var_name}:             {var_value_encryption}')
        #                 continue
        #         if 'PASS' in var_name and var_value is not None and len(var_value) > 3:  # 对密码打*
        #             only_print_on_main_process(f'{var_name}:                {var_value[0]}{"*" * (len(var_value) - 2)}{var_value[-1]}')
        #         else:
        #             only_print_on_main_process(f'{var_name}:                {var_value}')
        logger_prompt.debug(f'''读取的 BrokerConnConfig 配置是:\n {funboost_config_deafult.BrokerConnConfig().get_pwd_enc_json(indent=4)} ''')

        logger_prompt.debug(f'''读取的 FunboostCommonConfig 配置是:\n  {funboost_config_deafult.FunboostCommonConfig().get_json(indent=4)} ''')

    # only_print_on_main_process(f'读取的 BoostDecoratorDefaultParams 默认 @boost 装饰器入参的默认全局配置是： \n  '
    #                            f'{funboost_config_deafult.BoostDecoratorDefaultParams().get_json()}')


def use_config_form_funboost_config_module():
    """
    自动读取配置。会优先读取启动脚本的目录的funboost_config.py文件。没有则读取项目根目录下的funboost_config.py
    :return:
    """
    current_script_path = sys.path[0].replace('\\', '/')
    project_root_path = sys.path[1].replace('\\', '/')
    inspect_msg = f"""
    分布式函数调度框架会自动导入funboost_config模块
    当第一次运行脚本时候，函数调度框架会在你的python当前项目的根目录下 {project_root_path} 下，创建一个名为 funboost_config.py 的文件。
    自动读取配置，会优先读取启动脚本的所在目录 {current_script_path} 的funboost_config.py文件，
    如果没有 {current_script_path}/funboost_config.py 文件，则读取项目根目录 {project_root_path} 下的funboost_config.py做配置。
    只要 funboost_config.py 在任意 PYTHONPATH 的文件夹下，就能自动读取到。
    在 "{project_root_path}/funboost_config.py:1" 文件中，需要按需重新设置要使用到的中间件的键和值，例如没有使用rabbitmq而是使用redis做中间件，则不需要配置rabbitmq。
    """
    # sys.stdout.write(f'\033[0;33m{time.strftime("%H:%M:%S")}\033[0m  "{__file__}:{sys._getframe().f_lineno}"   \033[0;30;43m{inspect_msg}\033[0m\n')
    # noinspection PyProtectedMember
    if is_main_process() and _try_get_user_funboost_common_config('SHOW_HOW_FUNBOOST_CONFIG_SETTINGS') in (True, None):
        logger_prompt.debug(f'\033[0;93m{time.strftime("%H:%M:%S")}\033[0m  "{__file__}:{sys._getframe().f_lineno}"   \033[0;93;100m{inspect_msg}\033[0m\n')
    try:
        # noinspection PyUnresolvedReferences
        # import funboost_config
        m = importlib.import_module('funboost_config')
        importlib.reload(m)  # 这行是防止用户在导入框架之前，写了 from funboost_config import REDIS_HOST 这种，导致 m.__dict__.items() 不包括所有配置变量了。
        # print(dir(m))
        # nb_print(m.__dict__.items())
        if is_main_process():
            logger_prompt.debug(f'分布式函数调度框架 读取到\n "{m.__file__}:1" 文件里面的变量作为优先配置了\n')
        if not hasattr(m, 'BrokerConnConfig'):
            raise EnvironmentError(f'funboost 30.0版本升级了配置文件，中间件配置写成了类，请删除原来老的funboost_config.py配置文件:\n "{m.__file__}:1"')
        funboost_config_deafult.BrokerConnConfig.update_cls_attribute(**m.BrokerConnConfig().get_dict())
        funboost_config_deafult.FunboostCommonConfig.update_cls_attribute(**m.FunboostCommonConfig().get_dict())
        # funboost_config_deafult.BoostDecoratorDefaultParams.update_cls_attribute(**m.BoostDecoratorDefaultParams().get_dict())
        if hasattr(m, 'BoostDecoratorDefaultParams'):
            raise ValueError('funboost 40.0版本之后，采用 pydantic model BoostParams类或子类入参，不支持 funboost_config.py的 BoostDecoratorDefaultParams 配置,请删除掉 BoostDecoratorDefaultParams 这个配置')


    except ModuleNotFoundError:
        nb_print(
            f'''分布式函数调度框架检测到 你的项目根目录 {project_root_path} 和当前文件夹 {current_script_path}  下没有 funboost_config.py 文件，\n''')
        _auto_creat_config_file_to_project_root_path()
    else:
        show_frame_config()
        # print(getattr(m,'BoostDecoratorDefaultParams')().get_dict())


def _auto_creat_config_file_to_project_root_path():
    """
    在没有使用pycahrm运行代码时候，如果实在cmd 或者 linux 运行， python xx.py，
    请在临时会话窗口设置linux export PYTHONPATH=你的项目根目录 ，winwdos set PYTHONPATH=你的项目根目录
    :return:
    """
    # print(Path(sys.path[1]).as_posix())
    # print((Path(__file__).parent.parent).absolute().as_posix())
    # if Path(sys.path[1]).as_posix() in Path(__file__).parent.parent.absolute().as_posix():
    #     nb_print('不希望在本项目里面创建')
    #     return
    if '/lib/python' in sys.path[1] or r'\lib\python' in sys.path[1] or '.zip' in sys.path[1]:
        raise EnvironmentError(f'''如果是cmd 或者shell启动而不是pycharm 这种ide启动脚本，请先在会话窗口设置临时PYTHONPATH为你的项目路径，
                               windwos cmd 使用 set PYTHONNPATH=你的当前python项目根目录,
                               windows powershell 使用 $env:PYTHONPATH=你的当前python项目根目录,
                               linux 使用 export PYTHONPATH=你的当前你python项目根目录,
                               PYTHONPATH 作用是python的基本常识，请百度一下。
                               需要在会话窗口命令行设置临时的环境变量，而不是修改linux配置文件的方式设置永久环境变量，每个python项目的PYTHONPATH都要不一样，不要在配置文件写死
                               
                               懂PYTHONPATH 的重要性和妙用见： https://github.com/ydf0509/pythonpathdemo
                               ''')
        return  # 当没设置pythonpath时候，也不要在 /lib/python36.zip这样的地方创建配置文件。

    file_name = Path(sys.path[1]) / Path('funboost_config.py')
    copyfile(Path(__file__).absolute().parent / Path('funboost_config_deafult.py'), file_name)
    nb_print(f'在  {Path(sys.path[1])} 目录下自动生成了一个文件， 请刷新文件夹查看或修改 \n "{file_name}:1" 文件')
    # with (file_name).open(mode='w', encoding='utf8') as f:
    #     nb_print(f'在 {file_name} 目录下自动生成了一个文件， 请查看或修改 \n "{file_name}:1" 文件')
    #     f.write(config_file_content)

    file_name = Path(sys.path[1]) / Path('funboost_cli_user.py')
    copyfile(Path(__file__).absolute().parent / Path('core/cli/funboost_cli_user_templ.py'), file_name)


use_config_form_funboost_config_module()

```

### 代码文件: funboost\__init__.py
```python
# noinspection PyUnresolvedReferences
import atexit

import nb_log
# noinspection PyUnresolvedReferences
from nb_log import nb_print

'''
set_frame_config 这行要放在所有导入其他代码之前最好,以便防止其他项目提前 from funboost.funboost_config_deafult import xx ,
如果是 from funboost import funboost_config_deafult,在函数内部使用他的配置就没事,但最后不要让其他模块在 set_frame_config 之前导入.
set_frame_config这个模块的 use_config_form_funboost_config_module() 是核心,把用户的funboost_config.py的配置覆盖到funboost_config_deafult模块了

这段注释说明和使用的用户无关,只和框架开发人员有关.
'''

__version__ = "49.8"

from funboost.set_frame_config import show_frame_config

# noinspection PyUnresolvedReferences
from funboost.utils.dependency_packages_in_pythonpath import add_to_pythonpath  # 这是把 dependency_packages_in_pythonpath 添加到 PYTHONPATH了。
from funboost.utils import monkey_patches

from funboost.core.loggers import get_logger, get_funboost_file_logger, FunboostFileLoggerMixin, FunboostMetaTypeFileLogger, flogger
from funboost.core.func_params_model import (BoosterParams, BoosterParamsComplete, FunctionResultStatusPersistanceConfig,
                                             PriorityConsumingControlConfig, PublisherParams, BoosterParamsComplete)
from funboost.funboost_config_deafult import FunboostCommonConfig, BrokerConnConfig

# from funboost.core.fabric_deploy_helper import fabric_deploy, kill_all_remote_tasks # fabric2还没适配python3.12以上版本，不在这里导入，否则高版本python报错。
from funboost.utils.paramiko_util import ParamikoFolderUploader

from funboost.consumers.base_consumer import (wait_for_possible_has_finish_all_tasks_by_conusmer_list,
                                              FunctionResultStatus, AbstractConsumer)
from funboost.consumers.empty_consumer import EmptyConsumer
from funboost.core.exceptions import ExceptionForRetry, ExceptionForRequeue, ExceptionForPushToDlxqueue
from funboost.core.active_cousumer_info_getter import ActiveCousumerProcessInfoGetter
from funboost.core.msg_result_getter import HasNotAsyncResult, ResultFromMongo
from funboost.publishers.base_publisher import (PriorityConsumingControlConfig,
                                                AbstractPublisher, AsyncResult, AioAsyncResult)
from funboost.publishers.empty_publisher import EmptyPublisher
from funboost.factories.broker_kind__publsiher_consumer_type_map import register_custom_broker
from funboost.factories.publisher_factotry import get_publisher
from funboost.factories.consumer_factory import get_consumer

from funboost.timing_job import fsdf_background_scheduler, timing_publish_deco, funboost_aps_scheduler,ApsJobAdder
from funboost.constant import BrokerEnum, ConcurrentModeEnum

from funboost.core.booster import boost, Booster, BoostersManager
# from funboost.core.get_booster import get_booster, get_or_create_booster, get_boost_params_and_consuming_function
from funboost.core.kill_remote_task import RemoteTaskKiller
from funboost.funboost_config_deafult import BrokerConnConfig, FunboostCommonConfig
from funboost.core.cli.discovery_boosters import BoosterDiscovery

# from funboost.core.exit_signal import set_interrupt_signal_handler
from funboost.core.helper_funs import run_forever

from funboost.utils.ctrl_c_end import ctrl_c_recv
from funboost.utils.redis_manager import RedisMixin
from funboost.concurrent_pool.custom_threadpool_executor import show_current_threads_num

from funboost.core.current_task import funboost_current_task,fct,get_current_taskid



# atexit.register(ctrl_c_recv)  # 还是需要用户自己在代码末尾加才可以.
# set_interrupt_signal_handler()

# 有的包默认没加handlers，原始的日志不漂亮且不可跳转不知道哪里发生的。这里把warnning级别以上的日志默认加上handlers。
# nb_log.get_logger(name='', log_level_int=30, log_filename='pywarning.log')


```

### 代码文件: funboost\__init__old.py
```python
# noinspection PyUnresolvedReferences
import types

# noinspection PyUnresolvedReferences
from funboost.utils.dependency_packages_in_pythonpath import add_to_pythonpath

import typing
# noinspection PyUnresolvedReferences
from functools import update_wrapper, wraps, partial
import copy
# noinspection PyUnresolvedReferences
import nb_log
from funboost.funboost_config_deafult import BoostDecoratorDefaultParams
from funboost.helpers import (multi_process_pub_params_list,
                              run_consumer_with_multi_process, )
from funboost.core.global_boosters import GlobalBoosters
from funboost.core.fabric_deploy_helper import fabric_deploy

from funboost.consumers.base_consumer import (AbstractConsumer, FunctionResultStatusPersistanceConfig)
from funboost.publishers.base_publisher import (AbstractPublisher)
from funboost.factories.consumer_factory import get_consumer

# noinspection PyUnresolvedReferences
from funboost.utils import nb_print, patch_print, LogManager, get_logger, LoggerMixin


# 有的包默认没加handlers，原始的日志不漂亮且不可跳转不知道哪里发生的。这里把warnning级别以上的日志默认加上handlers。
# nb_log.get_logger(name='', log_level_int=30, _log_filename='pywarning.log')


class Booster(LoggerMixin):
    """
    为了被装饰的消费函数的敲代码时候的被pycharm自动补全而写的类。
    """

    def __init__(self, consuming_func_decorated: callable):
        """
        :param consuming_func_decorated:   传入被boost装饰的函数

        此框架非常非常注重，公有函数、方法、类 的名字和入参在ide开发环境下面的自动提示补全效果，如果不是为了这一点，框架能减少很多重复地方。
        此类是防止用户调用打错字母或者不知道怎么敲代码不知道有哪些入参。所以才有这个类。

        这个类是个补全类，能够使pycharm自动补全方法名字和入参。可以用，可以不用，用了后在pycharm里面补全效果会起作用。


       from funboost import boost, IdeAutoCompleteHelper

       @boost('queue_test_f01', qps=2, broker_kind=3)
       def f(a, b):
           print(f'{a} + {b} = {a + b}')


       if __name__ == '__main__':
           f(1000, 2000)
           IdeAutoCompleteHelper(f).clear()  # f.clear()
           for i in range(100, 200):
               f.pub(dict(a=i, b=i * 2))  # f.sub方法是强行用元编程加到f上去的，是运行时状态，pycharm只能补全非运行时态的静态东西。
               IdeAutoCompleteHelper(f).pub({'a': i * 3, 'b': i * 4})  # 和上面的发布等效，但可以自动补全方法名字和入参。
               f.push(a=i, b=i * 2)
               IdeAutoCompleteHelper(f).delay(i * 3,  i * 4)

           IdeAutoCompleteHelper(f).start_consuming_message()  # 和 f.consume()等效

        """
        wraps(consuming_func_decorated)(self)
        self.init_params: dict = consuming_func_decorated.init_params
        self.is_decorated_as_consume_function = consuming_func_decorated.is_decorated_as_consume_function
        self.consuming_func_decorated = consuming_func_decorated

        self.queue_name = consuming_func_decorated.queue_name

        self.consumer = consuming_func_decorated.consumer  # type: AbstractConsumer

        self.publisher = consuming_func_decorated.publisher  # type: AbstractPublisher
        self.publish = self.pub = self.apply_async = self.publisher.publish  # type: AbstractPublisher.publish
        self.push = self.delay = self.publisher.push  # type: AbstractPublisher.push
        self.clear = self.clear_queue = self.publisher.clear  # type: AbstractPublisher.clear
        self.get_message_count = self.publisher.get_message_count

        self.start_consuming_message = self.consume = self.start = self.consumer.start_consuming_message

        self.clear_filter_tasks = self.consumer.clear_filter_tasks

        self.wait_for_possible_has_finish_all_tasks = self.consumer.wait_for_possible_has_finish_all_tasks

        # self.pause = self.pause_consume = self.consumer.pause_consume
        self.continue_consume = self.consumer.continue_consume

        for k, v in consuming_func_decorated.__dict__.items():
            ''' 上面那些手动的是为了代码补全方便 ，这个是自动的补充所有'''
            if not k.startswith('_'):
                setattr(self, k, v)

    def multi_process_consume(self, process_num=1):
        """超高速多进程消费"""
        run_consumer_with_multi_process(self.consuming_func_decorated, process_num)

    multi_process_start = multi_process_consume

    def multi_process_pub_params_list(self, params_list, process_num=16):
        """超高速多进程发布，例如先快速发布1000万个任务到中间件，以后慢慢消费"""
        """
        用法例如，快速20进程发布1000万任务，充分利用多核加大cpu使用率。
        @boost('test_queue66c', qps=1/30,broker_kind=BrokerEnum.KAFKA_CONFLUENT)
        def f(x, y):
            print(f'函数开始执行时间 {time.strftime("%H:%M:%S")}')
        if __name__ == '__main__':
            f.multi_process_pub_params_list([{'x':i,'y':i*3}  for i in range(10000000)],process_num=20)
            f.consume()
        """
        multi_process_pub_params_list(self.consuming_func_decorated, params_list=params_list, process_num=process_num)

    # noinspection PyDefaultArgument
    def fabric_deploy(self, host, port, user, password,
                      path_pattern_exluded_tuple=('/.git/', '/.idea/', '/dist/', '/build/'),
                      file_suffix_tuple_exluded=('.pyc', '.log', '.gz'),
                      only_upload_within_the_last_modify_time=3650 * 24 * 60 * 60,
                      file_volume_limit=1000 * 1000, sftp_log_level=20, extra_shell_str='',
                      invoke_runner_kwargs={'hide': None, 'pty': True, 'warn': False},
                      python_interpreter='python3',
                      process_num=1):
        """
        入参见 fabric_deploy 函数。这里重复入参是为了代码在pycharm补全提示。
        """
        in_kwargs = locals()
        in_kwargs.pop('self')
        fabric_deploy(self.consuming_func_decorated, **in_kwargs)

    def __call__(self, *args, **kwargs):
        return self.consuming_func_decorated(*args, **kwargs)

    def __get__(self, instance, cls):
        """ https://python3-cookbook.readthedocs.io/zh_CN/latest/c09/p09_define_decorators_as_classes.html """
        if instance is None:
            return self
        else:
            return types.MethodType(self, instance)


IdeAutoCompleteHelper = Booster  # 兼容


class _Undefined:
    pass


def boost(queue_name,
          *,
          consumin_function_decorator: typing.Callable = _Undefined,
          function_timeout: float = _Undefined,
          concurrent_num: int = _Undefined,
          specify_concurrent_pool=_Undefined,
          specify_async_loop=_Undefined,
          concurrent_mode: int = _Undefined,
          max_retry_times: int = _Undefined,
          is_push_to_dlx_queue_when_retry_max_times: bool = _Undefined,
          log_level: int = _Undefined,
          is_print_detail_exception: bool = _Undefined,
          is_show_message_get_from_broker: bool = _Undefined,
          qps: float = _Undefined,
          is_using_distributed_frequency_control: bool = _Undefined,
          msg_expire_senconds: float = _Undefined,
          is_send_consumer_hearbeat_to_redis: bool = _Undefined,
          logger_prefix: str = _Undefined,
          create_logger_file: bool = _Undefined,
          do_task_filtering: bool = _Undefined,
          task_filtering_expire_seconds: float = _Undefined,
          is_do_not_run_by_specify_time_effect: bool = _Undefined,
          do_not_run_by_specify_time: bool = _Undefined,
          schedule_tasks_on_main_thread: bool = _Undefined,
          function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = _Undefined,
          user_custom_record_process_info_func: typing.Union[typing.Callable, None] = _Undefined,
          is_using_rpc_mode: bool = _Undefined,
          broker_exclusive_config: dict = _Undefined,
          broker_kind: int = _Undefined,
          boost_decorator_default_params=BoostDecoratorDefaultParams()
          ):
    """
    funboost.funboost_config_deafult.BoostDecoratorDefaultParams 的值会自动被你项目根目录下的funboost_config.BoostDecoratorDefaultParams的值覆盖，
    如果boost装饰器不传参，默认使用funboost_config.BoostDecoratorDefaultParams的配置

    入参也可以看文档 https://funboost.readthedocs.io/zh-cn/latest/articles/c3.html   3.3章节。

    # 为了代码提示好，这里重复一次入参意义。被此装饰器装饰的函数f，函数f对象本身自动加了一些方法，例如f.push 、 f.consume等。
    :param queue_name: 队列名字。
    :param consumin_function_decorator : 函数的装饰器。因为此框架做参数自动转指点，需要获取精准的入参名称，不支持在消费函数上叠加 @ *args  **kwargs的装饰器，如果想用装饰器可以这里指定。
    :param function_timeout : 超时秒数，函数运行超过这个时间，则自动杀死函数。为0是不限制。设置后代码性能会变差，非必要不要轻易设置。
    # 如果设置了qps，并且cocurrent_num是默认的50，会自动开了500并发，由于是采用的智能线程池任务少时候不会真开那么多线程而且会自动缩小线程数量。具体看ThreadPoolExecutorShrinkAble的说明
    # 由于有很好用的qps控制运行频率和智能扩大缩小的线程池，此框架建议不需要理会和设置并发数量只需要关心qps就行了，框架的并发是自适应并发数量，这一点很强很好用。
    :param concurrent_num:并发数量
    :param specify_concurrent_pool:使用指定的线程池（协程池），可以多个消费者共使用一个线程池，不为None时候。threads_num失效
    :param specify_async_loop:指定的async的loop循环，设置并发模式为async才能起作用。
    :param concurrent_mode:并发模式，1线程(ConcurrentModeEnum.THREADING) 2gevent(ConcurrentModeEnum.GEVENT)
                              3eventlet(ConcurrentModeEnum.EVENTLET) 4 asyncio(ConcurrentModeEnum.ASYNC) 5单线程(ConcurrentModeEnum.SINGLE_THREAD)
    :param max_retry_times: 最大自动重试次数，当函数发生错误，立即自动重试运行n次，对一些特殊不稳定情况会有效果。
           可以在函数中主动抛出重试的异常ExceptionForRetry，框架也会立即自动重试。
           主动抛出ExceptionForRequeue异常，则当前 消息会重返中间件，
           主动抛出 ExceptionForPushToDlxqueue  异常，可以使消息发送到单独的死信队列中，死信队列的名字是 队列名字 + _dlx。
           。
    :param is_push_to_dlx_queue_when_retry_max_times : 函数达到最大重试次数仍然没成功，是否发送到死信队列,死信队列的名字是 队列名字 + _dlx。
    :param log_level:框架的日志级别。logging.DEBUG(10)  logging.DEBUG(10) logging.INFO(20) logging.WARNING(30) logging.ERROR(40) logging.CRITICAL(50)
    :param is_print_detail_exception:是否打印详细的堆栈错误。为0则打印简略的错误占用控制台屏幕行数少。
    :param is_show_message_get_from_broker: 从中间件取出消息时候时候打印显示出来
    :param qps:指定1秒内的函数执行次数，例如可以是小数0.01代表每100秒执行一次，也可以是50代表1秒执行50次.为0则不控频。
    :param msg_expire_senconds:消息过期时间，为0永不过期，为10则代表，10秒之前发布的任务如果现在才轮到消费则丢弃任务。
    :param is_using_distributed_frequency_control: 是否使用分布式空频（依赖redis统计消费者数量，然后频率平分），默认只对当前实例化的消费者空频有效。
            假如实例化了2个qps为10的使用同一队列名的消费者，并且都启动，则每秒运行次数会达到20。如果使用分布式空频则所有消费者加起来的总运行次数是10。
    :param is_send_consumer_hearbeat_to_redis   是否将发布者的心跳发送到redis，有些功能的实现需要统计活跃消费者。因为有的中间件不是真mq。
    :param logger_prefix: 日志前缀，可使不同的消费者生成不同的日志前缀
    :param create_logger_file : 是否创建文件日志
    :param do_task_filtering :是否执行基于函数参数的任务过滤
    :param task_filtering_expire_seconds:任务过滤的失效期，为0则永久性过滤任务。例如设置过滤过期时间是1800秒 ，
           30分钟前发布过1 + 2 的任务，现在仍然执行，
           如果是30分钟以内发布过这个任务，则不执行1 + 2，现在把这个逻辑集成到框架，一般用于接口价格缓存。
    :param is_do_not_run_by_specify_time_effect :是否使不运行的时间段生效
    :param do_not_run_by_specify_time   :不运行的时间段
    :param schedule_tasks_on_main_thread :直接在主线程调度任务，意味着不能直接在当前主线程同时开启两个消费者。fun.consume()就阻塞了，这之后的代码不会运行
    :param function_result_status_persistance_conf   :配置。是否保存函数的入参，运行结果和运行状态到mongodb。
           这一步用于后续的参数追溯，任务统计和web展示，需要安装mongo。
    :param user_custom_record_process_info_func  提供一个用户自定义的保存消息处理记录到某个地方例如mysql数据库的函数，函数仅仅接受一个入参，入参类型是 FunctionResultStatus，用户可以打印参数
    :param is_using_rpc_mode 是否使用rpc模式，可以在发布端获取消费端的结果回调，但消耗一定性能，使用async_result.result时候会等待阻塞住当前线程。。
    :param broker_exclusive_config 加上一个不同种类中间件非通用的配置,不同中间件自身独有的配置，不是所有中间件都兼容的配置，因为框架支持30种消息队列，消息队列不仅仅是一般的先进先出queue这么简单的概念，
            例如kafka支持消费者组，rabbitmq也支持各种独特概念例如各种ack机制 复杂路由机制，每一种消息队列都有独特的配置参数意义，可以通过这里传递。
    :param broker_kind:中间件种类，支持30种消息队列。 入参见 BrokerEnum枚举类的属性。
    :param boost_decorator_default_params: oostDecoratorDefaultParams是
            @boost装饰器默认的全局入参。如果boost没有亲自指定某个入参，就自动使用funboost_config.py的BoostDecoratorDefaultParams中的配置。
                    如果你嫌弃每个 boost 装饰器相同入参太多重复了，可以在 funboost_config.py 文件中设置boost装饰器的全局默认值。
            BoostDecoratorDefaultParams() 实例化时候也可以传递这个boost装饰器任何的入参，BoostDecoratorDefaultParams是个数据类，百度python3.7dataclass的概念，类似。

            funboost.funboost_config_deafult.BoostDecoratorDefaultParams 的值会自动被你项目根目录下的funboost_config.BoostDecoratorDefaultParams的值覆盖

    """

    """
    这是此框架最重要的一个函数，必须看懂里面的入参有哪些。
    此函数的入参意义请查看 get_consumer的入参注释。

    本来是这样定义的，def boost(queue_name, **consumer_init_kwargs):
    为了更好的ide智能补全，重复写全函数入参。

    装饰器方式注册消费任务，如果有人过于喜欢装饰器方式，例如celery 装饰器方式的任务注册，觉得黑科技，那就可以使用这个装饰器。
    假如你的函数名是f,那么可以调用f.publish或f.pub来发布任务。调用f.start_consuming_message 或 f.consume 或 f.start消费任务。
    必要时候调用f.publisher.funcxx   和 f.conusmer.funcyy。


    装饰器版，使用方式例如：
    '''
    @boost('queue_test_f01', qps=0.2, broker_kind=2)
    def f(a, b):
        print(a + b)

    for i in range(10, 20):
        f.pub(dict(a=i, b=i * 2))
        f.push(i, i * 2)
    f.consume()
    # f.multi_process_conusme(8)             # # 这个是新加的方法，细粒度 线程 协程并发 同时叠加8个进程，速度炸裂。主要是无需导入run_consumer_with_multi_process函数。
    # run_consumer_with_multi_process(f,8)   # 这个是细粒度 线程 协程并发 同时叠加8个进程，速度炸裂。
    '''

    常规方式，使用方式如下
    '''
    def f(a, b):
        print(a + b)

    consumer = get_consumer('queue_test_f01', consuming_function=f,qps=0.2, broker_kind=2)
    # 需要手动指定consuming_function入参的值。
    for i in range(10, 20):
        consumer.publisher_of_same_queue.publish(dict(a=i, b=i * 2))
    consumer.start_consuming_message()

    '''

    装饰器版本的 boost 入参 和 get_consumer 入参99%一致，唯一不同的是 装饰器版本加在了函数上自动知道消费函数了，
    所以不需要传consuming_function参数。
    """
    # 装饰器版本能够自动知道消费函数，防止boost按照get_consumer的入参重复传参了consuming_function。
    consumer_init_params_include_boost_decorator_default_params = copy.copy(locals())
    consumer_init_params0 = copy.copy(consumer_init_params_include_boost_decorator_default_params)
    consumer_init_params0.pop('boost_decorator_default_params')
    consumer_init_params = copy.copy(consumer_init_params0)
    for k, v in consumer_init_params0.items():
        if v == _Undefined:
            # print(k,v,boost_decorator_default_params[k])
            consumer_init_params[k] = boost_decorator_default_params[k]  # boost装饰器没有亲指定某个传参，就使用funboost_config.py的BoostDecoratorDefaultParams的全局配置。

    # print(consumer_init_params)
    def _deco(func) -> Booster:  # 加这个-> 可以实现pycahrm动态补全

        func.init_params = consumer_init_params
        consumer = get_consumer(consuming_function=func, **consumer_init_params)  # type: AbstractConsumer
        func.is_decorated_as_consume_function = True
        func.consumer = consumer
        func.queue_name = queue_name

        func.publisher = consumer.publisher_of_same_queue
        func.publish = func.pub = func.apply_async = consumer.publisher_of_same_queue.publish
        func.push = func.delay = consumer.publisher_of_same_queue.push
        func.multi_process_pub_params_list = partial(multi_process_pub_params_list, func)
        func.clear = func.clear_queue = consumer.publisher_of_same_queue.clear
        func.get_message_count = consumer.publisher_of_same_queue.get_message_count

        func.start_consuming_message = func.consume = func.start = consumer.start_consuming_message
        func.multi_process_start = func.multi_process_consume = partial(run_consumer_with_multi_process, func)

        func.fabric_deploy = partial(fabric_deploy, func)

        func.clear_filter_tasks = consumer.clear_filter_tasks

        func.wait_for_possible_has_finish_all_tasks = consumer.wait_for_possible_has_finish_all_tasks

        func.pause = func.pause_consume = consumer.pause_consume
        func.continue_consume = consumer.continue_consume

        GlobalBoosters.regist(queue_name,func)

        # @wraps(func)
        # def __deco(*args, **kwargs):  # 这样函数的id变化了，导致win在装饰器内部开多进程不方便。
        #     return func(*args, **kwargs)
        return func

        # return __deco  # noqa # 两种方式都可以
        # return update_wrapper(__deco, func)

    return _deco  # noqa


task_deco = boost  # 两个装饰器名字都可以。task_deco是原来名字，兼容一下。

```

### 代码文件: funboost\__main__.py
```python
import sys

import fire
from funboost.core.cli.funboost_fire import BoosterFire, env_dict


def _check_pass_params():
    has_passing_arguments_project_root_path = False
    for a in sys.argv:
        if '--project_root_path=' in a:
            has_passing_arguments_project_root_path = True
            project_root_path = a.split('=')[-1]
            sys.path.insert(1, project_root_path)
            env_dict['project_root_path'] = project_root_path
    if has_passing_arguments_project_root_path is False:
        raise Exception('命令行没有传参 --project_root_path=')


def main():
    _check_pass_params()
    

    fire.Fire(BoosterFire, )


if __name__ == '__main__':
    main()

'''
python -m funboost  --project_root_path=/codes/funboost   --booster_dirs_str=test_frame/test_funboost_cli/test_find_boosters --max_depth=2  show_all_queues

python -m funboost  --project_root_path=/codes/funboost   --booster_dirs_str=test_frame/test_funboost_cli/test_find_boosters --max_depth=2  push test_find_queue1 --x=1 --y=2


python -m funboost  --project_root_path=/codes/funboost  start_web
'''

```

### 代码文件: funboost\assist\celery_helper.py
```python
import copy

import json
import logging
import os
import sys
import threading
from functools import partial

import celery

import nb_log
from funboost.funboost_config_deafult import BrokerConnConfig,FunboostCommonConfig
from funboost import  ConcurrentModeEnum
from funboost.core.loggers import get_funboost_file_logger,get_logger

celery_app = celery.Celery(main='funboost_celery', broker=BrokerConnConfig.CELERY_BROKER_URL,
                           backend=BrokerConnConfig.CELERY_RESULT_BACKEND,
                           task_routes={}, timezone=FunboostCommonConfig.TIMEZONE, enable_utc=False, )

celery_app.conf.task_acks_late = True
celery_app.conf.update({
    'worker_redirect_stdouts': False,
    'worker_concurrency': 200
}
)

logger = get_funboost_file_logger('funboost.CeleryHelper')


class CeleryHelper:
    celery_app = celery_app
    to_be_start_work_celery_queue_name_set = set()  # start_consuming_message时候，添加需要worker运行的queue name。

    concurrent_mode = None

    @staticmethod
    def update_celery_app_conf(celery_app_conf: dict):
        """
        更新celery app的配置，celery app配置大全见 https://docs.celeryq.dev/en/stable/userguide/configuration.html
        :param celery_app_conf: celery app 配置，字典
        :return:
        """
        celery_app.conf.update(celery_app_conf)
        # 例如  celery_app.conf.update({'broker_transport_options':{'visibility_timeout': 18000,'max_retries':5}})

    @staticmethod
    def show_celery_app_conf():
        logger.debug('展示celery app的配置')
        conf_dict_json_able = {}
        for k, v in celery_app.conf.items():
            conf_dict_json_able[k] = str(v)
            # print(k, ' : ', v)
        print('celery app 的配置是：', json.dumps(conf_dict_json_able, ensure_ascii=False, indent=4))

    @staticmethod
    def celery_start_beat(beat_schedule: dict):
        celery_app.conf.beat_schedule = beat_schedule  # 配置celery定时任务

        def _f():
            beat = partial(celery_app.Beat, loglevel='INFO', )
            beat().run()

        threading.Thread(target=_f).start()  # 使得可以很方便启动定时任务，继续启动函数消费

    @staticmethod
    def start_flower(port=5555):
        def _f():
            python_executable = sys.executable
            # print(python_executable)
            # cmd = f'''{python_executable} -m celery -A  funboost.assist.celery_helper  --broker={funboost_config_deafult.CELERY_BROKER_URL}  --result-backend={funboost_config_deafult.CELERY_RESULT_BACKEND}   flower --address=0.0.0.0 --port={port}  --auto_refresh=True '''
            cmd = f'''{python_executable} -m celery   --broker={BrokerConnConfig.CELERY_BROKER_URL}  --result-backend={BrokerConnConfig.CELERY_RESULT_BACKEND}   flower --address=0.0.0.0 --port={port}  --auto_refresh=True '''

            logger.info(f'启动flower命令:   {cmd}')
            os.system(cmd)

        threading.Thread(target=_f).start()

    @classmethod
    def add_start_work_celery_queue_name(cls, queue_name):
        cls.to_be_start_work_celery_queue_name_set.add(queue_name)

    @classmethod
    def realy_start_celery_worker(cls, worker_name=None, loglevel='INFO',worker_concurrency=200,start_consume_queue_name_list:list=None,is_start_consume_all_queues:bool=False):

        if is_start_consume_all_queues is False:
            to_be_start_work_celery_queue_name_set_new = copy.copy(cls.to_be_start_work_celery_queue_name_set)
            to_be_start_work_celery_queue_name_set_new.update(set(start_consume_queue_name_list or []))
        else:
            from funboost import BoostersManager
            # print(BoostersManager.get_all_queues())
            to_be_start_work_celery_queue_name_set_new = set(BoostersManager.get_all_queues())
        queue_names_str = ','.join(list(to_be_start_work_celery_queue_name_set_new))
        if not to_be_start_work_celery_queue_name_set_new:
            raise Exception('celery worker 没有需要运行的queue')
        # '--concurrency=200',
        # '--autoscale=5,500' threads 并发模式不支持自动扩大缩小并发数量,
        worker_name = worker_name or f'pid_{os.getpid()}'
        pool_name = 'threads'
        if cls.concurrent_mode == ConcurrentModeEnum.GEVENT:
            pool_name = 'gevent'
        if cls.concurrent_mode == ConcurrentModeEnum.EVENTLET:
            pool_name = 'eventlet'
        '''
        并发数量在app配置中已经制定了。自己用 update_celery_app_conf 方法更新就好了。
        celery_app.conf.update({
             # 'worker_redirect_stdouts': False,
             'worker_concurrency': 200
         }
         或
         CeleryHelper.update_celery_app_conf({ 'worker_concurrency': 500})
        '''
        cls.update_celery_app_conf({'worker_concurrency':worker_concurrency})
        argv = ['worker', f'--pool={pool_name}',
                '-n', f'worker_funboost_{worker_name}@%h', f'--loglevel={loglevel}',
                f'--queues={queue_names_str}',  # 并发数量是 在app配置中已经制定了。自己用 update_celery_app_conf 方法更新就好了。
                ]
        logger.info(f'celery 启动work参数 {argv}')
        celery_app.worker_main(argv)

    @staticmethod
    def use_nb_log_instead_celery_log(log_level: int = logging.INFO, log_filename='celery.log', formatter_template=7):
        """
        使用nb_log的日志来取代celery的日志
        """
        celery_app.conf.worker_hijack_root_logger = False
        # logging.getLogger('celery').handlers=[]
        # logging.getLogger('celery.worker.strategy').handlers = []
        # logging.getLogger('celery.app.trace').handlers = []
        # logging.getLogger('celery.worker').handlers = []
        # logging.getLogger('celery.app').handlers = []
        # logging.getLogger().handlers=[]
        get_logger('celery', log_level_int=log_level, log_filename=log_filename, formatter_template=formatter_template, )
        get_logger(None, log_level_int=logging.WARNING, log_filename=log_filename, formatter_template=formatter_template, )
        for name in ['celery','celery.worker.strategy','celery.app.trace','celery.worker','celery.app',None]:
            nb_log.LogManager(name).prevent_add_handlers()
        nb_log.LogManager(None).preset_log_level(logging.WARNING)

```

### 代码文件: funboost\assist\dramatiq_helper.py
```python
import argparse
from funboost.core.loggers import FunboostMetaTypeFileLogger
import dramatiq
from dramatiq.cli import main
from funboost.funboost_config_deafult import BrokerConnConfig
from dramatiq.brokers.redis import RedisBroker
from dramatiq.brokers.rabbitmq import RabbitmqBroker

if BrokerConnConfig.DRAMATIQ_URL.startswith('redis'):
    broker = RedisBroker(url=BrokerConnConfig.DRAMATIQ_URL)
elif BrokerConnConfig.DRAMATIQ_URL.startswith('amqp'):
    broker = RabbitmqBroker(url=BrokerConnConfig.DRAMATIQ_URL)
else:
    raise ValueError('DRAMATIQ_URL 配置错误，需要配置成url连接形式，例如 amqp://rabbitmq_user:rabbitmq_pass@127.0.0.1:5672/ 或者 redis://:passwd@192.168.64.151:6378/7 ')
dramatiq.set_broker(broker)

"""
 {'max_age', 'throws', 'pipe_target', 'pipe_ignore', 'on_success', 'retry_when', 'time_limit', 'min_backoff', 'max_retries', 'max_backoff', 'notify_shutdown', 'on_failure'}
"""


class DramatiqHelper(metaclass=FunboostMetaTypeFileLogger):

    broker = dramatiq.get_broker()
    to_be_start_work_celery_queue_name_set = set()  # 存放需要worker运行的queue name。

    queue_name__actor_map = {}

    @classmethod
    def realy_start_dramatiq_worker(cls):
        p = argparse.ArgumentParser()
        pa = p.parse_args()

        pa.broker = 'funboost.assist.dramatiq_helper'
        pa.modules = []
        pa.processes = 1
        pa.threads = 200
        pa.path = ''
        pa.queues = list(cls.to_be_start_work_celery_queue_name_set)
        pa.log_file = None
        pa.skip_logging = False
        pa.use_spawn = False
        pa.forks = []
        pa.worker_shutdown_timeout = 600000
        pa.verbose = 0
        pa.pid_file = None

        cls.logger.warning(f'dramatiq 命令行启动参数 {pa}')
        main(pa)


'''
Namespace(broker='test_dramatiq_raw', modules=[], processes=1, threads=8, path='.', queues=None, pid_file=None, log_file=None, skip_logging=False, use_spawn=False, forks=[], worker_shutdown_timeout=600000, verbose=0)
python -m dramatiq test_dramatiq_raw -p 1
'''

```

### 代码文件: funboost\assist\faststream_helper.py
```python
import asyncio

from faststream import FastStream
from faststream.rabbit import RabbitBroker
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.core.loggers import get_funboost_file_logger

get_funboost_file_logger('faststream.access.rabbit')

broker = RabbitBroker(BrokerConnConfig.RABBITMQ_URL, max_consumers=20)
app = FastStream(broker)

# asyncio.get_event_loop().run_until_complete(broker.connect())
#
# asyncio.get_event_loop().run_until_complete(broker.start())

def get_broker(max_consumers=None):
    return RabbitBroker(BrokerConnConfig.RABBITMQ_URL, max_consumers=max_consumers)
```

### 代码文件: funboost\assist\huey_helper.py
```python
import multiprocessing
import threading

from funboost.funboost_config_deafult import BrokerConnConfig
from huey import RedisHuey
from huey.consumer import Consumer

huey_obj = RedisHuey('funboost_huey', url=BrokerConnConfig.REDIS_URL,)

class HueyHelper:
    huey_obj = huey_obj
    queue_name__huey_task_fun_map = {}
    to_be_start_huey_queue_name_set= set()

    # @classmethod
    # def realy_start_huey_consume(cls):
    #     for queue_name in list(cls.to_be_start_huey_queue_name_set):
    #         multiprocessing.Process(target=cls._start_huey,args=(queue_name,)).start()  # huey的consumer的run方法无法在子线程运行，必须是主线程。
    #
    # @classmethod
    # def _start_huey(cls,queue_name):
    #     consumer_kwargs = {'huey': HueyHelper.queue_name__huey_obj_map[queue_name], 'workers': 200, 'periodic': True, 'initial_delay': 0.1, 'backoff': 1.15, 'max_delay': 10.0, 'scheduler_interval': 1, 'worker_type': 'thread', 'check_worker_health': True, 'health_check_interval': 10, 'flush_locks': False, 'extra_locks': None}
    #     huey_consumer = Consumer(**consumer_kwargs)
    #     huey_consumer.run()

    @classmethod
    def realy_start_huey_consume(cls):
        """ huey 启动所有函数开始消费"""
        consumer_kwargs = {'huey': huey_obj, 'workers': 200, 'periodic': True,
                           'initial_delay': 0.1, 'backoff': 1.15, 'max_delay': 10.0,
                           'scheduler_interval': 1, 'worker_type': 'thread',
                           'check_worker_health': True, 'health_check_interval': 10,
                           'flush_locks': False, 'extra_locks': None}
        huey_consumer = Consumer(**consumer_kwargs)
        huey_consumer.run()







```

### 代码文件: funboost\assist\rocketry_helper.py
```python

```

### 代码文件: funboost\assist\rq_helper.py
```python
import threading
import os
import uuid
from rq.worker import RandomWorker
from funboost.core.loggers import get_funboost_file_logger
from redis3 import Redis
from rq import Worker
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.assist.rq_windows_worker import WindowsWorker


def _install_signal_handlers_monkey(self):
    """ 不能在非主线程中操作信号"""
    pass


Worker._install_signal_handlers = _install_signal_handlers_monkey


class RandomWindowsWorker(RandomWorker, WindowsWorker):
    """ 这个是为了 每个队列都有机会同时拉取，默认是前面的队列先消费完才会消费下一个队列名"""

    pass


class RqHelper:
    redis_conn = Redis.from_url(BrokerConnConfig.REDIS_URL)

    queue_name__rq_job_map = {}
    to_be_start_work_rq_queue_name_set = set()

    @classmethod
    def realy_start_rq_worker(cls, threads_num=50):
        threads = []
        for i in range(threads_num):
            t = threading.Thread(target=cls.__rq_work)
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

    @classmethod
    def __rq_work(cls):
        worker_cls = RandomWindowsWorker if os.name == 'nt' else RandomWorker
        worker = worker_cls(queues=list(cls.to_be_start_work_rq_queue_name_set), connection=cls.redis_conn, name=uuid.uuid4().hex)
        worker.work()

    @staticmethod
    def add_nb_log_handler_to_rq():
        get_funboost_file_logger('rq', log_level_int=20,)

```

### 代码文件: funboost\assist\rq_windows_worker.py
```python
import time
import sys
import random

from funboost.utils import times
import rq
import rq.job
import rq.compat
import rq.worker

from rq.defaults import (DEFAULT_LOGGING_FORMAT, DEFAULT_LOGGING_DATE_FORMAT)


class WindowsWorker(rq.Worker):
    """
    An extension of the RQ worker class
    that works on Windows.

    Does not support task timeouts
    and will probably crash if the task goes badly,
    due to not using fork().
    """

    def __init__(self, *args, **kwargs):
        if kwargs.get('default_worker_ttl', None) is None:
            # Force a small worker_ttl,
            # Otherwise the process seems to hang somewhere within connection.lpop and
            # you can't kill the worker with Ctrl+C until the timeout expires (Ctrl+Break works, though).
            # The default timeout is 420, however, which is too long.
            kwargs['default_worker_ttl'] = 2
        super(WindowsWorker, self).__init__(*args, **kwargs)

    def work(self, burst=False, logging_level="INFO", date_format=DEFAULT_LOGGING_DATE_FORMAT,
             log_format=DEFAULT_LOGGING_FORMAT, max_jobs=None, with_scheduler=False):
        """Starts the work loop.

        Pops and performs all jobs on the current list of queues.  When all
        queues are empty, block and wait for new jobs to arrive on any of the
        queues, unless `burst` mode is enabled.

        The return value indicates whether any jobs were processed.
        """
        self.log.info('Using rq_win.WindowsWorker (experimental)')
        self.default_worker_ttl=2
        return super(WindowsWorker, self).work(
            burst=burst,
            logging_level=logging_level,
            date_format=date_format,
            log_format=log_format,
            max_jobs=max_jobs,
            with_scheduler=with_scheduler
        )


    def execute_job(self, job, queue):
        """Spawns a work horse to perform the actual work and passes it a job.
        The worker will wait for the work horse and make sure it executes
        within the given timeout bounds, or will end the work horse with
        SIGALRM.
        """
        self.main_work_horse(job, queue)

    def main_work_horse(self, job, queue):
        """This is the entry point of the newly spawned work horse."""
        # After fork()'ing, always assure we are generating random sequences
        # that are different from the worker.
        random.seed()

        self._is_horse = True

        success = self.perform_job(job, queue)

        self._is_horse = False

    def perform_job(self, job, queue, heartbeat_ttl=None):
        """Performs the actual work of a job.  Will/should only be called
        inside the work horse's process.
        """
        self.prepare_job_execution(job)

        self.procline('Processing %s from %s since %s' % (
            job.func_name,
            job.origin, time.time()))

        try:
            job.started_at = times.now()

            # I have DISABLED the time limit!
            rv = job.perform()

            # Pickle the result in the same try-except block since we need to
            # use the same exc handling when pickling fails
            job._result = rv
            job._status = rq.job.JobStatus.FINISHED
            job.ended_at = times.now()

            #
            # Using the code from Worker.handle_job_success
            #
            with self.connection.pipeline() as pipeline:
                pipeline.watch(job.dependents_key)
                queue.enqueue_dependents(job, pipeline=pipeline)

                self.set_current_job_id(None, pipeline=pipeline)
                self.increment_successful_job_count(pipeline=pipeline)

                result_ttl = job.get_result_ttl(self.default_result_ttl)
                if result_ttl != 0:
                    job.save(pipeline=pipeline, include_meta=False)

                job.cleanup(result_ttl, pipeline=pipeline,
                            remove_from_queue=False)

                pipeline.execute()

        except:
            # Use the public setter here, to immediately update Redis
            job.status = rq.job.JobStatus.FAILED
            self.handle_exception(job, *sys.exc_info())
            return False

        if rv is None:
            self.log.info('Job OK')
        else:
            self.log.info('Job OK, result = %s' % (rq.worker.yellow(rq.compat.text_type(rv)),))

        if result_ttl == 0:
            self.log.info('Result discarded immediately.')
        elif result_ttl > 0:
            self.log.info('Result is kept for %d seconds.' % result_ttl)
        else:
            self.log.warning('Result will never expire, clean up result key manually.')

        return True
```

### 代码文件: funboost\assist\taskiq_helper.py
```python


```

### 代码文件: funboost\assist\__init__.py
```python

```

### 代码文件: funboost\beggar_version_implementation\beggar_redis_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/12/18 0018 10:06
"""
这里是最精简的乞丐版的基于redis的分布式函数执行的实现。相对于完整版，砍掉所有功能，只是演示框架的最精简最本质的实现。
主要是砍掉很多功能，大大简化代码行数，演示框架思路是如何分布式执行python
函数的，这个只做精简演示，不要亲自去使用这里，功能太弱。

完整版支持3种并发类型，乞丐版只支持多线程并发。完整版的线程池是有界队列，线程大小动态伸缩，乞丐版线程池的线程数量只会增加不能主动主动缩小。

完整版支持15种函数辅助控制，包括控频、超时杀死、消费确认 等15种功能，
乞丐版为了简化代码演示，全部不支持。

完整版支持10种消息队列中间件，这里只演示大家喜欢的redis作为中间件。
"""
import json
import redis
from concurrent.futures import ThreadPoolExecutor
from funboost.funboost_config_deafult import BrokerConnConfig

redis_db_frame = redis.Redis(host=BrokerConnConfig.REDIS_HOST, password=BrokerConnConfig.REDIS_PASSWORD,
                             port=BrokerConnConfig.REDIS_PORT, db=BrokerConnConfig.REDIS_DB,
                             ssl=BrokerConnConfig.REDIS_USE_SSL,
                             decode_responses=True)


class BeggarRedisConsumer:
    """保持和完整版差不多的代码形态。如果仅仅是像这里的十分简化的版本，一个函数实现也可以了。例如下面的函数。"""

    def __init__(self, queue_name, consume_function, threads_num):
        self.pool = ThreadPoolExecutor(threads_num)  # 最好是使用BoundedThreadpoolexecutor或customThreadpoolexecutor。无界队列会迅速取完redis消息。
        self.consume_function = consume_function
        self.queue_name = queue_name

    def start_consuming_message(self):
        while True:
            try:
                redis_task = redis_db_frame.blpop(self.queue_name, timeout=60)
                if redis_task:
                    task_str = redis_task[1]
                    print(f'从redis的 [{self.queue_name}] 队列中 取出的消息是： {task_str}  ')
                    task_dict = json.loads(task_str)
                    self.pool.submit(self.consume_function, **task_dict)
                else:
                    print(f'redis的 {self.queue_name} 队列中没有任务')
            except redis.RedisError as e:
                print(e)


def start_consuming_message(queue_name, consume_function, threads_num=50):
    """
    本例子实现的功能和中间件过于简单，单一函数最好了。
    看不懂有类的代码，不用看上面那个类，看这个函数就可以，使用一个10行代码的函数实现乞丐版分布式函数执行框架。

    """
    pool = ThreadPoolExecutor(threads_num)
    while True:
        try:
            redis_task = redis_db_frame.brpop(queue_name, timeout=60)
            if redis_task:
                task_str = redis_task[1]
                # print(f'从redis的 {queue_name} 队列中 取出的消息是： {task_str}')
                pool.submit(consume_function, **json.loads(task_str))
            else:
                print(f'redis的 {queue_name} 队列中没有任务')
        except redis.RedisError as e:
            print(e)


if __name__ == '__main__':
    import time


    def add(x, y):
        time.sleep(5)
        print(f'{x} + {y} 的结果是 {x + y}')


    # 推送任务
    for i in range(100):
        print(i)
        redis_db_frame.lpush('test_beggar_redis_consumer_queue', json.dumps(dict(x=i, y=i * 2)))

    # 消费任务
    # consumer = BeggarRedisConsumer('test_beggar_redis_consumer_queue', consume_function=add, threads_num=100)
    # consumer.start_consuming_message()

    start_consuming_message('test_beggar_redis_consumer_queue', consume_function=add, threads_num=10)

```

### 代码文件: funboost\beggar_version_implementation\README.md
```python
# 这是乞丐版代码实现

主要是砍掉很多功能，大大简化代码行数，演示框架思路是如何分布式执行python
函数的，不要亲自去使用这里，功能太弱。

完整版支持5种并发类型，乞丐版只支持多线程并发。

完整版支持20种函数辅助控制，包括控频、超时杀死、消费确认 等15种功能，
乞丐版为了简化代码演示，全部不支持。

完整版支持30种消息队列中间件，这里只演示大家喜欢的redis作为中间件。
```

### 代码文件: funboost\concurrent_pool\async_helper.py
```python
from functools import partial
import asyncio
from concurrent.futures import Executor
from funboost.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAble
# from funboost.concurrent_pool.flexible_thread_pool import FlexibleThreadPool

# 没有使用内置的concurrent.futures.ThreadpoolExecutor线程池，而是使用智能伸缩线程池。
async_executor_default = ThreadPoolExecutorShrinkAble(500)
# async_executor_default = FlexibleThreadPool(50)  # 这个不支持future特性


def get_or_create_event_loop():
    try:
        # Python 3.7+
        return asyncio.get_running_loop()
    except RuntimeError:
        # 没有正在运行的 loop
        try:
            # Python 3.6~3.9：get_event_loop 会自动创建
            return asyncio.get_event_loop()
        except RuntimeError:
            # Python 3.10+：get_event_loop 不再自动创建
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
        
async def simple_run_in_executor(f, *args, async_executor: Executor = None, async_loop=None, **kwargs):
    """
    一个很强的函数，使任意同步同步函数f，转化成asyncio异步api语法，
    例如 r = await  simple_run_in_executor(block_fun, 20)，可以不阻塞事件循环。

    asyncio.run_coroutine_threadsafe 和 run_in_executor 是一对反义词。

    asyncio.run_coroutine_threadsafe 是在非异步的上下文环境(也就是正常的同步语法的函数里面)下调用异步函数对象（协程），
    因为当前函数定义没有被async修饰，就不能在函数里面使用await，必须使用这。这个是将asyncio包的future对象转化返回一个concurrent.futures包的future对象。

    run_in_executor 是在异步环境（被async修饰的异步函数）里面，调用同步函数，将函数放到线程池运行防止阻塞整个事件循环的其他任务。
    这个是将 一个concurrent.futures包的future对象 转化为 asyncio包的future对象，
    asyncio包的future对象是一个asyncio包的awaitable对象，所以可以被await，concurrent.futures.Future对象不能被await。


    :param f:  f是一个同步的阻塞函数，f前面不能是由async定义的。
    :param args: f函数的位置方式入参
    :async_executor: 线程池
    :param async_loop: async的loop对象
    :param kwargs:f函数的关键字方式入参
    :return:
    """
    loopx = async_loop or get_or_create_event_loop()
    async_executorx = async_executor or async_executor_default
    # print(id(loopx))
    result = await loopx.run_in_executor(async_executorx, partial(f, *args, **kwargs))
    return result






if __name__ == '__main__':
    import time
    import requests


    def block_fun(x):
        print(x)
        time.sleep(5)
        return x * 10


    async def enter_fun(xx):  # 入口函数，模拟一旦异步，必须处处异步。不能直接调用block_fun，否则阻塞其他任务。
        await asyncio.sleep(1)
        # r = block_fun(xx)  # 如果这么用就完蛋了，阻塞事件循环， 运行完所有任务需要更久。
        r = await  simple_run_in_executor(block_fun, xx)
        print(r)


    loopy = asyncio.get_event_loop()
    print(id(loopy))
    tasks = []
    tasks.append(simple_run_in_executor(requests.get, url='http://www.baidu.com', timeout=10))  # 同步变异步用法。

    tasks.append(simple_run_in_executor(block_fun, 1))
    tasks.append(simple_run_in_executor(block_fun, 2))
    tasks.append(simple_run_in_executor(block_fun, 3))
    tasks.append(simple_run_in_executor(time.sleep, 8))

    tasks.append(enter_fun(4))
    tasks.append(enter_fun(5))
    tasks.append(enter_fun(6))

    print('开始')
    loopy.run_until_complete(asyncio.wait(tasks))
    print('结束')

    time.sleep(200)

```

### 代码文件: funboost\concurrent_pool\async_pool_executor.py
```python
import sys

import atexit
import asyncio
import threading
import time
import traceback
from threading import Thread
import traceback

from funboost.concurrent_pool.base_pool_type import FunboostBaseConcurrentPool
from funboost.core.loggers import FunboostFileLoggerMixin

# if os.name == 'posix':
#     import uvloop
#
#     asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())  # 打猴子补丁最好放在代码顶层，否则很大机会出问题。

"""
# 也可以采用 janus 的 线程安全的queue方式来实现异步池，此queue性能和本模块实现的生产 消费相比，性能并没有提高，所以就不重新用这这个包来实现一次了。
import janus
import asyncio
import time
import threading
import nb_log
queue = janus.Queue(maxsize=6000)

async def consume():
    while 1:
        # time.sleep(1)
        val = await queue.async_q.get() # 这是async，不要看错了
        print(val)

def push():
    for i in range(50000):
        # time.sleep(0.2)
        # print(i)
        queue.sync_q.put(i)  # 这是sync。不要看错了。


if __name__ == '__main__':
    threading.Thread(target=push).start()
    loop = asyncio.get_event_loop()
    loop.create_task(consume())
    loop.run_forever()
"""

if sys.platform == "darwin":  # mac 上会出错
      import selectors
      selectors.DefaultSelector = selectors.PollSelector

class AsyncPoolExecutor(FunboostFileLoggerMixin,FunboostBaseConcurrentPool):
    """
    使api和线程池一样，最好的性能做法是submit也弄成 async def，生产和消费在同一个线程同一个loop一起运行，但会对调用链路的兼容性产生破坏，从而调用方式不兼容线程池。
    """

    def __init__(self, size, specify_async_loop=None,
                 is_auto_start_specify_async_loop_in_child_thread=True):
        """

        :param size: 同时并发运行的协程任务数量。
        :param specify_loop: 可以指定loop,异步三方包的连接池发请求不能使用不同的loop去使用连接池.
        """
        self._size = size
        self._specify_async_loop = specify_async_loop
        self._is_auto_start_specify_async_loop_in_child_thread = is_auto_start_specify_async_loop_in_child_thread
        self.loop = specify_async_loop or asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._diff_init()
        # self._lock = threading.Lock()
        t = Thread(target=self._start_loop_in_new_thread, daemon=False)
        # t.setDaemon(True)  # 设置守护线程是为了有机会触发atexit，使程序自动结束，不用手动调用shutdown
        t.start()
     

    # def submit000(self, func, *args, **kwargs):
    #     # 这个性能比下面的采用 run_coroutine_threadsafe + result返回快了3倍多。
    #     with self._lock:
    #         while 1:
    #             if not self._queue.full():
    #                 self.loop.call_soon_threadsafe(self._queue.put_nowait, (func, args, kwargs))
    #                 break
    #             else:
    #                 time.sleep(0.01)

    def _diff_init(self):
        if sys.version_info.minor < 10:
            # self._sem = asyncio.Semaphore(self._size, loop=self.loop)
            self._queue = asyncio.Queue(maxsize=self._size, loop=self.loop)
        else:
            # self._sem = asyncio.Semaphore(self._size) # python3.10后，很多类和方法都删除了loop传参
            self._queue = asyncio.Queue(maxsize=self._size)


    def submit(self, func, *args, **kwargs):
        future = asyncio.run_coroutine_threadsafe(self._produce(func, *args, **kwargs), self.loop)  # 这个 run_coroutine_threadsafe 方法也有缺点，消耗的性能巨大。
        future.result()  # 阻止过快放入，放入超过队列大小后，使submit阻塞。 背压是为了防止 迅速掏空消息队列几千万消息到内存.

    async def _produce(self, func, *args, **kwargs):
        await self._queue.put((func, args, kwargs))

    async def _consume(self):
        while True:
            func, args, kwargs = await self._queue.get()
            if isinstance(func, str) and func.startswith('stop'):
                # self.logger.debug(func)
                break
            # noinspection PyBroadException,PyUnusedLocal
            try:
                await func(*args, **kwargs)
            except BaseException as e:
                self.logger.exception(f'func:{func}, args:{args}, kwargs:{kwargs} exc_type:{type(e)}  traceback_exc:{traceback.format_exc()}')
            # self._queue.task_done()

    async def __run(self):
        for _ in range(self._size):
            asyncio.ensure_future(self._consume())

    def _start_loop_in_new_thread(self, ):
        # self._loop.run_until_complete(self.__run())  # 这种也可以。
        # self._loop.run_forever()

        # asyncio.set_event_loop(self.loop)
        # self.loop.run_until_complete(asyncio.wait([self._consume() for _ in range(self._size)], loop=self.loop))
        # self._can_be_closed_flag = True
        if self._specify_async_loop is None:
            for _ in range(self._size):
                self.loop.create_task(self._consume())
        else:
            for _ in range(self._size):
                asyncio.run_coroutine_threadsafe(self._consume(),self.loop) # 这是 asyncio 专门提供的用于从其他线程向事件循环安全提交任务的函数。
        if self._specify_async_loop is None:
            self.loop.run_forever()
        else:
            if self._is_auto_start_specify_async_loop_in_child_thread:
                try:
                    self.loop.run_forever() #如果是指定的loop不能多次启动一个loop.
                except Exception as e:
                    self.logger.warning(f'{e} {traceback.format_exc()}')   # 如果多个线程使用一个loop，不能重复启动loop，否则会报错。
            else:
                pass # 用户需要自己在自己的业务代码中去手动启动loop.run_forever() 


    # def shutdown(self):
    #     if self.loop.is_running():  # 这个可能是atregster触发，也可能是用户手动调用，需要判断一下，不能关闭两次。
    #         for i in range(self._size):
    #             self.submit(f'stop{i}', )
    #         while not self._can_be_closed_flag:
    #             time.sleep(0.1)
    #         self.loop.stop()
    #         self.loop.close()
    #         print('关闭循环')



if __name__ == '__main__':
    def test_async_pool_executor():
        from funboost.concurrent_pool import CustomThreadPoolExecutor as ThreadPoolExecutor
        # from concurrent.futures.thread import ThreadPoolExecutor
        # noinspection PyUnusedLocal
        async def f(x):
            await asyncio.sleep(1)
            pass
            print('打印', x)
            # await asyncio.sleep(1)
            # raise Exception('aaa')

        def f2(x):
            pass
            # time.sleep(0.001)
            print('打印', x)

        print(1111)

        t1 = time.time()
        pool = AsyncPoolExecutor(20)
        # pool = ThreadPoolExecutor(200)  # 协程不能用线程池运行，否则压根不会执行print打印，对于一部函数 f(x)得到的是一个协程，必须进一步把协程编排成任务放在loop循环里面运行。
        for i in range(1, 501):
            print('放入', i)
            pool.submit(f, i)
        # time.sleep(5)
        # pool.submit(f, 'hi')
        # pool.submit(f, 'hi2')
        # pool.submit(f, 'hi3')
        # print(2222)
        pool.shutdown()
        print(time.time() - t1)


    test_async_pool_executor()
    # test_async_producer_consumer()

    print(sys.version_info)

```

### 代码文件: funboost\concurrent_pool\base_pool_type.py
```python


class FunboostBaseConcurrentPool:

    def __deepcopy__(self, memodict={}):
        """
        pydantic 的默认类型声明，对象需要能deepcopy
        """
        return self
```

### 代码文件: funboost\concurrent_pool\bounded_processpoolexcutor_gt_py37.py
```python
import multiprocessing
import concurrent.futures
import sys
import threading
from concurrent.futures import _base
from concurrent.futures.process import _ExceptionWithTraceback, _ResultItem  # noqa
from functools import wraps
import os

from funboost.core.loggers import get_funboost_file_logger

name = 'bounded_pool_executor'

logger = get_funboost_file_logger('BoundedProcessPoolExecutor')


def _process_worker(call_queue, result_queue):
    """Evaluates calls from call_queue and places the results in result_queue.

    This worker is run in a separate process.

    Args:
        call_queue: A multiprocessing.Queue of _CallItems that will be read and
            evaluated by the worker.
        result_queue: A multiprocessing.Queue of _ResultItems that will written
            to by the worker.
        shutdown: A multiprocessing.Event that will be set as a signal to the
            worker that it should exit when call_queue is empty.
    """
    while True:
        call_item = call_queue.get(block=True)
        if call_item is None:
            # Wake up queue management thread
            result_queue.put(os.getpid())
            return
        try:
            r = call_item.fn(*call_item.args, **call_item.kwargs)
        except BaseException as e:
            exc = _ExceptionWithTraceback(e, e.__traceback__)
            result_queue.put(_ResultItem(call_item.work_id, exception=exc))
            logger.exception(e)  # 主要是直接显示错误。
        else:
            result_queue.put(_ResultItem(call_item.work_id,
                                         result=r))


def _process_worker_grater_than_py37(call_queue, result_queue, initializer, initargs):
    """Evaluates calls from call_queue and places the results in result_queue.

    This worker is run in a separate process.

    Args:
        call_queue: A ctx.Queue of _CallItems that will be read and
            evaluated by the worker.
        result_queue: A ctx.Queue of _ResultItems that will written
            to by the worker.
        initializer: A callable initializer, or None
        initargs: A tuple of args for the initializer
    """
    from concurrent.futures.process import _sendback_result
    if initializer is not None:
        try:
            initializer(*initargs)
        except BaseException:
            _base.LOGGER.critical('Exception in initializer:', exc_info=True)
            # The parent will notice that the process stopped and
            # mark the pool broken
            return
    while True:
        call_item = call_queue.get(block=True)
        # print(call_item)
        if call_item is None:
            # Wake up queue management thread
            result_queue.put(os.getpid())
            return
        try:
            r = call_item.fn(*call_item.args, **call_item.kwargs)
        except BaseException as e:
            exc = _ExceptionWithTraceback(e, e.__traceback__)
            _sendback_result(result_queue, call_item.work_id, exception=exc)
            logger.exception(e)  # 主要是直接显示错误。
        else:
            _sendback_result(result_queue, call_item.work_id, result=r)
            del r

        # Liberate the resource as soon as possible, to avoid holding onto
        # open files or shared memory that is not needed anymore
        del call_item


def _deco(f):
    @wraps(f)
    def __deco(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except BaseException as e:
            logger.exception(e)

    return __deco


class _BoundedPoolExecutor:
    semaphore = None

    def acquire(self):
        self.semaphore.acquire()

    def release(self, fn):
        self.semaphore.release()

    def submit(self, fn, *args, **kwargs):
        self.acquire()
        future = super().submit(fn, *args, **kwargs)  # noqa
        future.add_done_callback(self.release)

        return future


class BoundedProcessPoolExecutor(_BoundedPoolExecutor, concurrent.futures.ProcessPoolExecutor):

    def __init__(self, max_workers=None):

        if sys.version >= '3.7':
            # print(sys.version)
            concurrent.futures.process._process_worker = _process_worker_grater_than_py37
        else:
            concurrent.futures.process._process_worker = _process_worker
        super().__init__(max_workers)
        self.semaphore = multiprocessing.BoundedSemaphore(max_workers)


class BoundedThreadPoolExecutor(_BoundedPoolExecutor, concurrent.futures.ThreadPoolExecutor):

    def __init__(self, max_workers=None):
        super().__init__(max_workers)
        self.semaphore = threading.BoundedSemaphore(max_workers)






```

### 代码文件: funboost\concurrent_pool\bounded_processpoolexcutor_py36.py
```python
import multiprocessing
import concurrent.futures
import threading
from concurrent.futures.process import _ExceptionWithTraceback, _ResultItem  # noqa
from functools import wraps
import os

from funboost.core.loggers import get_funboost_file_logger

name = 'bounded_pool_executor'

logger = get_funboost_file_logger('BoundedProcessPoolExecutor')


def _process_worker(call_queue, result_queue):
    """Evaluates calls from call_queue and places the results in result_queue.

    This worker is run in a separate process.

    Args:
        call_queue: A multiprocessing.Queue of _CallItems that will be read and
            evaluated by the worker.
        result_queue: A multiprocessing.Queue of _ResultItems that will written
            to by the worker.
        shutdown: A multiprocessing.Event that will be set as a signal to the
            worker that it should exit when call_queue is empty.
    """
    while True:
        call_item = call_queue.get(block=True)
        if call_item is None:
            # Wake up queue management thread
            result_queue.put(os.getpid())
            return
        try:
            r = call_item.fn(*call_item.args, **call_item.kwargs)
        except BaseException as e:
            exc = _ExceptionWithTraceback(e, e.__traceback__)
            result_queue.put(_ResultItem(call_item.work_id, exception=exc))
            logger.exception(e)  # 主要是直接显示错误。
        else:
            result_queue.put(_ResultItem(call_item.work_id,
                                         result=r))


def _deco(f):
    @wraps(f)
    def __deco(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except BaseException as e:
            logger.exception(e)

    return __deco


class _BoundedPoolExecutor:
    semaphore = None

    def acquire(self):
        self.semaphore.acquire()

    def release(self, fn):
        self.semaphore.release()

    def submit(self, fn, *args, **kwargs):
        self.acquire()
        future = super().submit(fn, *args, **kwargs)  # noqa
        future.add_done_callback(self.release)

        return future


class BoundedProcessPoolExecutor(_BoundedPoolExecutor, concurrent.futures.ProcessPoolExecutor):

    def __init__(self, max_workers=None):
        super().__init__(max_workers)
        self.semaphore = multiprocessing.BoundedSemaphore(max_workers)
        concurrent.futures.process._process_worker = _process_worker


class BoundedThreadPoolExecutor(_BoundedPoolExecutor, concurrent.futures.ThreadPoolExecutor):

    def __init__(self, max_workers=None):
        super().__init__(max_workers)
        self.semaphore = threading.BoundedSemaphore(max_workers)


def test_f(x):
    import time
    time.sleep(5)
    print(x * 10)
    1 / 0


if __name__ == '__main__':
    import nb_log

    # pool = BoundedProcessPoolExecutor(4)
    pool = BoundedThreadPoolExecutor(4)
    for i in range(10):
        print(i)
        pool.submit(test_f, i)
```

### 代码文件: funboost\concurrent_pool\bounded_threadpoolexcutor.py
```python
# coding=utf-8
"""
一个有界任务队列的thradpoolexcutor
直接捕获错误日志
"""
from functools import wraps
import queue
from concurrent.futures import ThreadPoolExecutor, Future
# noinspection PyProtectedMember
from concurrent.futures.thread import _WorkItem  # noqa

from funboost.concurrent_pool import FunboostBaseConcurrentPool
from funboost.core.loggers import get_funboost_file_logger

logger = get_funboost_file_logger('BoundedThreadPoolExecutor')


def _deco(f):
    @wraps(f)
    def __deco(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except BaseException as e:
            logger.exception(e)

    return __deco if f is not None else f


class BoundedThreadPoolExecutor(ThreadPoolExecutor,FunboostBaseConcurrentPool ):
    def __init__(self, max_workers=None, thread_name_prefix=''):
        ThreadPoolExecutor.__init__(self, max_workers, thread_name_prefix)
        self._work_queue = queue.Queue(max_workers * 2)

    def submit(self, fn, *args, **kwargs):
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('cannot schedule new futures after shutdown')
            f = Future()
            fn_deco = _deco(fn)
            w = _WorkItem(f, fn_deco, args, kwargs)
            self._work_queue.put(w)
            self._adjust_thread_count()
            return f


if __name__ == '__main__':
    def fun():
        print(1 / 0.2)

    # 如果是官方线程池，这样不报错你还以为代码没毛病呢。
    with BoundedThreadPoolExecutor(10) as pool:
        for i in range(20):
            pool.submit(fun)

```

### 代码文件: funboost\concurrent_pool\concurrent_pool_with_multi_process.py
```python
import time
import multiprocessing
import threading
import asyncio
from funboost.core.loggers import FunboostFileLoggerMixin
import atexit
import os
import typing
from funboost.concurrent_pool.custom_threadpool_executor import CustomThreadpoolExecutor

from funboost.concurrent_pool.async_pool_executor import AsyncPoolExecutor


class ConcurrentPoolWithProcess(FunboostFileLoggerMixin):
    def _start_a_pool(self, pool_class, max_works):
        pool = pool_class(max_works)
        while True:
            func, args, kwargs = self._multi_process_queue.get()  # 结束可以放None，然后这里判断，终止。或者joinable queue
            print(func, args, kwargs)
            pool.submit(func, *args, **kwargs)

    def __init__(self, pool_class: typing.Type = CustomThreadpoolExecutor, max_works=500, process_num=1):
        self._multi_process_queue = multiprocessing.Queue(100)
        for _ in range(process_num):
            multiprocessing.Process(target=self._start_a_pool, args=(pool_class, max_works), daemon=False).start()

    # noinspection PyUnusedLocal
    def _queue_call_back(self, result):
        self._multi_process_queue.task_done()

    def submit(self, func, *args, **kwargs):
        self._multi_process_queue.put((func, args, kwargs))

    def shutdown(self, wait=True):
        pass


def test_f(x):
    time.sleep(1)
    print(x * 10, os.getpid())


async def async_f(x):
    await asyncio.sleep(1)
    print(x * 10)


if __name__ == '__main__':
    pool = ConcurrentPoolWithProcess(AsyncPoolExecutor, 20, 2)
    # pool = GeventPoolExecutor(200,)

    # time.sleep(15)
    for i in range(1000):
        time.sleep(0.1)
        pool.submit(async_f, i)

```

### 代码文件: funboost\concurrent_pool\custom_evenlet_pool_executor.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/7/3 10:35
import atexit
import time
import warnings
# from eventlet import greenpool, monkey_patch, patcher, Timeout

from funboost.concurrent_pool import FunboostBaseConcurrentPool
from funboost.core.loggers import get_funboost_file_logger
# print('eventlet 导入')
from funboost.core.lazy_impoter import EventletImporter


def check_evenlet_monkey_patch(raise_exc=True):
    try:
        if not EventletImporter().patcher.is_monkey_patched('socket'):  # 随便选一个检测标志
            if raise_exc:
                warnings.warn(f'检测到没有打 evenlet 包的猴子补丁 ,请在起始脚本文件首行加上     import eventlet;eventlet.monkey_patch(all=True) ')
                raise Exception('检测到没有打 evenlet 包的猴子补丁 ,请在起始脚本文件首行加上    import eventlet;eventlet.monkey_patch(all=True)')
        else:
            return 1
    except ModuleNotFoundError:
        if raise_exc:
            warnings.warn(f'检测到没有打 evenlet 包的猴子补丁 ,请在起始脚本文件首行加上     import eventlet;eventlet.monkey_patch(all=True) ')
            raise Exception('检测到没有打 evenlet 包的猴子补丁 ,请在起始脚本文件首行加上    import eventlet;eventlet.monkey_patch(all=True)')


logger_evenlet_timeout_deco = get_funboost_file_logger('evenlet_timeout_deco')


def evenlet_timeout_deco(timeout_t):
    def _evenlet_timeout_deco(f):
        def __evenlet_timeout_deco(*args, **kwargs):
            timeout = EventletImporter().Timeout(timeout_t, )
            # timeout.start()  # 与gevent不一样,直接start了。
            result = None
            try:
                result = f(*args, **kwargs)
            except EventletImporter().Timeout as t:
                logger_evenlet_timeout_deco.error(f'函数 {f} 运行超过了 {timeout_t} 秒')
                if t is not timeout:
                    print(t)
                    # raise  # not my timeout
            finally:
                timeout.cancel()
                return result

        return __evenlet_timeout_deco

    return _evenlet_timeout_deco


def get_eventlet_pool_executor(*args2, **kwargs2):
    class CustomEventletPoolExecutor(EventletImporter().greenpool.GreenPool, FunboostBaseConcurrentPool):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            check_evenlet_monkey_patch()  # basecomer.py中检查。
            atexit.register(self.shutdown)

        def submit(self, *args, **kwargs):  # 保持为一直的公有用法。
            # nb_print(args)
            self.spawn_n(*args, **kwargs)
            # self.spawn_n(*args, **kwargs)

        def shutdown(self):
            self.waitall()

    return CustomEventletPoolExecutor(*args2, **kwargs2)


if __name__ == '__main__':
    # greenpool.GreenPool.waitall()
    EventletImporter().monkey_patch(all=True)


    def f2(x):

        time.sleep(2)
        print(x)


    pool = get_eventlet_pool_executor(4)

    for i in range(15):
        print(f'放入{i}')
        pool.submit(evenlet_timeout_deco(8)(f2), i)

```

### 代码文件: funboost\concurrent_pool\custom_gevent_pool_executor.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/7/2 14:11
import atexit
import time
import warnings
# from collections import Callable
from typing import Callable
import threading
from funboost.core.lazy_impoter import GeventImporter

# from nb_log import LoggerMixin, nb_print, LogManager
from funboost.concurrent_pool import FunboostBaseConcurrentPool
from funboost.core.loggers import get_funboost_file_logger, FunboostFileLoggerMixin


# print('gevent 导入')

def check_gevent_monkey_patch(raise_exc=True):
    try:
        if not GeventImporter().monkey.is_module_patched('socket'):  # 随便选一个检测标志
            if raise_exc:
                warnings.warn(f'检测到 你还没有打gevent包的猴子补丁，请在所运行的起始脚本第一行写上  【import gevent.monkey;gevent.monkey.patch_all()】  这句话。')
                raise Exception(f'检测到 你还没有打gevent包的猴子补丁，请在所运行的起始脚本第一行写上  【import gevent.monkey;gevent.monkey.patch_all()】  这句话。')
        else:
            return 1
    except ModuleNotFoundError:
        if raise_exc:
            warnings.warn(f'检测到 你还没有打gevent包的猴子补丁，请在所运行的起始脚本第一行写上  【import gevent.monkey;gevent.monkey.patch_all()】  这句话。')
            raise Exception(f'检测到 你还没有打gevent包的猴子补丁，请在所运行的起始脚本第一行写上  【import gevent.monkey;gevent.monkey.patch_all()】  这句话。')


logger_gevent_timeout_deco = get_funboost_file_logger('gevent_timeout_deco')


def gevent_timeout_deco(timeout_t):
    def _gevent_timeout_deco(f):
        def __gevent_timeout_deceo(*args, **kwargs):
            timeout = GeventImporter().gevent.Timeout(timeout_t, )
            timeout.start()
            result = None
            try:
                result = f(*args, **kwargs)
            except GeventImporter().gevent.Timeout as t:
                logger_gevent_timeout_deco.error(f'函数 {f} 运行超过了 {timeout_t} 秒')
                if t is not timeout:
                    print(t)
                    # raise  # not my timeout
            finally:
                timeout.close()
                return result

        return __gevent_timeout_deceo

    return _gevent_timeout_deco


def get_gevent_pool_executor(size=None, greenlet_class=None):
    class GeventPoolExecutor(GeventImporter().gevent_pool.Pool, FunboostBaseConcurrentPool):
        def __init__(self, size2=None, greenlet_class2=None):
            check_gevent_monkey_patch()  # basecomer.py中检查。
            super().__init__(size2, greenlet_class2)
            atexit.register(self.shutdown)

        def submit(self, *args, **kwargs):
            self.spawn(*args, **kwargs)

        def shutdown(self):
            self.join()

    return GeventPoolExecutor(size, greenlet_class)


class GeventPoolExecutor2(FunboostFileLoggerMixin, FunboostBaseConcurrentPool):
    def __init__(self, max_works, ):
        self._q = GeventImporter().JoinableQueue(maxsize=max_works)
        # self._q = Queue(maxsize=max_works)
        for _ in range(max_works):
            GeventImporter().gevent.spawn(self.__worker)
        # atexit.register(self.__atexit)
        self._q.join(timeout=100)

    def __worker(self):
        while True:
            fn, args, kwargs = self._q.get()
            try:
                fn(*args, **kwargs)
            except BaseException as exc:
                self.logger.exception(f'函数 {fn.__name__} 中发生错误，错误原因是 {type(exc)} {exc} ')
            finally:
                pass
                self._q.task_done()

    def submit(self, fn: Callable, *args, **kwargs):
        self._q.put((fn, args, kwargs))

    def __atexit(self):
        self.logger.critical('想即将退出程序。')
        self._q.join()


class GeventPoolExecutor3(FunboostFileLoggerMixin, FunboostBaseConcurrentPool):
    def __init__(self, max_works, ):
        self._q = GeventImporter().gevent.queue.Queue(max_works)
        self.g_list = []
        for _ in range(max_works):
            self.g_list.append(GeventImporter().gevent.spawn(self.__worker))
        atexit.register(self.__atexit)

    def __worker(self):
        while True:
            fn, args, kwargs = self._q.get()
            try:
                fn(*args, **kwargs)
            except BaseException as exc:
                self.logger.exception(f'函数 {fn.__name__} 中发生错误，错误原因是 {type(exc)} {exc} ')

    def submit(self, fn: Callable, *args, **kwargs):
        self._q.put((fn, args, kwargs))

    def joinall(self):
        GeventImporter().gevent.joinall(self.g_list)

    def joinall_in_new_thread(self):
        threading.Thread(target=self.joinall)

    def __atexit(self):
        self.logger.critical('想即将退出程序。')
        self.joinall()


if __name__ == '__main__':
    GeventImporter().monkey.patch_all(thread=False)


    def f2(x):

        time.sleep(3)
        print(x * 10)


    pool = GeventPoolExecutor3(40)

    for i in range(20):
        time.sleep(0.1)
        print(f'放入{i}')
        pool.submit(gevent_timeout_deco(8)(f2), i)
    # pool.joinall_in_new_thread()
    print(66666666)

```

### 代码文件: funboost\concurrent_pool\custom_threadpool_executor.py
```python
"""
史上最强的python线程池。

最智能的可自动实时调节线程数量的线程池。此线程池和官方concurrent.futures的线程池 是鸭子类关系，所以可以一键替换类名 或者 import as来替换类名。
对比官方线程池，有4个创新功能或改进。

1、主要是不仅能扩大，还可自动缩小(官方内置的ThreadpoolExecutor不具备此功能，此概念是什么意思和目的，可以百度java ThreadpoolExecutor的KeepAliveTime参数的介绍)，
   例如实例化一个1000线程的线程池，上一分钟疯狂高频率的对线程池submit任务，线程池会扩张到最大线程数量火力全开运行，
   但之后的七八个小时平均每分钟只submit一两个任务，官方线程池会一直维持在1000线程，而此线程池会自动缩小，靠什么来识别预测啥时机可以自动缩小呢，就是KeepAliveTime。

2、非常节制的开启多线程，例如实例化一个最大100线程数目的pool，每隔2秒submit一个函数任务，而函数每次只需要1秒就能完成，实际上只需要调节增加到1个线程就可以，不需要慢慢增加到100个线程
官方的线程池不够智能，会一直增加到最大线程数目，此线程池则不会。

3、线程池任务的queue队列，修改为有界队列

4、此线程池运行函数出错时候，直接显示线程错误，官方的线程池则不会显示错误，例如函数中写1/0,任然不现实错误。

此实现了submit，还实现future相关的内容，真正的和内置的ThreadpoolExecutor 完全替代。

可以在各种地方加入 time.sleep 来验证 第1条和第2条的自动智能缩放功能。
"""
import logging

import os
import atexit
import queue
import sys
import threading
import time
import weakref

from funboost.concurrent_pool import FunboostBaseConcurrentPool
from nb_log import LoggerLevelSetterMixin
from funboost.core.loggers import FunboostFileLoggerMixin,get_funboost_file_logger
from concurrent.futures import Executor, Future



_shutdown = False
_threads_queues = weakref.WeakKeyDictionary()


def check_not_monkey():
    from funboost.concurrent_pool.custom_evenlet_pool_executor import check_evenlet_monkey_patch
    from funboost.concurrent_pool.custom_gevent_pool_executor import check_gevent_monkey_patch
    if check_gevent_monkey_patch(raise_exc=False):
        raise Exception('指定使用多线程模式时候，请不要打gevent包的补丁')
    if check_evenlet_monkey_patch(raise_exc=False):
        raise Exception('指定使用多线程模式时候，请不要打evenlet包的补丁')


def _python_exit():
    global _shutdown
    _shutdown = True
    items = list(_threads_queues.items())
    for t, q in items:
        q.put(None)
    for t, q in items:
        t.join()


atexit.register(_python_exit)


class _WorkItem(FunboostFileLoggerMixin):
    def __init__(self, future, fn, args, kwargs):
        self.future = future
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        # noinspection PyBroadException
        if not self.future.set_running_or_notify_cancel():
            return
        try:
            result = self.fn(*self.args, **self.kwargs)
        except BaseException as exc:
            self.logger.exception(f'函数 {self.fn.__name__} 中发生错误，错误原因是 {type(exc)} {exc} ')
            self.future.set_exception(exc)
            # Break a reference cycle with the exception 'exc'
            self = None  # noqa
        else:
            self.future.set_result(result)

    def __str__(self):
        return f'{(self.fn.__name__, self.args, self.kwargs)}'


def set_threadpool_executor_shrinkable(min_works=1, keep_alive_time=5):
    ThreadPoolExecutorShrinkAble.MIN_WORKERS = min_works
    ThreadPoolExecutorShrinkAble.KEEP_ALIVE_TIME = keep_alive_time


class ThreadPoolExecutorShrinkAble(Executor, FunboostFileLoggerMixin, LoggerLevelSetterMixin,FunboostBaseConcurrentPool):
    # 为了和官方自带的THredpoolexecutor保持完全一致的鸭子类，参数设置成死的，不让用户传参了。
    # 建议用猴子补丁修改这两个参数，为了保持入参api和内置的concurrent.futures 相同。
    # MIN_WORKERS = 5   # 最小值可以设置为0，代表线程池无论多久没有任务最少要保持多少个线程待命。
    # KEEP_ALIVE_TIME = 60  # 这个参数表名，当前线程从queue.get(block=True, timeout=KEEP_ALIVE_TIME)多久没任务，就线程结束。

    MIN_WORKERS = 1
    KEEP_ALIVE_TIME = 60

    def __init__(self, max_workers: int = None, thread_name_prefix='',work_queue_maxsize=10):
        """
        最好需要兼容官方concurren.futures.ThreadPoolExecutor 和改版的BoundedThreadPoolExecutor，入参名字和个数保持了一致。
        :param max_workers:
        :param thread_name_prefix:
        """
        # print(max_workers)
        self._max_workers = max_workers or (os.cpu_count() or 1) * 5
        self._thread_name_prefix = thread_name_prefix
        # print(self._max_workers)
        # self.work_queue = self._work_queue = queue.Queue(self._max_workers or 10)
        self.work_queue = self._work_queue = queue.Queue(work_queue_maxsize)
        # self._threads = set()
        self._threads = weakref.WeakSet()
        self._lock_compute_threads_free_count = threading.Lock()
        self.threads_free_count = 0
        self._shutdown = False
        self._shutdown_lock = threading.Lock()
        self.pool_ident = id(self)

    def _change_threads_free_count(self, change_num):
        with self._lock_compute_threads_free_count:
            self.threads_free_count += change_num

    def submit(self, func, *args, **kwargs):
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('不能添加新的任务到线程池')
            f = Future()
            w = _WorkItem(f, func, args, kwargs)
            self.work_queue.put(w)
            self._adjust_thread_count()
            return f

    def _adjust_thread_count(self):
        # print(self.threads_free_count, self.MIN_WORKERS, len(self._threads), self._max_workers)
        if self.threads_free_count <= self.MIN_WORKERS and len(self._threads) < self._max_workers:
            t = _CustomThread(self).set_log_level(self.logger.level)
            t.daemon = True
            t.start()
            self._threads.add(t)
            _threads_queues[t] = self._work_queue

    def shutdown(self, wait=True):  # noqa
        with self._shutdown_lock:
            self._shutdown = True
            self.work_queue.put(None)
        if wait:
            for t in self._threads:
                t.join()




# 两个名字都可以，兼容以前的老名字（中文意思是 自定义线程池），但新名字更能表达意思（可缩小线程池）。
CustomThreadpoolExecutor = CustomThreadPoolExecutor = ThreadPoolExecutorShrinkAble


# noinspection PyProtectedMember
class _CustomThread(threading.Thread, FunboostFileLoggerMixin, LoggerLevelSetterMixin):
    _lock_for_judge_threads_free_count = threading.Lock()

    def __init__(self, executorx: ThreadPoolExecutorShrinkAble):
        super().__init__()
        self._executorx = executorx

    def _remove_thread(self, stop_resson=''):
        # noinspection PyUnresolvedReferences
        self.logger.debug(f'停止线程 {self._ident}, 触发条件是 {stop_resson} ')
        self._executorx._change_threads_free_count(-1)
        self._executorx._threads.remove(self)
        _threads_queues.pop(self)

    # noinspection PyProtectedMember
    def run(self):
        # noinspection PyUnresolvedReferences
        # print(logging.getLogger(None).level,logging.getLogger(None).handlers)
        # print(self.logger.level)
        # print(self.logger.handlers)
        self.logger.debug(f'新启动线程 {self._ident} ')
        self._executorx._change_threads_free_count(1)
        while True:
            try:
                work_item = self._executorx.work_queue.get(block=True, timeout=self._executorx.KEEP_ALIVE_TIME)
            except queue.Empty:
                # continue
                # self._remove_thread()
                with self._lock_for_judge_threads_free_count:
                    if self._executorx.threads_free_count > self._executorx.MIN_WORKERS:
                        self._remove_thread(
                            f'{self._executorx.pool_ident} 线程池中的 {self.ident} 线程 超过 {self._executorx.KEEP_ALIVE_TIME} 秒没有任务，线程池中不在工作状态中的线程数量是 '
                            f'{self._executorx.threads_free_count}，超过了指定的最小核心数量 {self._executorx.MIN_WORKERS}')
                        break  # 退出while 1，即是结束。这里才是决定线程结束销毁，_remove_thread只是个名字而已，不是由那个来销毁线程。
                    else:
                        continue

            if work_item is not None:
                self._executorx._change_threads_free_count(-1)
                work_item.run()
                del work_item
                self._executorx._change_threads_free_count(1)
                continue
            if _shutdown or self._executorx._shutdown:
                self._executorx.work_queue.put(None)
                break


process_name_set = set()
logger_show_current_threads_num = get_funboost_file_logger('show_current_threads_num',formatter_template=5, do_not_use_color_handler=False)


def show_current_threads_num(sleep_time=600, process_name='', block=False, daemon=True):
    """另起一个线程每隔多少秒打印有多少线程，这个和可缩小线程池的实现没有关系"""
    process_name = sys.argv[0] if process_name == '' else process_name

    def _show_current_threads_num():
        while True:
            # logger_show_current_threads_num.info(f'{process_name} 进程 的 并发数量是 -->  {threading.active_count()}')
            # nb_print(f'  {process_name} {os.getpid()} 进程 的 线程数量是 -->  {threading.active_count()}')
            logger_show_current_threads_num.info(
                f'  {process_name} {os.getpid()} 进程 的 总线程数量是 -->  {threading.active_count()}')
            time.sleep(sleep_time)

    if process_name not in process_name_set:
        if block:
            _show_current_threads_num()
        else:
            t = threading.Thread(target=_show_current_threads_num, daemon=daemon)
            t.start()
        process_name_set.add(process_name)


def get_current_threads_num():
    return threading.active_count()


if __name__ == '__main__':
    show_current_threads_num(sleep_time=5)


    def f1(a):
        time.sleep(0.2)  # 可修改这个数字测试多线程数量调节功能。
        print(f'{a} 。。。。。。。')
        return a * 10
        # raise Exception('抛个错误测试')  # 官方的不会显示函数出错你，你还以为你写的代码没毛病呢。


    pool = ThreadPoolExecutorShrinkAble(1)
    # pool = ThreadPoolExecutor(200)  # 测试对比官方自带

    for i in range(30):
        time.sleep(0.1)  # 这里的间隔时间模拟，当任务来临不密集，只需要少量线程就能搞定f1了，因为f1的消耗时间短，
        # 不需要开那么多线程，CustomThreadPoolExecutor比ThreadPoolExecutor 优势之一。
        futurex = pool.submit(f1, i)
        # print(futurex.result())

    # 1/下面测试阻塞主线程退出的情况。注释掉可以测主线程退出的情况。
    # 2/此代码可以证明，在一段时间后，连续长时间没任务，官方线程池的线程数目还是保持在最大数量了。而此线程池会自动缩小，实现了java线程池的keppalivetime功能。
    time.sleep(1000000)

```

### 代码文件: funboost\concurrent_pool\custom_threadpool_executor000.py
```python
"""
可自动实时调节线程数量的线程池。
比官方ThreadpoolExecutor的改进是
1.有界队列
2.实时调节线程数量，指的是当任务很少时候会去关闭很多线程。官方ThreadpoolExecurot只能做到忙时候开启很多线程，但不忙时候线程没有关闭线程，
此线程池实现了java ThreadpoolExecutor线程池的keppaliveTime参数的功能，linux系统能承受的线程总数有限，一般不到2万。
3.能非常智能节制的开启多线程。比如设置线程池大小为500，线程池的运行函数消耗时间是只需要0.1秒，如果每隔2秒钟来一个任务。1个线程足够了，官方线程池是一直增长到500，然后不增长，官方的太不智能了。

这个线程池是框架的默认线程方式的线程池，如果不设置并发方式就用的这里。

此实现了submit，但没实现future相关的内容。
"""

import atexit
import queue
import sys
import threading
import time
import weakref

from nb_log import LoggerMixin, nb_print, LoggerLevelSetterMixin, LogManager
from funboost.concurrent_pool.custom_evenlet_pool_executor import check_evenlet_monkey_patch
from funboost.concurrent_pool.custom_gevent_pool_executor import check_gevent_monkey_patch

_shutdown = False
_threads_queues = weakref.WeakKeyDictionary()


def _python_exit():
    global _shutdown
    _shutdown = True
    items = list(_threads_queues.items())
    for t, q in items:
        q.put(None)
    for t, q in items:
        t.join()


atexit.register(_python_exit)


class _WorkItem(LoggerMixin):
    def __init__(self, fn, args, kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        # noinspection PyBroadException
        try:
            self.fn(*self.args, **self.kwargs)
        except BaseException as exc:
            self.logger.exception(f'函数 {self.fn.__name__} 中发生错误，错误原因是 {type(exc)} {exc} ')

    def __str__(self):
        return f'{(self.fn.__name__, self.args, self.kwargs)}'


def check_not_monkey():
    if check_gevent_monkey_patch(raise_exc=False):
        raise Exception('请不要打gevent包的补丁')
    if check_evenlet_monkey_patch(raise_exc=False):
        raise Exception('请不要打evenlet包的补丁')


class CustomThreadPoolExecutor(LoggerMixin, LoggerLevelSetterMixin):
    def __init__(self, max_workers=None, thread_name_prefix=''):
        """
        最好需要兼容官方concurren.futures.ThreadPoolExecutor 和改版的BoundedThreadPoolExecutor，入参名字和个数保持了一致。
        :param max_workers:
        :param thread_name_prefix:
        """
        self._max_workers = max_workers or 4
        self._min_workers = 5  # 这是对应的 java Threadpoolexecutor的corePoolSize，为了保持线程池公有方法和与py官方内置的concurren.futures.ThreadPoolExecutor一致，不增加更多的实例化时候入参，这里写死为5.
        self._thread_name_prefix = thread_name_prefix
        self.work_queue = queue.Queue(max_workers)
        # self._threads = set()
        self._threads = weakref.WeakSet()
        self._lock_compute_threads_free_count = threading.Lock()
        self.threads_free_count = 0
        self._shutdown = False
        self._shutdown_lock = threading.Lock()
        # self.logger.setLevel(20)

    def set_min_workers(self, min_workers=10):
        self._min_workers = min_workers
        return self

    def change_threads_free_count(self, change_num):
        with self._lock_compute_threads_free_count:
            self.threads_free_count += change_num

    def submit(self, func, *args, **kwargs):
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('不能添加新的任务到线程池')
        self.work_queue.put(_WorkItem(func, args, kwargs))
        self._adjust_thread_count()

    def _adjust_thread_count(self):
        # if len(self._threads) < self._threads_num:
        # self.logger.debug((self.threads_free_count, len(self._threads), len(_threads_queues), get_current_threads_num()))
        if self.threads_free_count < self._min_workers and len(self._threads) < self._max_workers:
            # t = threading.Thread(target=_work,
            #                      args=(self._work_queue,self))
            t = _CustomThread(self).set_log_level(self.logger.level)
            t.setDaemon(True)
            t.start()
            self._threads.add(t)
            _threads_queues[t] = self.work_queue

    def shutdown(self, wait=True):
        with self._shutdown_lock:
            self._shutdown = True
            self.work_queue.put(None)
        if wait:
            for t in self._threads:
                t.join()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown(wait=True)
        return False


class _CustomThread(threading.Thread, LoggerMixin, LoggerLevelSetterMixin):
    _lock_for_judge_threads_free_count = threading.Lock()

    def __init__(self, executorx: CustomThreadPoolExecutor):
        super().__init__()
        self._executorx = executorx
        self._run_times = 0

    # noinspection PyProtectedMember
    def _remove_thread(self, stop_resson=''):
        # noinspection PyUnresolvedReferences
        self.logger.debug(f'停止线程 {self._ident}, 触发条件是 {stop_resson} ')
        self._executorx.change_threads_free_count(-1)
        self._executorx._threads.remove(self)
        _threads_queues.pop(self)

    # noinspection PyProtectedMember
    def run(self):
        # noinspection PyUnresolvedReferences
        self.logger.debug(f'新启动线程 {self._ident} ')
        self._executorx.change_threads_free_count(1)
        while True:
            try:
                work_item = self._executorx.work_queue.get(block=True, timeout=60)
            except queue.Empty:
                with self._lock_for_judge_threads_free_count:
                    if self._executorx.threads_free_count > self._executorx._min_workers:
                        self._remove_thread(f'当前线程超过60秒没有任务，线程池中不在工作状态中的线程数量是 {self._executorx.threads_free_count}，超过了指定的数量 {self._executorx._min_workers}')
                        break  # 退出while 1，即是结束。这里才是决定线程结束销毁，_remove_thread只是个名字而已，不是由那个来销毁线程。
                    else:
                        continue

            # nb_print(work_item)
            if work_item is not None:
                self._executorx.change_threads_free_count(-1)
                work_item.run()
                del work_item
                self._executorx.change_threads_free_count(1)
                continue
            if _shutdown or self._executorx._shutdown:
                self._executorx.work_queue.put(None)
                break


process_name_set = set()
logger_show_current_threads_num = LogManager('show_current_threads_num').get_logger_and_add_handlers(
    formatter_template=5, log_filename='show_current_threads_num.log', do_not_use_color_handler=True)


def show_current_threads_num(sleep_time=60, process_name='', block=False):
    process_name = sys.argv[0] if process_name == '' else process_name

    def _show_current_threads_num():
        while True:
            # logger_show_current_threads_num.info(f'{process_name} 进程 的 并发数量是 -->  {threading.active_count()}')
            nb_print(f'{process_name} 进程 的 线程数量是 -->  {threading.active_count()}')
            time.sleep(sleep_time)

    if process_name not in process_name_set:
        if block:
            _show_current_threads_num()
        else:
            t = threading.Thread(target=_show_current_threads_num, daemon=True)
            t.start()
        process_name_set.add(process_name)


def get_current_threads_num():
    return threading.active_count()


if __name__ == '__main__':
    from funboost.utils import decorators
    from funboost.concurrent_pool.bounded_threadpoolexcutor import BoundedThreadPoolExecutor


    # @decorators.keep_circulating(1)
    def f1(a):
        time.sleep(0.2)
        nb_print(f'{a} 。。。。。。。')
        # raise Exception('抛个错误测试')


    # show_current_threads_num()
    pool = CustomThreadPoolExecutor(200).set_log_level(10).set_min_workers()
    # pool = BoundedThreadPoolExecutor(200)   # 测试对比原来写的BoundedThreadPoolExecutor
    show_current_threads_num(sleep_time=5)
    for i in range(300):
        time.sleep(0.3)  # 这里的间隔时间模拟，当任务来临不密集，只需要少量线程就能搞定f1了，因为f1的消耗时间短，不需要开那么多线程，CustomThreadPoolExecutor比BoundedThreadPoolExecutor 优势之一。
        pool.submit(f1, str(i))

    nb_print(6666)
    # pool.shutdown(wait=True)
    pool.submit(f1, 'yyyy')

    # 下面测试阻塞主线程退出的情况。注释掉可以测主线程退出的情况。
    while True:
        time.sleep(10)

```

### 代码文件: funboost\concurrent_pool\fixed_thread_pool.py
```python
"""
flxed_thread_pool.py 固定大小的非智能线程池, 最简单的粗暴实现线程池方式,任何人都可以写得出来.
弊端是代码不会自动结束,因为线程池的每个线程 while 1是非守护线程,不能自动判断代码是否需要结束.
如果有的人的代码是长期运行不需要结束的,可以用这种线程池。
"""

import threading
import traceback
from queue import Queue
# import nb_log
from funboost.concurrent_pool import FunboostBaseConcurrentPool
from funboost.core.loggers import FunboostFileLoggerMixin


class FixedThreadPool(FunboostFileLoggerMixin,FunboostBaseConcurrentPool):
    def __init__(self, max_workers: int = 8):
        self._max_workers = max_workers
        self._work_queue = Queue(maxsize=10)
        self._start_thrads()

    def submit(self, func, *args, **kwargs):
        self._work_queue.put([func, args, kwargs])

    def _forever_fun(self):
        while True:
            func, args, kwargs = self._work_queue.get()
            try:
                func(*args, **kwargs)
            except BaseException as e:
                self.logger.error(f'func:{func}, args:{args}, kwargs:{kwargs} exc_type:{type(e)}  traceback_exc:{traceback.format_exc()}')

    def _start_thrads(self):
        for i in range(self._max_workers):
            threading.Thread(target=self._forever_fun).start()


if __name__ == '__main__':
    def f3(x):
        # time.sleep(1)
        # 1 / 0
        if x % 10000 == 0:
            print(x)


    pool = FixedThreadPool(100)
    for j in range(10):
        pool.submit(f3, j)

```

### 代码文件: funboost\concurrent_pool\flexible_thread_pool.py
```python
"""
比 ThreadPoolExecutorShrinkAble 更简单的的弹性线程池。完全彻底从头手工开发

这个线程池 submit没有返回值，不返回future对象，不支持map方法。

此线程池性能比concurrent.futures.ThreadPoolExecutor高200%

顺便兼容asyns def的函数并发运行
"""

import asyncio
import inspect
import os
import queue
import threading
from functools import wraps

from funboost.concurrent_pool import FunboostBaseConcurrentPool
from funboost.core.loggers import FunboostFileLoggerMixin, LoggerLevelSetterMixin, FunboostMetaTypeFileLogger


class FlexibleThreadPool(FunboostFileLoggerMixin, LoggerLevelSetterMixin, FunboostBaseConcurrentPool):
    KEEP_ALIVE_TIME = 10
    MIN_WORKERS = 1

    def __init__(self, max_workers: int = None,work_queue_maxsize=10):
        self.work_queue = queue.Queue(work_queue_maxsize)
        self.max_workers = max_workers
        self._threads_num = 0
        self.threads_free_count = 0
        self._lock_compute_start_thread = threading.Lock()
        self._lock_compute_threads_free_count = threading.Lock()
        self._lock_for_adjust_thread = threading.Lock()
        self._lock_for_judge_threads_free_count = threading.Lock()
        self.pool_ident = id(self)
        # self.asyncio_loop = asyncio.new_event_loop()

    def _change_threads_free_count(self, change_num):
        with self._lock_compute_threads_free_count:
            self.threads_free_count += change_num

    def _change_threads_start_count(self, change_num):
        with self._lock_compute_start_thread:
            self._threads_num += change_num

    def submit(self, func, *args, **kwargs):
        self.work_queue.put([func, args, kwargs])
        with self._lock_for_adjust_thread:
            if self.threads_free_count <= self.MIN_WORKERS and self._threads_num < self.max_workers:
                _KeepAliveTimeThread(self).start()


class FlexibleThreadPoolMinWorkers0(FlexibleThreadPool):
    MIN_WORKERS = 0


def run_sync_or_async_fun000(func, *args, **kwargs):
    """这种方式造成电脑很卡,不行"""
    fun_is_asyncio = inspect.iscoroutinefunction(func)
    if fun_is_asyncio:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            loop.close()
    else:
        return func(*args, **kwargs)


tl = threading.local()


def _get_thread_local_loop() -> asyncio.AbstractEventLoop:
    if not hasattr(tl, 'asyncio_loop'):
        tl.asyncio_loop = asyncio.new_event_loop()
    return tl.asyncio_loop


def run_sync_or_async_fun(func, *args, **kwargs):
    fun_is_asyncio = inspect.iscoroutinefunction(func)
    if fun_is_asyncio:
        loop = _get_thread_local_loop()
        try:
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            pass
            # loop.close()
    else:
        return func(*args, **kwargs)


def sync_or_async_fun_deco(func):
    @wraps(func)
    def _inner(*args, **kwargs):
        return run_sync_or_async_fun(func, *args, **kwargs)

    return _inner


# noinspection PyProtectedMember
class _KeepAliveTimeThread(threading.Thread, metaclass=FunboostMetaTypeFileLogger):
    def __init__(self, thread_pool: FlexibleThreadPool):
        super().__init__()
        self.pool = thread_pool

    def run(self) -> None:
        # 可以设置 LogManager('_KeepAliveTimeThread').preset_log_level(logging.INFO) 来屏蔽下面的话,见文档6.17.b
        self.logger.debug(f'新启动线程 {self.ident} ')
        self.pool._change_threads_free_count(1)
        self.pool._change_threads_start_count(1)
        while 1:
            try:
                func, args, kwargs = self.pool.work_queue.get(block=True, timeout=self.pool.KEEP_ALIVE_TIME)
            except queue.Empty:
                with self.pool._lock_for_judge_threads_free_count:
                    # print(self.pool.threads_free_count)
                    if self.pool.threads_free_count > self.pool.MIN_WORKERS:
                        # 可以设置 LogManager('_KeepAliveTimeThread').preset_log_level(logging.INFO) 来屏蔽下面的话,见文档6.17.b
                        self.logger.debug(f'停止线程 {self._ident}, 触发条件是 {self.pool.pool_ident} 线程池中的 {self.ident} 线程 超过 {self.pool.KEEP_ALIVE_TIME} 秒没有任务，线程池中不在工作状态中的线程数量是 {self.pool.threads_free_count}，超过了指定的最小核心数量 {self.pool.MIN_WORKERS}')  # noqa
                        self.pool._change_threads_free_count(-1)
                        self.pool._change_threads_start_count(-1)
                        break  # 退出while 1，即是结束。
                    else:
                        continue
            self.pool._change_threads_free_count(-1)
            try:
                fun = sync_or_async_fun_deco(func)
                fun(*args, **kwargs)
            except BaseException as exc:
                self.logger.exception(f'函数 {func.__name__} 中发生错误，错误原因是 {type(exc)} {exc} ')
            self.pool._change_threads_free_count(1)





if __name__ == '__main__':
    import time
    from concurrent.futures import ThreadPoolExecutor
    from custom_threadpool_executor import ThreadPoolExecutorShrinkAble


    def testf(x):
        # time.sleep(10)
        if x % 10000 == 0:
            print(x)


    async def aiotestf(x):
        # await asyncio.sleep(1)
        if x % 10 == 0 or 1:
            print(x)
        return x * 2


    pool = FlexibleThreadPool(100)
    # pool = ThreadPoolExecutor(100)
    # pool = ThreadPoolExecutorShrinkAble(100)

    for i in range(20000):
        # time.sleep(2)
        pool.submit(aiotestf, i)

    # for i in range(100000):
    #     pool.submit(testf, i)

    # while 1:
    #     time.sleep(1000)
    # loop.run_forever()

```

### 代码文件: funboost\concurrent_pool\pool_commons.py
```python
import functools
import threading
import typing
import os

from funboost.concurrent_pool.flexible_thread_pool import FlexibleThreadPool
from funboost.concurrent_pool.base_pool_type import FunboostBaseConcurrentPool


class ConcurrentPoolBuilder:
    _pid__pool_map = {}
    _lock = threading.Lock()

    @classmethod
    def get_pool(cls, pool_type: typing.Type[FunboostBaseConcurrentPool], max_workers: int = None):
        key = (os.getpid(), pool_type)
        with cls._lock:
            if key not in cls._pid__pool_map:
                pool = pool_type(max_workers)  # noqa
                cls._pid__pool_map[key] = pool
            return cls._pid__pool_map[key]


if __name__ == '__main__':
    for i in range(10):
        pool = functools.partial(ConcurrentPoolBuilder.get_pool, FlexibleThreadPool, 200)()
        print(id(pool))

```

### 代码文件: funboost\concurrent_pool\readme.md
```python
####  这个里面是实现各种并发池，框架使用不同种类的并发池从而使用不同的并发模式来执行函数任务。


```python

'''
各种并发池的api都实现了submit，然后就自动执行函数。类似concurrent.futures包的api
'''


def fun(x):
    print(x)

pool = Pool(50)
pool.submit(fun,1)


```

```text
实现的池包括


gevent

eventlet

asyncio

custom_threadpool_executor.py 可变有界线程池,可变是指线程池嫩自动扩大，最厉害的是能自动缩小线程数量，官方不具备此功能。
如果线程池submit任务稀疏，即使设置500并发，但不会开到500线程，官方不具备此功能。 


flexible_thread_pool.py  从新开始写的，完全没有任何官方半点代码的线程池，和 custom_threadpool_executor.py 功能一样，
可变有界线程池，可以自动扩大也能自动缩小，增加了支持运行 async def 的函数。


flxed_thread_pool.py 固定大小的线程池, 最简单的实现线程池方式,任何人都可以写得出来.弊端是代码不会自动结束,因为线程池的每个线程 while 1是非守护线程,不能自动判断代码是否需要结束.
如果有的人的代码是长期运行不需要结束的,可以用这种线程池
```


#### 框架的默认的多线程并发池是 flexible_thread_pool.py ，这个池能同时支持并发运行def 函数和async def函数。

#### 框架的默认的asyncio并发池是 AsyncPoolExecutor


```

### 代码文件: funboost\concurrent_pool\single_thread_executor.py
```python
from typing import Callable

from funboost.concurrent_pool import FunboostBaseConcurrentPool


class SoloExecutor(FunboostBaseConcurrentPool):
    # noinspection PyUnusedLocal
    def __init__(self, max_workers: int = 1):
        pass

    # noinspection PyMethodMayBeStatic
    def submit(self, fn: Callable, *args, **kwargs):
        return fn(*args, **kwargs)

    # noinspection PyMethodMayBeStatic
    def shutdown(self, wait=True):
        pass

```

### 代码文件: funboost\concurrent_pool\__init__.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 9:46
"""
并发池 包括
有界队列线程池 加 错误提示
eventlet协程
gevent协程
自定义的有界队列线程池 加 错误提示，同时线程数量在任务数量少的时候可自动减少。项目中默认使用的并发方式是基于这个。

此文件夹包括5种并发池，可以单独用于任何项目，即使没有使用这个函数调度框架。
"""
from .base_pool_type import FunboostBaseConcurrentPool
from .async_pool_executor import AsyncPoolExecutor
from .bounded_threadpoolexcutor import BoundedThreadPoolExecutor
from .custom_threadpool_executor import CustomThreadPoolExecutor
from .flexible_thread_pool import FlexibleThreadPool
from .pool_commons import ConcurrentPoolBuilder
```

### 代码文件: funboost\concurrent_pool\backup\async_pool_executor0223.py
```python
import atexit
import asyncio
import threading
import time
import traceback
from threading import Thread
import nb_log  # noqa

# if os.name == 'posix':
#     import uvloop
#
#     asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())  # 打猴子补丁最好放在代码顶层，否则很大机会出问题。

"""
# 也可以采用 janus 的 线程安全的queue方式来实现异步池，此queue性能和本模块实现的生产 消费相比，性能并没有提高，所以就不重新用这这个包来实现一次了。
import janus
import asyncio
import time
import threading
import nb_log
queue = janus.Queue(maxsize=6000)

async def consume():
    while 1:
        # time.sleep(1)
        val = await queue.async_q.get() # 这是async，不要看错了
        print(val)

def push():
    for i in range(50000):
        # time.sleep(0.2)
        # print(i)
        queue.sync_q.put(i)  # 这是sync。不要看错了。


if __name__ == '__main__':
    threading.Thread(target=push).start()
    loop = asyncio.get_event_loop()
    loop.create_task(consume())
    loop.run_forever()
"""


class AsyncPoolExecutor2:
    def __init__(self, size, loop=None):
        self._size = size
        self.loop = loop or asyncio.new_event_loop()
        self._sem = asyncio.Semaphore(self._size, loop=self.loop)
        # atexit.register(self.shutdown)
        Thread(target=self._start_loop_in_new_thread).start()

    def submit(self, func, *args, **kwargs):
        while self._sem.locked():
            time.sleep(0.001)
        asyncio.run_coroutine_threadsafe(self._run_func(func, *args, **kwargs), self.loop)

    async def _run_func(self, func, *args, **kwargs):
        async with self._sem:
            result = await func(*args, **kwargs)
            return result

    def _start_loop_in_new_thread(self, ):
        self.loop.run_forever()

    def shutdown(self):
        self.loop.stop()
        self.loop.close()


class AsyncPoolExecutor(nb_log.LoggerMixin):
    """
    使api和线程池一样，最好的性能做法是submit也弄成 async def，生产和消费在同一个线程同一个loop一起运行，但会对调用链路的兼容性产生破坏，从而调用方式不兼容线程池。
    """

    def __init__(self, size, loop=None):
        """

        :param size: 同时并发运行的协程任务数量。
        :param loop:
        """
        self._size = size
        self.loop = loop or asyncio.new_event_loop()
        self._sem = asyncio.Semaphore(self._size, )
        self._queue = asyncio.Queue(maxsize=size, )
        self._lock = threading.Lock()
        t = Thread(target=self._start_loop_in_new_thread,daemon=True)
        # t.setDaemon(True)  # 设置守护线程是为了有机会触发atexit，使程序自动结束，不用手动调用shutdown
        t.start()
        self._can_be_closed_flag = False
        atexit.register(self.shutdown)

        self._event = threading.Event()
        # print(self._event.is_set())
        self._event.set()

    def submit000(self, func, *args, **kwargs):
        # 这个性能比下面的采用 run_coroutine_threadsafe + result返回快了3倍多。
        with self._lock:
            while 1:
                if not self._queue.full():
                    self.loop.call_soon_threadsafe(self._queue.put_nowait, (func, args, kwargs))
                    break
                else:
                    time.sleep(0.01)

    def submit(self, func, *args, **kwargs):
        future = asyncio.run_coroutine_threadsafe(self._produce(func, *args, **kwargs), self.loop)  # 这个 run_coroutine_threadsafe 方法也有缺点，消耗的性能巨大。
        future.result()  # 阻止过快放入，放入超过队列大小后，使submit阻塞。

    async def _produce(self, func, *args, **kwargs):
        await self._queue.put((func, args, kwargs))

    async def _consume(self):
        while True:
            func, args, kwargs = await self._queue.get()
            if isinstance(func, str) and func.startswith('stop'):
                # self.logger.debug(func)
                break
            # noinspection PyBroadException,PyUnusedLocal
            try:
                await func(*args, **kwargs)
            except BaseException as e:
                traceback.print_exc()
            # self._queue.task_done()

    async def __run(self):
        for _ in range(self._size):
            asyncio.ensure_future(self._consume())

    def _start_loop_in_new_thread(self, ):
        # self._loop.run_until_complete(self.__run())  # 这种也可以。
        # self._loop.run_forever()

        # asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(asyncio.wait([self.loop.create_task(self._consume()) for _ in range(self._size)],))
        self._can_be_closed_flag = True

    def shutdown(self):
        if self.loop.is_running():  # 这个可能是atregster触发，也可能是用户手动调用，需要判断一下，不能关闭两次。
            for i in range(self._size):
                self.submit(f'stop{i}', )
            while not self._can_be_closed_flag:
                time.sleep(0.1)
            self.loop.stop()
            self.loop.close()
            print('关闭循环')


class AsyncProducerConsumer:
    """
    参考 https://asyncio.readthedocs.io/en/latest/producer_consumer.html 官方文档。
    A simple producer/consumer example, using an asyncio.Queue:
    """

    """
    边生产边消费。此框架没用到这个类，这个要求生产和消费在同一个线程里面，对原有同步方式的框架代码改造不方便。
    """

    def __init__(self, items, concurrent_num=200, consume_fun_specify=None):
        """

        :param items: 要消费的参数列表
        :param concurrent_num: 并发数量
        :param consume_fun_specify: 指定的异步消费函数对象，如果不指定就要继承并重写consume_fun函数。
        """
        self.queue = asyncio.Queue()
        self.items = items
        self.consumer_params.concurrent_num = concurrent_num
        self.consume_fun_specify = consume_fun_specify

    async def produce(self):
        for item in self.items:
            await self.queue.put(item)

    async def consume(self):
        while True:
            # wait for an item from the producer
            item = await self.queue.get()
            # process the item
            # print('consuming {}...'.format(item))
            # simulate i/o operation using sleep
            try:
                if self.consume_fun_specify:
                    await self.consume_fun_specify(item)
                else:
                    await self.consume_fun(item)
            except BaseException as e:
                print(e)

            # Notify the queue that the item has been processed
            self.queue.task_done()

    @staticmethod
    async def consume_fun(item):
        """
        要么继承此类重写此方法，要么在类的初始化时候指定consume_fun_specify为一个异步函数。
        :param item:
        :return:
        """
        print(item, '请重写 consume_fun 方法')
        await asyncio.sleep(1)

    async def __run(self):
        # schedule the consumer
        tasks = []
        for _ in range(self.consumer_params.concurrent_num):
            task = asyncio.ensure_future(self.consume())
            tasks.append(task)
        # run the producer and wait for completion
        await self.produce()
        # wait until the consumer has processed all items
        await self.queue.join()
        # the consumer is still awaiting for an item, cancel it
        for task in tasks:
            task.cancel()

    def start_run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__run())
        # loop.close()


if __name__ == '__main__':
    def test_async_pool_executor():
        from funboost.concurrent_pool import CustomThreadPoolExecutor as ThreadPoolExecutor
        # from concurrent.futures.thread import ThreadPoolExecutor
        # noinspection PyUnusedLocal
        async def f(x):
            # await asyncio.sleep(0.1)
            pass
            print('打印', x)
            # await asyncio.sleep(1)
            # raise Exception('aaa')

        def f2(x):
            pass
            # time.sleep(0.001)
            print('打印', x)

        print(1111)

        t1 = time.time()
        pool = AsyncPoolExecutor(20)
        # pool = ThreadPoolExecutor(200)  # 协程不能用线程池运行，否则压根不会执行print打印，对于一部函数 f(x)得到的是一个协程，必须进一步把协程编排成任务放在loop循环里面运行。
        for i in range(1, 501):
            print('放入', i)
            pool.submit(f, i)
        # time.sleep(5)
        # pool.submit(f, 'hi')
        # pool.submit(f, 'hi2')
        # pool.submit(f, 'hi3')
        # print(2222)
        pool.shutdown()
        print(time.time() - t1)


    async def _my_fun(item):
        print('嘻嘻', item)
        # await asyncio.sleep(1)


    def test_async_producer_consumer():
        AsyncProducerConsumer([i for i in range(100000)], concurrent_num=200, consume_fun_specify=_my_fun).start_run()
        print('over')


    test_async_pool_executor()
    # test_async_producer_consumer()

```

### 代码文件: funboost\concurrent_pool\backup\async_pool_executor_back.py
```python
import atexit
import asyncio
import threading
import time
import traceback
from threading import Thread
import nb_log

from funboost.concurrent_pool.async_helper import get_or_create_event_loop  # noqa

# if os.name == 'posix':
#     import uvloop
#
#     asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())  # 打猴子补丁最好放在代码顶层，否则很大机会出问题。

"""
# 也可以采用 janus 的 线程安全的queue方式来实现异步池，此queue性能和本模块实现的生产 消费相比，性能并没有提高，所以就不重新用这这个包来实现一次了。
import janus
import asyncio
import time
import threading
import nb_log
queue = janus.Queue(maxsize=6000)

async def consume():
    while 1:
        # time.sleep(1)
        val = await queue.async_q.get() # 这是async，不要看错了
        print(val)

def push():
    for i in range(50000):
        # time.sleep(0.2)
        # print(i)
        queue.sync_q.put(i)  # 这是sync。不要看错了。


if __name__ == '__main__':
    threading.Thread(target=push).start()
    loop = asyncio.get_event_loop()
    loop.create_task(consume())
    loop.run_forever()
"""


class AsyncPoolExecutor2:
    def __init__(self, size, loop=None):
        self._size = size
        self.loop = loop or asyncio.new_event_loop()
        self._sem = asyncio.Semaphore(self._size, loop=self.loop)
        # atexit.register(self.shutdown)
        Thread(target=self._start_loop_in_new_thread).start()

    def submit(self, func, *args, **kwargs):
        while self._sem.locked():
            time.sleep(0.001)
        asyncio.run_coroutine_threadsafe(self._run_func(func, *args, **kwargs), self.loop)

    async def _run_func(self, func, *args, **kwargs):
        async with self._sem:
            result = await func(*args, **kwargs)
            return result

    def _start_loop_in_new_thread(self, ):
        self.loop.run_forever()

    def shutdown(self):
        self.loop.stop()
        self.loop.close()


class AsyncPoolExecutor(nb_log.LoggerMixin):
    """
    使api和线程池一样，最好的性能做法是submit也弄成 async def，生产和消费在同一个线程同一个loop一起运行，但会对调用链路的兼容性产生破坏，从而调用方式不兼容线程池。
    """

    def __init__(self, size, loop=None):
        """

        :param size: 同时并发运行的协程任务数量。
        :param loop:
        """
        self._size = size
        self.loop = loop or asyncio.new_event_loop()
        self._sem = asyncio.Semaphore(self._size, loop=self.loop)
        self._queue = asyncio.Queue(maxsize=size, loop=self.loop)
        self._lock = threading.Lock()
        t = Thread(target=self._start_loop_in_new_thread,daemon=True)
        # t.setDaemon(True)  # 设置守护线程是为了有机会触发atexit，使程序自动结束，不用手动调用shutdown
        t.start()
        self._can_be_closed_flag = False
        atexit.register(self.shutdown)

        self._event = threading.Event()
        # print(self._event.is_set())
        self._event.set()

    def submit000(self, func, *args, **kwargs):
        # 这个性能比下面的采用 run_coroutine_threadsafe + result返回快了3倍多。
        with self._lock:
            while 1:
                if not self._queue.full():
                    self.loop.call_soon_threadsafe(self._queue.put_nowait, (func, args, kwargs))
                    break
                else:
                    time.sleep(0.01)

    def submit(self, func, *args, **kwargs):
        future = asyncio.run_coroutine_threadsafe(self._produce(func, *args, **kwargs), self.loop)  # 这个 run_coroutine_threadsafe 方法也有缺点，消耗的性能巨大。
        future.result()  # 阻止过快放入，放入超过队列大小后，使submit阻塞。

    async def _produce(self, func, *args, **kwargs):
        await self._queue.put((func, args, kwargs))

    async def _consume(self):
        while True:
            func, args, kwargs = await self._queue.get()
            if isinstance(func, str) and func.startswith('stop'):
                # self.logger.debug(func)
                break
            # noinspection PyBroadException,PyUnusedLocal
            try:
                await func(*args, **kwargs)
            except BaseException as e:
                traceback.print_exc()
            # self._queue.task_done()

    async def __run(self):
        for _ in range(self._size):
            asyncio.ensure_future(self._consume())

    def _start_loop_in_new_thread(self, ):
        # self._loop.run_until_complete(self.__run())  # 这种也可以。
        # self._loop.run_forever()

        # asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(asyncio.wait([self._consume() for _ in range(self._size)], loop=self.loop))
        self._can_be_closed_flag = True

    def shutdown(self):
        if self.loop.is_running():  # 这个可能是atregster触发，也可能是用户手动调用，需要判断一下，不能关闭两次。
            for i in range(self._size):
                self.submit(f'stop{i}', )
            while not self._can_be_closed_flag:
                time.sleep(0.1)
            self.loop.stop()
            self.loop.close()
            print('关闭循环')


class AsyncProducerConsumer:
    """
    参考 https://asyncio.readthedocs.io/en/latest/producer_consumer.html 官方文档。
    A simple producer/consumer example, using an asyncio.Queue:
    """

    """
    边生产边消费。此框架没用到这个类，这个要求生产和消费在同一个线程里面，对原有同步方式的框架代码改造不方便。
    """

    def __init__(self, items, concurrent_num=200, consume_fun_specify=None):
        """

        :param items: 要消费的参数列表
        :param concurrent_num: 并发数量
        :param consume_fun_specify: 指定的异步消费函数对象，如果不指定就要继承并重写consume_fun函数。
        """
        self.queue = asyncio.Queue()
        self.items = items
        self.consumer_params.concurrent_num = concurrent_num
        self.consume_fun_specify = consume_fun_specify

    async def produce(self):
        for item in self.items:
            await self.queue.put(item)

    async def consume(self):
        while True:
            # wait for an item from the producer
            item = await self.queue.get()
            # process the item
            # print('consuming {}...'.format(item))
            # simulate i/o operation using sleep
            try:
                if self.consume_fun_specify:
                    await self.consume_fun_specify(item)
                else:
                    await self.consume_fun(item)
            except BaseException as e:
                print(e)

            # Notify the queue that the item has been processed
            self.queue.task_done()

    @staticmethod
    async def consume_fun(item):
        """
        要么继承此类重写此方法，要么在类的初始化时候指定consume_fun_specify为一个异步函数。
        :param item:
        :return:
        """
        print(item, '请重写 consume_fun 方法')
        await asyncio.sleep(1)

    async def __run(self):
        # schedule the consumer
        tasks = []
        for _ in range(self.consumer_params.concurrent_num):
            task = asyncio.ensure_future(self.consume())
            tasks.append(task)
        # run the producer and wait for completion
        await self.produce()
        # wait until the consumer has processed all items
        await self.queue.join()
        # the consumer is still awaiting for an item, cancel it
        for task in tasks:
            task.cancel()

    def start_run(self):
        loop = get_or_create_event_loop()
        loop.run_until_complete(self.__run())
        # loop.close()


if __name__ == '__main__':
    def test_async_pool_executor():
        from funboost.concurrent_pool import CustomThreadPoolExecutor as ThreadPoolExecutor
        # from concurrent.futures.thread import ThreadPoolExecutor
        # noinspection PyUnusedLocal
        async def f(x):
            # await asyncio.sleep(0.1)
            pass
            print('打印', x)
            # await asyncio.sleep(1)
            # raise Exception('aaa')

        def f2(x):
            pass
            # time.sleep(0.001)
            print('打印', x)

        print(1111)

        t1 = time.time()
        pool = AsyncPoolExecutor(20)
        # pool = ThreadPoolExecutor(200)  # 协程不能用线程池运行，否则压根不会执行print打印，对于一部函数 f(x)得到的是一个协程，必须进一步把协程编排成任务放在loop循环里面运行。
        for i in range(1, 501):
            print('放入', i)
            pool.submit(f, i)
        # time.sleep(5)
        # pool.submit(f, 'hi')
        # pool.submit(f, 'hi2')
        # pool.submit(f, 'hi3')
        # print(2222)
        pool.shutdown()
        print(time.time() - t1)


    async def _my_fun(item):
        print('嘻嘻', item)
        # await asyncio.sleep(1)


    def test_async_producer_consumer():
        AsyncProducerConsumer([i for i in range(100000)], concurrent_num=200, consume_fun_specify=_my_fun).start_run()
        print('over')


    test_async_pool_executor()
    # test_async_producer_consumer()

```

### 代码文件: funboost\concurrent_pool\backup\async_pool_executor_janus.py
```python
import atexit
import asyncio
import threading
import time
import traceback
from threading import Thread
import nb_log  # noqa

# if os.name == 'posix':
#     import uvloop
#
#     asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())  # 打猴子补丁最好放在代码顶层，否则很大机会出问题。

"""
# 也可以采用 janus 的 线程安全的queue方式来实现异步池，此queue性能和本模块实现的生产 消费相比，性能并没有提高，所以就不重新用这这个包来实现一次了。
import janus
import asyncio
import time
import threading
import nb_log
queue = janus.Queue(maxsize=6000)

async def consume():
    while 1:
        # time.sleep(1)
        val = await queue.async_q.get() # 这是async，不要看错了
        print(val)

def push():
    for i in range(50000):
        # time.sleep(0.2)
        # print(i)
        queue.sync_q.put(i)  # 这是sync。不要看错了。


if __name__ == '__main__':
    threading.Thread(target=push).start()
    loop = asyncio.get_event_loop()
    loop.create_task(consume())
    loop.run_forever()
"""





class AsyncPoolExecutor(nb_log.LoggerMixin):
    """
    使api和线程池一样，最好的性能做法是submit也弄成 async def，生产和消费在同一个线程同一个loop一起运行，但会对调用链路的兼容性产生破坏，从而调用方式不兼容线程池。
    """

    def __init__(self, size, loop=None):
        """

        :param size: 同时并发运行的协程任务数量。
        :param loop:
        """
        self._size = size
        self.loop = loop or asyncio.new_event_loop()
        self.queue = janus.Queue(maxsize=6000)
        self._lock = threading.Lock()
        t = Thread(target=self._start_loop_in_new_thread,daemon=True)
        # t.setDaemon(True)  # 设置守护线程是为了有机会触发atexit，使程序自动结束，不用手动调用shutdown
        t.start()
        self._can_be_closed_flag = False
        atexit.register(self.shutdown)

        self._event = threading.Event()
        # print(self._event.is_set())
        self._event.set()

    def submit000(self, func, *args, **kwargs):
        # 这个性能比下面的采用 run_coroutine_threadsafe + result返回快了3倍多。
        with self._lock:
            while 1:
                if not self._queue.full():
                    self.loop.call_soon_threadsafe(self._queue.put_nowait, (func, args, kwargs))
                    break
                else:
                    time.sleep(0.01)

    def submit(self, func, *args, **kwargs):
        future = asyncio.run_coroutine_threadsafe(self._produce(func, *args, **kwargs), self.loop)  # 这个 run_coroutine_threadsafe 方法也有缺点，消耗的性能巨大。
        future.result()  # 阻止过快放入，放入超过队列大小后，使submit阻塞。

    async def _produce(self, func, *args, **kwargs):
        await self._queue.put((func, args, kwargs))

    async def _consume(self):
        while True:
            func, args, kwargs = await self._queue.get()
            if isinstance(func, str) and func.startswith('stop'):
                # self.logger.debug(func)
                break
            # noinspection PyBroadException,PyUnusedLocal
            try:
                await func(*args, **kwargs)
            except BaseException as e:
                traceback.print_exc()
            # self._queue.task_done()

    async def __run(self):
        for _ in range(self._size):
            asyncio.ensure_future(self._consume())

    def _start_loop_in_new_thread(self, ):
        # self._loop.run_until_complete(self.__run())  # 这种也可以。
        # self._loop.run_forever()

        # asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(asyncio.wait([self._consume() for _ in range(self._size)], loop=self.loop))
        self._can_be_closed_flag = True

    def shutdown(self):
        if self.loop.is_running():  # 这个可能是atregster触发，也可能是用户手动调用，需要判断一下，不能关闭两次。
            for i in range(self._size):
                self.submit(f'stop{i}', )
            while not self._can_be_closed_flag:
                time.sleep(0.1)
            self.loop.stop()
            self.loop.close()
            print('关闭循环')





if __name__ == '__main__':
    def test_async_pool_executor():
        from funboost.concurrent_pool import CustomThreadPoolExecutor as ThreadPoolExecutor
        # from concurrent.futures.thread import ThreadPoolExecutor
        # noinspection PyUnusedLocal
        async def f(x):
            # await asyncio.sleep(0.1)
            pass
            print('打印', x)
            # await asyncio.sleep(1)
            # raise Exception('aaa')

        def f2(x):
            pass
            # time.sleep(0.001)
            print('打印', x)

        print(1111)

        t1 = time.time()
        pool = AsyncPoolExecutor(20)
        # pool = ThreadPoolExecutor(200)  # 协程不能用线程池运行，否则压根不会执行print打印，对于一部函数 f(x)得到的是一个协程，必须进一步把协程编排成任务放在loop循环里面运行。
        for i in range(1, 501):
            print('放入', i)
            pool.submit(f, i)
        # time.sleep(5)
        # pool.submit(f, 'hi')
        # pool.submit(f, 'hi2')
        # pool.submit(f, 'hi3')
        # print(2222)
        pool.shutdown()
        print(time.time() - t1)





    test_async_pool_executor()
    # test_async_producer_consumer()

```

### 代码文件: funboost\concurrent_pool\backup\grok_async_pool.py
```python
import asyncio
import queue
import threading
from concurrent.futures import Future,ThreadPoolExecutor
import time
from flask.cli import traceback
import nb_log
import uuid

from funboost.concurrent_pool.async_helper import simple_run_in_executor

class AsyncPool:
    def __init__(self, size, loop=None,min_tasks=1,  idle_timeout=1):
        # 初始化参数
        self.min_tasks = min_tasks
        self.max_tasks = size
        self.sync_queue = queue.Queue(maxsize=size)  # 同步队列
        # self.async_queue = asyncio.Queue(maxsize=size)  # 异步队列
        self.loop = asyncio.new_event_loop()  # 创建事件循环
        self.workers = set()  # 工作协程集合
        self._lock = threading.Lock()
        self._lock_for_adjust = threading.Lock()
        self.idle_timeout = idle_timeout

        self.async_queue = None
        def create_async_queue():
            self.async_queue = asyncio.Queue(maxsize=size)
        self.loop.call_soon_threadsafe(create_async_queue)

        # 启动事件循环线程
        self.loop_thread = threading.Thread(target=self._run_loop, daemon=False)
        self.loop_thread.start()
        print("事件循环线程已启动")

        # 启动任务转移协程
        asyncio.run_coroutine_threadsafe(self._transfer_tasks(),self.loop )
        print("任务转移协程已启动")

        # 初始化工作协程
        # self._adjust_workers(min_tasks)
        # print(f"已初始化 {min_tasks} 个工作协程")

    def _run_loop(self):
        """运行事件循环"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _transfer_tasks(self):
        """将任务从同步队列转移到异步队列"""
        while True:
            try:
                task =await simple_run_in_executor(self.sync_queue.get,timeout=0.1,async_loop=self.loop)
                await self.async_queue.put(task)
                print("任务转移到异步队列")
            except Exception: 
                print(traceback.format_exc())
                
            # try:
            #     task = self.sync_queue.get(timeout=0.01)
            #     self.sync_queue.task_done()
            #     print("任务转移到异步队列")
            #     await self.async_queue.put(task)
            # except queue.Empty:
            #     await asyncio.sleep(0.01)
         

    async def _worker(self,worker_uuid):
        """工作协程，处理任务"""
        while True:
            try:
                print(f"工作协程等待任务...  {self.async_queue.qsize()}")
                coro, args, kwargs, future = await asyncio.wait_for(
                    self.async_queue.get(), timeout=self.idle_timeout
                )
                print("工作协程获取到任务")
               
                try:
                    result = await coro(*args, **kwargs)  # 执行异步任务
                    future.set_result(result)
                    print(f"任务完成，结果: {result}")
                except Exception as e:
                    future.set_exception(e)
                    print(f"任务失败: {e}")
                finally:
                    pass
                    # self.async_queue.task_done()
                    if len(self.workers) > self.max_tasks:
                        print("工作协程超过了，准备退出")
                        with self._lock:
                            self.workers.remove(worker_uuid)
                        return
            except asyncio.TimeoutError:
                with self._lock:
                    if len(self.workers) > self.min_tasks:
                        print("工作协程获取任务超时，准备退出")
                        self.workers.remove(worker_uuid)
                        return
            except Exception as e:
                traceback.print_exc()
                return

    # def _adjust_workers(self, target_count):
    #     """调整工作协程数量"""
    #     with self._lock_for_adjust:
    #         current_count = len(self.workers)
    #         if target_count > current_count and current_count < self.max_tasks:
    #             for _ in range(target_count - current_count):
    #                 worker = asyncio.run_coroutine_threadsafe(self._worker(), self.loop)
    #                 self.workers.add(worker)
    #                 print(f"添加工作协程，总数: {len(self.workers)}")

    def submit(self, coro, *args, **kwargs):
        """提交任务"""
        if not asyncio.iscoroutinefunction(coro):
            raise ValueError("Submitted function must be an async def coroutine")

        future = Future()
        task = (coro, args, kwargs, future)
        
        self.sync_queue.put(task)  # 提交任务到同步队列
        print("提交任务到同步队列")
        if len(self.workers) < self.max_tasks:
            uuidx = uuid.uuid4()
            asyncio.run_coroutine_threadsafe(self._worker(uuidx), self.loop)
            self.workers.add(uuidx)
            print(f"添加工作协程，总数: {len(self.workers)}")
        return future



# 测试函数
async def example_task(n):
    # print(f"example_task {n} 开始运行")
    await asyncio.sleep(1)
    print(f"example_task {n} 完成")
    return n * 2

# 主程序
if __name__ == "__main__":
    pool = AsyncPool(5)
    for i in range(20):
        pool.submit(example_task, i)
    # for i, f in enumerate(futures):
    #     print(f"任务 {i} 结果: {f.result()}")  # 等待并获取结果
    # pool.shutdown()

    
    time.sleep(20)
    print('新一轮提交')
    for i in range(20):
        pool.submit(example_task, 100+i)

```

### 代码文件: funboost\concurrent_pool\backup\__init__.py
```python

```

### 代码文件: funboost\consumers\base_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:11
"""
所有中间件类型消费者的抽象基类。使实现不同中间件的消费者尽可能代码少。
整个流程最难的都在这里面。因为要实现多种并发模型，和对函数施加20多种运行控制方式，所以代码非常长。

框架做主要的功能都是在这个文件里面实现的.
"""
import functools
import sys
import typing
import abc
import copy
from apscheduler.jobstores.memory import MemoryJobStore
from funboost.core.funboost_time import FunboostTime
from pathlib import Path
# from multiprocessing import Process
import datetime
# noinspection PyUnresolvedReferences,PyPackageRequirements
import pytz
import json
import logging
import atexit
import os
import uuid
import time
import traceback
import inspect
from functools import wraps
import threading
from threading import Lock
import asyncio

import nb_log
from funboost.core.current_task import funboost_current_task, FctContext
from funboost.core.loggers import develop_logger

from funboost.core.func_params_model import BoosterParams, PublisherParams, BaseJsonAbleModel
from funboost.core.serialization import PickleHelper, Serialization
from funboost.core.task_id_logger import TaskIdLogger
from funboost.constant import FunctionKind


from nb_libs.path_helper import PathHelper
from nb_log import (get_logger, LoggerLevelSetterMixin, LogManager, is_main_process,
                    nb_log_config_default)
from funboost.core.loggers import FunboostFileLoggerMixin, logger_prompt

from apscheduler.jobstores.redis import RedisJobStore

from apscheduler.executors.pool import ThreadPoolExecutor as ApschedulerThreadPoolExecutor

from funboost.funboost_config_deafult import FunboostCommonConfig
from funboost.concurrent_pool.single_thread_executor import SoloExecutor

from funboost.core.function_result_status_saver import ResultPersistenceHelper, FunctionResultStatus, RunStatus

from funboost.core.helper_funs import delete_keys_and_return_new_dict, get_publish_time, MsgGenerater

from funboost.concurrent_pool.async_helper import get_or_create_event_loop, simple_run_in_executor
from funboost.concurrent_pool.async_pool_executor import AsyncPoolExecutor
# noinspection PyUnresolvedReferences
from funboost.concurrent_pool.bounded_threadpoolexcutor import \
    BoundedThreadPoolExecutor
from funboost.utils.redis_manager import RedisMixin
# from func_timeout import func_set_timeout  # noqa
from funboost.utils.func_timeout import dafunc

from funboost.concurrent_pool.custom_threadpool_executor import check_not_monkey
from funboost.concurrent_pool.flexible_thread_pool import FlexibleThreadPool, sync_or_async_fun_deco
# from funboost.concurrent_pool.concurrent_pool_with_multi_process import ConcurrentPoolWithProcess
from funboost.consumers.redis_filter import RedisFilter, RedisImpermanencyFilter
from funboost.factories.publisher_factotry import get_publisher

from funboost.utils import decorators, time_util, redis_manager
from funboost.constant import ConcurrentModeEnum, BrokerEnum, ConstStrForClassMethod,RedisKeys
from funboost.core import kill_remote_task
from funboost.core.exceptions import ExceptionForRequeue, ExceptionForPushToDlxqueue

# from funboost.core.booster import BoostersManager  互相导入
from funboost.core.lazy_impoter import funboost_lazy_impoter


# patch_apscheduler_run_job()

class GlobalVars:
    global_concurrent_mode = None
    has_start_a_consumer_flag = False


# noinspection DuplicatedCode
class AbstractConsumer(LoggerLevelSetterMixin, metaclass=abc.ABCMeta, ):
    time_interval_for_check_do_not_run_time = 60
    BROKER_KIND = None
    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {}  # 每种中间件的概念有所不同，用户可以从 broker_exclusive_config 中传递该种中间件特有的配置意义参数。

    @property
    @decorators.synchronized
    def publisher_of_same_queue(self):
        if not self._publisher_of_same_queue:
            self._publisher_of_same_queue = get_publisher(publisher_params=self.publisher_params)
        return self._publisher_of_same_queue

    def bulid_a_new_publisher_of_same_queue(self):
        return get_publisher(publisher_params=self.publisher_params)

    @property
    @decorators.synchronized
    def publisher_of_dlx_queue(self):
        """ 死信队列发布者 """
        if not self._publisher_of_dlx_queue:
            publisher_params_dlx = copy.copy(self.publisher_params)
            publisher_params_dlx.queue_name = self._dlx_queue_name
            publisher_params_dlx.consuming_function = None
            self._publisher_of_dlx_queue = get_publisher(publisher_params=publisher_params_dlx)
        return self._publisher_of_dlx_queue

    @classmethod
    def join_dispatch_task_thread(cls):
        """

        :return:
        """
        # ConsumersManager.join_all_consumer_dispatch_task_thread()
        if GlobalVars.has_start_a_consumer_flag:
            # self.keep_circulating(10,block=True,)(time.sleep)()
            while 1:
                time.sleep(10)

    def __init__(self, consumer_params: BoosterParams):

        """
        """
        self.raw_consumer_params = copy.copy(consumer_params)
        self.consumer_params = copy.copy(consumer_params)
        # noinspection PyUnresolvedReferences
        file_name = self.consumer_params.consuming_function.__code__.co_filename
        # noinspection PyUnresolvedReferences
        line = self.consumer_params.consuming_function.__code__.co_firstlineno
        self.consumer_params.auto_generate_info['where_to_instantiate'] = f'{file_name}:{line}'

        self.queue_name = self._queue_name = consumer_params.queue_name
        self.consuming_function = consumer_params.consuming_function
        if consumer_params.consuming_function is None:
            raise ValueError('必须传 consuming_function 参数')

        self._msg_schedule_time_intercal = 0 if consumer_params.qps in (None, 0) else 1.0 / consumer_params.qps

        self._concurrent_mode_dispatcher = ConcurrentModeDispatcher(self)
        if consumer_params.concurrent_mode == ConcurrentModeEnum.ASYNC:
            self._run = self._async_run  # 这里做了自动转化，使用async_run代替run
        self.logger: logging.Logger
        self._build_logger()
        # stdout_write(f'''{time.strftime("%H:%M:%S")} "{self.consumer_params.auto_generate_info['where_to_instantiate']}"  \033[0;37;44m此行 实例化队列名 {self.queue_name} 的消费者, 类型为 {self.__class__}\033[0m\n''')
        print(f'''\033[0m
         "{self.consumer_params.auto_generate_info['where_to_instantiate']}" \033[0m此行 实例化队列名 {self.queue_name} 的消费者, 类型为 {self.__class__} ''')

        # only_print_on_main_process(f'{current_queue__info_dict["queue_name"]} 的消费者配置:\n', un_strict_json_dumps.dict2json(current_queue__info_dict))

        # self._do_task_filtering = consumer_params.do_task_filtering
        # self.consumer_params.is_show_message_get_from_broker = consumer_params.is_show_message_get_from_broker
        self._redis_filter_key_name = f'filter_zset:{consumer_params.queue_name}' if consumer_params.task_filtering_expire_seconds else f'filter_set:{consumer_params.queue_name}'
        filter_class = RedisFilter if consumer_params.task_filtering_expire_seconds == 0 else RedisImpermanencyFilter
        self._redis_filter = filter_class(self._redis_filter_key_name, consumer_params.task_filtering_expire_seconds)
        self._redis_filter.delete_expire_filter_task_cycle()
 
        # if  self.consumer_params.concurrent_mode == ConcurrentModeEnum.ASYNC and self.consumer_params.specify_async_loop is None:
        #     self.consumer_params.specify_async_loop= get_or_create_event_loop()
        self._lock_for_count_execute_task_times_every_unit_time = Lock()
        if self.consumer_params.concurrent_mode == ConcurrentModeEnum.ASYNC:
            self._async_lock_for_count_execute_task_times_every_unit_time = asyncio.Lock()
        # self._unit_time_for_count = 10  # 每隔多少秒计数，显示单位时间内执行多少次，暂时固定为10秒。
        # self._execute_task_times_every_unit_time = 0  # 每单位时间执行了多少次任务。
        # self._execute_task_times_every_unit_time_fail =0  # 每单位时间执行了多少次任务失败。
        # self._lock_for_count_execute_task_times_every_unit_time = Lock()
        # self._current_time_for_execute_task_times_every_unit_time = time.time()
        # self._consuming_function_cost_time_total_every_unit_time = 0
        # self._last_execute_task_time = time.time()  # 最近一次执行任务的时间。
        # self._last_10s_execute_count = 0
        # self._last_10s_execute_count_fail = 0
        #
        # self._last_show_remaining_execution_time = 0
        # self._show_remaining_execution_time_interval = 300
        #
        # self._msg_num_in_broker = 0
        # self._last_timestamp_when_has_task_in_queue = 0
        # self._last_timestamp_print_msg_num = 0

        self.metric_calculation = MetricCalculation(self)

        self._result_persistence_helper: ResultPersistenceHelper
        self._check_broker_exclusive_config()
        broker_exclusive_config_merge = dict()
        broker_exclusive_config_merge.update(self.BROKER_EXCLUSIVE_CONFIG_DEFAULT)
        broker_exclusive_config_merge.update(self.consumer_params.broker_exclusive_config)
        # print(broker_exclusive_config_merge)
        self.consumer_params.broker_exclusive_config = broker_exclusive_config_merge

        self._stop_flag = None
        self._pause_flag = threading.Event()  # 暂停消费标志，从reids读取
        self._last_show_pause_log_time = 0
        # self._redis_key_stop_flag = f'funboost_stop_flag'
        # self._redis_key_pause_flag = RedisKeys.REDIS_KEY_PAUSE_FLAG

        # 控频要用到的成员变量
        self._last_submit_task_timestamp = 0
        self._last_start_count_qps_timestamp = time.time()
        self._has_execute_times_in_recent_second = 0

        self._publisher_of_same_queue = None  #
        self._dlx_queue_name = f'{self.queue_name}_dlx'
        self._publisher_of_dlx_queue = None  # 死信队列发布者

        self._do_not_delete_extra_from_msg = False
        self._concurrent_pool = None

        self.consumer_identification = f'{nb_log_config_default.computer_name}_{nb_log_config_default.computer_ip}_' \
                                       f'{time_util.DatetimeConverter().datetime_str.replace(":", "-")}_{os.getpid()}_{id(self)}'
        # noinspection PyUnresolvedReferences
        self.consumer_identification_map = {'queue_name': self.queue_name,
                                            'computer_name': nb_log_config_default.computer_name,
                                            'computer_ip': nb_log_config_default.computer_ip,
                                            'process_id': os.getpid(),
                                            'consumer_id': id(self),
                                            'consumer_uuid': str(uuid.uuid4()),
                                            'start_datetime_str': time_util.DatetimeConverter().datetime_str,
                                            'start_timestamp': time.time(),
                                            'hearbeat_datetime_str': time_util.DatetimeConverter().datetime_str,
                                            'hearbeat_timestamp': time.time(),
                                            'consuming_function': self.consuming_function.__name__,
                                            'code_filename': Path(self.consuming_function.__code__.co_filename).as_posix()
                                            }

        self._has_start_delay_task_scheduler = False
        self._consuming_function_is_asyncio = inspect.iscoroutinefunction(self.consuming_function)
        self.custom_init()
        # develop_logger.warning(consumer_params._log_filename)
        # self.publisher_params = PublisherParams(queue_name=consumer_params.queue_name, consuming_function=consumer_params.consuming_function,
        #                                         broker_kind=self.BROKER_KIND, log_level=consumer_params.log_level,
        #                                         logger_prefix=consumer_params.logger_prefix,
        #                                         create_logger_file=consumer_params.create_logger_file,
        #                                         log_filename=consumer_params.log_filename,
        #                                         logger_name=consumer_params.logger_name,
        #                                         broker_exclusive_config=self.consumer_params.broker_exclusive_config)
        self.publisher_params = BaseJsonAbleModel.init_by_another_model(PublisherParams, self.consumer_params)
        # print(self.publisher_params)
        if is_main_process:
            self.logger.info(f'{self.queue_name} consumer 的消费者配置:\n {self.consumer_params.json_str_value()}')

        atexit.register(self.join_dispatch_task_thread)

        self._save_consumer_params()

        if self.consumer_params.is_auto_start_consuming_message:
            _ = self.publisher_of_same_queue
            self.start_consuming_message()

    def _save_consumer_params(self):
        """
        保存队列的消费者参数，以便在web界面查看。
        :return:
        """
        if self.consumer_params.is_send_consumer_hearbeat_to_redis:
            RedisMixin().redis_db_frame.sadd(RedisKeys.FUNBOOST_ALL_QUEUE_NAMES,self.queue_name)
            RedisMixin().redis_db_frame.hmset(RedisKeys.FUNBOOST_QUEUE__CONSUMER_PARAMS,
                                    {self.queue_name: self.consumer_params.json_str_value()})
            RedisMixin().redis_db_frame.sadd(RedisKeys.FUNBOOST_ALL_IPS,nb_log_config_default.computer_ip)
        
    
    def _build_logger(self):
        logger_prefix = self.consumer_params.logger_prefix
        if logger_prefix != '':
            logger_prefix += '--'
            # logger_name = f'{logger_prefix}{self.__class__.__name__}--{concurrent_name}--{queue_name}--{self.consuming_function.__name__}'
        logger_name = self.consumer_params.logger_name or f'funboost.{logger_prefix}{self.__class__.__name__}--{self.queue_name}'
        self.logger_name = logger_name
        log_filename = self.consumer_params.log_filename or f'funboost.{self.queue_name}.log'
        self.logger = LogManager(logger_name, logger_cls=TaskIdLogger).get_logger_and_add_handlers(
            log_level_int=self.consumer_params.log_level,
            log_filename=log_filename if self.consumer_params.create_logger_file else None,
            error_log_filename=nb_log.generate_error_file_name(log_filename),
            formatter_template=FunboostCommonConfig.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER, )
        self.logger.info(f'队列 {self.queue_name} 的日志写入到 {nb_log_config_default.LOG_PATH} 文件夹的 {log_filename} 和 {nb_log.generate_error_file_name(log_filename)} 文件中')

    def _check_broker_exclusive_config(self):
        broker_exclusive_config_keys = self.BROKER_EXCLUSIVE_CONFIG_DEFAULT.keys()
        if self.consumer_params.broker_exclusive_config:
            if set(self.consumer_params.broker_exclusive_config.keys()).issubset(broker_exclusive_config_keys):
                self.logger.info(f'当前消息队列中间件能支持特殊独有配置 {self.consumer_params.broker_exclusive_config.keys()}')
            else:
                self.logger.warning(f'当前消息队列中间件含有不支持的特殊配置 {self.consumer_params.broker_exclusive_config.keys()}，能支持的特殊独有配置包括 {broker_exclusive_config_keys}')

    def _check_monkey_patch(self):
        if self.consumer_params.concurrent_mode == ConcurrentModeEnum.GEVENT:
            from funboost.concurrent_pool.custom_gevent_pool_executor import check_gevent_monkey_patch
            check_gevent_monkey_patch()
        elif self.consumer_params.concurrent_mode == ConcurrentModeEnum.EVENTLET:
            from funboost.concurrent_pool.custom_evenlet_pool_executor import check_evenlet_monkey_patch
            check_evenlet_monkey_patch()
        else:
            check_not_monkey()

    # def _log_error(self, msg, exc_info=None):
    #     self.logger.error(msg=f'{msg} \n', exc_info=exc_info, extra={'sys_getframe_n': 3})  # 这是改变日志栈层级
    #     self.error_file_logger.error(msg=f'{msg} \n', exc_info=exc_info, extra={'sys_getframe_n': 3})
    #
    # def _log_critical(self, msg, exc_info=None):
    #     self.logger.critical(msg=f'{msg} \n', exc_info=exc_info, extra={'sys_getframe_n': 3})
    #     self.error_file_logger.critical(msg=f'{msg} \n', exc_info=exc_info, extra={'sys_getframe_n': 3})

    @property
    @decorators.synchronized
    def concurrent_pool(self):
        return self._concurrent_mode_dispatcher.build_pool()

    def custom_init(self):
        pass

    def keep_circulating(self, time_sleep=0.001, exit_if_function_run_sucsess=False, is_display_detail_exception=True,
                         block=True, daemon=False):
        """间隔一段时间，一直循环运行某个方法的装饰器
        :param time_sleep :循环的间隔时间
        :param is_display_detail_exception
        :param exit_if_function_run_sucsess :如果成功了就退出循环
        :param block:是否阻塞在当前主线程运行。
        :param daemon:是否守护线程
        """

        def _keep_circulating(func):
            @wraps(func)
            def __keep_circulating(*args, **kwargs):

                # noinspection PyBroadException
                def ___keep_circulating():
                    while 1:
                        if self._stop_flag == 1:
                            break
                        try:
                            result = func(*args, **kwargs)
                            if exit_if_function_run_sucsess:
                                return result
                        except BaseException as e:
                            log_msg = func.__name__ + '   运行出错\n ' + traceback.format_exc(
                                limit=10) if is_display_detail_exception else str(e)
                            # self.logger.error(msg=f'{log_msg} \n', exc_info=True)
                            # self.error_file_logger.error(msg=f'{log_msg} \n', exc_info=True)
                            self.logger.error(msg=log_msg, exc_info=True)
                        finally:
                            time.sleep(time_sleep)
                            # print(func,time_sleep)

                if block:
                    return ___keep_circulating()
                else:
                    threading.Thread(target=___keep_circulating, daemon=daemon).start()

            return __keep_circulating

        return _keep_circulating

    # noinspection PyAttributeOutsideInit
    def start_consuming_message(self):
        # ConsumersManager.show_all_consumer_info()
        # noinspection PyBroadException
        pid_queue_name_tuple = (os.getpid(), self.queue_name)
        if pid_queue_name_tuple in funboost_lazy_impoter.BoostersManager.pid_queue_name__has_start_consume_set:
            self.logger.warning(f'{pid_queue_name_tuple} 已启动消费,不要一直去启动消费,funboost框架自动阻止.')  # 有的人乱写代码,无数次在函数内部或for循环里面执行 f.consume(),一个队列只需要启动一次消费,不然每启动一次性能消耗很大,直到程序崩溃
            return
        else:
            funboost_lazy_impoter.BoostersManager.pid_queue_name__has_start_consume_set.add(pid_queue_name_tuple)
        GlobalVars.has_start_a_consumer_flag = True
        try:
            self._concurrent_mode_dispatcher.check_all_concurrent_mode()
            self._check_monkey_patch()
        except BaseException:  # noqa
            traceback.print_exc()
            os._exit(4444)  # noqa
        self.logger.info(f'开始消费 {self._queue_name} 中的消息')
        self._result_persistence_helper = ResultPersistenceHelper(self.consumer_params.function_result_status_persistance_conf, self.queue_name)

        self._distributed_consumer_statistics = DistributedConsumerStatistics(self)
        if self.consumer_params.is_send_consumer_hearbeat_to_redis:
            self._distributed_consumer_statistics.run()
            self.logger.warning(f'启动了分布式环境 使用 redis 的键 hearbeat:{self._queue_name} 统计活跃消费者 ，当前消费者唯一标识为 {self.consumer_identification}')

        self.keep_circulating(60, block=False, daemon=False)(self.check_heartbeat_and_message_count)()
        if self.consumer_params.is_support_remote_kill_task:
            kill_remote_task.RemoteTaskKiller(self.queue_name, None).start_cycle_kill_task()
            self.consumer_params.is_show_message_get_from_broker = True  # 方便用户看到从消息队列取出来的消息的task_id,然后使用task_id杀死运行中的消息。
        if self.consumer_params.do_task_filtering:
            self._redis_filter.delete_expire_filter_task_cycle()  # 这个默认是RedisFilter类，是个pass不运行。所以用别的消息中间件模式，不需要安装和配置redis。
        if self.consumer_params.schedule_tasks_on_main_thread:
            self.keep_circulating(1, daemon=False)(self._dispatch_task)()
        else:
            self._concurrent_mode_dispatcher.schedulal_task_with_no_block()

    def _start_delay_task_scheduler(self):
        from funboost.timing_job import FsdfBackgroundScheduler
        from funboost.timing_job.apscheduler_use_redis_store import FunboostBackgroundSchedulerProcessJobsWithinRedisLock
        # print(self.consumer_params.delay_task_apsscheduler_jobstores_kind )
        if self.consumer_params.delay_task_apscheduler_jobstores_kind == 'redis':
            jobstores = {
                "default": RedisJobStore(**redis_manager.get_redis_conn_kwargs(),
                                         jobs_key=RedisKeys.gen_funboost_redis_apscheduler_jobs_key_by_queue_name(self.queue_name),
                                         run_times_key=RedisKeys.gen_funboost_redis_apscheduler_run_times_key_by_queue_name(self.queue_name),
                                         )
            }
            self._delay_task_scheduler = FunboostBackgroundSchedulerProcessJobsWithinRedisLock(timezone=FunboostCommonConfig.TIMEZONE, daemon=False,
                                                       jobstores=jobstores  # push 方法的序列化带thredignn.lock
                                                       )
            self._delay_task_scheduler.set_process_jobs_redis_lock_key(
                RedisKeys.gen_funboost_apscheduler_redis_lock_key_by_queue_name(self.queue_name))
        elif self.consumer_params.delay_task_apscheduler_jobstores_kind == 'memory':
            jobstores = {"default": MemoryJobStore()}
            self._delay_task_scheduler = FsdfBackgroundScheduler(timezone=FunboostCommonConfig.TIMEZONE, daemon=False,
                                                       jobstores=jobstores  # push 方法的序列化带thredignn.lock
                                                       )

        else:
            raise Exception(f'delay_task_apsscheduler_jobstores_kind is error: {self.consumer_params.delay_task_apscheduler_jobstores_kind}')


        # self._delay_task_scheduler.add_executor(ApschedulerThreadPoolExecutor(2))  # 只是运行submit任务到并发池，不需要很多线程。
        # self._delay_task_scheduler.add_listener(self._apscheduler_job_miss, EVENT_JOB_MISSED)
        self._delay_task_scheduler.start()

        self.logger.warning('启动延时任务sheduler')

    logger_apscheduler = get_logger('push_for_apscheduler_use_database_store', log_filename='push_for_apscheduler_use_database_store.log')

    @classmethod
    def _push_apscheduler_task_to_broker(cls, queue_name, msg):
        funboost_lazy_impoter.BoostersManager.get_or_create_booster_by_queue_name(queue_name).publish(msg)
       
    @abc.abstractmethod
    def _dispatch_task(self):
        """
        每个子类必须实现这个的方法，完成如何从中间件取出消息，并将函数和运行参数添加到工作池。

        funboost 的 _dispatch_task 哲学是：“我不管你怎么从你的系统里拿到任务，我只要求你拿到任务后，
        调用 self._submit_task(msg) 方法把它交给我处理就行。”

        所以无论获取消息是 拉模式 还是推模式 还是轮询模式，无论是是单条获取 还是多条批量多条获取，
        都能轻松扩展任意东西作为funboost的中间件。 

        :return:
        """
        raise NotImplementedError

    def _convert_msg_before_run(self, msg: typing.Union[str, dict]) -> dict:
        """
        转换消息,消息没有使用funboost来发送,并且没有extra相关字段时候
        用户也可以按照4.21文档,继承任意Consumer类,并实现方法 _user_convert_msg_before_run,先转换不规范的消息.
        """
        """ 一般消息至少包含这样
        {
          "a": 42,
          "b": 84,
          "extra": {
            "task_id": "queue_2_result:9b79a372-f765-4a33-8639-9d15d7a95f61",
            "publish_time": 1701687443.3596,
            "publish_time_format": "2023-12-04 18:57:23"
          }
        }
        """

        """
        extra_params = {'task_id': task_id, 'publish_time': round(time.time(), 4),
                        'publish_time_format': time.strftime('%Y-%m-%d %H:%M:%S')}
        """
        msg = self._user_convert_msg_before_run(msg)
        msg = Serialization.to_dict(msg)
        # 以下是清洗补全字段.
        if 'extra' not in msg:
            msg['extra'] = {'is_auto_fill_extra': True}
        extra = msg['extra']
        if 'task_id' not in extra:
            extra['task_id'] = MsgGenerater.generate_task_id(self._queue_name)
        if 'publish_time' not in extra:
            extra['publish_time'] = MsgGenerater.generate_publish_time()
        if 'publish_time_format':
            extra['publish_time_format'] = MsgGenerater.generate_publish_time_format()
        return msg
    
    def _user_convert_msg_before_run(self, msg: typing.Union[str, dict]) -> dict:
        """
        用户也可以提前清洗数据
        """
        # print(msg)
        return msg

    def _submit_task(self, kw):

        kw['body'] = self._convert_msg_before_run(kw['body'])
        self._print_message_get_from_broker(kw['body'])
        if self._judge_is_daylight():
            self._requeue(kw)
            time.sleep(self.time_interval_for_check_do_not_run_time)
            return
        function_only_params = delete_keys_and_return_new_dict(kw['body'], )
        if self._get_priority_conf(kw, 'do_task_filtering') and self._redis_filter.check_value_exists(
                function_only_params,self._get_priority_conf(kw, 'filter_str')):  # 对函数的参数进行检查，过滤已经执行过并且成功的任务。
            self.logger.warning(f'redis的 [{self._redis_filter_key_name}] 键 中 过滤任务 {kw["body"]}')
            self._confirm_consume(kw) # 不运行就必须确认消费，否则会发不能确认消费，导致消息队列中间件认为消息没有被消费。
            return
        publish_time = get_publish_time(kw['body'])
        msg_expire_senconds_priority = self._get_priority_conf(kw, 'msg_expire_senconds')
        if msg_expire_senconds_priority and time.time() - msg_expire_senconds_priority > publish_time:
            self.logger.warning(
                f'消息发布时戳是 {publish_time} {kw["body"].get("publish_time_format", "")},距离现在 {round(time.time() - publish_time, 4)} 秒 ,'
                f'超过了指定的 {msg_expire_senconds_priority} 秒，丢弃任务')
            self._confirm_consume(kw)
            return 0

        msg_eta = self._get_priority_conf(kw, 'eta')
        msg_countdown = self._get_priority_conf(kw, 'countdown')
        misfire_grace_time = self._get_priority_conf(kw, 'misfire_grace_time')
        run_date = None
        # print(kw)
        if msg_countdown:
            run_date = FunboostTime(kw['body']['extra']['publish_time']).datetime_obj + datetime.timedelta(seconds=msg_countdown)
        if msg_eta:

            run_date = FunboostTime(msg_eta).datetime_obj
        # print(run_date,time_util.DatetimeConverter().datetime_obj)
        # print(run_date.timestamp(),time_util.DatetimeConverter().datetime_obj.timestamp())
        # print(self.concurrent_pool)
        if run_date:  # 延时任务
            # print(repr(run_date),repr(datetime.datetime.now(tz=pytz.timezone(frame_config.TIMEZONE))))
            if self._has_start_delay_task_scheduler is False:
                self._has_start_delay_task_scheduler = True
                self._start_delay_task_scheduler()

            # 这种方式是扔到线程池
            # self._delay_task_scheduler.add_job(self.concurrent_pool.submit, 'date', run_date=run_date, args=(self._run,), kwargs={'kw': kw},
            #                                    misfire_grace_time=misfire_grace_time)

            # 这种方式是延时任务重新以普通任务方式发送到消息队列
            msg_no_delay = copy.deepcopy(kw['body'])
            self.__delete_eta_countdown(msg_no_delay)
            # print(msg_no_delay)
            # 数据库作为apscheduler的jobstores时候， 不能用 self.pbulisher_of_same_queue.publish，self不能序列化
            self._delay_task_scheduler.add_job(self._push_apscheduler_task_to_broker, 'date', run_date=run_date,
                                               kwargs={'queue_name': self.queue_name, 'msg': msg_no_delay, },
                                               misfire_grace_time=misfire_grace_time,
                                              )
            self._confirm_consume(kw)

        else:  # 普通任务
            self.concurrent_pool.submit(self._run, kw)

        if self.consumer_params.is_using_distributed_frequency_control:  # 如果是需要分布式控频。
            active_num = self._distributed_consumer_statistics.active_consumer_num
            self._frequency_control(self.consumer_params.qps / active_num, self._msg_schedule_time_intercal * active_num)
        else:
            self._frequency_control(self.consumer_params.qps, self._msg_schedule_time_intercal)

        while 1:  # 这一块的代码为支持暂停消费。
            # print(self._pause_flag)
            if self._pause_flag.is_set():
                if time.time() - self._last_show_pause_log_time > 60:
                    self.logger.warning(f'已设置 {self.queue_name} 队列中的任务为暂停消费')
                    self._last_show_pause_log_time = time.time()
                time.sleep(5)
            else:
                break

    def __delete_eta_countdown(self, msg_body: dict):
        self.__dict_pop(msg_body.get('extra', {}), 'eta')
        self.__dict_pop(msg_body.get('extra', {}), 'countdown')
        self.__dict_pop(msg_body.get('extra', {}), 'misfire_grace_time')

    @staticmethod
    def __dict_pop(dictx, key):
        try:
            dictx.pop(key)
        except KeyError:
            pass

    def _frequency_control(self, qpsx: float, msg_schedule_time_intercalx: float):
        # 以下是消费函数qps控制代码。无论是单个消费者空频还是分布式消费控频，都是基于直接计算的，没有依赖redis inrc计数，使得控频性能好。
        if qpsx is None:  # 不需要控频的时候，就不需要休眠。
            return
        if qpsx <= 5:
            """ 原来的简单版 """
            time.sleep(msg_schedule_time_intercalx)
        elif 5 < qpsx <= 20:
            """ 改进的控频版,防止消息队列中间件网络波动，例如1000qps使用redis,不能每次间隔1毫秒取下一条消息，
            如果取某条消息有消息超过了1毫秒，后面不能匀速间隔1毫秒获取，time.sleep不能休眠一个负数来让时光倒流"""
            time_sleep_for_qps_control = max((msg_schedule_time_intercalx - (time.time() - self._last_submit_task_timestamp)) * 0.99, 10 ** -3)
            # print(time.time() - self._last_submit_task_timestamp)
            # print(time_sleep_for_qps_control)
            time.sleep(time_sleep_for_qps_control)
            self._last_submit_task_timestamp = time.time()
        else:
            """基于当前消费者计数的控频，qps很大时候需要使用这种"""
            if time.time() - self._last_start_count_qps_timestamp > 1:
                self._has_execute_times_in_recent_second = 1
                self._last_start_count_qps_timestamp = time.time()
            else:
                self._has_execute_times_in_recent_second += 1
            # print(self._has_execute_times_in_recent_second)
            if self._has_execute_times_in_recent_second >= qpsx:
                time.sleep((1 - (time.time() - self._last_start_count_qps_timestamp)) * 1)

    def _print_message_get_from_broker(self, msg, broker_name=None):
        # print(999)
        if self.consumer_params.is_show_message_get_from_broker:
            # self.logger.debug(f'从 {broker_name} 中间件 的 {self._queue_name} 中取出的消息是 {msg}')
            self.logger.debug(f'从 {broker_name or self.consumer_params.broker_kind} 中间件 的 {self._queue_name} 中取出的消息是 {Serialization.to_json_str(msg)}')

    def _get_priority_conf(self, kw: dict, broker_task_config_key: str):
        broker_task_config = kw['body'].get('extra', {}).get(broker_task_config_key, None)
        if not broker_task_config:
            return getattr(self.consumer_params, f'{broker_task_config_key}', None)
        else:
            return broker_task_config

    # noinspection PyMethodMayBeStatic
    def _get_concurrent_info(self):
        concurrent_info = ''
        '''  影响了日志长度和一丝丝性能。
        if self._concurrent_mode == 1:
            concurrent_info = f'[{threading.current_thread()}  {threading.active_count()}]'
        elif self._concurrent_mode == 2:
            concurrent_info = f'[{gevent.getcurrent()}  {threading.active_count()}]'
        elif self._concurrent_mode == 3:
            # noinspection PyArgumentList
            concurrent_info = f'[{eventlet.getcurrent()}  {threading.active_count()}]'
        '''
        return concurrent_info

    def _set_do_not_delete_extra_from_msg(self):
        """例如从死信队列，把完整的包括extra的消息移到另一个正常队列，不要把extra中的参数去掉
        queue2queue.py 的 consume_and_push_to_another_queue 中操作了这个，普通用户无需调用这个方法。
        """
        self._do_not_delete_extra_from_msg = True

    def user_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus):  # 这个可以继承
        pass

    async def aio_user_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus):  # 这个可以继承
        pass

    def _convert_real_function_only_params_by_conusuming_function_kind(self, function_only_params: dict,extra_params:dict):
        """对于实例方法和classmethod 方法， 从消息队列的消息恢复第一个入参， self 和 cls"""
        can_not_json_serializable_keys = extra_params.get('can_not_json_serializable_keys',[])
        if self.consumer_params.consuming_function_kind in [FunctionKind.CLASS_METHOD, FunctionKind.INSTANCE_METHOD]:
            real_function_only_params = copy.copy(function_only_params)
            method_first_param_name = None
            method_first_param_value = None
            for k, v in function_only_params.items():
                if isinstance(v, dict) and ConstStrForClassMethod.FIRST_PARAM_NAME in v:
                    method_first_param_name = k
                    method_first_param_value = v
                    break
            # method_cls = getattr(sys.modules[self.consumer_params.consuming_function_class_module],
            #                      self.consumer_params.consuming_function_class_name)
            if self.publisher_params.consuming_function_kind == FunctionKind.CLASS_METHOD:
                method_cls = getattr(PathHelper.import_module(method_first_param_value[ConstStrForClassMethod.CLS_MODULE]),
                                     method_first_param_value[ConstStrForClassMethod.CLS_NAME])
                real_function_only_params[method_first_param_name] = method_cls
            elif self.publisher_params.consuming_function_kind == FunctionKind.INSTANCE_METHOD:
                method_cls = getattr(PathHelper.import_module(method_first_param_value[ConstStrForClassMethod.CLS_MODULE]),
                                     method_first_param_value[ConstStrForClassMethod.CLS_NAME])
                obj = method_cls(**method_first_param_value[ConstStrForClassMethod.OBJ_INIT_PARAMS])
                real_function_only_params[method_first_param_name] = obj
            # print(real_function_only_params)
            if can_not_json_serializable_keys:
                for key in can_not_json_serializable_keys:
                    real_function_only_params[key] = PickleHelper.to_obj(real_function_only_params[key])
            return real_function_only_params
        else:
            if can_not_json_serializable_keys:
                for key in can_not_json_serializable_keys:
                    function_only_params[key] = PickleHelper.to_obj(function_only_params[key])
            return function_only_params

    # noinspection PyProtectedMember
    def _run(self, kw: dict, ):
        # print(kw)
        try:
            t_start_run_fun = time.time()
            max_retry_times = self._get_priority_conf(kw, 'max_retry_times')
            current_function_result_status = FunctionResultStatus(self.queue_name, self.consuming_function.__name__, kw['body'], )
            current_retry_times = 0
            function_only_params = delete_keys_and_return_new_dict(kw['body'])
            for current_retry_times in range(max_retry_times + 1):
                current_function_result_status.run_times = current_retry_times + 1
                current_function_result_status.run_status = RunStatus.running
                self._result_persistence_helper.save_function_result_to_mongo(current_function_result_status)
                current_function_result_status = self._run_consuming_function_with_confirm_and_retry(kw, current_retry_times=current_retry_times,
                                                                                                     function_result_status=current_function_result_status)
                if (current_function_result_status.success is True or current_retry_times == max_retry_times
                        or current_function_result_status._has_requeue
                        or current_function_result_status._has_to_dlx_queue
                        or current_function_result_status._has_kill_task):
                    break
                else:
                    if self.consumer_params.retry_interval:
                        time.sleep(self.consumer_params.retry_interval)
            if not (current_function_result_status._has_requeue and self.BROKER_KIND in [BrokerEnum.RABBITMQ_AMQPSTORM, BrokerEnum.RABBITMQ_PIKA, BrokerEnum.RABBITMQ_RABBITPY]):  # 已经nack了，不能ack，否则rabbitmq delevar tag 报错
                self._confirm_consume(kw)
            current_function_result_status.run_status = RunStatus.finish
            self._result_persistence_helper.save_function_result_to_mongo(current_function_result_status)
            if self._get_priority_conf(kw, 'do_task_filtering'):
                self._redis_filter.add_a_value(function_only_params,self._get_priority_conf(kw, 'filter_str'))  # 函数执行成功后，添加函数的参数排序后的键值对字符串到set中。
            if current_function_result_status.success is False and current_retry_times == max_retry_times:
                log_msg = f'函数 {self.consuming_function.__name__} 达到最大重试次数 {self._get_priority_conf(kw, "max_retry_times")} 后,仍然失败， 入参是  {function_only_params} '
                if self.consumer_params.is_push_to_dlx_queue_when_retry_max_times:
                    log_msg += f'  。发送到死信队列 {self._dlx_queue_name} 中'
                    self.publisher_of_dlx_queue.publish(kw['body'])
                # self.logger.critical(msg=f'{log_msg} \n', )
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)

            if self._get_priority_conf(kw, 'is_using_rpc_mode'):
                # print(function_result_status.get_status_dict(without_datetime_obj=
                if (current_function_result_status.success is False and current_retry_times == max_retry_times) or current_function_result_status.success is True:
                    with RedisMixin().redis_db_filter_and_rpc_result.pipeline() as p:
                        # RedisMixin().redis_db_frame.lpush(kw['body']['extra']['task_id'], json.dumps(function_result_status.get_status_dict(without_datetime_obj=True)))
                        # RedisMixin().redis_db_frame.expire(kw['body']['extra']['task_id'], 600)
                        current_function_result_status.rpc_result_expire_seconds = self.consumer_params.rpc_result_expire_seconds
                        p.lpush(kw['body']['extra']['task_id'],
                                Serialization.to_json_str(current_function_result_status.get_status_dict(without_datetime_obj=True)))
                        p.expire(kw['body']['extra']['task_id'], self.consumer_params.rpc_result_expire_seconds)
                        p.execute()

            with self._lock_for_count_execute_task_times_every_unit_time:
                self.metric_calculation.cal(t_start_run_fun,current_function_result_status)
            self.user_custom_record_process_info_func(current_function_result_status)  # 两种方式都可以自定义,记录结果,建议继承方式,不使用boost中指定 user_custom_record_process_info_func
            if self.consumer_params.user_custom_record_process_info_func:
                self.consumer_params.user_custom_record_process_info_func(current_function_result_status)
        except BaseException as e:
            log_msg = f' error 严重错误 {type(e)} {e} '
            # self.logger.critical(msg=f'{log_msg} \n', exc_info=True)
            # self.error_file_logger.critical(msg=f'{log_msg} \n', exc_info=True)
            self.logger.critical(msg=log_msg, exc_info=True)
        fct = funboost_current_task()
        fct.set_fct_context(None)

    # noinspection PyProtectedMember
    def _run_consuming_function_with_confirm_and_retry(self, kw: dict, current_retry_times,
                                                       function_result_status: FunctionResultStatus, ):
        function_only_params = delete_keys_and_return_new_dict(kw['body']) if self._do_not_delete_extra_from_msg is False else kw['body']
        task_id = kw['body']['extra']['task_id']
        t_start = time.time()
        # function_result_status.run_times = current_retry_times + 1
        fct = funboost_current_task()
        fct_context = FctContext(function_params=function_only_params,
                                 full_msg=kw['body'],
                                 function_result_status=function_result_status,
                                 logger=self.logger, queue_name=self.queue_name,)

        try:
            function_run = self.consuming_function
            if self._consuming_function_is_asyncio:
                fct_context.asyncio_use_thread_concurrent_mode = True
                function_run = sync_or_async_fun_deco(function_run)
            else:
                pass
                fct_context.asynco_use_thread_concurrent_mode = False
            fct.set_fct_context(fct_context)
            function_timeout = self._get_priority_conf(kw, 'function_timeout')
            function_run = function_run if self.consumer_params.consumin_function_decorator is None else self.consumer_params.consumin_function_decorator(function_run)
            function_run = function_run if not function_timeout else self._concurrent_mode_dispatcher.timeout_deco(
                function_timeout)(function_run)

            if self.consumer_params.is_support_remote_kill_task:
                if kill_remote_task.RemoteTaskKiller(self.queue_name, task_id).judge_need_revoke_run():  # 如果远程指令杀死任务，如果还没开始运行函数，就取消运行
                    function_result_status._has_kill_task = True
                    self.logger.warning(f'取消运行 {task_id} {function_only_params}')
                    return function_result_status
                function_run = kill_remote_task.kill_fun_deco(task_id)(function_run)  # 用杀死装饰器包装起来在另一个线程运行函数,以便等待远程杀死。
            function_result_status.result = function_run(**self._convert_real_function_only_params_by_conusuming_function_kind(function_only_params,kw['body']['extra']))
            # if asyncio.iscoroutine(function_result_status.result):
            #     log_msg = f'''异步的协程消费函数必须使用 async 并发模式并发,请设置消费函数 {self.consuming_function.__name__} 的concurrent_mode 为 ConcurrentModeEnum.ASYNC 或 4'''
            #     # self.logger.critical(msg=f'{log_msg} \n')
            #     # self.error_file_logger.critical(msg=f'{log_msg} \n')
            #     self._log_critical(msg=log_msg)
            #     # noinspection PyProtectedMember,PyUnresolvedReferences
            #
            #     os._exit(4)
            function_result_status.success = True
            if self.consumer_params.log_level <= logging.DEBUG:
                result_str_to_be_print = str(function_result_status.result)[:100] if len(str(function_result_status.result)) < 100 else str(function_result_status.result)[:100] + '  。。。。。  '
                # print(funboost_current_task().task_id)
                # print(fct.function_result_status.task_id)
                # print(get_current_taskid())
                self.logger.debug(f' 函数 {self.consuming_function.__name__}  '
                                  f'第{current_retry_times + 1}次 运行, 正确了，函数运行时间是 {round(time.time() - t_start, 4)} 秒,入参是 {function_only_params} , '
                                  f'结果是  {result_str_to_be_print}   {self._get_concurrent_info()}  ')
        except BaseException as e:
            if isinstance(e, (ExceptionForRequeue,)):  # mongo经常维护备份时候插入不了或挂了，或者自己主动抛出一个ExceptionForRequeue类型的错误会重新入队，不受指定重试次数逇约束。
                log_msg = f'函数 [{self.consuming_function.__name__}] 中发生错误 {type(e)}  {e} 。消息重新放入当前队列 {self._queue_name}'
                # self.logger.critical(msg=f'{log_msg} \n')
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)
                time.sleep(0.1)  # 防止快速无限出错入队出队，导致cpu和中间件忙
                # 重回队列如果不修改task_id,insert插入函数消费状态结果到mongo会主键重复。要么保存函数消费状态使用replace，要么需要修改taskikd
                # kw_new = copy.deepcopy(kw)
                # new_task_id =f'{self._queue_name}_result:{uuid.uuid4()}'
                # kw_new['body']['extra']['task_id'] = new_task_id
                # self._requeue(kw_new)
                self._requeue(kw)
                function_result_status._has_requeue = True
            if isinstance(e, ExceptionForPushToDlxqueue):
                log_msg = f'函数 [{self.consuming_function.__name__}] 中发生错误 {type(e)}  {e}，消息放入死信队列 {self._dlx_queue_name}'
                # self.logger.critical(msg=f'{log_msg} \n')
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)
                self.publisher_of_dlx_queue.publish(kw['body'])  # 发布到死信队列，不重回当前队列
                function_result_status._has_to_dlx_queue = True
            if isinstance(e, kill_remote_task.TaskHasKilledError):
                log_msg = f'task_id 为 {task_id} , 函数 [{self.consuming_function.__name__}] 运行入参 {function_only_params}   ，已被远程指令杀死 {type(e)}  {e}'
                # self.logger.critical(msg=f'{log_msg} ')
                # self.error_file_logger.critical(msg=f'{log_msg} ')
                self.logger.critical(msg=log_msg)
                function_result_status._has_kill_task = True
            if isinstance(e, (ExceptionForRequeue, ExceptionForPushToDlxqueue, kill_remote_task.TaskHasKilledError)):
                return function_result_status
            log_msg = f'''函数 {self.consuming_function.__name__}  第{current_retry_times + 1}次运行发生错误，
                          函数运行时间是 {round(time.time() - t_start, 4)} 秒,  入参是  {function_only_params}    
                          {type(e)} {e} '''
            # self.logger.error(msg=f'{log_msg} \n', exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            # self.error_file_logger.error(msg=f'{log_msg} \n', exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            self.logger.error(msg=log_msg, exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            # traceback.print_exc()
            function_result_status.exception = f'{e.__class__.__name__}    {str(e)}'
            function_result_status.exception_msg = str(e)
            function_result_status.exception_type = e.__class__.__name__

            function_result_status.result = FunctionResultStatus.FUNC_RUN_ERROR
        return function_result_status

    # noinspection PyProtectedMember
    async def _async_run(self, kw: dict, ):
        # """虽然和上面有点大面积重复相似，这个是为了asyncio模式的，asyncio模式真的和普通同步模式的代码思维和形式区别太大，
        # 框架实现兼容async的消费函数很麻烦复杂，连并发池都要单独写"""
        try:
            t_start_run_fun = time.time()
            max_retry_times = self._get_priority_conf(kw, 'max_retry_times')
            current_function_result_status = FunctionResultStatus(self.queue_name, self.consuming_function.__name__, kw['body'], )
            current_retry_times = 0
            function_only_params = delete_keys_and_return_new_dict(kw['body'])
            for current_retry_times in range(max_retry_times + 1):
                current_function_result_status.run_times = current_retry_times + 1
                current_function_result_status.run_status = RunStatus.running
                self._result_persistence_helper.save_function_result_to_mongo(current_function_result_status)
                current_function_result_status = await self._async_run_consuming_function_with_confirm_and_retry(kw, current_retry_times=current_retry_times,
                                                                                                                 function_result_status=current_function_result_status)
                if current_function_result_status.success is True or current_retry_times == max_retry_times or current_function_result_status._has_requeue:
                    break
                else:
                    if self.consumer_params.retry_interval:
                        await asyncio.sleep(self.consumer_params.retry_interval)

            if not (current_function_result_status._has_requeue and self.BROKER_KIND in [BrokerEnum.RABBITMQ_AMQPSTORM, BrokerEnum.RABBITMQ_PIKA, BrokerEnum.RABBITMQ_RABBITPY]):
                await simple_run_in_executor(self._confirm_consume, kw)
            current_function_result_status.run_status = RunStatus.finish
            await simple_run_in_executor(self._result_persistence_helper.save_function_result_to_mongo, current_function_result_status)
            if self._get_priority_conf(kw, 'do_task_filtering'):
                # self._redis_filter.add_a_value(function_only_params)  # 函数执行成功后，添加函数的参数排序后的键值对字符串到set中。
                await simple_run_in_executor(self._redis_filter.add_a_value, function_only_params,self._get_priority_conf(kw, 'filter_str'))
            if current_function_result_status.success is False and current_retry_times == max_retry_times:
                log_msg = f'函数 {self.consuming_function.__name__} 达到最大重试次数 {self._get_priority_conf(kw, "max_retry_times")} 后,仍然失败， 入参是  {function_only_params} '
                if self.consumer_params.is_push_to_dlx_queue_when_retry_max_times:
                    log_msg += f'  。发送到死信队列 {self._dlx_queue_name} 中'
                    await simple_run_in_executor(self.publisher_of_dlx_queue.publish, kw['body'])
                # self.logger.critical(msg=f'{log_msg} \n', )
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)

                # self._confirm_consume(kw)  # 错得超过指定的次数了，就确认消费了。
            if self._get_priority_conf(kw, 'is_using_rpc_mode'):
                def push_result():
                    with RedisMixin().redis_db_filter_and_rpc_result.pipeline() as p:
                        current_function_result_status.rpc_result_expire_seconds = self.consumer_params.rpc_result_expire_seconds
                        p.lpush(kw['body']['extra']['task_id'],
                                Serialization.to_json_str(current_function_result_status.get_status_dict(without_datetime_obj=True)))
                        p.expire(kw['body']['extra']['task_id'], self.consumer_params.rpc_result_expire_seconds)
                        p.execute()

                if (current_function_result_status.success is False and current_retry_times == max_retry_times) or current_function_result_status.success is True:
                    await simple_run_in_executor(push_result)

            async with self._async_lock_for_count_execute_task_times_every_unit_time:
                self.metric_calculation.cal(t_start_run_fun, current_function_result_status)

            self.user_custom_record_process_info_func(current_function_result_status)  # 两种方式都可以自定义,记录结果.建议使用文档4.21.b的方式继承来重写
            await self.aio_user_custom_record_process_info_func(current_function_result_status)
            if self.consumer_params.user_custom_record_process_info_func:
                self.consumer_params.user_custom_record_process_info_func(current_function_result_status)

        except BaseException as e:
            log_msg = f' error 严重错误 {type(e)} {e} '
            # self.logger.critical(msg=f'{log_msg} \n', exc_info=True)
            # self.error_file_logger.critical(msg=f'{log_msg} \n', exc_info=True)
            self.logger.critical(msg=log_msg, exc_info=True)
        fct = funboost_current_task()
        fct.set_fct_context(None)

    # noinspection PyProtectedMember
    async def _async_run_consuming_function_with_confirm_and_retry(self, kw: dict, current_retry_times,
                                                                   function_result_status: FunctionResultStatus, ):
        """虽然和上面有点大面积重复相似，这个是为了asyncio模式的，asyncio模式真的和普通同步模式的代码思维和形式区别太大，
        框架实现兼容async的消费函数很麻烦复杂，连并发池都要单独写"""
        function_only_params = delete_keys_and_return_new_dict(kw['body']) if self._do_not_delete_extra_from_msg is False else kw['body']
        function_result_status.run_times = current_retry_times + 1
        # noinspection PyBroadException
        t_start = time.time()
        fct = funboost_current_task()
        fct_context = FctContext(function_params=function_only_params,
                                 full_msg=kw['body'],
                                 function_result_status=function_result_status,
                                 logger=self.logger,queue_name=self.queue_name,)
        fct.set_fct_context(fct_context)
        try:
            corotinue_obj = self.consuming_function(**self._convert_real_function_only_params_by_conusuming_function_kind(function_only_params,kw['body']['extra']))
            if not asyncio.iscoroutine(corotinue_obj):
                log_msg = f'''当前设置的并发模式为 async 并发模式，但消费函数不是异步协程函数，请不要把消费函数 {self.consuming_function.__name__} 的 concurrent_mode 设置错误'''
                # self.logger.critical(msg=f'{log_msg} \n')
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)
                # noinspection PyProtectedMember,PyUnresolvedReferences
                os._exit(444)
            if not self.consumer_params.function_timeout:
                rs = await corotinue_obj
                # rs = await asyncio.wait_for(corotinue_obj, timeout=4)
            else:
                rs = await asyncio.wait_for(corotinue_obj, timeout=self.consumer_params.function_timeout)
            function_result_status.result = rs
            function_result_status.success = True
            if self.consumer_params.log_level <= logging.DEBUG:
                result_str_to_be_print = str(rs)[:100] if len(str(rs)) < 100 else str(rs)[:100] + '  。。。。。  '
                self.logger.debug(f' 函数 {self.consuming_function.__name__}  '
                                  f'第{current_retry_times + 1}次 运行, 正确了，函数运行时间是 {round(time.time() - t_start, 4)} 秒,'
                                  f'入参是 【 {function_only_params} 】 ,结果是 {result_str_to_be_print}  。 {corotinue_obj} ')
        except BaseException as e:
            if isinstance(e, (ExceptionForRequeue,)):  # mongo经常维护备份时候插入不了或挂了，或者自己主动抛出一个ExceptionForRequeue类型的错误会重新入队，不受指定重试次数逇约束。
                log_msg = f'函数 [{self.consuming_function.__name__}] 中发生错误 {type(e)}  {e} 。 消息重新放入当前队列 {self._queue_name}'
                # self.logger.critical(msg=f'{log_msg} \n')
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)
                # time.sleep(1)  # 防止快速无限出错入队出队，导致cpu和中间件忙
                await asyncio.sleep(0.1)
                # return self._requeue(kw)
                await simple_run_in_executor(self._requeue, kw)
                function_result_status._has_requeue = True
            if isinstance(e, ExceptionForPushToDlxqueue):
                log_msg = f'函数 [{self.consuming_function.__name__}] 中发生错误 {type(e)}  {e}，消息放入死信队列 {self._dlx_queue_name}'
                # self.logger.critical(msg=f'{log_msg} \n')
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)
                await simple_run_in_executor(self.publisher_of_dlx_queue.publish, kw['body'])  # 发布到死信队列，不重回当前队列
                function_result_status._has_to_dlx_queue = True
            if isinstance(e, (ExceptionForRequeue, ExceptionForPushToDlxqueue)):
                return function_result_status
            log_msg = f'''函数 {self.consuming_function.__name__}  第{current_retry_times + 1}次运行发生错误，
                          函数运行时间是 {round(time.time() - t_start, 4)} 秒,  入参是  {function_only_params}     
                          原因是 {type(e)} {e} '''
            # self.logger.error(msg=f'{log_msg} \n', exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            # self.error_file_logger.error(msg=f'{log_msg} \n', exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            self.logger.error(msg=log_msg, exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            function_result_status.exception = f'{e.__class__.__name__}    {str(e)}'
            function_result_status.exception_msg = str(e)
            function_result_status.exception_type = e.__class__.__name__
            function_result_status.result = FunctionResultStatus.FUNC_RUN_ERROR
        return function_result_status

    @abc.abstractmethod
    def _confirm_consume(self, kw):
        """确认消费"""
        raise NotImplementedError

    def check_heartbeat_and_message_count(self):
        self.metric_calculation.msg_num_in_broker = self.publisher_of_same_queue.get_message_count()
        self.metric_calculation.last_get_msg_num_ts = time.time()
        if time.time() - self.metric_calculation.last_timestamp_print_msg_num > 600:
            if self.metric_calculation.msg_num_in_broker != -1:
                self.logger.info(f'队列 [{self._queue_name}] 中还有 [{self.metric_calculation.msg_num_in_broker}] 个任务')
            self.metric_calculation.last_timestamp_print_msg_num = time.time()
        if self.metric_calculation.msg_num_in_broker != 0:
            self.metric_calculation.last_timestamp_when_has_task_in_queue = time.time()
        return self.metric_calculation.msg_num_in_broker

    @abc.abstractmethod
    def _requeue(self, kw):
        """重新入队"""
        raise NotImplementedError

    def _apscheduler_job_miss(self, event):
        """
        这是 apscheduler 包的事件钩子。
        ev.function_args = job.args
        ev.function_kwargs = job.kwargs
        ev.function = job.func
        :return:
        """
        # print(event.scheduled_run_time)
        misfire_grace_time = self._get_priority_conf(event.function_kwargs["kw"], 'misfire_grace_time')
        log_msg = f''' 现在时间是 {time_util.DatetimeConverter().datetime_str} ,比此任务规定的本应该的运行时间 {event.scheduled_run_time} 相比 超过了指定的 {misfire_grace_time} 秒,放弃执行此任务 
                             {event.function_kwargs["kw"]["body"]} '''
        # self.logger.critical(msg=f'{log_msg} \n')
        # self.error_file_logger.critical(msg=f'{log_msg} \n')
        self.logger.critical(msg=log_msg)
        self._confirm_consume(event.function_kwargs["kw"])

        '''
        if self._get_priority_conf(event.function_kwargs["kw"], 'execute_delay_task_even_if_when_task_is_expired') is False:
            self.logger.critical(f'现在时间是 {time_util.DatetimeConverter().datetime_str} ,此任务设置的延时运行已过期 \n'
                                 f'{event.function_kwargs["kw"]["body"]} ， 此任务放弃执行')
            self._confirm_consume(event.function_kwargs["kw"])
        else:
            self.logger.warning(f'现在时间是 {time_util.DatetimeConverter().datetime_str} ,此任务设置的延时运行已过期 \n'
                                f'{event.function_kwargs["kw"]["body"]} ，'
                                f'但框架为了防止是任务积压导致消费延后，所以仍然使其运行一次')
            event.function(*event.function_args, **event.function_kwargs)
        '''

    def pause_consume(self):
        """从远程机器可以设置队列为暂停消费状态，funboost框架会自动停止消费，此功能需要配置好redis"""
        RedisMixin().redis_db_frame.hset(RedisKeys.REDIS_KEY_PAUSE_FLAG, self.queue_name,'1')

    def continue_consume(self):
        """从远程机器可以设置队列为暂停消费状态，funboost框架会自动继续消费，此功能需要配置好redis"""
        RedisMixin().redis_db_frame.hset(RedisKeys.REDIS_KEY_PAUSE_FLAG, self.queue_name,'0')

    @decorators.FunctionResultCacher.cached_function_result_for_a_time(120)
    def _judge_is_daylight(self):
        if self.consumer_params.is_do_not_run_by_specify_time_effect and (
                self.consumer_params.do_not_run_by_specify_time[0] < time_util.DatetimeConverter().time_str < self.consumer_params.do_not_run_by_specify_time[1]):
            self.logger.warning(
                f'现在时间是 {time_util.DatetimeConverter()} ，现在时间是在 {self.consumer_params.do_not_run_by_specify_time} 之间，不运行')
            return True

    def wait_for_possible_has_finish_all_tasks(self, minutes: int = 3):
        """
        判断队列所有任务是否消费完成了。
        由于是异步消费，和存在队列一边被消费，一边在推送，或者还有结尾少量任务还在确认消费者实际还没彻底运行完成。  但有时候需要判断 所有任务，务是否完成，提供一个不精确的判断，要搞清楚原因和场景后再慎用。
        一般是和celery一样，是永久运行的后台任务，永远无限死循环去任务执行任务，但有的人有判断是否执行完成的需求。
        :param minutes: 消费者连续多少分钟没执行任务任务 并且 消息队列中间件中没有，就判断为消费完成，为了防止是长耗时任务，一般判断完成是真正提供的minutes的2个周期时间。
        :return:

        """
        if minutes <= 1:
            raise ValueError('疑似完成任务，判断时间最少需要设置为3分钟内,最好是是10分钟')
        no_task_time = 0
        while 1:
            # noinspection PyBroadException
            message_count = self.metric_calculation.msg_num_in_broker
            # print(message_count,self._last_execute_task_time,time.time() - self._last_execute_task_time,no_task_time)
            if message_count == 0 and self.metric_calculation.last_execute_task_time != 0 and (time.time() - self.metric_calculation.last_execute_task_time) > minutes * 60:
                no_task_time += 30
            else:
                no_task_time = 0
            time.sleep(30)
            if no_task_time > minutes * 60:
                break

    def clear_filter_tasks(self):
        RedisMixin().redis_db_frame.delete(self._redis_filter_key_name)
        self.logger.warning(f'清空 {self._redis_filter_key_name} 键的任务过滤')

    def __str__(self):
        return f'队列为 {self.queue_name} 函数为 {self.consuming_function} 的消费者'


# noinspection PyProtectedMember
class ConcurrentModeDispatcher(FunboostFileLoggerMixin):

    def __init__(self, consumerx: AbstractConsumer):
        self.consumer = consumerx
        self._concurrent_mode = self.consumer.consumer_params.concurrent_mode
        self.timeout_deco = None
        if self._concurrent_mode in (ConcurrentModeEnum.THREADING, ConcurrentModeEnum.SINGLE_THREAD):
            # self.timeout_deco = decorators.timeout
            self.timeout_deco = dafunc.func_set_timeout  # 这个超时装饰器性能好很多。
        elif self._concurrent_mode == ConcurrentModeEnum.GEVENT:
            from funboost.concurrent_pool.custom_gevent_pool_executor import gevent_timeout_deco
            self.timeout_deco = gevent_timeout_deco
        elif self._concurrent_mode == ConcurrentModeEnum.EVENTLET:
            from funboost.concurrent_pool.custom_evenlet_pool_executor import evenlet_timeout_deco
            self.timeout_deco = evenlet_timeout_deco
        # self.logger.info(f'{self.consumer} 设置并发模式 {self.consumer.consumer_params.concurrent_mode}')

    def check_all_concurrent_mode(self):
        if GlobalVars.global_concurrent_mode is not None and \
                self.consumer.consumer_params.concurrent_mode != GlobalVars.global_concurrent_mode:
            # print({self.consumer._concurrent_mode, ConsumersManager.global_concurrent_mode})
            if not {self.consumer.consumer_params.concurrent_mode, GlobalVars.global_concurrent_mode}.issubset({ConcurrentModeEnum.THREADING,
                                                                                                                ConcurrentModeEnum.ASYNC,
                                                                                                                ConcurrentModeEnum.SINGLE_THREAD}):
                # threding、asyncio、solo 这几种模式可以共存。但同一个解释器不能同时选择 gevent + 其它并发模式，也不能 eventlet + 其它并发模式。
                raise ValueError('''由于猴子补丁的原因，同一解释器中不可以设置两种并发类型,请查看显示的所有消费者的信息，
                                 搜索 concurrent_mode 关键字，确保当前解释器内的所有消费者的并发模式只有一种(或可以共存),
                                 asyncio threading single_thread 并发模式可以共存，但gevent和threading不可以共存，
                                 gevent和eventlet不可以共存''')

        GlobalVars.global_concurrent_mode = self.consumer.consumer_params.concurrent_mode

    def build_pool(self):
        if self.consumer._concurrent_pool is not None:
            return self.consumer._concurrent_pool

        pool_type = None  # 是按照ThreadpoolExecutor写的三个鸭子类，公有方法名和功能写成完全一致，可以互相替换。
        if self._concurrent_mode == ConcurrentModeEnum.THREADING:
            # pool_type = CustomThreadPoolExecutor
            # pool_type = BoundedThreadPoolExecutor
            pool_type = FlexibleThreadPool
        elif self._concurrent_mode == ConcurrentModeEnum.GEVENT:
            from funboost.concurrent_pool.custom_gevent_pool_executor import get_gevent_pool_executor
            pool_type = get_gevent_pool_executor
        elif self._concurrent_mode == ConcurrentModeEnum.EVENTLET:
            from funboost.concurrent_pool.custom_evenlet_pool_executor import get_eventlet_pool_executor
            pool_type = get_eventlet_pool_executor
        elif self._concurrent_mode == ConcurrentModeEnum.ASYNC:
            pool_type = AsyncPoolExecutor
        elif self._concurrent_mode == ConcurrentModeEnum.SINGLE_THREAD:
            pool_type = SoloExecutor
        # elif self._concurrent_mode == ConcurrentModeEnum.LINUX_FORK:
        #     pool_type = SimpleProcessPool
        # pool_type = BoundedProcessPoolExecutor
        # from concurrent.futures import ProcessPoolExecutor
        # pool_type = ProcessPoolExecutor
        if self._concurrent_mode == ConcurrentModeEnum.ASYNC:
            self.consumer._concurrent_pool = self.consumer.consumer_params.specify_concurrent_pool or pool_type(
                self.consumer.consumer_params.concurrent_num,
                  specify_async_loop=self.consumer.consumer_params.specify_async_loop,
                  is_auto_start_specify_async_loop_in_child_thread=self.consumer.consumer_params.is_auto_start_specify_async_loop_in_child_thread)
        else:
            # print(pool_type)
            self.consumer._concurrent_pool = self.consumer.consumer_params.specify_concurrent_pool or pool_type(self.consumer.consumer_params.concurrent_num)
        # print(self._concurrent_mode,self.consumer._concurrent_pool)
        return self.consumer._concurrent_pool

    # def schedulal_task_with_no_block(self):
    #     if ConsumersManager.schedual_task_always_use_thread:
    #         t = Thread(target=self.consumer.keep_circulating(1)(self.consumer._dispatch_task))
    #         ConsumersManager.schedulal_thread_to_be_join.append(t)
    #         t.start()
    #     else:
    #         if self._concurrent_mode in [ConcurrentModeEnum.THREADING, ConcurrentModeEnum.ASYNC,
    #                                      ConcurrentModeEnum.SINGLE_THREAD, ]:
    #             t = Thread(target=self.consumer.keep_circulating(1)(self.consumer._dispatch_task))
    #             ConsumersManager.schedulal_thread_to_be_join.append(t)
    #             t.start()
    #         elif self._concurrent_mode == ConcurrentModeEnum.GEVENT:
    #             import gevent
    #             g = gevent.spawn(self.consumer.keep_circulating(1)(self.consumer._dispatch_task), )
    #             ConsumersManager.schedulal_thread_to_be_join.append(g)
    #         elif self._concurrent_mode == ConcurrentModeEnum.EVENTLET:
    #             import eventlet
    #             g = eventlet.spawn(self.consumer.keep_circulating(1)(self.consumer._dispatch_task), )
    #             ConsumersManager.schedulal_thread_to_be_join.append(g)

    def schedulal_task_with_no_block(self):
        self.consumer.keep_circulating(1, block=False, daemon=False)(self.consumer._dispatch_task)()


def wait_for_possible_has_finish_all_tasks_by_conusmer_list(consumer_list: typing.List[AbstractConsumer], minutes: int = 3):
    """
   判断多个消费者是否消费完成了。
   由于是异步消费，和存在队列一边被消费，一边在推送，或者还有结尾少量任务还在确认消费者实际还没彻底运行完成。  但有时候需要判断 所有任务，务是否完成，提供一个不精确的判断，要搞清楚原因和场景后再慎用。
   一般是和celery一样，是永久运行的后台任务，永远无限死循环去任务执行任务，但有的人有判断是否执行完成的需求。
   :param consumer_list: 多个消费者列表
   :param minutes: 消费者连续多少分钟没执行任务任务 并且 消息队列中间件中没有，就判断为消费完成。为了防止是长耗时任务，一般判断完成是真正提供的minutes的2个周期时间。
   :return:

    """
    with BoundedThreadPoolExecutor(len(consumer_list)) as pool:
        for consumer in consumer_list:
            pool.submit(consumer.wait_for_possible_has_finish_all_tasks(minutes))


class MetricCalculation:
    UNIT_TIME_FOR_COUNT = 10 # 这个不要随意改,需要其他地方配合,每隔多少秒计数，显示单位时间内执行多少次，暂时固定为10秒。

    def __init__(self,conusmer:AbstractConsumer) -> None:
        self.consumer = conusmer

        self.unit_time_for_count = self.UNIT_TIME_FOR_COUNT  # 
        self.execute_task_times_every_unit_time_temp = 0  # 每单位时间执行了多少次任务。
        self.execute_task_times_every_unit_time_temp_fail =0  # 每单位时间执行了多少次任务失败。
        self.current_time_for_execute_task_times_every_unit_time = time.time()
        self.consuming_function_cost_time_total_every_unit_time_tmp = 0
        self.last_execute_task_time = time.time()  # 最近一次执行任务的时间。
        self.last_x_s_execute_count = 0
        self.last_x_s_execute_count_fail = 0
        self.last_x_s_avarage_function_spend_time = None
        self.last_show_remaining_execution_time = 0
        self.show_remaining_execution_time_interval = 300
        self.msg_num_in_broker = 0
        self.last_get_msg_num_ts = 0
        self.last_timestamp_when_has_task_in_queue = 0
        self.last_timestamp_print_msg_num = 0

        self.total_consume_count_from_start =0
        self.total_consume_count_from_start_fail =0
        self.total_cost_time_from_start = 0  # 函数运行累计花费时间
        self.last_x_s_total_cost_time = None

    def cal(self,t_start_run_fun:float,current_function_result_status:FunctionResultStatus):
        self.last_execute_task_time = time.time()
        current_msg_cost_time = time.time() - t_start_run_fun
        self.execute_task_times_every_unit_time_temp += 1
        self.total_consume_count_from_start  +=1
        self.total_cost_time_from_start += current_msg_cost_time
        if current_function_result_status.success is False:
            self.execute_task_times_every_unit_time_temp_fail += 1
            self.total_consume_count_from_start_fail +=1
        self.consuming_function_cost_time_total_every_unit_time_tmp += current_msg_cost_time
        
        if time.time() - self.current_time_for_execute_task_times_every_unit_time > self.unit_time_for_count:
            self.last_x_s_execute_count = self.execute_task_times_every_unit_time_temp
            self.last_x_s_execute_count_fail = self.execute_task_times_every_unit_time_temp_fail
            self.last_x_s_total_cost_time = self.consuming_function_cost_time_total_every_unit_time_tmp
            self.last_x_s_avarage_function_spend_time = round(self.last_x_s_total_cost_time / self.last_x_s_execute_count, 3)
            msg = f'{self.unit_time_for_count} 秒内执行了 {self.last_x_s_execute_count} 次函数 [ {self.consumer.consuming_function.__name__} ] ,' \
                  f'失败了{self.last_x_s_execute_count_fail} 次,函数平均运行耗时 {self.last_x_s_avarage_function_spend_time} 秒。 '
            self.consumer.logger.info(msg)
            if time.time() - self.last_show_remaining_execution_time > self.show_remaining_execution_time_interval:
                self.msg_num_in_broker = self.consumer.publisher_of_same_queue.get_message_count()
                self.last_get_msg_num_ts = time.time()
                if self.msg_num_in_broker != -1:  # 有的中间件无法统计或没实现统计队列剩余数量的，统一返回的是-1，不显示这句话。
                    need_time = time_util.seconds_to_hour_minute_second(self.msg_num_in_broker / (self.execute_task_times_every_unit_time_temp / self.unit_time_for_count) /
                                                                        self.consumer._distributed_consumer_statistics.active_consumer_num)
                    msg += f''' 预计还需要 {need_time} 时间 才能执行完成 队列 {self.consumer.queue_name} 中的 {self.msg_num_in_broker} 个剩余任务'''
                    self.consumer.logger.info(msg)
                self.last_show_remaining_execution_time = time.time()
            if self.consumer.consumer_params.is_send_consumer_hearbeat_to_redis is True:
                RedisMixin().redis_db_frame.hincrby(RedisKeys.FUNBOOST_QUEUE__RUN_COUNT_MAP,self.consumer.queue_name,self.execute_task_times_every_unit_time_temp)
                RedisMixin().redis_db_frame.hincrby(RedisKeys.FUNBOOST_QUEUE__RUN_FAIL_COUNT_MAP,self.consumer.queue_name,self.execute_task_times_every_unit_time_temp_fail)

            self.current_time_for_execute_task_times_every_unit_time = time.time()
            self.consuming_function_cost_time_total_every_unit_time_tmp = 0
            self.execute_task_times_every_unit_time_temp = 0
            self.execute_task_times_every_unit_time_temp_fail = 0

    def get_report_hearbeat_info(self) ->dict:
        return {
            'unit_time_for_count':self.unit_time_for_count,
            'last_x_s_execute_count':self.last_x_s_execute_count,
            'last_x_s_execute_count_fail':self.last_x_s_execute_count_fail,
            'last_execute_task_time':self.last_execute_task_time,
            'last_x_s_avarage_function_spend_time':self.last_x_s_avarage_function_spend_time,
            # 'last_show_remaining_execution_time':self.last_show_remaining_execution_time,
            'msg_num_in_broker':self.msg_num_in_broker,
            'current_time_for_execute_task_times_every_unit_time':self.current_time_for_execute_task_times_every_unit_time,
            'last_timestamp_when_has_task_in_queue':self.last_timestamp_when_has_task_in_queue,
            'total_consume_count_from_start':self.total_consume_count_from_start,
            'total_consume_count_from_start_fail':self.total_consume_count_from_start_fail,
            'total_cost_time_from_start':self.total_cost_time_from_start,
            'last_x_s_total_cost_time':self.last_x_s_total_cost_time,
            'avarage_function_spend_time_from_start':round(self.total_cost_time_from_start / self.total_consume_count_from_start,3) if self.total_consume_count_from_start else None,
        }


class DistributedConsumerStatistics(RedisMixin, FunboostFileLoggerMixin):
    """
    为了兼容模拟mq的中间件（例如redis，他没有实现amqp协议，redis的list结构和真mq差远了），获取一个队列有几个连接活跃消费者数量。
    分布式环境中的消费者统计。主要目的有3点

    1、统计活跃消费者数量用于分布式控频。
        获取分布式的消费者数量后，用于分布式qps控频。如果不获取全环境中的消费者数量，则只能用于当前进程中的消费控频。
        即使只有一台机器，例如把xx.py启动3次，xx.py的consumer设置qps为10，如果不使用分布式控频，会1秒钟最终运行30次函数而不是10次。

    2、记录分布式环境中的活跃消费者的所有消费者 id，如果消费者id不在此里面说明已掉线或关闭，消息可以重新分发，用于不支持服务端天然消费确认的中间件。

    3、从redis中获取停止和暂停状态，以便支持在别的地方发送命令停止或者暂停消费。
    """
    SHOW_CONSUMER_NUM_INTERVAL = 600
    HEARBEAT_EXPIRE_SECOND = 25
    SEND_HEARTBEAT_INTERVAL = 10

    if HEARBEAT_EXPIRE_SECOND < SEND_HEARTBEAT_INTERVAL * 2:
        raise ValueError(f'HEARBEAT_EXPIRE_SECOND:{HEARBEAT_EXPIRE_SECOND} , SEND_HEARTBEAT_INTERVAL:{SEND_HEARTBEAT_INTERVAL} ')

    def __init__(self, consumer: AbstractConsumer):
        # self._consumer_identification = consumer_identification
        # self._consumer_identification_map = consumer_identification_map
        # self._queue_name = queue_name
        self._consumer_identification = consumer.consumer_identification
        self._consumer_identification_map = consumer.consumer_identification_map
        self._queue_name = consumer.queue_name
        self._consumer = consumer
        self._redis_key_name = f'funboost_hearbeat_queue__str:{self._queue_name}'
        self.active_consumer_num = 1
        self._last_show_consumer_num_timestamp = 0

        self._queue__consumer_identification_map_key_name = RedisKeys.gen_funboost_hearbeat_queue__dict_key_by_queue_name(self._queue_name)
        self._server__consumer_identification_map_key_name = RedisKeys.gen_funboost_hearbeat_server__dict_key_by_ip(nb_log_config_default.computer_ip)

    def run(self):
        self.send_heartbeat()
        self._consumer.keep_circulating(self.SEND_HEARTBEAT_INTERVAL, block=False, daemon=False)(self.send_heartbeat)()

    def _send_heartbeat_with_dict_value(self, redis_key, ):
        # 发送当前消费者进程心跳的，值是字典，按一个机器或者一个队列运行了哪些进程。

        results = self.redis_db_frame.smembers(redis_key)
        with self.redis_db_frame.pipeline() as p:
            for result in results:
                result_dict = Serialization.to_dict(result)
                if self.timestamp() - result_dict['hearbeat_timestamp'] > self.HEARBEAT_EXPIRE_SECOND \
                        or self._consumer_identification_map['consumer_uuid'] == result_dict['consumer_uuid']:
                    # 因为这个是10秒钟运行一次，15秒还没更新，那肯定是掉线了。如果消费者本身是自己也先删除。
                    p.srem(redis_key, result)
            self._consumer_identification_map['hearbeat_datetime_str'] = time_util.DatetimeConverter().datetime_str
            self._consumer_identification_map['hearbeat_timestamp'] = self.timestamp()
            self._consumer_identification_map.update(self._consumer.metric_calculation.get_report_hearbeat_info())
            value = Serialization.to_json_str(self._consumer_identification_map, )
            p.sadd(redis_key, value)
            p.execute()


    def _send_msg_num(self):
        dic = {'msg_num_in_broker':self._consumer.metric_calculation.msg_num_in_broker,
               'last_get_msg_num_ts':self._consumer.metric_calculation.last_get_msg_num_ts,
               'report_ts':time.time(),
               }
        self.redis_db_frame.hset(RedisKeys.QUEUE__MSG_COUNT_MAP, self._consumer.queue_name, json.dumps(dic))

    def send_heartbeat(self):
        # 根据队列名心跳的，值是字符串，方便值作为其他redis的键名

        results = self.redis_db_frame.smembers(self._redis_key_name)
        with self.redis_db_frame.pipeline() as p:
            for result in results:
                if self.timestamp() - float(result.split('&&')[-1]) > self.HEARBEAT_EXPIRE_SECOND or \
                        self._consumer_identification == result.split('&&')[0]:  # 因为这个是10秒钟运行一次，15秒还没更新，那肯定是掉线了。如果消费者本身是自己也先删除。
                    p.srem(self._redis_key_name, result)
            p.sadd(self._redis_key_name, f'{self._consumer_identification}&&{self.timestamp()}')
            p.execute()

        self._send_heartbeat_with_dict_value(self._queue__consumer_identification_map_key_name)
        self._send_heartbeat_with_dict_value(self._server__consumer_identification_map_key_name)
        self._show_active_consumer_num()
        self._get_stop_and_pause_flag_from_redis()
        self._send_msg_num()

    def _show_active_consumer_num(self):
        self.active_consumer_num = self.redis_db_frame.scard(self._redis_key_name) or 1
        if time.time() - self._last_show_consumer_num_timestamp > self.SHOW_CONSUMER_NUM_INTERVAL:
            self.logger.info(f'分布式所有环境中使用 {self._queue_name} 队列的，一共有 {self.active_consumer_num} 个消费者')
            self._last_show_consumer_num_timestamp = time.time()

    def get_queue_heartbeat_ids(self, without_time: bool):
        if without_time:
            return [idx.split('&&')[0] for idx in self.redis_db_frame.smembers(self._redis_key_name)]
        else:
            return [idx for idx in self.redis_db_frame.smembers(self._redis_key_name)]

    # noinspection PyProtectedMember
    def _get_stop_and_pause_flag_from_redis(self):
        stop_flag = self.redis_db_frame.hget(RedisKeys.REDIS_KEY_STOP_FLAG,self._consumer.queue_name)
        if stop_flag is not None and int(stop_flag) == 1:
            self._consumer._stop_flag = 1
        else:
            self._consumer._stop_flag = 0

        pause_flag = self.redis_db_frame.hget(RedisKeys.REDIS_KEY_PAUSE_FLAG,self._consumer.queue_name)
        if pause_flag is not None and int(pause_flag) == 1:
            self._consumer._pause_flag.set()
        else:
            self._consumer._pause_flag.clear()
  
      

```

### 代码文件: funboost\consumers\celery_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32

import time
from funboost.assist.celery_helper import CeleryHelper, celery_app
from celery import Task as CeleryTask
from funboost.consumers.base_consumer import AbstractConsumer


class CeleryConsumer(AbstractConsumer):
    """
    celery作为中间件实现的。
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'celery_task_config': {}}

    # celery的可以配置项大全  https://docs.celeryq.dev/en/stable/userguide/configuration.html#new-lowercase-settings
    # celery @app.task() 所有可以配置项可以看  D:\ProgramData\Miniconda3\Lib\site-packages\celery\app\task.py

    '''
        #: Execution strategy used, or the qualified name of one.
        Strategy = 'celery.worker.strategy:default'

        #: Request class used, or the qualified name of one.
        Request = 'celery.worker.request:Request'

        #: The application instance associated with this task class.
        _app = None

        #: Name of the task.
        name = None

        #: Enable argument checking.
        #: You can set this to false if you don't want the signature to be
        #: checked when calling the task.
        #: Defaults to :attr:`app.strict_typing <@Celery.strict_typing>`.
        typing = None

        #: Maximum number of retries before giving up.  If set to :const:`None`,
        #: it will **never** stop retrying.
        max_retries = 3

        #: Default time in seconds before a retry of the task should be
        #: executed.  3 minutes by default.
        default_retry_delay = 3 * 60

        #: Rate limit for this task type.  Examples: :const:`None` (no rate
        #: limit), `'100/s'` (hundred tasks a second), `'100/m'` (hundred tasks
        #: a minute),`'100/h'` (hundred tasks an hour)
        rate_limit = None

        #: If enabled the worker won't store task state and return values
        #: for this task.  Defaults to the :setting:`task_ignore_result`
        #: setting.
        ignore_result = None

        #: If enabled the request will keep track of subtasks started by
        #: this task, and this information will be sent with the result
        #: (``result.children``).
        trail = True

        #: If enabled the worker will send monitoring events related to
        #: this task (but only if the worker is configured to send
        #: task related events).
        #: Note that this has no effect on the task-failure event case
        #: where a task is not registered (as it will have no task class
        #: to check this flag).
        send_events = True

        #: When enabled errors will be stored even if the task is otherwise
        #: configured to ignore results.
        store_errors_even_if_ignored = None

        #: The name of a serializer that are registered with
        #: :mod:`kombu.serialization.registry`.  Default is `'json'`.
        serializer = None

        #: Hard time limit.
        #: Defaults to the :setting:`task_time_limit` setting.
        time_limit = None

        #: Soft time limit.
        #: Defaults to the :setting:`task_soft_time_limit` setting.
        soft_time_limit = None

        #: The result store backend used for this task.
        backend = None

        #: If enabled the task will report its status as 'started' when the task
        #: is executed by a worker.  Disabled by default as the normal behavior
        #: is to not report that level of granularity.  Tasks are either pending,
        #: finished, or waiting to be retried.
        #:
        #: Having a 'started' status can be useful for when there are long
        #: running tasks and there's a need to report what task is currently
        #: running.
        #:
        #: The application default can be overridden using the
        #: :setting:`task_track_started` setting.
        track_started = None

        #: When enabled messages for this task will be acknowledged **after**
        #: the task has been executed, and not *just before* (the
        #: default behavior).
        #:
        #: Please note that this means the task may be executed twice if the
        #: worker crashes mid execution.
        #:
        #: The application default can be overridden with the
        #: :setting:`task_acks_late` setting.
        acks_late = None

        #: When enabled messages for this task will be acknowledged even if it
        #: fails or times out.
        #:
        #: Configuring this setting only applies to tasks that are
        #: acknowledged **after** they have been executed and only if
        #: :setting:`task_acks_late` is enabled.
        #:
        #: The application default can be overridden with the
        #: :setting:`task_acks_on_failure_or_timeout` setting.
        acks_on_failure_or_timeout = None

        #: Even if :attr:`acks_late` is enabled, the worker will
        #: acknowledge tasks when the worker process executing them abruptly
        #: exits or is signaled (e.g., :sig:`KILL`/:sig:`INT`, etc).
        #:
        #: Setting this to true allows the message to be re-queued instead,
        #: so that the task will execute again by the same worker, or another
        #: worker.
        #:
        #: Warning: Enabling this can cause message loops; make sure you know
        #: what you're doing.
        reject_on_worker_lost = None

        #: Tuple of expected exceptions.
        #:
        #: These are errors that are expected in normal operation
        #: and that shouldn't be regarded as a real error by the worker.
        #: Currently this means that the state will be updated to an error
        #: state, but the worker won't log the event as an error.
        throws = ()

        #: Default task expiry time.
        expires = None

        #: Default task priority.
        priority = None

        #: Max length of result representation used in logs and events.
        resultrepr_maxsize = 1024

        #: Task request stack, the current request will be the topmost.
        request_stack = None
    '''

    def custom_init(self):
        # 这就是核心，@boost时候会 @ celery app.task装饰器
        celery_task_deco_options = dict(name=self. queue_name,
                                        max_retries=self.consumer_params.max_retry_times, bind=True)
        if self.consumer_params.qps:
            celery_task_deco_options['rate_limit'] = f'{self.consumer_params.qps}/s'
        if self.consumer_params.function_timeout:
            celery_task_deco_options['soft_time_limit'] = self.consumer_params.function_timeout
        celery_task_deco_options.update(self.consumer_params.broker_exclusive_config['celery_task_config'])

        @celery_app.task(**celery_task_deco_options)
        def f(this: CeleryTask, *args, **kwargs):
            self.logger.debug(f' 这条消息是 celery 从 {self.queue_name} 队列中取出 ,是由 celery 框架调度 {self.consuming_function.__name__} 函数处理: args:  {args} ,  kwargs: {kwargs}')
            # return self.consuming_function(*args, **kwargs) # 如果没有声明 autoretry_for ，那么消费函数出错了就不会自动重试了。
            try:
                return self.consuming_function(*args, **kwargs)
            except Exception as exc:  # 改成自动重试。
                # print(this.request.__dict__,dir(this))
                if this.request.retries != self.consumer_params.max_retry_times:
                    log_msg = f'fun: {self.consuming_function}  args: {args} , kwargs: {kwargs} 消息第{this.request.retries}次运行出错,  {exc} \n'
                    self.logger.error(log_msg, exc_info=self.consumer_params.is_print_detail_exception)
                else:
                    log_msg = f'fun: {self.consuming_function}  args: {args} , kwargs: {kwargs} 消息达到最大重试次数{this.request.retries}次仍然出错,  {exc} \n'
                    self.logger.critical(log_msg, exc_info=self.consumer_params.is_print_detail_exception)
                # 发生异常，尝试重试任务,countdown 是多少秒后重试
                raise this.retry(exc=exc, countdown=self.consumer_params.retry_interval)

        celery_app.conf.task_routes.update({self.queue_name: {"queue": self.queue_name}})  # 自动配置celery每个函数使用不同的队列名。
        self.celery_task = f
        CeleryHelper.concurrent_mode = self.consumer_params.concurrent_mode

    def start_consuming_message(self):
        # 不单独每个函数都启动一次celery的worker消费，是把要消费的 queue name放到列表中，CeleryHelper.realy_start_celery_worker 一次性启动多个函数消费。
        CeleryHelper.add_start_work_celery_queue_name(self.queue_name)
        super().start_consuming_message()

    def _dispatch_task(self):
        """ 完全由celery框架接管控制消费，不使用funboost的AbstractConsumer的_run"""
        while 1:
            time.sleep(100)

    def _confirm_consume(self, kw):
        """完全由celery框架接管控制消费和ack确认消费，不需要funboost自己的代码来执行"""
        pass

    def _requeue(self, kw):
        pass

```

### 代码文件: funboost\consumers\confirm_mixin.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/23 0023 21:10
import json
import time
from funboost.utils.redis_manager import RedisMixin
from funboost.utils import decorators
from funboost.core.serialization import Serialization
"""
此模块是依赖redis的确认消费，所以比较复杂。
"""


# noinspection PyUnresolvedReferences
class ConsumerConfirmMixinWithTheHelpOfRedis(RedisMixin):
    """
    使用redis的zset结构，value为任务，score为时间戳，这样具有良好的按时间范围搜索特性和删除特性。
    把这个抽离出来了。，是因为这个不仅可以给redis做消息确认，也可以给其他不支持消费确认的消息中间件增加消费确认。

    """
    # 超时未确认的时间，例如取出来后600秒都没有确认消费，就重新消费。这在rabbitmq和nsq对应的相同功能参数是heartbeat_interval。
    # 这个弊端很多，例如一个函数本身就需要10分钟以上，重回队列会造成死循环消费。已近废弃了。基于消费者的心跳是确认消费好的方式。
    UNCONFIRMED_TIMEOUT = 600

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._unack_zset_name = f'{self._queue_name}__unack'

    def start_consuming_message(self):
        self.consumer_params.is_send_consumer_hearbeat_to_redis = True
        super().start_consuming_message()
        self.keep_circulating(60, block=False)(self._requeue_tasks_which_unconfirmed)()

    def _add_task_str_to_unack_zset(self, task_str, ):
        self.redis_db_frame.zadd(self._unack_zset_name, {task_str: time.time()})

    def _confirm_consume(self, kw):
        self.redis_db_frame.zrem(self._unack_zset_name, kw['task_str'])

    def _requeue_tasks_which_unconfirmed(self):
        """不使用这种方案，不适合本来来就需要长耗时的函数，很死板"""
        # 防止在多个进程或多个机器中同时做扫描和放入未确认消费的任务。使用个分布式锁。
        lock_key = f'fsdf_lock__requeue_tasks_which_unconfirmed_timeout:{self._queue_name}'
        with decorators.RedisDistributedLockContextManager(self.redis_db_frame, lock_key, ) as lock:
            if lock.has_aquire_lock:
                time_max = time.time() - self.UNCONFIRMED_TIMEOUT
                for value in self.redis_db_frame.zrangebyscore(self._unack_zset_name, 0, time_max):
                    self.logger.warning(f'向 {self._queue_name} 重新放入未消费确认的任务 {value}')
                    self._requeue({'body': Serialization.to_dict(value)})
                    self.redis_db_frame.zrem(self._unack_zset_name, value)
                self.logger.info(f'{self._unack_zset_name} 中有待确认消费任务的数量是'
                                 f' {self.redis_db_frame.zcard(self._unack_zset_name)}')


# noinspection PyUnresolvedReferences
class ConsumerConfirmMixinWithTheHelpOfRedisByHearbeat(ConsumerConfirmMixinWithTheHelpOfRedis):
    """
    使用的是根据心跳，判断非活跃消费者，将非活跃消费者对应的unack zset的重新回到消费队列。
    """
    SCAN_COUNT = 2000

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._unack_zset_name = f'{self._queue_name}__unack_id_{self.consumer_identification}'
        self.consumer_params.is_send_consumer_hearbeat_to_redis = True
        self._last_show_unacked_msg_num_log = 0

    def _requeue_tasks_which_unconfirmed(self):
        lock_key = f'fsdf_lock__requeue_tasks_which_unconfirmed:{self._queue_name}'
        with decorators.RedisDistributedLockContextManager(self.redis_db_frame, lock_key, ).set_log_level(30) as lock:
            if lock.has_aquire_lock:
                # self._distributed_consumer_statistics.send_heartbeat() # 已经周期运行了。
                current_queue_hearbeat_ids = self._distributed_consumer_statistics.get_queue_heartbeat_ids(without_time=True)
                current_queue_unacked_msg_queues = self.redis_db_frame.scan(0, f'{self._queue_name}__unack_id_*', count=self.SCAN_COUNT) # 不要在funboost的队列所在db放弃他缓存keys，要保持db的keys少于1000，否则要多次scan。
                # print(current_queue_unacked_msg_queues)
                for current_queue_unacked_msg_queue in current_queue_unacked_msg_queues[1]:
                    current_queue_unacked_msg_queue_name = current_queue_unacked_msg_queue
                    if time.time() - self._last_show_unacked_msg_num_log > 600:
                        self.logger.info(f'{current_queue_unacked_msg_queue_name} 中有待确认消费任务的数量是'
                                         f' {self.redis_db_frame.zcard(current_queue_unacked_msg_queue_name)}')
                        self._last_show_unacked_msg_num_log = time.time()
                    if current_queue_unacked_msg_queue_name.split(f'{self._queue_name}__unack_id_')[1] not in current_queue_hearbeat_ids:
                        self.logger.warning(f'{current_queue_unacked_msg_queue_name} 是掉线或关闭消费者的')
                        while 1:
                            if self.redis_db_frame.exists(current_queue_unacked_msg_queue_name):
                                for unacked_task_str in self.redis_db_frame.zrevrange(current_queue_unacked_msg_queue_name, 0, 1000):
                                    self.logger.warning(f'从 {current_queue_unacked_msg_queue_name} 向 {self._queue_name} 重新放入掉线消费者未消费确认的任务'
                                                        f' {unacked_task_str}')
                                    # self.redis_db_frame.lpush(self._queue_name, unacked_task_str)
                                    self.publisher_of_same_queue.publish(unacked_task_str) # redis优先级队列的入队不一样，不使用上面。
                                    self.redis_db_frame.zrem(current_queue_unacked_msg_queue_name, unacked_task_str)
                    else:
                        pass
                        # print('是活跃消费者')

```

### 代码文件: funboost\consumers\dramatiq_consumer.py
```python
import time

import dramatiq

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.assist.dramatiq_helper import DramatiqHelper


class DramatiqConsumer(AbstractConsumer):
    """
    dramatiq作为中间件实现的。
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'dramatiq_actor_options': {}}
    """
    dramatiq_actor_options 的值可以是：
     {'max_age', 'throws', 'pipe_target', 'pipe_ignore', 'on_success', 'retry_when', 'time_limit', 'min_backoff', 'max_retries', 'max_backoff', 'notify_shutdown', 'on_failure'}
    """

    def custom_init(self):
        # 这就是核心，
        dramatiq_actor_options = self.consumer_params.broker_exclusive_config['dramatiq_actor_options']
        if self.consumer_params.function_timeout:
            dramatiq_actor_options['time_limit'] = self.consumer_params.function_timeout * 1000  # dramatiq的超时单位是毫秒，funboost是秒。
        dramatiq_actor_options['max_retries'] = self.consumer_params.max_retry_times

        @dramatiq.actor(actor_name=self.queue_name, queue_name=self.queue_name,
                        **dramatiq_actor_options)
        def f(*args, **kwargs):
            self.logger.debug(f' 这条消息是 dramatiq 从 {self.queue_name} 队列中取出 ,是由 dramatiq 框架调度 {self.consuming_function.__name__} 函数处理: args:  {args} ,  kwargs: {kwargs}')
            return self.consuming_function(*args, **kwargs)

        DramatiqHelper.queue_name__actor_map[self.queue_name] = f

    def start_consuming_message(self):
        # 不单独每个函数都启动一次celery的worker消费，是把要消费的 queue name放到列表中，realy_start_dramatiq_worker 一次性启动多个函数消费。
        DramatiqHelper.to_be_start_work_celery_queue_name_set.add(self.queue_name)
        super().start_consuming_message()

    def _dispatch_task(self):
        """ 完全由dramatiq框架接管控制消费，不使用funboost的AbstractConsumer的_run"""
        while 1:
            time.sleep(100)

    def _confirm_consume(self, kw):
        """dramatiq框架默认自带，不需要funboost实现"""

    def _requeue(self, kw):
        pass

```

### 代码文件: funboost\consumers\empty_consumer.py
```python
﻿# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/8 0008 13:32

import abc
from funboost.consumers.base_consumer import AbstractConsumer


class EmptyConsumer(AbstractConsumer, metaclass=abc.ABCMeta):
    """
    一个空的消费者基类，作为自定义 Broker 的模板。

    这个类其实是多余的，因为用户完全可以继承AbstractConsumer，然后实现custom_init方法，然后实现_dispatch_task, _confirm_consume, _requeue方法来新增自定义broker。
    这个类是为了清晰明确的告诉你，仅仅需要下面三个方法，就可以实现一个自定义broker，因为AbstractConsumer基类功能太丰富了，基类方法是在太多了，用户不知道需要继承重写哪方法
    
    
    """
    def custom_init(self):
        pass

    @abc.abstractmethod
    def _dispatch_task(self):
        """
        核心调度任务。此方法需要实现一个循环，负责从你的中间件中获取消息，
        然后调用 `self._submit_task(msg)` 将任务提交到框架的并发池中执行。 可以参考funboos源码中的各种消费者实现。
        """
        raise NotImplemented('not realization')

    @abc.abstractmethod
    def _confirm_consume(self, kw):
        """确认消费，就是ack概念"""
        raise NotImplemented('not realization')

    @abc.abstractmethod
    def _requeue(self, kw):
        """重新入队"""
        raise NotImplemented('not realization')

```

### 代码文件: funboost\consumers\faststream_consumer.py
```python
import asyncio
import json
import threading
import time

from funboost import EmptyConsumer
from funboost.assist.faststream_helper import broker,app,get_broker
from faststream import FastStream,Context
from faststream.annotations import Logger

from funboost.concurrent_pool.async_helper import simple_run_in_executor
from funboost.core.helper_funs import delete_keys_and_return_new_dict


class FastStreamConsumer(EmptyConsumer):
    def custom_init(self):
        self.broker = get_broker(max_consumers=self.consumer_params.concurrent_num)
        subc = self.broker.subscriber(self.queue_name)
        # @broker.subscriber(self.queue_name)
        async def f(msg:str, logger: Logger,message=Context(),broker=Context(),context=Context(),):
            self.logger.debug(f' 这条消息是 faststream 从 {self.queue_name} 队列中取出 ,是由 faststream 框架调度 {self.consuming_function.__name__} 函数处理,msg:{message} {context}')
            # print(logger.name)
            # return self.consuming_function(*args, **kwargs) # 如果没有声明 autoretry_for ，那么消费函数出错了就不会自动重试了。
            # print(msg)
            function_only_params = delete_keys_and_return_new_dict(Serialization.to_dict(msg))
            if self._consuming_function_is_asyncio:
                result = await self.consuming_function(**function_only_params)
            else:
                result = await simple_run_in_executor(self.consuming_function,**function_only_params)
            # print(result)
            return result
        subc(f)
        self.faststream_subscriber = subc

    def _dispatch_task(self):
        """ 完全由faststream框架接管控制消费，不使用funboost的AbstractConsumer的_run"""
        while 1:
            time.sleep(100)


    def _confirm_consume(self, kw):
        pass

    def start_consuming_message(self):
        def _f():
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.broker.connect())
            loop.run_until_complete(self.faststream_subscriber.start())
            loop.run_forever()
        self.keep_circulating(10, block=False)(_f)()
        # threading.Thread(target=_f).start()

    def _requeue(self, kw):
        pass
```

### 代码文件: funboost\consumers\httpsqs_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json
import time
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers.httpsqs_publisher import HttpsqsPublisher
from funboost.core.func_params_model import PublisherParams

class HttpsqsConsumer(AbstractConsumer):
    """
    httpsqs作为中间件
    """


    def custom_init(self):
        # noinspection PyAttributeOutsideInit
        self.httpsqs_publisher = HttpsqsPublisher(publisher_params=PublisherParams(queue_name=self.queue_name))

    # noinspection DuplicatedCode
    def _dispatch_task(self):
        while True:
            text = self.httpsqs_publisher.opt_httpsqs('get')
            if text == 'HTTPSQS_GET_END':
                time.sleep(0.5)
            else:
                kw = {'body': text}
                self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        try:
            kw['body'].pop('extra')
        except KeyError:
            pass
        self.httpsqs_publisher.publish(kw['body'])

```

### 代码文件: funboost\consumers\http_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import asyncio
import json

# from aiohttp import web
# from aiohttp.web_request import Request

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.lazy_impoter import AioHttpImporter


class HTTPConsumer(AbstractConsumer, ):
    """
    http 实现消息队列，不支持持久化，但不需要安装软件。
    """
    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'host': '127.0.0.1', 'port': None}

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        # try:
        #     self._ip, self._port = self.queue_name.split(':')
        #     self._port = int(self._port)
        # except BaseException as e:
        #     self.logger.critical(f'http作为消息队列时候,队列名字必须设置为 例如 192.168.1.101:8200  这种,  ip:port')
        #     raise e
        self._ip = self.consumer_params.broker_exclusive_config['host']
        self._port = self.consumer_params.broker_exclusive_config['port']
        if self._port is None:
            raise ValueError('please specify port')

    # noinspection DuplicatedCode
    def _dispatch_task(self):
        # flask_app = Flask(__name__)
        #
        # @flask_app.route('/queue', methods=['post'])
        # def recv_msg():
        #     msg = request.form['msg']
        #     kw = {'body': json.loads(msg)}
        #     self._submit_task(kw)
        #     return 'finish'
        #
        # flask_app.run('0.0.0.0', port=self._port,debug=False)

        routes = AioHttpImporter().web.RouteTableDef()

        # noinspection PyUnusedLocal
        @routes.get('/')
        async def hello(request):
            return AioHttpImporter().web.Response(text="Hello, from funboost")

        @routes.post('/queue')
        async def recv_msg(request: AioHttpImporter().Request):
            data = await request.post()
            msg = data['msg']
            kw = {'body': msg}
            self._submit_task(kw)
            return AioHttpImporter().web.Response(text="finish")

        app = AioHttpImporter().web.Application()
        app.add_routes(routes)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        AioHttpImporter().web.run_app(app, host='0.0.0.0', port=self._port, )

    def _confirm_consume(self, kw):
        pass  # 没有确认消费的功能。

    def _requeue(self, kw):
        pass

```

### 代码文件: funboost\consumers\http_consumer000.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import cgi
import io
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse

from funboost.consumers.base_consumer import AbstractConsumer


class HttpHandler(BaseHTTPRequestHandler):
    consumer = None  # type:AbstractConsumer

    def do_GET(self):
        parsed_path = parse.urlparse(self.path)
        message_parts = [
            'CLIENT VALUES:',
            'client_address={} ({})'.format(
                self.client_address,
                self.address_string()),
            'command={}'.format(self.command),
            'path={}'.format(self.path),
            'real path={}'.format(parsed_path.path),
            'query={}'.format(parsed_path.query),
            'request_version={}'.format(self.request_version),
            '',
            'SERVER VALUES:',
            'server_version={}'.format(self.server_version),
            'sys_version={}'.format(self.sys_version),
            'protocol_version={}'.format(self.protocol_version),
            '',
            'HEADERS RECEIVED:',
        ]
        for name, value in sorted(self.headers.items()):
            message_parts.append(
                '{}={}'.format(name, value.rstrip())
            )
        message_parts.append('')
        message = '\r\n'.join(message_parts)
        self.send_response(200)
        self.send_header('Content-Type',
                         'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))

    def do_POST(self):
        # 分析提交的表单数据
        # print(self.path)
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,  # noqa
            environ={
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': self.headers['Content-Type'],
            }
        )

        if self.path == '/queue':
            msg = form['msg'].value
            # print(msg)
            kw = {'body': msg}
            self.consumer._submit_task(kw)

        # 开始回复
        self.send_response(200)
        self.send_header('Content-Type',
                         'text/plain; charset=utf-8')
        self.end_headers()

        out = io.TextIOWrapper(
            self.wfile,
            encoding='utf-8',
            line_buffering=False,
            write_through=True,
        )

        out.write('Client: {}\n'.format(self.client_address))
        out.write('User-agent: {}\n'.format(
            self.headers['user-agent']))
        out.write('Path: {}\n'.format(self.path))
        out.write('Form data:\n')
        # print(form.keys())
        # 表单信息内容回放
        for field in form.keys():
            field_item = form[field]
            if field_item.filename:
                # 字段中包含的是一个上传文件
                file_data = field_item.file.read()
                file_len = len(file_data)
                del file_data
                out.write(
                    '\tUploaded {} as {!r} ({} bytes)\n'.format(
                        field, field_item.filename, file_len)
                )
            else:
                # 通常形式的值
                out.write('\t{}={}\n'.format(
                    field, form[field].value))

        # 将编码 wrapper 到底层缓冲的连接断开，
        # 使得将 wrapper 删除时，
        # 并不关闭仍被服务器使用 socket 。
        out.detach()

class HTTPConsumer(AbstractConsumer, ):
    """
    http 实现消息队列，不支持持久化，但不需要安装软件。
    """
    BROKER_KIND = 23

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._ip, self._port = self.queue_name.split(':')
        self._port = int(self._port)

    # noinspection DuplicatedCode
    def _dispatch_task(self):
        class CustomHandler(HttpHandler):
            consumer = self

        server = HTTPServer(('0.0.0.0', self._port), CustomHandler)
        print(f'Starting server, 0.0.0.0:{self._port}')
        server.serve_forever()

    def _confirm_consume(self, kw):
        pass  # 没有确认消费的功能。

    def _requeue(self, kw):
        pass

```

### 代码文件: funboost\consumers\huey_consumer.py
```python
import time

from huey import RedisHuey
from huey.consumer import Consumer

from funboost import AbstractConsumer
from funboost.assist.huey_helper import HueyHelper


class HueyConsumer(AbstractConsumer):
    """
    huey作为中间件实现的。
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'huey_task_kwargs': {}}
    """
    retries=0, retry_delay=0, priority=None, context=False,
             name=None, expires=None, **kwargs
    """

    def custom_init(self):
        # 这就是核心，
        huey_task_kwargs = self.consumer_params.broker_exclusive_config['huey_task_kwargs']
        huey_task_kwargs['retries'] = self.consumer_params.max_retry_times

        @HueyHelper.huey_obj.task(name=self.queue_name,
                        **huey_task_kwargs)
        def f(*args, **kwargs):
            self.logger.debug(f' 这条消息是 huey 从 {self.queue_name} 队列中取出 ,是由 huey 框架调度 {self.consuming_function.__name__} 函数处理: args:  {args} ,  kwargs: {kwargs}')
            return self.consuming_function(*args, **kwargs)

        HueyHelper.queue_name__huey_task_fun_map[self.queue_name] = f

    def start_consuming_message(self):
        # 不单独每个函数都启动一次celery的worker消费，是把要消费的 queue name放到列表中，realy_start_dramatiq_worker 一次性启动多个函数消费。
        HueyHelper.to_be_start_huey_queue_name_set.add(self.queue_name)
        super().start_consuming_message()

    def _dispatch_task(self):
        """ 完全由dramatiq框架接管控制消费，不使用funboost的AbstractConsumer的_run"""
        while 1:
            time.sleep(100)

    def _confirm_consume(self, kw):
        """dramatiq框架默认自带，不需要funboost实现"""

    def _requeue(self, kw):
        pass

```

### 代码文件: funboost\consumers\kafka_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json
# noinspection PyPackageRequirements

from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.lazy_impoter import KafkaPythonImporter
from funboost.funboost_config_deafult import BrokerConnConfig
# from nb_log import get_logger
from funboost.core.loggers import get_funboost_file_logger

# LogManager('kafka').get_logger_and_add_handlers(30)
get_funboost_file_logger('kafka', log_level_int=30)


class KafkaConsumer(AbstractConsumer):
    """
    kafka作为中间件实现的。自动确认消费，最多消费一次，随意重启会丢失正在大批正在运行的任务。推荐使用 confluent_kafka 中间件，kafka_consumer_manually_commit.py。

    可以让消费函数内部 sleep60秒，突然停止消费代码，使用 kafka-consumer-groups.sh --bootstrap-server 127.0.0.1:9092 --describe --group funboost 来证实自动确认消费和手动确认消费的区别。
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'group_id': 'funboost_kafka', 'auto_offset_reset': 'earliest'}
    # not_all_brokers_general_settings配置 ，支持独立的中间件配置参数是 group_id 和 auto_offset_reset
    """
    auto_offset_reset 介绍
      auto_offset_reset (str): A policy for resetting offsets on
            OffsetOutOfRange errors: 'earliest' will move to the oldest
            available message, 'latest' will move to the most recent. Any
            other value will raise the exception. Default: 'latest'.
    """

    def _dispatch_task(self):
        try:
            admin_client = KafkaPythonImporter().KafkaAdminClient(bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS)
            admin_client.create_topics([KafkaPythonImporter().NewTopic(self._queue_name, 10, 1)])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except KafkaPythonImporter().TopicAlreadyExistsError:
            pass

        self._producer = KafkaPythonImporter().KafkaProducer(bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS)
        consumer = KafkaPythonImporter().OfficialKafkaConsumer(self._queue_name, bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS,
                                                               group_id=self.consumer_params.broker_exclusive_config["group_id"],
                                                               enable_auto_commit=True,
                                                               auto_offset_reset=self.consumer_params.broker_exclusive_config["auto_offset_reset"],
                                                               )
        #  auto_offset_reset (str): A policy for resetting offsets on
        #             OffsetOutOfRange errors: 'earliest' will move to the oldest
        #             available message, 'latest' will move to the most recent. Any
        #             other value will raise the exception. Default: 'latest'.       默认是latest

        # kafka 的 group_id

        # REMIND 由于是很高数量的并发消费，线程很多，分区很少，这里设置成自动确认消费了，否则多线程提交同一个分区的偏移量导致超前错乱，就没有意义了。
        # REMIND 要保证很高的可靠性和一致性，请用rabbitmq。
        # REMIND 好处是并发高。topic像翻书一样，随时可以设置偏移量重新消费。多个分组消费同一个主题，每个分组对相同主题的偏移量互不干扰 。
        for message in consumer:
            # 注意: message ,value都是原始的字节数据，需要decode
            if self.consumer_params.is_show_message_get_from_broker:
                self.logger.debug(
                    f'从kafka的 [{message.topic}] 主题,分区 {message.partition} 中 取出的消息是：  {message.value.decode()}')
            kw = {'consumer': consumer, 'message': message, 'body': message.value}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # 使用kafka的自动commit模式。

    def _requeue(self, kw):
        self._producer.send(self._queue_name, json.dumps(kw['body']).encode())

```

### 代码文件: funboost\consumers\kafka_consumer_manually_commit.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2021/4/18 0008 13:32


import json
import threading
from collections import defaultdict, OrderedDict
# noinspection PyPackageRequirements
import time

# noinspection PyPackageRequirements
# pip install kafka-python==2.0.2

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.lazy_impoter import KafkaPythonImporter
from funboost.funboost_config_deafult import BrokerConnConfig
from confluent_kafka.cimpl import TopicPartition
from confluent_kafka import Consumer as ConfluentConsumer  # 这个包在win下不好安装，用户用这个中间件的时候自己再想办法安装。win用户需要安装c++ 14.0以上环境。


class KafkaConsumerManuallyCommit(AbstractConsumer):
    """
    confluent_kafla作为中间件实现的。操作kafka中间件的速度比kafka-python快10倍。
    这个是自动间隔2秒的手动确认，由于是异步在并发池中并发消费，可以防止强制关闭程序造成正在运行的任务丢失，比自动commit好。
    如果使用kafka，推荐这个。

    可以让消费函数内部 sleep 60秒，突然停止消费代码，使用 kafka-consumer-groups.sh --bootstrap-server 127.0.0.1:9092 --describe --group frame_group 来证实自动确认消费和手动确认消费的区别。
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'group_id': 'funboost_confluent_kafka', 'auto_offset_reset': 'earliest'}

    def custom_init(self):
        self._lock_for_operate_offset_dict = threading.Lock()

    def _dispatch_task(self):

        try:
            admin_client = KafkaPythonImporter().KafkaAdminClient(bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS)
            admin_client.create_topics([KafkaPythonImporter().NewTopic(self._queue_name, 10, 1)])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except KafkaPythonImporter().TopicAlreadyExistsError:
            pass

        self._producer = KafkaPythonImporter().KafkaProducer(bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS)
        # consumer 配置 https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
        self._confluent_consumer = ConfluentConsumer({
            'bootstrap.servers': ','.join(BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS),
            'group.id': self.consumer_params.broker_exclusive_config["group_id"],
            'auto.offset.reset': self.consumer_params.broker_exclusive_config["auto_offset_reset"],
            'enable.auto.commit': False
        })
        self._confluent_consumer.subscribe([self._queue_name])

        self._recent_commit_time = time.time()
        self._partion__offset_consume_status_map = defaultdict(OrderedDict)
        while 1:
            msg = self._confluent_consumer.poll(timeout=10)
            self._manually_commit()
            if msg is None:
                continue
            if msg.error():
                print("Consumer error: {}".format(msg.error()))
                continue
            # msg的类型  https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#message
            # value()  offset() partition()
            # print('Received message: {}'.format(msg.value().decode('utf-8'))) # noqa
            self._partion__offset_consume_status_map[msg.partition()][msg.offset()] = 0
            kw = {'partition': msg.partition(), 'offset': msg.offset(), 'body': msg.value()}  # noqa
            if self.consumer_params.is_show_message_get_from_broker:
                self.logger.debug(
                    f'从kafka的 [{self._queue_name}] 主题,分区 {msg.partition()} 中 的 offset {msg.offset()} 取出的消息是：  {msg.value()}')  # noqa
            self._submit_task(kw)


    def _manually_commit(self):
        """
        kafka要求消费线程数量和分区数量是一对一或一对多，不能多对一，消息并发处理收到分区数量的限制，这种是支持超高线程数量消费，所以commit非常复杂。
        因为这种是可以支持单分区200线程消费，消费本身和拉取kafka任务不在同一个线程，而且可能offset较大的比offset较小的任务先完成，
        每隔2秒对1组offset，对连续消费状态是1的最大offset进行commit
        :return:
        """
        with self._lock_for_operate_offset_dict:
            if time.time() - self._recent_commit_time > 2:
                partion_max_consumed_offset_map = dict()
                to_be_remove_from_partion_max_consumed_offset_map = defaultdict(list)
                for partion, offset_consume_status in self._partion__offset_consume_status_map.items():
                    sorted_keys = sorted(offset_consume_status.keys())
                    offset_consume_status_ordered = {key: offset_consume_status[key] for key in sorted_keys}
                    max_consumed_offset = None

                    for offset, consume_status in offset_consume_status_ordered.items():
                        # print(offset,consume_status)
                        if consume_status == 1:
                            max_consumed_offset = offset
                            to_be_remove_from_partion_max_consumed_offset_map[partion].append(offset)
                        else:
                            break
                    if max_consumed_offset is not None:
                        partion_max_consumed_offset_map[partion] = max_consumed_offset
                # self.logger.info(partion_max_consumed_offset_map)
                # TopicPartition
                offsets = list()
                for partion, max_consumed_offset in partion_max_consumed_offset_map.items():
                    # print(partion,max_consumed_offset)
                    offsets.append(TopicPartition(topic=self._queue_name, partition=partion, offset=max_consumed_offset + 1))
                if len(offsets):
                    self._confluent_consumer.commit(offsets=offsets, asynchronous=False)
                self._recent_commit_time = time.time()
                for partion, offset_list in to_be_remove_from_partion_max_consumed_offset_map.items():
                    for offset in offset_list:
                        del self._partion__offset_consume_status_map[partion][offset]

    def _confirm_consume(self, kw):
        with self._lock_for_operate_offset_dict:
            self._partion__offset_consume_status_map[kw['partition']][kw['offset']] = 1
            # print(self._partion__offset_consume_status_map)

    def _requeue(self, kw):
        self._producer.send(self._queue_name, json.dumps(kw['body']).encode())


class SaslPlainKafkaConsumer(KafkaConsumerManuallyCommit):

    def _dispatch_task(self):

        try:
            admin_client = KafkaPythonImporter().KafkaAdminClient(
                **BrokerConnConfig.KFFKA_SASL_CONFIG)
            admin_client.create_topics([KafkaPythonImporter().NewTopic(self._queue_name, 10, 1)])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except KafkaPythonImporter().TopicAlreadyExistsError:
            pass

        self._producer = KafkaPythonImporter().KafkaProducer(
            **BrokerConnConfig.KFFKA_SASL_CONFIG)
        # consumer 配置 https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
        self._confluent_consumer = ConfluentConsumer({
            'bootstrap.servers': ','.join(BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS),
            'security.protocol': BrokerConnConfig.KFFKA_SASL_CONFIG['security_protocol'],
            'sasl.mechanisms': BrokerConnConfig.KFFKA_SASL_CONFIG['sasl_mechanism'],
            'sasl.username': BrokerConnConfig.KFFKA_SASL_CONFIG['sasl_plain_username'],
            'sasl.password': BrokerConnConfig.KFFKA_SASL_CONFIG['sasl_plain_password'],
            'group.id': self.consumer_params.broker_exclusive_config["group_id"],
            'auto.offset.reset': self.consumer_params.broker_exclusive_config["auto_offset_reset"],
            'enable.auto.commit': False
        })
        self._confluent_consumer.subscribe([self._queue_name])

        self._recent_commit_time = time.time()
        self._partion__offset_consume_status_map = defaultdict(OrderedDict)

        while 1:
            msg = self._confluent_consumer.poll(timeout=10)
            self._manually_commit()
            if msg is None:
                continue
            if msg.error():
                print("Consumer error: {}".format(msg.error()))
                continue
            # msg的类型  https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#message
            # value()  offset() partition()
            # print('Received message: {}'.format(msg.value().decode('utf-8'))) # noqa
            self._partion__offset_consume_status_map[msg.partition(
            )][msg.offset()] = 0
            kw = {'partition': msg.partition(), 'offset': msg.offset(), 'body': msg.value()}  # noqa
            if self.consumer_params.is_show_message_get_from_broker:
                self.logger.debug(
                    f'从kafka的 [{self._queue_name}] 主题,分区 {msg.partition()} 中 的 offset {msg.offset()} 取出的消息是：  {msg.value()}')  # noqa
            self._submit_task(kw)

```

### 代码文件: funboost\consumers\kombu_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2021/04/18 0008 13:32
# import time
import os

import traceback
from pathlib import Path
from kombu.entity import Exchange, Queue
from kombu.connection import Connection
from kombu.transport.virtual.base import Channel
from kombu.transport.virtual.base import Message
from kombu.transport import redis
from kombu.transport.redis import Empty


from funboost.consumers.base_consumer import AbstractConsumer
from funboost.funboost_config_deafult import BrokerConnConfig



has_patch_kombu_redis = False


def patch_kombu_redis():
    """
    给kombu的redis 模式打猴子补丁
    kombu有bug，redis中间件 unnacked 中的任务即使客户端掉线了或者突然关闭脚本中正在运行的任务，也永远不会被重新消费。
    这个很容易验证那个测试，把消费函数写成sleep 100秒，启动20秒后把脚本关掉，取出来的任务在 unacked 队列中那个永远不会被确认消费，也不会被重新消费。
    """
    global has_patch_kombu_redis
    if not has_patch_kombu_redis:
        redis_multichannelpoller_get_raw = redis.MultiChannelPoller.get

        # noinspection PyUnusedLocal
        def monkey_get(self, callback, timeout=None):
            try:
                redis_multichannelpoller_get_raw(self, callback, timeout)
            except Empty:
                self.maybe_restore_messages()
                raise Empty()

        redis.MultiChannelPoller.get = monkey_get
        has_patch_kombu_redis = True


''' kombu 能支持的消息队列中间件有如下，可以查看 D:\ProgramData\Miniconda3\Lib\site-packages\kombu\transport\__init__.py 文件。

TRANSPORT_ALIASES = {
    'amqp': 'kombu.transport.pyamqp:Transport',
    'amqps': 'kombu.transport.pyamqp:SSLTransport',
    'pyamqp': 'kombu.transport.pyamqp:Transport',
    'librabbitmq': 'kombu.transport.librabbitmq:Transport',
    'memory': 'kombu.transport.memory:Transport',
    'redis': 'kombu.transport.redis:Transport',
    'rediss': 'kombu.transport.redis:Transport',
    'SQS': 'kombu.transport.SQS:Transport',
    'sqs': 'kombu.transport.SQS:Transport',
    'mongodb': 'kombu.transport.mongodb:Transport',
    'zookeeper': 'kombu.transport.zookeeper:Transport',
    'sqlalchemy': 'kombu.transport.sqlalchemy:Transport',
    'sqla': 'kombu.transport.sqlalchemy:Transport',
    'SLMQ': 'kombu.transport.SLMQ.Transport',
    'slmq': 'kombu.transport.SLMQ.Transport',
    'filesystem': 'kombu.transport.filesystem:Transport',
    'qpid': 'kombu.transport.qpid:Transport',
    'sentinel': 'kombu.transport.redis:SentinelTransport',
    'consul': 'kombu.transport.consul:Transport',
    'etcd': 'kombu.transport.etcd:Transport',
    'azurestoragequeues': 'kombu.transport.azurestoragequeues:Transport',
    'azureservicebus': 'kombu.transport.azureservicebus:Transport',
    'pyro': 'kombu.transport.pyro:Transport'
}

'''


# noinspection PyAttributeOutsideInit
class KombuConsumer(AbstractConsumer, ):
    """
    使用kombu作为中间件,这个能直接一次性支持很多种小众中间件，但性能很差，除非是分布式函数调度框架没实现的中间件种类用户才可以用这种，用户也可以自己对比性能。
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'kombu_url': None,  # 如果这里也配置了kombu_url,则优先使用跟着你的kombu_url，否则使用funboost_config. KOMBU_URL
                                       'transport_options': {},  # transport_options是kombu的transport_options 。
                                       'prefetch_count': 500
                                       }
    # prefetch_count 是预获取消息数量
    ''' transport_options是kombu的transport_options 。 
       例如使用kombu使用redis作为中间件时候，可以设置 visibility_timeout 来决定消息取出多久没有ack，就自动重回队列。
       kombu的每个中间件能设置什么 transport_options 可以看 kombu的源码中的 transport_options 参数说明。

例如kombu redis的Transport Options 说明
D:\ProgramData\Miniconda3\envs\py311\Lib\site-packages\kombu\transport\redis.py

Transport Options
=================
* ``sep``
* ``ack_emulation``: (bool) If set to True transport will
  simulate Acknowledge of AMQP protocol.
* ``unacked_key``
* ``unacked_index_key``
* ``unacked_mutex_key``
* ``unacked_mutex_expire``
* ``visibility_timeout``
* ``unacked_restore_limit``
* ``fanout_prefix``
* ``fanout_patterns``
* ``global_keyprefix``: (str) The global key prefix to be prepended to all keys
  used by Kombu
* ``socket_timeout``
* ``socket_connect_timeout``
* ``socket_keepalive``
* ``socket_keepalive_options``
* ``queue_order_strategy``
* ``max_connections``
* ``health_check_interval``
* ``retry_on_timeout``
* ``priority_steps``


      '''

    def custom_init(self):
        self.kombu_url = self.consumer_params.broker_exclusive_config['kombu_url'] or BrokerConnConfig.KOMBU_URL
        self._middware_name = self.kombu_url.split(":")[0]
        # logger_name = f'{self.consumer_params.logger_prefix}{self.__class__.__name__}--{self._middware_name}--{self._queue_name}'
        # self.logger = get_logger(logger_name, log_level_int=self.consumer_params.log_level,
        #                          _log_filename=f'{logger_name}.log' if self.consumer_params.create_logger_file else None,
        #                          formatter_template=FunboostCommonConfig.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER,
        #                          )  #
        if self.kombu_url.startswith('filesystem://'):
            self._create_msg_file_dir()

    def _create_msg_file_dir(self):
        os.makedirs(self.consumer_params.broker_exclusive_config['transport_options']['data_folder_in'], exist_ok=True)
        os.makedirs(self.consumer_params.broker_exclusive_config['transport_options']['data_folder_out'], exist_ok=True)
        processed_folder = self.consumer_params.broker_exclusive_config['transport_options'].get('processed_folder', None)
        if processed_folder:
            os.makedirs(processed_folder, exist_ok=True)

    # noinspection DuplicatedCode
    def _dispatch_task(self):  # 这个倍while 1 启动的，会自动重连。
        patch_kombu_redis()

        def callback(body: dict, message: Message):
            # print(type(body),body,type(message),message)
            # self.logger.debug(f""" 从 kombu {self._middware_name} 中取出的消息是 {body}""")
            kw = {'body': body, 'message': message, }
            self._submit_task(kw)

        self.exchange = Exchange('funboost_exchange', 'direct', durable=True)
        self.queue = Queue(self._queue_name, exchange=self.exchange, routing_key=self._queue_name, auto_delete=False, no_ack=False)
        # https://docs.celeryq.dev/projects/kombu/en/stable/reference/kombu.html?highlight=visibility_timeout#kombu.Connection 每种中间件的transport_options不一样。
        self.conn = Connection(self.kombu_url, transport_options=self.consumer_params.broker_exclusive_config['transport_options'])
        self.queue(self.conn).declare()
        with self.conn.Consumer(self.queue, callbacks=[callback], no_ack=False, prefetch_count=self.consumer_params.broker_exclusive_config['prefetch_count']) as consumer:
            # Process messages and handle events on all channels
            channel = consumer.channel  # type:Channel
            channel.body_encoding = 'no_encode'  # 这里改了编码，存到中间件的参数默认把消息base64了，我觉得没必要不方便查看消息明文。
            while True:
                self.conn.drain_events()

    def _confirm_consume(self, kw):
        kw['message'].ack()

    def _requeue(self, kw):
        kw['message'].requeue()

```

### 代码文件: funboost\consumers\local_python_queue_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:36
import json
from queue import Queue,SimpleQueue
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.queues.memory_queues_map import PythonQueues


class LocalPythonQueueConsumer(AbstractConsumer):
    """
    python 内置queue对象作为消息队列，这个要求发布和消费必须在同一python解释器内部运行，不支持分布式。
    """

    @property
    def local_python_queue(self) -> Queue:
        return PythonQueues.get_queue(self._queue_name)

    def _dispatch_task(self):
        while True:
            task = self.local_python_queue.get()
            if isinstance(task, dict):
                task = json.dumps(task)
            # self.logger.debug(f'从当前python解释器内部的 [{self._queue_name}] 队列中 取出的消息是：  {json.dumps(task)}  ')
            kw = {'body': task}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        self.local_python_queue.put(kw['body'])


```

### 代码文件: funboost\consumers\memory_deque_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:36
import json
from collections import deque

from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers import meomory_deque_publisher


class LocalPythonQueueConsumer(AbstractConsumer):
    """
    python 内置queue对象作为消息队列，这个要求发布和消费必须在同一python解释器内部运行，不支持分布式。
    """

    @property
    def local_python_queue(self) -> deque:
        return meomory_deque_publisher.deque_queue_name__deque_obj_map[self._queue_name]

    def _dispatch_task(self):
        while True:
            task = self.local_python_queue.popleft()
            # self.logger.debug(f'从当前python解释器内部的 [{self._queue_name}] 队列中 取出的消息是：  {json.dumps(task)}  ')
            kw = {'body': task}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        self.local_python_queue.append(kw['body'])

```

### 代码文件: funboost\consumers\mongomq_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:33
import time
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers.mongomq_publisher import MongoMixin, MongoMqPublisher
from funboost.core.func_params_model import PublisherParams

class MongoMqConsumer(AbstractConsumer, MongoMixin):
    """
    Mongo queue包实现的基于mongo的消息队列，支持消费确认。
    """


    def _dispatch_task(self):
        mp = MongoMqPublisher(publisher_params=PublisherParams(queue_name=self.queue_name))
        while True:
            job = mp.queue.next()
            if job is not None:
                # self.logger.debug(f'从mongo的 [{self._queue_name}] 队列中 取出的消息是：   消息是：  {job.payload}  ')
                kw = {'body': job.payload, 'job': job}
                self._submit_task(kw)
            else:
                time.sleep(0.1)

    def _confirm_consume(self, kw):
        kw['job'].complete()

    def _requeue(self, kw):
        kw['job'].release()

```

### 代码文件: funboost\consumers\mqtt_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json
# import time
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.lazy_impoter import PahoMqttImporter
from funboost.funboost_config_deafult import BrokerConnConfig
# import paho.mqtt.client as mqtt


class MqttConsumer(AbstractConsumer):
    """
    emq 作为中间件 实现的消费者 ，使用共享订阅。
    """


    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        # fsdf 表示 funboost.相当于kafka的消费者组作用。
        # 这个是共享订阅，见  https://blog.csdn.net/emqx_broker/article/details/103027813
        self._topic_shared = f'$share/fsdf/{self._queue_name}'

    # noinspection DuplicatedCode
    def _dispatch_task(self):
        client = PahoMqttImporter().mqtt.Client()
        # client.username_pw_set('admin', password='public')
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.on_disconnect = self._on_socket_close
        client.on_socket_close = self._on_socket_close
        client.connect(BrokerConnConfig.MQTT_HOST, BrokerConnConfig.MQTT_TCP_PORT, 600)  # 600为keepalive的时间间隔
        client.subscribe(self._topic_shared, qos=0)  # on message 是异把消息丢到线程池，本身不可能失败。
        client.loop_forever(retry_first_connection=True)  # 保持连接

    def _on_socket_close(self, client, userdata, socket):
        self.logger.critical(f'{client, userdata, socket}')
        self._dispatch_task()

    # noinspection PyPep8Naming
    def _on_disconnect(self, client, userdata, reasonCode, properties):
        self.logger.critical(f'{client, userdata, reasonCode, properties}')

    def _on_connect(self, client, userdata, flags, rc):
        self.logger.info(f'连接mqtt服务端成功, {client, userdata, flags, rc}')

    # noinspection PyUnusedLocal
    def _on_message(self, client, userdata, msg):
        # print(msg.topic + " " + str(msg.payload))
        kw = {'body': msg.payload}
        self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        pass

```

### 代码文件: funboost\consumers\nameko_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/8 0008 13:32
from multiprocessing import Process

import threading

import typing
from funboost.constant import BrokerEnum


from nameko.containers import ServiceContainer
from nameko.rpc import rpc
from nameko.runners import ServiceRunner

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers.nameko_publisher import get_nameko_config

all_queue_name__nameko_service_cls_map = {}


class NamekoConsumer(AbstractConsumer, ):
    """
    nameko作为中间件实现的。
    """


    def custom_init(self):
        try:
            from funboost.concurrent_pool.custom_evenlet_pool_executor import check_evenlet_monkey_patch
            check_evenlet_monkey_patch()
        except Exception as e:
            self.logger.critical('nameko 必须使用eventlet 并发，并且eventlet包打猴子补丁')
            raise e

        class MyService:
            name = self.queue_name

            @rpc
            def call(this, *args, **kwargs):
                return self.consuming_function(*args, **kwargs)

        all_queue_name__nameko_service_cls_map[self.queue_name] = MyService

    def _dispatch_task(self):
        container = ServiceContainer(all_queue_name__nameko_service_cls_map[self.queue_name], config=get_nameko_config())
        container.start()
        container.wait()

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        pass



def batch_start_nameko_consumers(boost_fun_list: typing.List):
    runner = ServiceRunner(config=get_nameko_config())
    for boost_fun in boost_fun_list:
        runner.add_service(all_queue_name__nameko_service_cls_map[boost_fun.queue_name])
    runner.start()
    runner.wait()


def batch_start_nameko_service_in_new_thread(boost_fun_list: typing.List):
    threading.Thread(target=batch_start_nameko_consumers, args=(boost_fun_list,)).start()


def batch_start_nameko_service_in_new_process(boost_fun_list: typing.List, process_num=1):
    for i in range(process_num):
        Process(target=batch_start_nameko_consumers, args=(boost_fun_list,)).start()

```

### 代码文件: funboost\consumers\nats_consumer.py
```python
﻿import json
# from pynats import NATSClient, NATSMessage  # noqa

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.lazy_impoter import NatsImporter
from funboost.funboost_config_deafult import BrokerConnConfig


class NatsConsumer(AbstractConsumer):
    """
    nats作为中间件实现的。
    """


    def _dispatch_task(self):
        # print(88888888888888)
        nats_client = NatsImporter().NATSClient(BrokerConnConfig.NATS_URL, socket_timeout=600, socket_keepalive=True)
        nats_client.connect()

        def callback(msg: NatsImporter().NATSMessage):
            # print(type(msg))
            # print(msg.reply)
            # print(f"Received a message with subject {msg.subject}: {msg.payload}")
            kw = {'body': msg.payload}
            self._submit_task(kw)

        nats_client.subscribe(subject=self.queue_name, callback=callback)
        nats_client.wait()

    def _confirm_consume(self, kw):
        pass   # 没有确认消费

    def _requeue(self, kw):
        self.publisher_of_same_queue.publish(kw['body'])

```

### 代码文件: funboost\consumers\nsq_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json

from funboost.core.lazy_impoter import GnsqImporter
# from gnsq import Consumer, Message

from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.consumers.base_consumer import AbstractConsumer
# from nb_log import LogManager
from funboost.core.loggers import get_funboost_file_logger

get_funboost_file_logger('gnsq',log_level_int=20)


class NsqConsumer(AbstractConsumer):
    """
    nsq作为中间件实现的。
    """


    def _dispatch_task(self):
        consumer = GnsqImporter().Consumer(self._queue_name, 'frame_channel', BrokerConnConfig.NSQD_TCP_ADDRESSES,
                            max_in_flight=self.consumer_params.concurrent_num, heartbeat_interval=60, timeout=600, )  # heartbeat_interval 不能设置为600

        @consumer.on_message.connect
        def handler(consumerx: GnsqImporter().Consumer, message: GnsqImporter().Message):
            # 第一条消息不能并发，第一条消息之后可以并发。
            # self.logger.debug(f'从nsq的 [{self._queue_name}] 主题中 取出的消息是：  {message.body.decode()}')
            message.enable_async()
            kw = {'consumer': consumerx, 'message': message, 'body': message.body}
            self._submit_task(kw)

        consumer.start()

    def _confirm_consume(self, kw):
        kw['message'].finish()

    def _requeue(self, kw):
        kw['message'].requeue()

```

### 代码文件: funboost\consumers\peewee_conusmer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:33
import json
from funboost.constant import BrokerEnum
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.queues.peewee_queue import PeeweeQueue,TaskStatus


class PeeweeConsumer(AbstractConsumer):
    """
    peewee实现的操作5种数据库模拟消息队列，支持消费确认。
    """


    def _dispatch_task(self):
        self.queue = PeeweeQueue(self.queue_name)
        while True:
            task_dict = self.queue.get()
            # print(task_dict)
            # self.logger.debug(f'从数据库 {frame_config.SQLACHEMY_ENGINE_URL[:25]}。。 的 [{self._queue_name}] 队列中 取出的消息是：   消息是：  {sqla_task_dict}')
            kw = {'body':task_dict['body'], 'job_id': task_dict['job_id']}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        self.queue.set_success(kw['job_id'])

    def _requeue(self, kw):
        self.queue.requeue_task(kw['job_id'])




```

### 代码文件: funboost\consumers\persist_queue_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:35
import json
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers.persist_queue_publisher import PersistQueuePublisher
from funboost.core.func_params_model import PublisherParams

class PersistQueueConsumer(AbstractConsumer):
    """
    persist queue包实现的本地持久化消息队列。
    """

    def _dispatch_task(self):
        pub = PersistQueuePublisher(publisher_params=PublisherParams(queue_name=self.queue_name))
        while True:
            item = pub.queue.get()
            # self.logger.debug(f'从本地持久化sqlite的 [{self._queue_name}] 队列中 取出的消息是：   {item}  ')
            kw = {'body': item, 'q': pub.queue, 'item': item}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        kw['q'].ack(kw['item'])

    def _requeue(self, kw):
        kw['q'].nack(kw['item'])

```

### 代码文件: funboost\consumers\pulsar_consumer.py
```python
'''

import pulsar

client = pulsar.Client('pulsar://localhost:6650')
consumer = client.subscribe('my-topic',
                            subscription_name='my-sub')

while True:
    msg = consumer.receive()
    print("Received message: '%s'" % msg.data())
    consumer.acknowledge(msg)

client.close()
'''

# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import os

import json
from _pulsar import ConsumerType
from pulsar.schema import schema
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.funboost_config_deafult import BrokerConnConfig


class PulsarConsumer(AbstractConsumer, ):
    """
    pulsar作为中间件实现的。
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'subscription_name': 'funboost_group',
                                       'replicate_subscription_state_enabled': True,
                                       'consumer_type': ConsumerType.Shared,
                                       }

    def custom_init(self):
        pass

    def _dispatch_task(self):
        try:
            import pulsar  # 需要用户自己 pip install pulsar-client ，目前20221206只支持linux安装此python包。
        except ImportError:
            raise ImportError('需要用户自己 pip install pulsar-client ，')
        self._client = pulsar.Client(BrokerConnConfig.PULSAR_URL, )
        self._consumer = self._client.subscribe(self._queue_name, schema=schema.StringSchema(), consumer_name=f'funboost_consumer_{os.getpid()}',
                                                subscription_name=self.consumer_params.broker_exclusive_config['subscription_name'],
                                                consumer_type=self.consumer_params.broker_exclusive_config['consumer_type'],
                                                replicate_subscription_state_enabled=self.consumer_params.broker_exclusive_config['replicate_subscription_state_enabled'])
        while True:
            msg = self._consumer.receive()
            if msg:
                kw = {'body': msg.data(), 'msg': msg}
                self._submit_task(kw)

    def _confirm_consume(self, kw):
        self._consumer.acknowledge(kw['msg'])

    def _requeue(self, kw):
        self._consumer.negative_acknowledge(kw['msg'])

```

### 代码文件: funboost\consumers\rabbitmq_amqpstorm_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:30

import amqpstorm
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers.rabbitmq_amqpstorm_publisher import RabbitmqPublisherUsingAmqpStorm
from funboost.core.func_params_model import PublisherParams


class RabbitmqConsumerAmqpStorm(AbstractConsumer):
    """
    使用AmqpStorm实现的，多线程安全的，不用加锁。
    funboost 强烈推荐使用这个做消息队列中间件。
    """
    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'x-max-priority': None,'no_ack':False}  # x-max-priority 是 rabbitmq的优先级队列配置，必须为整数，强烈建议要小于5。为None就代表队列不支持优先级。

    def _dispatch_task(self):
        # noinspection PyTypeChecker
        def callback(amqpstorm_message: amqpstorm.Message):
            body = amqpstorm_message.body
            # self.logger.debug(f'从rabbitmq的 [{self._queue_name}] 队列中 取出的消息是：  {body}')
            kw = {'amqpstorm_message': amqpstorm_message, 'body': body}
            self._submit_task(kw)

        rp = RabbitmqPublisherUsingAmqpStorm(publisher_params=PublisherParams(queue_name=self.queue_name,
                                                                              broker_exclusive_config=self.consumer_params.broker_exclusive_config))
        rp.init_broker()
        rp.channel_wrapper_by_ampqstormbaic.qos(self.consumer_params.concurrent_num)
        rp.channel_wrapper_by_ampqstormbaic.consume(callback=callback, queue=self.queue_name, no_ack=self.consumer_params.broker_exclusive_config['no_ack'],
                                                    )
        self._rp=rp
        rp.channel.start_consuming(auto_decode=True)

    def _confirm_consume(self, kw):
        # noinspection PyBroadException
        if self.consumer_params.broker_exclusive_config['no_ack'] is False:
            try:
                kw['amqpstorm_message'].ack()  # 确认消费
            except BaseException as e:
                self.logger.error(f'AmqpStorm确认消费失败  {type(e)} {e}')

    def _requeue(self, kw):
        # amqpstorm.Message.delivery_tag
        # print(kw['amqpstorm_message'].delivery_tag)
        kw['amqpstorm_message'].nack(requeue=True)
        # kw['amqpstorm_message'].reject(requeue=True)
        # kw['amqpstorm_message'].ack()
        # self.publisher_of_same_queue.publish(kw['body'])


```

### 代码文件: funboost\consumers\rabbitmq_pika_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:27
import os
import functools
import json
from threading import Lock
# # from nb_log import LogManager, get_logger
# from funboost.constant import BrokerEnum
# from funboost.publishers.base_publisher import deco_mq_conn_error
from funboost.core.loggers import get_funboost_file_logger
import pikav1.exceptions
from pikav1.exceptions import AMQPError
import pikav1
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.funboost_config_deafult import BrokerConnConfig

get_funboost_file_logger('pikav1', log_level_int=20)


class RabbitmqConsumer(AbstractConsumer):
    """
    使用pika包实现的。
    """


    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._lock_for_pika = Lock()
        self.logger.critical('pika 多线程中操作同一个 channel 有问题，如果使用 rabbitmq 建议设置中间件为 BrokerEnum.RABBITMQ_AMQPSTORM')
        os._exit(444) # noqa

    def _dispatch_task(self):
        # channel = RabbitMqFactory(is_use_rabbitpy=0).get_rabbit_cleint().creat_a_channel()
        # channel.queue_declare(queue=self._queue_name, durable=True)
        # channel.basic_qos(prefetch_count=self.consumer_params.concurrent_num)
        def callback(ch, method, properties, body):
            body = body.decode()
            # self.logger.debug(f'从rabbitmq的 [{self._queue_name}] 队列中 取出的消息是：  {body}')
            kw = {'ch': ch, 'method': method, 'properties': properties, 'body': body}
            self._submit_task(kw)

        while True:
            # 文档例子  https://github.com/pika/pika
            try:
                self.logger.warning(f'使用pika 链接mq')
                # self.rabbit_client = RabbitMqFactory(is_use_rabbitpy=0).get_rabbit_cleint()
                # self.channel = self.rabbit_client.creat_a_channel()

                credentials = pikav1.PlainCredentials(BrokerConnConfig.RABBITMQ_USER, BrokerConnConfig.RABBITMQ_PASS)
                self.connection = pikav1.BlockingConnection(pikav1.ConnectionParameters(
                    BrokerConnConfig.RABBITMQ_HOST, BrokerConnConfig.RABBITMQ_PORT, BrokerConnConfig.RABBITMQ_VIRTUAL_HOST, credentials, heartbeat=600))
                self.channel = self.connection.channel()
                self.rabbitmq_queue = self.channel.queue_declare(queue=self._queue_name, durable=True)
                self.channel.basic_consume(on_message_callback = callback,
                                           queue=self._queue_name,
                                           # no_ack=True
                                           )
                self.channel.start_consuming()
            # Don't recover if connection was closed by broker
            # except pikav0.exceptions.ConnectionClosedByBroker:
            #     break
            # Don't recover on channel errors
            except pikav1.exceptions.AMQPChannelError as e:
                # break
                self.logger.error(e)
                continue
                # Recover on all other connection errors
            except pikav1.exceptions.AMQPConnectionError as e:
                self.logger.error(e)
                continue

    def _confirm_consume000(self, kw):
        with self._lock_for_pika:
            try:
                kw['ch'].basic_ack(delivery_tag=kw['method'].delivery_tag)  # 确认消费
            except AMQPError as e:
                self.logger.error(f'pika确认消费失败  {e}')

    def _confirm_consume(self, kw):
        # with self._lock_for_pika:
        #     self.__ack_message_pika(kw['ch'], kw['method'].delivery_tag)
        kw['ch'].connection.add_callback_threadsafe(functools.partial(self.__ack_message_pika, kw['ch'], kw['method'].delivery_tag))

    def _requeue(self, kw):
        kw['ch'].connection.add_callback_threadsafe(functools.partial(self.__nack_message_pika, kw['ch'], kw['method'].delivery_tag))
        # with self._lock_for_pika:
        # return kw['ch'].basic_nack(delivery_tag=kw['method'].delivery_tag)  # 立即重新入队。
        # with self._lock_for_pika:
        #     self.__nack_message_pika(kw['ch'], kw['method'].delivery_tag)

    def __nack_message_pika(self, channelx, delivery_tagx):
        """Note that `channel` must be the same pika channel instance via which
        the message being ACKed was retrieved (AMQP protocol constraint).
        """
        if channelx.is_open:
            channelx.basic_nack(delivery_tagx)
        else:
            # Channel is already closed, so we can't ACK this message;
            # log and/or do something that makes sense for your app in this case.
            self.logger.error(channelx.is_open)
            pass

    def __ack_message_pika(self, channelx, delivery_tagx):
        """Note that `channel` must be the same pika channel instance via which
        the message being ACKed was retrieved (AMQP protocol constraint).
        """
        if channelx.is_open:
            channelx.basic_ack(delivery_tagx)
        else:
            # Channel is already closed, so we can't ACK this message;
            # log and/or do something that makes sense for your app in this case.
            self.logger.error(channelx.is_open)
            pass

```

### 代码文件: funboost\consumers\rabbitmq_pika_consumerv0.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:27
import functools
import json
from threading import Lock

from funboost.publishers.base_publisher import deco_mq_conn_error
import pikav0.exceptions
from pikav0.exceptions import AMQPError
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from nb_log import LogManager, get_logger
from funboost.utils.rabbitmq_factory import RabbitMqFactory

get_logger('pikav0', log_level_int=20)


class RabbitmqConsumer(AbstractConsumer):
    """
    使用pika包实现的。
    """


    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._lock_for_pika = Lock()
        raise Exception('不建议使用这个中间件模式，建议使用 BrokerEnum.RABBITMQ_AMQPSTORM 操作rabbitmq')

    def _dispatch_task(self):
        # channel = RabbitMqFactory(is_use_rabbitpy=0).get_rabbit_cleint().creat_a_channel()
        # channel.queue_declare(queue=self._queue_name, durable=True)
        # channel.basic_qos(prefetch_count=self.consumer_params.concurrent_num)
        def callback(ch, method, properties, body):
            body = body.decode()
            self.logger.debug(f'从rabbitmq的 [{self._queue_name}] 队列中 取出的消息是：  {body}')
            kw = {'ch': ch, 'method': method, 'properties': properties, 'body': body}
            self._submit_task(kw)

        while True:
            # 文档例子  https://github.com/pika/pika
            try:
                self.logger.warning(f'使用pika 链接mq')
                self.rabbit_client = RabbitMqFactory(is_use_rabbitpy=0).get_rabbit_cleint()
                self.channel = self.rabbit_client.creat_a_channel()
                self.rabbitmq_queue = self.channel.queue_declare(queue=self._queue_name, durable=True)
                self.channel.basic_consume(callback,
                                           queue=self._queue_name,
                                           # no_ack=True
                                           )
                self.channel.start_consuming()
            # Don't recover if connection was closed by broker
            # except pikav0.exceptions.ConnectionClosedByBroker:
            #     break
            # Don't recover on channel errors
            except pikav0.exceptions.AMQPChannelError as e:
                # break
                self.logger.error(e)
                continue
                # Recover on all other connection errors
            except pikav0.exceptions.AMQPConnectionError as e:
                self.logger.error(e)
                continue

    def _confirm_consume000(self, kw):
        with self._lock_for_pika:
            try:
                kw['ch'].basic_ack(delivery_tag=kw['method'].delivery_tag)  # 确认消费
            except AMQPError as e:
                self.logger.error(f'pika确认消费失败  {e}')

    def _confirm_consume(self, kw):
        with self._lock_for_pika:
            self.__ack_message_pika(kw['ch'], kw['method'].delivery_tag)
        # kw['ch'].connection.add_callback_threadsafe(functools.partial(self.__ack_message_pika, kw['ch'], kw['method'].delivery_tag))

    def _requeue(self, kw):
        # kw['ch'].connection.add_callback_threadsafe(functools.partial(self.__nack_message_pika, kw['ch'], kw['method'].delivery_tag))
        # with self._lock_for_pika:
        # return kw['ch'].basic_nack(delivery_tag=kw['method'].delivery_tag)  # 立即重新入队。
        with self._lock_for_pika:
            self.__nack_message_pika(kw['ch'], kw['method'].delivery_tag)

    def __nack_message_pika(self, channelx, delivery_tagx):
        """Note that `channel` must be the same pika channel instance via which
        the message being ACKed was retrieved (AMQP protocol constraint).
        """
        if channelx.is_open:
            channelx.basic_nack(delivery_tagx)
        else:
            # Channel is already closed, so we can't ACK this message;
            # log and/or do something that makes sense for your app in this case.
            self.logger.error(channelx.is_open)
            pass

    def __ack_message_pika(self, channelx, delivery_tagx):
        """Note that `channel` must be the same pika channel instance via which
        the message being ACKed was retrieved (AMQP protocol constraint).
        """
        if channelx.is_open:
            channelx.basic_ack(delivery_tagx)
        else:
            # Channel is already closed, so we can't ACK this message;
            # log and/or do something that makes sense for your app in this case.
            self.logger.error(channelx.is_open)
            pass

```

### 代码文件: funboost\consumers\rabbitmq_rabbitpy_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:31
import json
import rabbitpy
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.utils.rabbitmq_factory import RabbitMqFactory


class RabbitmqConsumerRabbitpy(AbstractConsumer):
    """
    使用rabbitpy实现的
    """
    def custom_init(self):
        raise Exception('不建议使用这个中间件模式，建议使用 BrokerEnum.RABBITMQ_AMQPSTORM 操作rabbitmq')

    def _dispatch_task(self):
        # noinspection PyTypeChecker
        channel = RabbitMqFactory(is_use_rabbitpy=1).get_rabbit_cleint().creat_a_channel()  # type:  rabbitpy.AMQP         #
        channel.queue_declare(queue=self._queue_name, durable=True)
        channel.basic_qos(prefetch_count=self.consumer_params.concurrent_num)
        for message in channel.basic_consume(self._queue_name, no_ack=False):
            body = message.body.decode()
            # self.logger.debug(f'从rabbitmq {self._queue_name} 队列中 取出的消息是：  {body}')
            kw = {'message': message, 'body': body}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        kw['message'].ack()

    def _requeue(self, kw):
        kw['message'].nack(requeue=True)

```

### 代码文件: funboost\consumers\redis_brpoplpush_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json
# import time
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.utils import  decorators
from funboost.utils.redis_manager import RedisMixin


class RedisBrpopLpushConsumer(AbstractConsumer, RedisMixin):
    """
    redis作为中间件实现的，使用redis brpoplpush 实现的，并且使用心跳来解决 关闭/掉线 重新分发问题。

    """


    def start_consuming_message(self):
        self.consumer_params.is_send_consumer_hearbeat_to_redis = True
        super().start_consuming_message()
        self.keep_circulating(60, block=False)(self._requeue_tasks_which_unconfirmed)()

    # noinspection DuplicatedCode
    def _dispatch_task(self):
        unack_list_name = f'unack_{self._queue_name}_{self.consumer_identification}'
        while True:
            msg = self.redis_db_frame.brpoplpush(self._queue_name, unack_list_name, timeout=60)
            if msg:
                kw = {'body': msg, 'raw_msg': msg}
                self._submit_task(kw)

    def _confirm_consume(self, kw):
        self.redis_db_frame.lrem(f'unack_{self._queue_name}_{self.consumer_identification}',count=1,value= kw['raw_msg'], )

    def _requeue(self, kw):
        self.redis_db_frame.lpush(self._queue_name, json.dumps(kw['body']))

    def _requeue_tasks_which_unconfirmed(self):
        lock_key = f'fsdf_lock__requeue_tasks_which_unconfirmed:{self._queue_name}'
        with decorators.RedisDistributedLockContextManager(self.redis_db_frame, lock_key, ) as lock:
            if lock.has_aquire_lock:
                self._distributed_consumer_statistics.send_heartbeat()
                current_queue_hearbeat_ids = self._distributed_consumer_statistics.get_queue_heartbeat_ids(without_time=True)
                current_queue_unacked_msg_queues = self.redis_db_frame.scan(0, f'unack_{self._queue_name}_*', count=100)
                for current_queue_unacked_msg_queue in current_queue_unacked_msg_queues[1]:
                    current_queue_unacked_msg_queue_str = current_queue_unacked_msg_queue
                    if current_queue_unacked_msg_queue_str.split(f'unack_{self._queue_name}_')[1] not in current_queue_hearbeat_ids:
                        msg_list = self.redis_db_frame.lrange(current_queue_unacked_msg_queue_str, 0, -1)
                        self.logger.warning(f"""{current_queue_unacked_msg_queue_str} 是掉线或关闭消费者的待确认任务, 将 一共 {len(msg_list)} 个消息,
                                            详情是 {msg_list} 推送到正常消费队列 {self._queue_name} 队列中。
                                            """)
                        self.redis_db_frame.lpush(self._queue_name, *msg_list)
                        self.redis_db_frame.delete(current_queue_unacked_msg_queue_str)

```

### 代码文件: funboost\consumers\redis_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json
# import time
import time



from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.utils.redis_manager import RedisMixin
from funboost.core.serialization import Serialization

class RedisConsumer(AbstractConsumer, RedisMixin):
    """
    redis作为中间件实现的，使用redis list 结构实现的。
    这个如果消费脚本在运行时候随意反复重启或者非正常关闭或者消费宕机，会丢失大批任务。高可靠需要用rabbitmq或者redis_ack_able或者redis_stream的中间件方式。

    这个是复杂版，一次性拉取100个,减少和redis的交互，简单版在 funboost/consumers/redis_consumer_simple.py
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'redis_bulk_push':1,'pull_msg_batch_size':100}   #redis_bulk_push 是否redis批量推送

    # noinspection DuplicatedCode
    def _dispatch_task(self):
        pull_msg_batch_size =  self.consumer_params.broker_exclusive_config['pull_msg_batch_size']
        while True:
            # if False:
            #     pass
            with self.redis_db_frame.pipeline() as p:
                p.lrange(self._queue_name, 0, pull_msg_batch_size- 1)
                p.ltrim(self._queue_name, pull_msg_batch_size, -1)
                task_str_list = p.execute()[0]
            if task_str_list:
                # self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {task_str_list}  ')
                self._print_message_get_from_broker( task_str_list)
                for task_str in task_str_list:
                    kw = {'body': task_str}
                    self._submit_task(kw)
            else:
                result = self.redis_db_frame.brpop(self._queue_name, timeout=60)
                if result:
                    # self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {result[1].decode()}  ')
                    kw = {'body': result[1]}
                    self._submit_task(kw)

    def _dispatch_task00(self):
        while True:
            result = self.redis_db_frame.blpop(self._queue_name, timeout=60)
            if result:
                # self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {result[1].decode()}  ')
                kw = {'body': result[1]}
                self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # redis没有确认消费的功能。

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name,Serialization.to_json_str(kw['body']))

```

### 代码文件: funboost\consumers\redis_consumer_ack_able.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
"""

这个是加强版的可确认消费的redis消费实现，所以比redis_conusmer实现复杂很多。
这个可以确保随意反复多次停止重启脚本，任务永不丢失
"""
import json
import time
from deprecated.sphinx import deprecated
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.consumers.confirm_mixin import ConsumerConfirmMixinWithTheHelpOfRedis, ConsumerConfirmMixinWithTheHelpOfRedisByHearbeat


@deprecated(version='1.0', reason="This class not used")
class RedisConsumerAckAble000(ConsumerConfirmMixinWithTheHelpOfRedis, AbstractConsumer, ):
    """
    随意重启代码会极小概率丢失1个任务。
    redis作为中间件实现的。将取出来的消息同时放入一个set中，代表unack消费状态。以支持对机器和python进程的随意关闭和断电。
    和celery的配置  task_reject_on_worker_lost = True task_acks_late = True后，处理逻辑几乎不约而同相似。
    """


    def _dispatch_task(self):
        while True:
            result = self.redis_db_frame.blpop(self._queue_name, timeout=60)
            # task_bytes = self.redis_db_frame.lpop(self._queue_name)
            if result:
                task_str = result[1]
                # 如果运行了第20行，但没运行下面这一行，仍然有极小概率会丢失1个任务。但比不做控制随意关停，丢失几百个线程你的redis任务强多了。
                self._add_task_str_to_unack_zset(task_str, )
                # self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：     {task_str}  ')
                kw = {'body': task_str, 'task_str': task_str}
                self._submit_task(kw)

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name, json.dumps(kw['body']))


@deprecated(version='1.0', reason="This class not used")
class RedisConsumerAckAble111(ConsumerConfirmMixinWithTheHelpOfRedis, AbstractConsumer, ):
    """
    随意重启代码不会丢失任务，使用的是超时10分钟没有确认消费就认为是已经断开了，重新回到代消费队列。
    redis作为中间件实现的。将取出来的消息同时放入一个set中，代表unack消费状态。以支持对机器和python进程的随意关闭和断电。
    和celery的配置  task_reject_on_worker_lost = True task_acks_late = True后，处理逻辑几乎不约而同相似。

    lua_4 = '''
   local v = redis.call("lpop", KEYS[1])
   if v then
   redis.call('rpush',KEYS[2],v)
    end
   return v'''
    # script_4 = r.register_script(lua_4)
    #
    # print(script_4(keys=["text_pipelien1","text_pipelien1b"]))
    """


    def _dispatch_task(self):
        lua = '''
                     local v = redis.call("lpop", KEYS[1])
                     if v then
                     redis.call('zadd',KEYS[2],ARGV[1],v)
                      end
                     return v
                '''
        script = self.redis_db_frame.register_script(lua)
        while True:
            return_v = script(keys=[self._queue_name, self._unack_zset_name], args=[time.time()])
            if return_v:
                task_str = return_v
                self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：     {task_str}  ')
                kw = {'body': task_str, 'task_str': task_str}
                self._submit_task(kw)
            else:
                # print('xiuxi')
                time.sleep(0.1)

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name, json.dumps(kw['body']))


class RedisConsumerAckAble(ConsumerConfirmMixinWithTheHelpOfRedisByHearbeat, AbstractConsumer, ):
    """
    随意重启代码不会丢失任务，采用的是配合redis心跳，将心跳过期的未确认的队列，全部重回消费队列。这种不需要等待10分钟，判断更精确。
    redis作为中间件实现的。将取出来的消息同时放入一个set中，代表unack消费状态。以支持对机器和python进程的随意关闭和断电。
    和celery的配置  task_reject_on_worker_lost = True task_acks_late = True后，处理逻辑几乎不约而同相似。

    lua_4 = '''
   local v = redis.call("lpop", KEYS[1])
   if v then
   redis.call('rpush',KEYS[2],v)
    end
   return v'''
    # script_4 = r.register_script(lua_4)
    #
    # print(script_4(keys=["text_pipelien1","text_pipelien1b"]))
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = { 'pull_msg_batch_size': 100}

    def _dispatch_task000(self):
        # 可以采用lua脚本，也可以采用redis的watch配合pipeline使用。比代码分两行pop和zadd比还能减少一次io交互，还能防止丢失小概率一个任务。
        lua = '''
                     local v = redis.call("lpop", KEYS[1])
                     if v then
                     redis.call('zadd',KEYS[2],ARGV[1],v)
                      end
                     return v 
                '''
        script = self.redis_db_frame.register_script(lua)
        while True:
            return_v = script(keys=[self._queue_name, self._unack_zset_name], args=[time.time()])
            if return_v:
                task_str = return_v
                self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：     {task_str}  ')
                kw = {'body': task_str, 'task_str': task_str}
                self._submit_task(kw)
            else:
                # print('xiuxi')
                time.sleep(0.5)

    def _dispatch_task(self):
        pull_msg_batch_size = self.consumer_params.broker_exclusive_config['pull_msg_batch_size']
        lua = f'''
                     local task_list = redis.call("lrange", KEYS[1],0,{pull_msg_batch_size-1})
                     redis.call("ltrim", KEYS[1],{pull_msg_batch_size},-1)
                     if (#task_list > 0) then
                        for task_index,task_value in ipairs(task_list)
                        do
                            redis.call('zadd',KEYS[2],ARGV[1],task_value)
                        end
                        return task_list
                    else
                        --local v = redis.call("blpop",KEYS[1],4)      
                        --return v
                      end

                '''
        """
        local v = redis.call("blpop",KEYS[1],60)  # redis 的lua 脚本禁止使用blpop
        local v = redis.call("lpop",KEYS[1])
        """
        script = self.redis_db_frame.register_script(lua)
        while True:
            task_str_list = script(keys=[self._queue_name, self._unack_zset_name], args=[time.time()])
            if task_str_list:
                self._print_message_get_from_broker( task_str_list)
                # self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {task_str_list}  ')
                for task_str in task_str_list:
                    kw = {'body': task_str, 'task_str': task_str}
                    self._submit_task(kw)
            else:
                time.sleep(0.2)

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name, json.dumps(kw['body']))

```

### 代码文件: funboost\consumers\redis_consumer_ack_using_timeout.py
```python
﻿# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2024/8/8 0008 13:32
import json
import time
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.serialization import Serialization
from funboost.utils.decorators import RedisDistributedLockContextManager
from funboost.utils.redis_manager import RedisMixin


class RedisConsumerAckUsingTimeout(AbstractConsumer, RedisMixin):
    """
    redis作为中间件实现的。
    使用超时未能ack就自动重入消息队列，例如消息取出后，由于突然断电或重启或其他原因，导致消息以后再也不能主动ack了，超过一定时间就重新放入消息队列
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'ack_timeout': 3600}

    # RedisConsumerAckUsingTimeout的ack timeot 是代表消息取出后过了多少秒还未ack，就自动重回队列。这个配置一定要大于函数消耗时间，否则不停的重回队列。
    '''用法，如何设置ack_timeout，是使用 broker_exclusive_config 中传递，就能覆盖这里的3600，用户不用改BROKER_EXCLUSIVE_CONFIG_DEFAULT的源码。
    @boost(BoosterParams(queue_name='test_redis_ack__use_timeout', broker_kind=BrokerEnum.REIDS_ACK_USING_TIMEOUT,
                         concurrent_num=5, log_level=20, broker_exclusive_config={'ack_timeout': 30}))
    '''

    def custom_init(self):
        self._unack_zset_name = f'{self._queue_name}__unack_using_timeout'
        self._ack_timeout = self.consumer_params.broker_exclusive_config['ack_timeout']
        self._last_show_unack_ts = time.time()

    def start_consuming_message(self):
        self.consumer_params.is_send_consumer_hearbeat_to_redis = True
        super().start_consuming_message()
        self.keep_circulating(10, block=False)(self._requeue_tasks_which_unconfirmed)()

    # def _add_task_str_to_unack_zset(self, task_str, ):
    #     self.redis_db_frame.zadd(self._unack_zset_name, {task_str: time.time()})

    def _confirm_consume(self, kw):
        self.redis_db_frame.zrem(self._unack_zset_name, kw['task_str'])

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name, Serialization.to_json_str(kw['body']))

    def _dispatch_task(self):
        lua = '''
                     local v = redis.call("lpop", KEYS[1])
                     if v then
                     redis.call('zadd',KEYS[2],ARGV[1],v)
                      end
                     return v
                '''
        script = self.redis_db_frame.register_script(lua)
        while True:
            return_v = script(keys=[self._queue_name, self._unack_zset_name], args=[time.time()])
            if return_v:
                task_str = return_v
                kw = {'body': task_str, 'task_str': task_str}
                self._submit_task(kw)
            else:
                time.sleep(0.1)

    def _requeue_tasks_which_unconfirmed(self):
        """不使用这种方案，不适合本来来就需要长耗时的函数，很死板"""
        # 防止在多个进程或多个机器中同时做扫描和放入未确认消费的任务。使用个分布式锁。
        lock_key = f'funboost_lock__requeue_tasks_which_unconfirmed_timeout:{self._queue_name}'
        with RedisDistributedLockContextManager(self.redis_db_frame, lock_key, ) as lock:
            if lock.has_aquire_lock:
                time_max = time.time() - self._ack_timeout
                for value in self.redis_db_frame.zrangebyscore(self._unack_zset_name, 0, time_max):
                    self.logger.warning(f'超过了 {self._ack_timeout} 秒未能确认消费, 向 {self._queue_name} 队列重新放入未消费确认的任务 {value} ,')
                    self._requeue({'body': value})
                    self.redis_db_frame.zrem(self._unack_zset_name, value)
                if time.time() - self._last_show_unack_ts > 600:  # 不要频繁提示打扰
                    self.logger.info(f'{self._unack_zset_name} 中有待确认消费任务的数量是'
                                     f' {self.redis_db_frame.zcard(self._unack_zset_name)}')
                    self._last_show_unack_ts = time.time()

```

### 代码文件: funboost\consumers\redis_consumer_priority.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
"""

这个是加强版的可确认消费的redis消费实现，所以比redis_conusmer实现复杂很多。
这个可以确保随意反复多次停止重启脚本，任务不丢失，没人采用lua，随意反复重启代码极小概率丢失一个任务。

这个是支持任务优先级的redis队列实现。
"""
import json
import time

import redis5

from funboost.consumers.redis_consumer_ack_able import RedisConsumerAckAble


class RedisPriorityConsumer(RedisConsumerAckAble):
    """
       使用多个redis list来实现redis支持队列优先级。brpop可以支持监听多个redis键。
       根据消息的 priroty 来决定发送到哪个队列。我这个想法和celery依赖的kombu实现的redis具有队列优先级是一样的。

       注意：  rabbitmq、celery队列优先级都指的是同一个队列中的每个消息具有不同的优先级，消息可以不遵守先进先出，而是优先级越高的消息越先取出来。
              队列优先级其实是某个队列中的消息的优先级，这是队列的 x-max-priority 的原生概念。

              队列优先级有的人错误的以为是 queuexx 和queueyy两个队列，以为是优先消费queuexx的消息，这是大错特错的想法。
              队列优先级是指某个队列中的每个消息可以具有不同的优先级，不是在不同队列名之间来比较哪个队列名具有更高的优先级。
    """
    """用法如下。
    第一，如果使用redis做支持优先级的消息队列， @boost中要选择 broker_kind = BrokerEnum.REDIS_PRIORITY
    第二，broker_exclusive_config={'x-max-priority':4} 意思是这个队列中的任务消息支持多少种优先级，一般写5就完全够用了。
    第三，发布消息时候要使用publish而非push,发布要加入参  
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
    funboost 的 consumer的 _shedual_task 非常灵活，用户实现把从消息队列取出的消息通过_submit_task方法
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
    def join_shedual_task_thread(cls):
        """

        :return:
        """
        # ConsumersManager.join_all_consumer_shedual_task_thread()
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

        atexit.register(self.join_shedual_task_thread)

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
            self.keep_circulating(1, daemon=False)(self._shedual_task)()
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
    def _shedual_task(self):
        """
        每个子类必须实现这个的方法，完成如何从中间件取出消息，并将函数和运行参数添加到工作池。

        funboost 的 _shedual_task 哲学是：“我不管你怎么从你的系统里拿到任务，我只要求你拿到任务后，
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
    #         t = Thread(target=self.consumer.keep_circulating(1)(self.consumer._shedual_task))
    #         ConsumersManager.schedulal_thread_to_be_join.append(t)
    #         t.start()
    #     else:
    #         if self._concurrent_mode in [ConcurrentModeEnum.THREADING, ConcurrentModeEnum.ASYNC,
    #                                      ConcurrentModeEnum.SINGLE_THREAD, ]:
    #             t = Thread(target=self.consumer.keep_circulating(1)(self.consumer._shedual_task))
    #             ConsumersManager.schedulal_thread_to_be_join.append(t)
    #             t.start()
    #         elif self._concurrent_mode == ConcurrentModeEnum.GEVENT:
    #             import gevent
    #             g = gevent.spawn(self.consumer.keep_circulating(1)(self.consumer._shedual_task), )
    #             ConsumersManager.schedulal_thread_to_be_join.append(g)
    #         elif self._concurrent_mode == ConcurrentModeEnum.EVENTLET:
    #             import eventlet
    #             g = eventlet.spawn(self.consumer.keep_circulating(1)(self.consumer._shedual_task), )
    #             ConsumersManager.schedulal_thread_to_be_join.append(g)

    def schedulal_task_with_no_block(self):
        self.consumer.keep_circulating(1, block=False, daemon=False)(self.consumer._shedual_task)()


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

    def _shedual_task(self):
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

    def _shedual_task(self):
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

    这个类其实是多余的，因为用户完全可以继承AbstractConsumer，然后实现custom_init方法，然后实现_shedual_task, _confirm_consume, _requeue方法来新增自定义broker。
    这个类是为了清晰明确的告诉你，仅仅需要下面三个方法，就可以实现一个自定义broker，因为AbstractConsumer基类功能太丰富了，基类方法是在太多了，用户不知道需要继承重写哪方法
    
    
    """
    def custom_init(self):
        pass

    @abc.abstractmethod
    def _shedual_task(self):
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

    def _shedual_task(self):
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
    def _shedual_task(self):
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
    def _shedual_task(self):
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
    def _shedual_task(self):
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

    def _shedual_task(self):
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

    def _shedual_task(self):
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

    def _shedual_task(self):

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

    def _shedual_task(self):

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
    def _shedual_task(self):  # 这个倍while 1 启动的，会自动重连。
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

    def _shedual_task(self):
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

    def _shedual_task(self):
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


    def _shedual_task(self):
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
    def _shedual_task(self):
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
        self._shedual_task()

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

    def _shedual_task(self):
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


    def _shedual_task(self):
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


    def _shedual_task(self):
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


    def _shedual_task(self):
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

    def _shedual_task(self):
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

    def _shedual_task(self):
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

    def _shedual_task(self):
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

    def _shedual_task(self):
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

    def _shedual_task(self):
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

    def _shedual_task(self):
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
    def _shedual_task(self):
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
    def _shedual_task(self):
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

    def _shedual_task00(self):
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


    def _shedual_task(self):
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


    def _shedual_task(self):
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

    def _shedual_task000(self):
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

    def _shedual_task(self):
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

    def _shedual_task(self):
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
    第三，发布消息时候要使用publish而非push,发布要加入参  priority_control_config=PriorityConsumingControlConfig(other_extra_params={'priroty': priorityxx})，
         其中 priorityxx 必须是整数，要大于等于0且小于队列的x-max-priority。x-max-priority这个概念是rabbitmq的原生概念，celery中也是这样的参数名字。

         发布的消息priroty 越大，那么该消息就越先被取出来，这样就达到了打破先进先出的规律。比如优先级高的消息可以给vip用户来运行函数实时，优先级低的消息可以离线跑批。

    from funboost import register_custom_broker, boost, PriorityConsumingControlConfig,BrokerEnum

    @boost('test_redis_priority_queue3', broker_kind=BrokerEnum.REDIS_PRIORITY, qps=5,concurrent_num=2,broker_exclusive_config={'x-max-priority':4})
    def f(x):
        print(x)


    if __name__ == '__main__':
        for i in range(1000):
            randx = random.randint(1, 4)
            f.publish({'x': randx}, priority_control_config=PriorityConsumingControlConfig(other_extra_params={'priroty': randx}))
        print(f.get_message_count())
        f.consume()
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'x-max-priority': None}  # x-max-priority 是 rabbitmq的优先级队列配置，必须为整数，强烈建议要小于5。为None就代表队列不支持优先级。

    def _shedual_task0000(self):

        while True:
            # task_str_list = script(keys=[queues_str, self._unack_zset_name], args=[time.time()])
            task_tuple = self.redis_db_frame.blpop(keys=self.publisher_of_same_queue.queue_list, timeout=60)  # 监听了多个键名，所以间接实现了优先级，和kombu的redis 支持优先级的设计思路不谋而合。
            if task_tuple:
                msg = task_tuple[1]
                self.redis_db_frame.zadd(self._unack_zset_name, {msg: time.time()})
                # self.logger.debug(task_tuple)
                # self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {task_str_list}  ')
                kw = {'body': msg, 'task_str': msg}
                self._submit_task(kw)

    def _shedual_task(self):
        """https://redis.readthedocs.io/en/latest/advanced_features.html#default-pipelines """
        while True:
            # task_str_list = script(keys=[queues_str, self._unack_zset_name], args=[time.time()])
            while True:
                try:
                    with self.redis_db_frame.pipeline() as p:
                        p.watch(self._unack_zset_name, *self.publisher_of_same_queue.queue_list, )
                        task_tuple = p.blpop(keys=self.publisher_of_same_queue.queue_list, timeout=60)  # 监听了多个键名，所以间接实现了优先级，和kombu的redis 支持优先级的设计思路不谋而合。
                        # print(task_tuple)
                        if task_tuple:
                            msg = task_tuple[1]
                            p.zadd(self._unack_zset_name, {msg: time.time()})
                            # self.logger.debug(task_tuple)
                            p.unwatch()
                            p.execute()
                            break
                except redis5.WatchError:
                    continue
            if task_tuple:
                # self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {task_str_list}  ')
                kw = {'body': msg, 'task_str': msg}
                self._submit_task(kw)

    def _requeue(self, kw):
        self.publisher_of_same_queue.publish(kw['body'])

```

### 代码文件: funboost\consumers\redis_consumer_simple.py
```python
﻿# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/8 0008 13:32
import json
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.serialization import Serialization
from funboost.utils.redis_manager import RedisMixin


class RedisConsumer(AbstractConsumer, RedisMixin):
    """
    redis作为中间件实现的。
    """


    def _shedual_task(self):
        while True:
            result = self.redis_db_frame.blpop(self._queue_name,timeout=60)
            if result:
                kw = {'body': result[1]}
                self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # redis没有确认消费的功能。

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name, Serialization.to_json_str(kw['body']))



```

### 代码文件: funboost\consumers\redis_filter.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:10
"""
任务消费完成后，如果重复发布则过滤。分别实现永久性过滤重复任务和过滤有效期内的重复任务。
任务过滤 = 函数参数过滤 = 字典过滤 = 排序后的键值对json字符串过滤。
"""

import json
import time
from collections import OrderedDict
import typing

from funboost.core.serialization import Serialization
from funboost.utils import  decorators
from funboost.core.loggers import FunboostFileLoggerMixin

from funboost.utils.redis_manager import RedisMixin


class RedisFilter(RedisMixin, FunboostFileLoggerMixin):
    """
    使用set结构，
    基于函数参数的任务过滤。这个是永久性的过滤，除非自己手动删除这个键。
    """

    def __init__(self, redis_key_name, redis_filter_task_expire_seconds):
        """
        :param redis_key_name: 任务过滤键
        :param redis_filter_task_expire_seconds: 任务过滤的过期时间
        """
        self._redis_key_name = redis_key_name
        self._redis_filter_task_expire_seconds = redis_filter_task_expire_seconds

        # @staticmethod
        # def _get_ordered_str(value):
        #     """对json的键值对在redis中进行过滤，需要先把键值对排序，否则过滤会不准确如 {"a":1,"b":2} 和 {"b":2,"a":1}"""
        #     value = Serialization.to_dict(value)
        #     ordered_dict = OrderedDict()
        #     for k in sorted(value):
        #         ordered_dict[k] = value[k]
        #     return json.dumps(ordered_dict)
    
    @staticmethod
    def generate_filter_str(value: typing.Union[str, dict],  filter_str: typing.Optional[str] = None):
        """对json的键值对在redis中进行过滤，需要先把键值对排序，否则过滤会不准确如 {"a":1,"b":2} 和 {"b":2,"a":1}"""
        if filter_str: # 如果用户单独指定了过滤字符串，就使用使用户指定的过滤字符串，否则使用排序后的键值对字符串
            return filter_str
        value = Serialization.to_dict(value)
        ordered_dict = OrderedDict()
        for k in sorted(value):
            ordered_dict[k] = value[k]
        # print(ordered_dict,filter_str)
        return json.dumps(ordered_dict)


    def add_a_value(self, value: typing.Union[str, dict], filter_str: typing.Optional[str] = None):
        self.redis_db_filter_and_rpc_result.sadd(self._redis_key_name, self.generate_filter_str(value, filter_str))

    def manual_delete_a_value(self, value: typing.Union[str, dict], filter_str: typing.Optional[str] = None):
        self.redis_db_filter_and_rpc_result.srem(self._redis_key_name, self.generate_filter_str(value, filter_str))

    def check_value_exists(self, value, filter_str: typing.Optional[str] = None):
        return self.redis_db_filter_and_rpc_result.sismember(self._redis_key_name, self.generate_filter_str(value, filter_str))

    def delete_expire_filter_task_cycle(self):
        pass


class RedisImpermanencyFilter(RedisFilter):
    """
    使用zset结构
    基于函数参数的任务过滤。这个是非永久性的过滤，例如设置过滤过期时间是1800秒 ，30分钟前发布过1 + 2 的任务，现在仍然执行，
    如果是30分钟内发布过这个任务，则不执行1 + 2，现在把这个逻辑集成到框架，一般用于接口缓存。
    """

    def add_a_value(self, value: typing.Union[str, dict], filter_str: typing.Optional[str] = None):
        self.redis_db_filter_and_rpc_result.zadd(self._redis_key_name, {self.generate_filter_str(value, filter_str):time.time()})

    def manual_delete_a_value(self, value: typing.Union[str, dict], filter_str: typing.Optional[str] = None):
        self.redis_db_filter_and_rpc_result.zrem(self._redis_key_name, self.generate_filter_str(value, filter_str))

    def check_value_exists(self, value, filter_str: typing.Optional[str] = None):
        # print(self.redis_db_filter_and_rpc_result.zrank(self._redis_key_name, self.generate_filter_str(value, filter_str)))
        is_exists = False if self.redis_db_filter_and_rpc_result.zscore(self._redis_key_name, self.generate_filter_str(value, filter_str)) is None else True
        # print(is_exists,value,filter_str,self.generate_filter_str(value, filter_str))
        return is_exists   

    @decorators.keep_circulating(60, block=False)
    def delete_expire_filter_task_cycle000(self):
        """
        一直循环删除过期的过滤任务。
        # REMIND 任务过滤过期时间最好不要小于60秒，否则删除会不及时,导致发布的新任务由于命中了任务过滤，而不能触发执行。一般实时价格接口是缓存5分钟或30分钟没有问题。
        :return:
        """
        time_max = time.time() - self._redis_filter_task_expire_seconds
        for value in self.redis_db_filter_and_rpc_result.zrangebyscore(self._redis_key_name, 0, time_max):
            self.logger.info(f'删除 {self._redis_key_name} 键中的过滤任务 {value}')
            self.redis_db_filter_and_rpc_result.zrem(self._redis_key_name, value)

    @decorators.keep_circulating(60, block=False)
    def delete_expire_filter_task_cycle(self):
        """

        一直循环删除过期的过滤任务。任务过滤过期时间最好不要小于60秒，否则删除会不及时,导致发布的新任务不能触发执行。一般实时价格接口是缓存5分钟或30分钟。
        :return:
        """
        time_max = time.time() - self._redis_filter_task_expire_seconds
        delete_num = self.redis_db_filter_and_rpc_result.zremrangebyscore(self._redis_key_name, 0, time_max)
        self.logger.warning(f'从{self._redis_key_name}  键删除 {delete_num} 个过期的过滤任务')
        self.logger.warning(f'{self._redis_key_name}  键中有 {self.redis_db_filter_and_rpc_result.zcard(self._redis_key_name)} 个没有过期的过滤任务')


class RedisImpermanencyFilterUsingRedisKey(RedisFilter):
    """
    直接把任务当做redis的key，使用redis自带的过期机制删除过期的过滤任务。
    基于函数参数的任务过滤。这个是非永久性的过滤，例如设置过滤过期时间是1800秒 ，30分钟前发布过1 + 2 的任务，现在仍然执行，
    如果是30分钟内发布过这个任务，则不执行1 + 2，现在把这个逻辑集成到框架，一般用于接口缓存。
    这种过滤模式键太多了，很难看，固定放到 redis_db_filter_and_rpc_result ，不放到消息队列的db里面。
    """

    def __add_dir_prefix(self, value):
        """
        添加一个前缀，以便redis形成一个树形文件夹，方便批量删除和折叠
        :return:
        """
        return f'{self._redis_key_name}:{value.replace(":", "：")}'  # 任务是json，带有：会形成很多树，换成中文冒号。

    def add_a_value(self, value: typing.Union[str, dict], filter_str: typing.Optional[str] = None):
        redis_key = self.__add_dir_prefix(self.generate_filter_str(value, filter_str))
        self.redis_db_filter_and_rpc_result.set(redis_key, 1)
        self.redis_db_filter_and_rpc_result.expire(redis_key, self._redis_filter_task_expire_seconds)

    def manual_delete_a_value(self, value: typing.Union[str, dict], filter_str: typing.Optional[str] = None):
        self.redis_db_filter_and_rpc_result.delete(self.__add_dir_prefix(self.generate_filter_str(value, filter_str)))

    def check_value_exists(self, value, filter_str: typing.Optional[str] = None):
        return True if self.redis_db_filter_and_rpc_result.exists(self.__add_dir_prefix(self.generate_filter_str(value, filter_str))) else True

    def delete_expire_filter_task_cycle(self):
        """
        redis服务端会自动删除过期的过滤任务键。不用在客户端管理。
        :return:
        """
        pass


if __name__ == '__main__':
    # params_filter = RedisFilter('filter_set:abcdefgh2', 120)
    params_filter = RedisImpermanencyFilter('filter_zset:abcdef2', 120)
    # params_filter = RedisImpermanencyFilterUsingRedisKey('filter_dir', 300)
    for i in range(10):
        # params_filter.add_a_value({'x': i, 'y': i * 2},str(i))
        params_filter.add_a_value({'x': i, 'y': i * 2},None)

    # params_filter.manual_delete_a_value({'a': 1, 'b': 2})
    print(params_filter.check_value_exists({'x': 1, 'y': 2}))
    # params_filter.delete_expire_filter_task_cycle()
    # params_filter.add_a_value({'a': 1, 'b': 5})
    # print(params_filter.check_value_exists({'a': 1, 'b': 2}))
    # time.sleep(130)
    # print(params_filter.check_value_exists({'a': 1, 'b': 2}))

```

### 代码文件: funboost\consumers\redis_pubsub_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.utils.redis_manager import RedisMixin


class RedisPbSubConsumer(AbstractConsumer, RedisMixin):
    """
    redis作为中间件实现的。
    """


    def _shedual_task0000(self):
        pub = self.redis_db_frame.pubsub()
        pub.subscribe(self.queue_name)
        for item in pub.listen():
            if item['type'] == 'message':

                kw = {'body': item['data']}
                self._submit_task(kw)

    def _shedual_task(self):
        pub = self.redis_db_frame.pubsub()
        pub.subscribe(self.queue_name)
        pub.parse_response()
        while True:  # 无限循环
            msg_list = pub.parse_response(timeout=60)  # 得到消息内容
            if msg_list:
                kw = {'body': msg_list[2]}
                self._submit_task(kw)



    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        pass

```

### 代码文件: funboost\consumers\redis_stream_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2021/4/3 0008 13:32
import json
import redis5
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.utils import decorators
from funboost.utils.redis_manager import RedisMixin


class RedisStreamConsumer(AbstractConsumer, RedisMixin):
    """
    redis 的 stream 结构 作为中间件实现的。需要redis 5.0以上，redis stream结构 是redis的消息队列，概念类似kafka，功能远超 list结构。
    """
    GROUP = 'funboost_group'
    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'group': 'funboost_group','pull_msg_batch_size': 100}

    def custom_init(self):
        self.group = self.consumer_params.broker_exclusive_config['group'] or self.GROUP

    def start_consuming_message(self):
        redis_server_info_dict = self.redis_db_frame.info()
        # print(redis_server_info_dict)
        if float(redis_server_info_dict['redis_version'][0]) < 5:
            raise EnvironmentError('必须是5.0版本以上redis服务端才能支持  stream 数据结构，'
                                   '请升级服务端，否则使用 REDIS_ACK_ABLE 方式使用redis 的 list 结构')
        if self.redis_db_frame.type(self._queue_name) == 'list':
            raise EnvironmentError(f'检测到已存在 {self._queue_name} 这个键，且类型是list， 必须换个队列名字或者删除这个 list 类型的键。'
                                   f'RedisStreamConsumer 使用的是 stream 数据结构')
        self.consumer_params.is_send_consumer_hearbeat_to_redis = True
        super().start_consuming_message()
        self.keep_circulating(60, block=False)(self._requeue_tasks_which_unconfirmed)()

    def _shedual_task(self):
        pull_msg_batch_size = self.consumer_params.broker_exclusive_config['pull_msg_batch_size']

        try:
            self.redis_db_frame.xgroup_create(self._queue_name,self.group , id=0, mkstream=True)
        except redis5.exceptions.ResponseError as e:
            self.logger.info(e)  # BUSYGROUP Consumer Group name already exists  不能重复创建消费者组。
        while True:
            # redis服务端必须是5.0以上，并且确保这个键的类型是stream不能是list数据结构。
            results = self.redis_db_frame.xreadgroup(self.group, self.consumer_identification,
                                                              {self.queue_name: ">"}, count=pull_msg_batch_size, block=60 * 1000)
            if results:
                # self.logger.debug(f'从redis的 [{self._queue_name}] stream 中 取出的消息是：  {results}  ')
                self._print_message_get_from_broker( results)
                # print(results[0][1])
                for msg_id, msg in results[0][1]:
                    kw = {'body': msg[''], 'msg_id': msg_id}
                    self._submit_task(kw)

    def _confirm_consume(self, kw):
        # self.redis_db_frame.xack(self._queue_name, 'distributed_frame_group', kw['msg_id'])
        # self.redis_db_frame.xdel(self._queue_name, kw['msg_id']) # 便于xlen
        with self.redis_db_frame.pipeline() as pipe:
            pipe.xack(self._queue_name, self.group, kw['msg_id'])
            pipe.xdel(self._queue_name, kw['msg_id'])  # 直接删除不需要保留， 便于xlen
            pipe.execute()

    def _requeue(self, kw):
        self.redis_db_frame.xack(self._queue_name, self.group, kw['msg_id'])
        self.redis_db_frame.xadd(self._queue_name, {'': json.dumps(kw['body'])})
        # print(self.redis_db_frame.xclaim(self._queue_name,
        #                                     'distributed_frame_group', self.consumer_identification,
        #                                     min_idle_time=0, message_ids=[kw['msg_id']]))

    def _requeue_tasks_which_unconfirmed(self):
        lock_key = f'funboost_lock__requeue_tasks_which_unconfirmed:{self._queue_name}'
        with decorators.RedisDistributedLockContextManager(self.redis_db_frame, lock_key, ) as lock:
            if lock.has_aquire_lock:
                self._distributed_consumer_statistics.send_heartbeat()
                current_queue_hearbeat_ids = self._distributed_consumer_statistics.get_queue_heartbeat_ids(without_time=True)
                xinfo_consumers = self.redis_db_frame.xinfo_consumers(self._queue_name, self.group)
                # print(current_queue_hearbeat_ids)
                # print(xinfo_consumers)
                for xinfo_item in xinfo_consumers:
                    # print(xinfo_item)
                    if xinfo_item['idle'] > 7 * 24 * 3600 * 1000 and xinfo_item['pending'] == 0:
                        self.redis_db_frame.xgroup_delconsumer(self._queue_name, self.group, xinfo_item['name'])
                    if xinfo_item['name'] not in current_queue_hearbeat_ids and xinfo_item['pending'] > 0:  # 说明这个消费者掉线断开或者关闭了。
                        pending_msg_list = self.redis_db_frame.xpending_range(
                            self._queue_name, self.group, '-', '+', 1000, xinfo_item['name'])
                        if pending_msg_list:
                            # min_idle_time 不需要，因为加了分布式锁，所以不需要基于idle最小时间的判断，并且启动了基于心跳的确认消费助手，检测消费者掉线或关闭或断开的准确率100%。
                            xclaim_task_list = self.redis_db_frame.xclaim(self._queue_name, self.group,
                                                                                   self.consumer_identification, force=True,
                                                                                   min_idle_time=0 * 1000,
                                                                                   message_ids=[task_item['message_id'] for task_item in pending_msg_list])
                            if xclaim_task_list:
                                self.logger.warning(f' {self._queue_name}  的分组 {self.group} 的消费者 {self.consumer_identification} 夺取 断开的消费者 {xinfo_item["name"]}'
                                                    f'  {len(xclaim_task_list)} 个任务，详细是 {xclaim_task_list} ')
                                for task in xclaim_task_list:
                                    kw = {'body': task[1][''], 'msg_id': task[0]}
                                    self._submit_task(kw)

```

### 代码文件: funboost\consumers\rocketmq_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/7/8 0008 13:27
import json
import time
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.rocketmq_publisher import RocketmqPublisher
from funboost.core.func_params_model import PublisherParams

class RocketmqConsumer(AbstractConsumer):
    """
    安装
    """

    GROUP_ID = 'g_funboost'

    def _shedual_task(self):
        try:
            from rocketmq.client import PushConsumer
        except BaseException as e:
            # print(traceback.format_exc())
            raise ImportError(f'rocketmq包 只支持linux和mac {e}')
        consumer = PushConsumer(f'{self.GROUP_ID}_{self._queue_name}')
        consumer.set_namesrv_addr(BrokerConnConfig.ROCKETMQ_NAMESRV_ADDR)
        consumer.set_thread_count(1)
        consumer.set_message_batch_max_size(self.consumer_params.concurrent_num)

        self._publisher = RocketmqPublisher(publisher_params=PublisherParams(queue_name=self._queue_name,))

        def callback(rocketmq_msg):
            # self.logger.debug(f'从rocketmq的 [{self._queue_name}] 主题的queue_id {rocketmq_msg.queue_id} 中 取出的消息是：{rocketmq_msg.body}')

            kw = {'body': rocketmq_msg.body, 'rocketmq_msg': rocketmq_msg}
            self._submit_task(kw)

        consumer.subscribe(self._queue_name, callback)
        consumer.start()

        while True:
            time.sleep(3600)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        self._publisher.publish(kw['body'])

```

### 代码文件: funboost\consumers\rq_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/8 0008 13:32

import time
from funboost.assist.rq_helper import RqHelper
from funboost.consumers.base_consumer import AbstractConsumer
from rq.decorators import job


class RqConsumer(AbstractConsumer):
    """
    redis作为中间件实现的。
    """

    def custom_init(self):
        self.rq_job = job(queue=self.queue_name, connection=RqHelper.redis_conn)(self.consuming_function)
        RqHelper.queue_name__rq_job_map[self.queue_name] = self.rq_job

    def start_consuming_message(self):
        RqHelper.to_be_start_work_rq_queue_name_set.add(self.queue_name)
        super().start_consuming_message()

    def _shedual_task(self):
        while 1:
            time.sleep(100)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        pass

```

### 代码文件: funboost\consumers\sqlachemy_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:33
import json
from funboost.constant import BrokerEnum
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.queues import sqla_queue


class SqlachemyConsumer(AbstractConsumer):
    """
    sqlachemy实现的操作5种数据库模拟消息队列，支持消费确认。
    """


    def _shedual_task(self):
        self.queue = sqla_queue.SqlaQueue(self._queue_name, BrokerConnConfig.SQLACHEMY_ENGINE_URL)
        while True:
            sqla_task_dict = self.queue.get()
            # self.logger.debug(f'从数据库 {frame_config.SQLACHEMY_ENGINE_URL[:25]}。。 的 [{self._queue_name}] 队列中 取出的消息是：   消息是：  {sqla_task_dict}')
            self._print_message_get_from_broker(f'从数据库 {BrokerConnConfig.SQLACHEMY_ENGINE_URL[:25]}', sqla_task_dict)
            kw = {'body': sqla_task_dict['body'], 'sqla_task_dict': sqla_task_dict}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        self.queue.set_success(kw['sqla_task_dict'])

    def _requeue(self, kw):
        self.queue.set_task_status(kw['sqla_task_dict'], sqla_queue.TaskStatus.REQUEUE)


```

### 代码文件: funboost\consumers\tcp_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json
from threading import Thread
import socket
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer


class TCPConsumer(AbstractConsumer, ):
    """
    socket 实现消息队列，不支持持久化，但不需要安装软件。
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'host': '127.0.0.1', 'port': None, 'bufsize': 10240}

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        # ip__port_str = self.queue_name.split(':')
        # ip_port = (ip__port_str[0], int(ip__port_str[1]))
        # self._ip_port_raw = ip_port
        # self._ip_port = ('', ip_port[1])
        # ip_port = ('', 9999)
        self._ip_port = (self.consumer_params.broker_exclusive_config['host'],
                         self.consumer_params.broker_exclusive_config['port'])
        self.bufsize = self.consumer_params.broker_exclusive_config['bufsize']

    # noinspection DuplicatedCode
    def _shedual_task(self):
      
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # tcp协议
        server.bind(self._ip_port)
        server.listen(128)
        self._server = server
        while True:
            tcp_cli_sock, addr = self._server.accept()
            Thread(target=self.__handle_conn, args=(tcp_cli_sock,)).start()  # 服务端多线程，可以同时处理多个tcp长链接客户端发来的消息。

    def __handle_conn(self, tcp_cli_sock):
        try:
            while True:
                data = tcp_cli_sock.recv(self.bufsize)
                # print('server收到的数据', data)
                if not data:
                    break
                # self._print_message_get_from_broker(f'udp {self._ip_port_raw}', data.decode())
                tcp_cli_sock.send('has_recived'.encode())
                # tcp_cli_sock.close()
                kw = {'body': data}
                self._submit_task(kw)
            tcp_cli_sock.close()
        except ConnectionResetError:
            pass

    def _confirm_consume(self, kw):
        pass  # 没有确认消费的功能。

    def _requeue(self, kw):
        pass

```

### 代码文件: funboost\consumers\txt_file_consumer.py
```python
﻿from pathlib import Path

from nb_filelock import FileLock
from persistqueue import Queue
import json
from persistqueue.serializers import json as json_serializer
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.funboost_config_deafult import BrokerConnConfig


class TxtFileConsumer(AbstractConsumer, ):
    """
    txt文件作为消息队列
    这个不想做消费确认了,要消费确认请选 SQLITE_QUEUE 、PERSISTQUEUE中间件
    """

    def _shedual_task(self):
        file_queue_path = str((Path(BrokerConnConfig.TXT_FILE_PATH) / self.queue_name).absolute())
        file_lock = FileLock(Path(file_queue_path) / f'_funboost_txtfile_{self.queue_name}.lock')
        queue = Queue(str((Path(BrokerConnConfig.TXT_FILE_PATH) / self.queue_name).absolute()), autosave=True, serializer=json_serializer)
        while True:
            with file_lock:
                item = queue.get()

                kw = {'body': item, 'q': queue, 'item': item}
                self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass
        # kw['q'].task_done()

    def _requeue(self, kw):
        pass
        # kw['q'].nack(kw['item'])

```

### 代码文件: funboost\consumers\udp_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json
import socket
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer


class UDPConsumer(AbstractConsumer, ):
    """
    socket 实现消息队列，不支持持久化，但不需要安装软件。
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'host': '127.0.0.1', 'port': None, 'bufsize': 10240}

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        
        self.__udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # ip__port_str = self.queue_name.split(':')
        # self.__ip_port = (ip__port_str[0], int(ip__port_str[1]))
        self.__ip_port = (self.consumer_params.broker_exclusive_config['host'],
                          self.consumer_params.broker_exclusive_config['port'])
        self._bufsize = self.consumer_params.broker_exclusive_config['bufsize']
        self.__udp_client.connect(self.__ip_port)

    # noinspection DuplicatedCode
    def _shedual_task(self):
        ip_port = ('', self.__ip_port[1])
        # ip_port = ('', 9999)
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # udp协议
        server.bind(ip_port)
        while True:
            data, client_addr = server.recvfrom(self._bufsize)
            # print('server收到的数据', data)
            # self._print_message_get_from_broker(f'udp {ip_port}', data.decode())
            server.sendto('has_recived'.encode(), client_addr)
            kw = {'body': data}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # 没有确认消费的功能。

    def _requeue(self, kw):
        self.__udp_client.send(json.dumps(kw['body']).encode())
        data = self.__udp_client.recv(self._bufsize)

```

### 代码文件: funboost\consumers\zeromq_consumer.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
import os
import socket
import json
# import time
# import zmq
import multiprocessing
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.lazy_impoter import ZmqImporter
# from nb_log import get_logger
from funboost.core.loggers import get_funboost_file_logger


# noinspection PyPep8
def check_port_is_used(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # noinspection PyPep8,PyBroadException
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        # 利用shutdown()函数使socket双向数据传输变为单向数据传输。shutdown()需要一个单独的参数，
        # 该参数表示了如何关闭socket。具体为：0表示禁止将来读；1表示禁止将来写；2表示禁止将来读和写。
        return True
    except BaseException:
        return False


logger_zeromq_broker = get_funboost_file_logger('zeromq_broker')


# noinspection PyUnresolvedReferences
def start_broker(port_router: int, port_dealer: int):
    try:
        context = ZmqImporter().zmq.Context()
        # noinspection PyUnresolvedReferences
        frontend = context.socket(ZmqImporter().zmq.ROUTER)
        backend = context.socket(ZmqImporter().zmq.DEALER)
        frontend.bind(f"tcp://*:{port_router}")
        backend.bind(f"tcp://*:{port_dealer}")

        # Initialize poll set
        poller = ZmqImporter().zmq.Poller()
        poller.register(frontend, ZmqImporter().zmq.POLLIN)
        poller.register(backend, ZmqImporter().zmq.POLLIN)
        logger_zeromq_broker.info(f'broker 绑定端口  {port_router}   {port_dealer}  成功')

        # Switch messages between sockets
        # noinspection DuplicatedCode
        while True:
            socks = dict(poller.poll())  # 轮询器 循环接收

            if socks.get(frontend) == ZmqImporter().zmq.POLLIN:
                message = frontend.recv_multipart()
                backend.send_multipart(message)

            if socks.get(backend) == ZmqImporter().zmq.POLLIN:
                message = backend.recv_multipart()
                frontend.send_multipart(message)
    except BaseException as e:
        logger_zeromq_broker.warning(e)


class ZeroMqConsumer(AbstractConsumer):
    """
    zeromq 中间件的消费者，zeromq基于socket代码，不会持久化，且不需要安装软件。
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'port': None}

    def custom_init(self):
        self._port = self.consumer_params.broker_exclusive_config['port']
        if self._port is None:
            raise ValueError('please specify port')

    def _start_broker_port(self):
        # threading.Thread(target=self._start_broker).start()
        # noinspection PyBroadException
        try:
            if not (10000 < int(self._port) < 65535):
                raise ValueError("请设置port是一个 10000到65535的之间的一个端口数字")
        except BaseException:
            self.logger.critical(f" 请设置port是一个 10000到65535的之间的一个端口数字")
            # noinspection PyProtectedMember
            os._exit(444)
        if check_port_is_used('127.0.0.1', int(self._port)):
            self.logger.debug(f"""{int(self._port)} router端口已经启动(或占用) """)
            return
        if check_port_is_used('127.0.0.1', int(self._port) + 1):
            self.logger.debug(f"""{int(self._port) + 1} dealer 端口已经启动(或占用) """)
            return
        multiprocessing.Process(target=start_broker, args=(int(self._port), int(self._port) + 1)).start()

    # noinspection DuplicatedCode
    def _shedual_task(self):
        self._start_broker_port()
        context = ZmqImporter().zmq.Context()
        # noinspection PyUnresolvedReferences
        zsocket = context.socket(ZmqImporter().zmq.REP)
        zsocket.connect(f"tcp://localhost:{int(self._port) + 1}")

        while True:
            message = zsocket.recv()
            # self.logger.debug(f""" 从 zeromq 取出的消息是 {message}""")
            self._submit_task({'body': message})
            zsocket.send('recv ok'.encode())

    def _confirm_consume(self, kw):
        pass  #

    def _requeue(self, kw):
        self.publisher_of_same_queue.publish(kw['body'])

```

### 代码文件: funboost\consumers\__init__.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:09
"""
实现基于各种中间件的消费者
"""
```

### 代码文件: funboost\contrib\api_publish_msg.py
```python
import traceback
import typing

from funboost import AioAsyncResult, AsyncResult,PriorityConsumingControlConfig

from funboost.core.cli.discovery_boosters import BoosterDiscovery
from funboost import BoostersManager
from fastapi import FastAPI
from pydantic import BaseModel


class MsgItem(BaseModel):
    queue_name: str  # 队列名
    msg_body: dict  # 消息体,就是boost函数的入参字典,例如 {"x":1,"y":2}
    need_result: bool = False  # 发布消息后,是否需要返回结果
    timeout: int = 60  # 等待结果返回的最大等待时间.


class PublishResponse(BaseModel):
    succ: bool
    msg: str
    status_and_result: typing.Optional[dict] = None  # 消费函数的消费状态和结果.


# 创建 FastAPI 应用实例
app = FastAPI()

'''
如果你在发布消息后还需要获取函数执行结果,
那么推荐使用asyncio类型的web框架例如 fastapi tornado,而不是使用flask django,更好的应付由于获取结果而需要的阻塞时间.不使用asyncio的话web框架需要设置开启很高的线程才行.
'''


@app.post("/funboost_publish_msg")
async def publish_msg(msg_item: MsgItem):
    status_and_result = None
    try:
        booster = BoostersManager.get_or_create_booster_by_queue_name(msg_item.queue_name)
        if msg_item.need_result:
            if booster.boost_params.is_using_rpc_mode is False:
                raise ValueError(f' need_result 为true,{booster.queue_name} 队列消费者 需要@boost设置支持rpc模式')
            async_result = await booster.aio_publish(msg_item.msg_body,priority_control_config=PriorityConsumingControlConfig(is_using_rpc_mode=True))
            status_and_result = await AioAsyncResult(async_result.task_id, timeout=msg_item.timeout).status_and_result
            print(status_and_result)
            # status_and_result = AsyncResult(async_result.task_id, timeout=msg_item.timeout).status_and_result
        else:
            await booster.aio_publish(msg_item.msg_body)
        return PublishResponse(succ=True, msg=f'{msg_item.queue_name} 队列,消息发布成功', status_and_result=status_and_result)
    except Exception as e:
        return PublishResponse(succ=False, msg=f'{msg_item.queue_name} 队列,消息发布失败 {type(e)} {e} {traceback.format_exc()}',
                               status_and_result=status_and_result)


# 运行应用
if __name__ == "__main__":
    import uvicorn

    uvicorn.run('funboost.contrib.api_publish_msg:app', host="0.0.0.0", port=16666, workers=4)

    '''
    test_frame/test_api_publish_msg 中有使用例子.
    '''

```

### 代码文件: funboost\contrib\django_db_deco.py
```python
from django.db import close_old_connections


def close_old_connections_deco(f):
    """
    如果是消费函数里面需要操作django orm,那么请写上 consumin_function_decorator=close_old_connections_deco
    @boost(BoosterParams(queue_name='create_student_queue',
                         broker_kind=BrokerEnum.REDIS_ACK_ABLE,
                         consumin_function_decorator=close_old_connections_deco, # 如果gone away 一直好不了,可以加这个装饰器. django_celery django-apschrduler 这些源码中 也是调用了 close_old_connections_deco方法.

                         )
           )
    """

    def _inner(*args, **kwargs):
        close_old_connections()
        try:
            result = f(*args, **kwargs)
        finally:
            close_old_connections()

        return result

    return _inner

```

### 代码文件: funboost\contrib\funboost框架的额外贡献功能.md
```python

## 这里是框架额外贡献的功能.
```

### 代码文件: funboost\contrib\queue2queue.py
```python
import os
import time
import typing
from multiprocessing import Process
import logging
import threading

from funboost import get_publisher, get_consumer, BrokerEnum, wait_for_possible_has_finish_all_tasks_by_conusmer_list
from funboost.core.func_params_model import PublisherParams, BoosterParams

""" 将队列中的消息移到另一个队列名中，例如把死信队列的消息移到正常队列。"""


def consume_and_push_to_another_queue(source_queue_name: str, source_broker_kind: str,
                                      target_queue_name: str, target_broker_kind: str,
                                      log_level: int = logging.DEBUG,
                                      exit_script_when_finish=False):
    """ 将队列中的消息移到另一个队列名中，例如把死信队列的消息移到正常队列。"""
    if source_queue_name == target_queue_name and source_broker_kind == target_broker_kind:
        raise ValueError('不能转移消息到当前队列名，否则死循环')

    target_publisher = get_publisher(publisher_params=PublisherParams(queue_name=target_queue_name, broker_kind=target_broker_kind, log_level=log_level))
    msg_cnt = 0
    msg_cnt_lock = threading.Lock()

    def _task_fun(**kwargs):
        # print(kwargs)
        nonlocal msg_cnt
        target_publisher.publish(kwargs)
        with msg_cnt_lock:
            msg_cnt += 1

    source_consumer = get_consumer(boost_params=BoosterParams(queue_name=source_queue_name, broker_kind=source_broker_kind, consuming_function=_task_fun, log_level=log_level))
    source_consumer._set_do_not_delete_extra_from_msg()
    source_consumer.start_consuming_message()
    if exit_script_when_finish:
        source_consumer.wait_for_possible_has_finish_all_tasks(2)
        print(f'消息转移完成，结束脚本,累计从 {source_queue_name} 转移消息到 {target_queue_name} 队列 总数是 {msg_cnt}')
        os._exit(888)  # 结束脚本


def _consume_and_push_to_another_queue_for_multi_process(source_queue_name: str, source_broker_kind: str,
                                                         target_queue_name: str, target_broker_kind: str,
                                                         log_level: int = logging.DEBUG,
                                                         ):
    consume_and_push_to_another_queue(source_queue_name, source_broker_kind, target_queue_name, target_broker_kind, log_level, False)
    while 1:
        time.sleep(3600)


def multi_prcocess_queue2queue(source_target_list: typing.List[typing.List],
                               log_level: int = logging.DEBUG, exit_script_when_finish=False, n=1):
    """
    转移多个队列，并使用多进程。
    :param source_target_list:  入参例如  [['test_queue77h5', BrokerEnum.RABBITMQ_AMQPSTORM, 'test_queue77h4', BrokerEnum.RABBITMQ_AMQPSTORM],['test_queue77h6', BrokerEnum.RABBITMQ_AMQPSTORM, 'test_queue77h7', BrokerEnum.REDIS]]
    :param log_level:
    :param exit_script_when_finish:
    :param n:
    :return:
    """
    source_consumer_list = []
    for (source_queue_name, source_broker_kind, target_queue_name, target_broker_kind) in source_target_list:
        for i in range(n):
            Process(target=_consume_and_push_to_another_queue_for_multi_process,
                    args=(source_queue_name, source_broker_kind, target_queue_name, target_broker_kind, log_level)).start()
        if exit_script_when_finish:
            def _fun():
                pass

            source_consumer = get_consumer(boost_params=BoosterParams(queue_name=source_queue_name, broker_kind=source_broker_kind, consuming_function=_fun,
                                                                      log_level=log_level))
            source_consumer_list.append(source_consumer)
    if exit_script_when_finish:
        wait_for_possible_has_finish_all_tasks_by_conusmer_list(consumer_list=source_consumer_list, minutes=2)
        for (source_queue_name, source_broker_kind, target_queue_name, target_broker_kind) in source_target_list:
            print(f'{source_queue_name}  转移到 {target_queue_name} 消息转移完成，结束脚本')
        os._exit(999)  #


if __name__ == '__main__':
    # 一次转移一个队列，使用单进程
    consume_and_push_to_another_queue('test_queue77h3_dlx', BrokerEnum.REDIS_PRIORITY,
                                      'test_queue77h3', BrokerEnum.REDIS_PRIORITY,
                                      log_level=logging.INFO, exit_script_when_finish=True)

    # 转移多个队列，并使用多进程。
    multi_prcocess_queue2queue([['test_queue77h5', BrokerEnum.RABBITMQ_AMQPSTORM, 'test_queue77h4', BrokerEnum.RABBITMQ_AMQPSTORM]],
                               log_level=logging.INFO, exit_script_when_finish=True, n=6)

```

### 代码文件: funboost\contrib\redis_consume_latest_msg_broker.py
```python
from funboost import register_custom_broker
from funboost import boost, FunctionResultStatus, BoosterParams
from funboost.consumers.redis_consumer_simple import RedisConsumer
from funboost.publishers.redis_publisher_simple import RedisPublisher

"""
此文件是演示添加自定义类型的中间件,演示怎么使用redis 实现先进后出 后进先出的队列，就是消费总是拉取最晚发布的消息，而不是优先消费最早发布的消息
lpush + lpop 或者 rpush + rpop 就会消费最新发布的消息，如果是 lpush + rpop 或者 rpush + lpop 则会先消费最早发布的消息(框架内置的目前就是消费最早发布的消息)。

此种方式也可以在子类中重写来更改 AbstractConsumer 基类的逻辑,例如你想在任务执行完成后把结果插入到mysql或者做更精细化的定制流程，可以不使用原来推荐的装饰器叠加方式
而是在类中直接重写方法

"""


class RedisConsumeLatestPublisher(RedisPublisher):
    def concrete_realization_of_publish(self, msg):
        self.redis_db_frame.lpush(self._queue_name, msg)


class RedisConsumeLatestConsumer(RedisConsumer):
    pass


BROKER_KIND_REDIS_CONSUME_LATEST = 'BROKER_KIND_REDIS_CONSUME_LATEST'
register_custom_broker(BROKER_KIND_REDIS_CONSUME_LATEST, RedisConsumeLatestPublisher, RedisConsumeLatestConsumer)  # 核心，这就是将自己写的类注册到框架中，框架可以自动使用用户的类，这样用户无需修改框架的源代码了。

if __name__ == '__main__':
    @boost(boost_params=BoosterParams(queue_name='test_list_queue2', broker_kind=BROKER_KIND_REDIS_CONSUME_LATEST, qps=10, ))
    def f(x):
        print(x * 10)


    f.clear()
    for i in range(50):
        f.push(i)
    print(f.publisher.get_message_count())
    f.consume()  # 从可以看到事从最后发布的消息开始消费。

```

### 代码文件: funboost\contrib\save_result_status_to_sqldb.py
```python
import copy
import functools
import json

from db_libs.sqla_lib import SqlaReflectHelper
from sqlalchemy import create_engine

from funboost import boost, FunctionResultStatus, funboost_config_deafult

"""
-- 如果用户是先保存到mysql中而非mongodb,用户自己先创建表,用于保存函数消费状态和结果.

CREATE TABLE funboost_consume_results
(
    _id              VARCHAR(255),
    `function`         VARCHAR(255),
    host_name        VARCHAR(255),
    host_process     VARCHAR(255),
    insert_minutes   VARCHAR(255),
    insert_time      datetime,
    insert_time_str  VARCHAR(255),
    msg_dict         JSON,
    params           JSON,
    params_str       VARCHAR(255),
    process_id       BIGINT(20),
    publish_time     FLOAT,
    publish_time_str VARCHAR(255),
    queue_name       VARCHAR(255),
    result           VARCHAR(255),
    run_times        INT,
    script_name      VARCHAR(255),
    script_name_long VARCHAR(255),
    success          BOOLEAN,
    task_id          VARCHAR(255),
    thread_id        BIGINT(20),
    time_cost        FLOAT,
    time_end         FLOAT,
    time_start       FLOAT,
    total_thread     INT,
    utime            VARCHAR(255),
    `exception`       MEDIUMTEXT ,
    rpc_result_expire_seconds BIGINT(20),
    primary key (_id),
    key idx_insert_time(insert_time),
    key idx_queue_name_insert_time(queue_name,insert_time),
    key idx_params_str(params_str)
)



"""


def _gen_insert_sql_and_values_by_dict(dictx: dict):
    key_list = [f'`{k}`' for k in dictx.keys()]
    fields = ", ".join(key_list)

    # 构建占位符字符串
    placeholders = ", ".join(['%s'] * len(dictx))

    # 构建插入语句
    insert_sql = f"INSERT INTO funboost_consume_results ({fields}) VALUES ({placeholders})"

    # 获取数据字典的值作为插入的值
    values = tuple(dictx.values())
    values_new = tuple([json.dumps(v) if isinstance(v, dict) else v for v in values])
    return insert_sql, values_new


def _gen_insert_sqlalchemy(dictx: dict):
    key_list = [f'`{k}`' for k in dictx.keys()]
    fields = ", ".join(key_list)

    value_list = dictx.keys()
    value_list_2 = [f':{f}' for f in value_list]
    values = ", ".join(value_list_2)

    # 构建插入语句
    insert_sql = f"INSERT INTO funboost_consume_results ({fields}) VALUES ({values})"

    return insert_sql


@functools.lru_cache()
def get_sqla_helper():
    enginex = create_engine(
        funboost_config_deafult.BrokerConnConfig.SQLACHEMY_ENGINE_URL,
        max_overflow=10,  # 超过连接池大小外最多创建的连接
        pool_size=50,  # 连接池大小
        pool_timeout=30,  # 池中没有线程最多等待的时间，否则报错
        pool_recycle=3600,  # 多久之后对线程池中的线程进行一次连接的回收（重置）
        echo=True)
    sqla_helper = SqlaReflectHelper(enginex)
    t_funboost_consume_results = sqla_helper.base_classes.funboost_consume_results
    return enginex, sqla_helper, t_funboost_consume_results


def save_result_status_to_sqlalchemy(function_result_status: FunctionResultStatus):
    """ function_result_status变量上有各种丰富的信息 ,用户可以使用其中的信息
    用户自定义记录函数消费信息的钩子函数

    例如  @boost('test_user_custom', user_custom_record_process_info_func=save_result_status_to_sqlalchemy)
    """
    enginex, sqla_helper, t_funboost_consume_results = get_sqla_helper()

    with sqla_helper.session as ss:
        status_dict = function_result_status.get_status_dict()
        status_dict_new = copy.copy(status_dict)
        for k, v in status_dict.items():
            if isinstance(v, dict):
                status_dict_new[k] = json.dumps(v)
        # sql = _gen_insert_sqlalchemy(status_dict) # 这种是sqlahemy sql方式插入.
        # ss.execute(sql, status_dict_new)
        ss.merge(t_funboost_consume_results(**status_dict_new)) # 这种是orm方式插入.

```

### 代码文件: funboost\contrib\__init__.py
```python

```

### 代码文件: funboost\core\active_cousumer_info_getter.py
```python
import json
import threading
import time
import typing
import uuid

from pydantic import main

from funboost.utils.redis_manager import RedisMixin

from funboost.core.loggers import FunboostFileLoggerMixin,nb_log_config_default
from funboost.core.serialization import Serialization
from funboost.constant import RedisKeys

class ActiveCousumerProcessInfoGetter(RedisMixin, FunboostFileLoggerMixin):
    """

    获取分布式环境中的消费进程信息。
    使用这里面的4个方法需要相应函数的@boost装饰器设置 is_send_consumer_hearbeat_to_redis=True，这样会自动发送活跃心跳到redis。否则查询不到该函数的消费者进程信息。
    要想使用消费者进程信息统计功能，用户无论使用何种消息队列中间件类型，用户都必须安装redis，并在 funboost_config.py 中配置好redis链接信息
    """

    def _get_all_hearbeat_info_by_redis_key_name(self, redis_key):
        results = self.redis_db_frame.smembers(redis_key)
        # print(type(results))
        # print(results)
        # 如果所有机器所有进程都全部关掉了，就没办法还剩一个线程执行删除了，这里还需要判断一次15秒。
        active_consumers_processor_info_list = []
        for result in results:
            result_dict = json.loads(result)
            if self.timestamp() - result_dict['hearbeat_timestamp'] < 15:
                active_consumers_processor_info_list.append(result_dict)
                if self.timestamp() - result_dict['current_time_for_execute_task_times_every_unit_time'] > 30:
                    result_dict['last_x_s_execute_count'] = 0
                    result_dict['last_x_s_execute_count_fail'] = 0
        return active_consumers_processor_info_list

    def get_all_hearbeat_info_by_queue_name(self, queue_name) -> typing.List[typing.Dict]:
        """
        根据队列名查询有哪些活跃的消费者进程
        返回结果例子：
        [{
                "code_filename": "/codes/funboost/test_frame/my/test_consume.py",
                "computer_ip": "172.16.0.9",
                "computer_name": "VM_0_9_centos",
                "consumer_id": 140477437684048,
                "consumer_uuid": "79473629-b417-4115-b516-4365b3cdf383",
                "consuming_function": "f2",
                "hearbeat_datetime_str": "2021-12-27 19:22:04",
                "hearbeat_timestamp": 1640604124.4643965,
                "process_id": 9665,
                "queue_name": "test_queue72c",
                "start_datetime_str": "2021-12-27 19:21:24",
                "start_timestamp": 1640604084.0780013
            }, ...............]
        """
        redis_key = RedisKeys.gen_funboost_hearbeat_queue__dict_key_by_queue_name(queue_name)
        return self._get_all_hearbeat_info_by_redis_key_name(redis_key)

    def get_all_hearbeat_info_by_ip(self, ip=None) -> typing.List[typing.Dict]:
        """
        根据机器的ip查询有哪些活跃的消费者进程，ip不传参就查本机ip使用funboost框架运行了哪些消费进程，传参则查询任意机器的消费者进程信息。
        返回结果的格式和上面的 get_all_hearbeat_dict_by_queue_name 方法相同。
        """
        ip = ip or nb_log_config_default.computer_ip
        redis_key = RedisKeys.gen_funboost_hearbeat_server__dict_key_by_ip(ip)
        return self._get_all_hearbeat_info_by_redis_key_name(redis_key)

    # def _get_all_hearbeat_info_partition_by_redis_key_prefix(self, redis_key_prefix):
    #     keys = self.redis_db_frame.scan(0, f'{redis_key_prefix}*', count=10000)[1]
    #     infos_map = {}
    #     for key in keys:
    #         infos = self.redis_db_frame.smembers(key)
    #         dict_key = key.replace(redis_key_prefix, '')
    #         infos_map[dict_key] = []
    #         for info_str in infos:
    #             info_dict = json.loads(info_str)
    #             if self.timestamp() - info_dict['hearbeat_timestamp'] < 15:
    #                 infos_map[dict_key].append(info_dict)
    #                 if self.timestamp() - info_dict['current_time_for_execute_task_times_every_unit_time'] > 30:
    #                     info_dict['last_x_s_execute_count'] = 0
    #                     info_dict['last_x_s_execute_count_fail'] = 0
    #     return infos_map

    def get_all_queue_names(self):
        return self.redis_db_frame.smembers(RedisKeys.FUNBOOST_ALL_QUEUE_NAMES)
    
    def get_all_ips(self):
        return self.redis_db_frame.smembers(RedisKeys.FUNBOOST_ALL_IPS)
    
    def _get_all_hearbeat_info_partition_by_redis_keys(self, keys):
        
        # keys = [f'{redis_key_prefix}{queue_name}' for queue_name in queue_names]
        infos_map = {}
        for key in keys:
            infos = self.redis_db_frame.smembers(key)
            dict_key = key.replace(RedisKeys.FUNBOOST_HEARTBEAT_QUEUE__DICT_PREFIX, '').replace(RedisKeys.FUNBOOST_HEARTBEAT_SERVER__DICT_PREFIX, '')
            infos_map[dict_key] = []
            for info_str in infos:
                info_dict = json.loads(info_str)
                if self.timestamp() - info_dict['hearbeat_timestamp'] < 15:
                    infos_map[dict_key].append(info_dict)
                    if self.timestamp() - info_dict['current_time_for_execute_task_times_every_unit_time'] > 30:
                        info_dict['last_x_s_execute_count'] = 0
                        info_dict['last_x_s_execute_count_fail'] = 0
        return infos_map

    def get_all_hearbeat_info_partition_by_queue_name(self) -> typing.Dict[typing.AnyStr, typing.List[typing.Dict]]:
        """获取所有队列对应的活跃消费者进程信息，按队列名划分,不需要传入队列名，自动扫描redis键。请不要在 funboost_config.py 的redis 指定的db中放太多其他业务的缓存键值对"""
        queue_names = self.get_all_queue_names()
        infos_map = self._get_all_hearbeat_info_partition_by_redis_keys([RedisKeys.gen_funboost_hearbeat_queue__dict_key_by_queue_name(queue_name) for queue_name in queue_names])
        # self.logger.info(f'获取所有队列对应的活跃消费者进程信息，按队列名划分，结果是 {json.dumps(infos_map, indent=4)}')
        return infos_map

    def get_all_hearbeat_info_partition_by_ip(self) -> typing.Dict[typing.AnyStr, typing.List[typing.Dict]]:
        """获取所有机器ip对应的活跃消费者进程信息，按机器ip划分,不需要传入机器ip，自动扫描redis键。请不要在 funboost_config.py 的redis 指定的db中放太多其他业务的缓存键值对 """
        ips = self.get_all_ips()
        infos_map = self._get_all_hearbeat_info_partition_by_redis_keys([RedisKeys.gen_funboost_hearbeat_server__dict_key_by_ip(ip) for ip in ips])
        self.logger.info(f'获取所有机器ip对应的活跃消费者进程信息，按机器ip划分，结果是 {json.dumps(infos_map, indent=4)}')
        return infos_map



class QueueConusmerParamsGetter(RedisMixin, FunboostFileLoggerMixin):

    def get_queue_params(self):
        queue__consumer_params_map  = self.redis_db_frame.hgetall('funboost_queue__consumer_parmas')
        return {k:Serialization.to_dict(v)  for k,v in queue__consumer_params_map.items()}

    def get_pause_flag(self):
        queue__pause_map = self.redis_db_frame.hgetall(RedisKeys.REDIS_KEY_PAUSE_FLAG)
        return {k:int(v)  for k,v in queue__pause_map.items()}

    def get_msg_num(self,ignore_report_ts=False):
        queue__msg_count_info_map = self.redis_db_frame.hgetall(RedisKeys.QUEUE__MSG_COUNT_MAP)
        queue__msg_count_dict = {}
        for queue_name,info_json in queue__msg_count_info_map.items():
            info_dict = json.loads(info_json)
            if ignore_report_ts or (info_dict['report_ts'] > time.time() - 15 and info_dict['last_get_msg_num_ts'] > time.time() - 1200):
                queue__msg_count_dict[queue_name] = info_dict['msg_num_in_broker']
        return queue__msg_count_dict

    @staticmethod
    def _sum_filed_from_active_consumers(active_consumers:typing.List[dict],filed:str):
        s = 0
        for c in active_consumers:
            # print(c)
            if c[filed]:
                # print(c[filed])
                s+=c[filed]
        return s
    
    def get_queues_history_run_count(self,):
        return self.redis_db_frame.hgetall(RedisKeys.FUNBOOST_QUEUE__RUN_COUNT_MAP)
    
    def get_queues_history_run_fail_count(self,):
        return self.redis_db_frame.hgetall(RedisKeys.FUNBOOST_QUEUE__RUN_FAIL_COUNT_MAP)
    
    def get_queue_params_and_active_consumers(self):
        queue__active_consumers_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name()

        # queue_name_list = list(queue__active_consumers_map.keys())
        queue__history_run_count_map = self.get_queues_history_run_count()
        queue__history_run_fail_count_map = self.get_queues_history_run_fail_count()

        queue__consumer_params_map  = self.get_queue_params()
        queue__pause_map = self.get_pause_flag()
        queue__msg_count_dict = self.get_msg_num(ignore_report_ts=True)
        queue_params_and_active_consumers = {}

        for queue, consumer_params in  queue__consumer_params_map.items():
            
            active_consumers = queue__active_consumers_map.get(queue, [])
            # print(queue,active_consumers)
            all_consumers_last_x_s_execute_count = self._sum_filed_from_active_consumers(active_consumers,'last_x_s_execute_count')
            all_consumers_last_x_s_execute_count_fail = self._sum_filed_from_active_consumers(active_consumers, 'last_x_s_execute_count_fail')
            all_consumers_last_x_s_total_cost_time = self._sum_filed_from_active_consumers(active_consumers, 'last_x_s_total_cost_time')
            all_consumers_last_x_s_avarage_function_spend_time = round( all_consumers_last_x_s_total_cost_time / all_consumers_last_x_s_execute_count,3) if all_consumers_last_x_s_execute_count else None
            
            all_consumers_total_consume_count_from_start = self._sum_filed_from_active_consumers(active_consumers, 'total_consume_count_from_start')
            all_consumers_total_cost_time_from_start =self._sum_filed_from_active_consumers(active_consumers, 'total_cost_time_from_start')
            all_consumers_avarage_function_spend_time_from_start = round(all_consumers_total_cost_time_from_start / all_consumers_total_consume_count_from_start,3) if all_consumers_total_consume_count_from_start else None

            queue_params_and_active_consumers[queue] = {
                'queue_params':consumer_params,
                'active_consumers':active_consumers,
                'pause_flag':queue__pause_map.get(queue,-1),
                'msg_num_in_broker':queue__msg_count_dict.get(queue,None),
                
                'history_run_count':queue__history_run_count_map.get(queue,None),
                'history_run_fail_count':queue__history_run_fail_count_map.get(queue,None),

                'all_consumers_last_x_s_execute_count':all_consumers_last_x_s_execute_count,
                'all_consumers_last_x_s_execute_count_fail':all_consumers_last_x_s_execute_count_fail,
                'all_consumers_last_x_s_avarage_function_spend_time':all_consumers_last_x_s_avarage_function_spend_time,
                'all_consumers_avarage_function_spend_time_from_start':all_consumers_avarage_function_spend_time_from_start,
                'all_consumers_total_consume_count_from_start':self._sum_filed_from_active_consumers(active_consumers, 'total_consume_count_from_start'),
                'all_consumers_total_consume_count_from_start_fail':self._sum_filed_from_active_consumers(active_consumers, 'total_consume_count_from_start_fail'),
            }
        return queue_params_and_active_consumers
    
    def cycle_get_queue_params_and_active_consumers_and_report(self,daemon=False):
        time_interval = 10
        report_uuid = str(uuid.uuid4()) 
        def _inner():
            while True:
                t_start = time.time()
                # 这个函数确保只有一个地方在上报数据，避免重复上报
                report_ts = self.timestamp()
                redis_report_uuid_ts_str = self.redis_db_frame.get(RedisKeys.FUNBOOST_LAST_GET_QUEUE_PARAMS_AND_ACTIVE_CONSUMERS_AND_REPORT__UUID_TS, )
                if redis_report_uuid_ts_str:
                    redis_report_uuid_ts = Serialization.to_dict(redis_report_uuid_ts_str)
                    if redis_report_uuid_ts['report_uuid'] != report_uuid and redis_report_uuid_ts['report_ts'] > report_ts - time_interval - 10 :
                        continue
                self.redis_db_frame.set(RedisKeys.FUNBOOST_LAST_GET_QUEUE_PARAMS_AND_ACTIVE_CONSUMERS_AND_REPORT__UUID_TS,
                                        Serialization.to_json_str({'report_uuid':report_uuid, 'report_ts':report_ts}))
                
                queue_params_and_active_consumers = self.get_queue_params_and_active_consumers()
                for queue,item in queue_params_and_active_consumers.items():
                    if len(item['active_consumers']) == 0:
                        continue
                    report_data = {k:v for k,v in item.items() if k not in ['queue_params','active_consumers']}
                    
                    report_data['report_ts'] = report_ts
                    self.redis_db_frame.zadd(RedisKeys.gen_funboost_queue_time_series_data_key_by_queue_name(queue),
                                            {Serialization.to_json_str(report_data):report_ts} )
                    # 删除过期时序数据,只保留最近1天数据
                    self.redis_db_frame.zremrangebyscore(
                        RedisKeys.gen_funboost_queue_time_series_data_key_by_queue_name(queue),
                        0, report_ts - 86400
                    )
                self.logger.info(f'上报时序数据耗时 {time.time() - t_start} 秒')

                time.sleep(time_interval)
        threading.Thread(target=_inner, daemon=daemon).start()

    def get_time_series_data_by_queue_name(self,queue_name,start_ts=None,end_ts=None):
        res = self.redis_db_frame.zrangebyscore(
            RedisKeys.gen_funboost_queue_time_series_data_key_by_queue_name(queue_name),
            max(float(start_ts or 0),self.timestamp() - 86400) ,float(end_ts or -1),withscores=True)
        # print(res)
        return [{'report_data':Serialization.to_dict(item[0]),'report_ts':item[1]} for item in res]

if __name__ == '__main__':
    # print(Serialization.to_json_str(QueueConusmerParamsGetter().get_queue_params_and_active_consumers()))
    # QueueConusmerParamsGetter().cycle_get_queue_params_and_active_consumers_and_report()
    print(QueueConusmerParamsGetter().get_time_series_data_by_queue_name('queue_test_g03t',1749617883,1749621483))
    # print(QueueConusmerParamsGetter().get_time_series_data_by_queue_name('queue_test_g03t',))
    
```

### 代码文件: funboost\core\booster.py
```python
from __future__ import annotations
import copy
import inspect
import os
import sys
import types
import typing

from funboost.concurrent_pool import FlexibleThreadPool
from funboost.concurrent_pool.async_helper import simple_run_in_executor
from funboost.constant import FunctionKind
from funboost.utils.class_utils import ClsHelper

from funboost.utils.ctrl_c_end import ctrl_c_recv
from funboost.core.loggers import flogger, develop_logger, logger_prompt

from functools import wraps

from funboost.core.exceptions import BoostDecoParamsIsOldVersion
from funboost.core.func_params_model import BoosterParams, FunctionResultStatusPersistanceConfig, PriorityConsumingControlConfig, PublisherParams

from funboost.factories.consumer_factory import get_consumer
from funboost.factories.publisher_factotry import get_publisher
from funboost.publishers.base_publisher import AbstractPublisher
from collections import defaultdict

from funboost.core.msg_result_getter import AsyncResult, AioAsyncResult


class Booster:
    """
    funboost极其重视代码能在pycharm下自动补全。元编程经常造成在pycharm下代码无法自动补全提示，主要是实现代码补全难。
    这种__call__写法在pycahrm下 不仅能补全消费函数的 push consume等方法，也能补全函数本身的入参，一举两得。代码能自动补全很重要。
    一个函数fun被 boost装饰器装饰后， isinstance(fun,Booster) 为True.

    pydatinc pycharm编程代码补全,请安装 pydantic插件, 在pycharm的  file -> settings -> Plugins -> 输入 pydantic 搜索,点击安装 pydantic 插件.

    Booster 是把Consumer 和 Publisher的方法集为一体。
    """

    def __init__(self, queue_name: typing.Union[BoosterParams, str] = None, *, boost_params: BoosterParams = None, **kwargs):
        """
        @boost 这是funboost框架最重要的一个函数，必须看懂BoosterParams里面的入参有哪些。
        pydatinc pycharm编程代码补全,请安装 pydantic插件, 在pycharm的  file -> settings -> Plugins -> 输入 pydantic 搜索,点击安装 pydantic 插件.
        (高版本的pycharm pydantic是内置支持代码补全的,由此可见,pydantic太好了,pycharm官方都来支持)

        强烈建议所有入参放在 BoosterParams() 中,不要直接在BoosterParams之外传参.现在是兼容老的直接在@boost中传参方式.
        """

        """
        '''
        # @boost('queue_test_f01', qps=0.2, ) # 老的入参方式
        @boost(BoosterParams(queue_name='queue_test_f01', qps=0.2, )) # 新的入参方式,所有入参放在 最流行的三方包 pydantic model BoosterParams 里面.
        def f(a, b):
            print(a + b)

        for i in range(10, 20):
            f.pub(dict(a=i, b=i * 2))
            f.push(i, i * 2)
        f.consume()
        # f.multi_process_conusme(8)             # # 这个是新加的方法，细粒度 线程 协程并发 同时叠加8个进程，速度炸裂。
        '''
        
        
        @boost('queue_test_f01', qps=0.2, ) 
        @boost(BoosterParams(queue_name='queue_test_f01', qps=0.2, ))
        @Booster(BoosterParams(queue_name='queue_test_f01', qps=0.2, ))
        @BoosterParams(queue_name='queue_test_f01', qps=0.2, )
        以上4种写法等效。 
        @boost(BoosterParams(queue_name='queue_test_f01', qps=0.2, )) 的写法升级到 pycharm 2024.2 版本后，导致被装饰的函数不能自动补全提示了，pycharm升级后自动补全功能反而抽风bug了。
        """

        # 以下代码很复杂，主要是兼容老的在@boost直接传参的方式,强烈建议使用新的入参方式,所有入参放在一个 BoosterParams 中，那就不需要理会下面这段逻辑.
        if isinstance(queue_name, str):
            if boost_params is None:
                boost_params = BoosterParams(queue_name=queue_name)
        elif queue_name is None and boost_params is None:
            raise ValueError('boost 入参错误')
        elif isinstance(queue_name, BoosterParams):
            boost_params = queue_name
        if isinstance(queue_name, str) or kwargs:
            flogger.warning(f'''你的 {queue_name} 队列， funboost 40.0版本以后： {BoostDecoParamsIsOldVersion.new_version_change_hint}''')
        boost_params_merge = boost_params.copy()
        boost_params_merge.update_from_dict(kwargs)
        self.boost_params: BoosterParams = boost_params_merge
        self.queue_name = boost_params_merge.queue_name

    def __str__(self):
        return f'{type(self)}  队列为 {self.queue_name} 函数为 {self.consuming_function} 的 booster'

    def __get__(self, instance, cls):
        """https://python3-cookbook.readthedocs.io/zh_CN/latest/c09/p09_define_decorators_as_classes.html"""
        if instance is None:
            return self
        else:
            return types.MethodType(self, instance)

    def __call__(self, *args, **kwargs) -> Booster:
        if len(kwargs) == 0 and len(args) == 1 and isinstance(args[0], typing.Callable):
            consuming_function = args[0]
            self.boost_params.consuming_function = consuming_function
            self.boost_params.consuming_function_raw = consuming_function
            self.boost_params.consuming_function_name = consuming_function.__name__
            # print(consuming_function)
            # print(ClsHelper.get_method_kind(consuming_function))
            # print(inspect.getsourcelines(consuming_function))
            if self.boost_params.consuming_function_kind is None:
                self.boost_params.consuming_function_kind = ClsHelper.get_method_kind(consuming_function)
            # if self.boost_params.consuming_function_kind in [FunctionKind.CLASS_METHOD,FunctionKind.INSTANCE_METHOD]:
            #     if self.boost_params.consuming_function_class_module is None:
            #         self.boost_params.consuming_function_class_module = consuming_function.__module__
            #     if self.boost_params.consuming_function_class_name is None:
            #         self.boost_params.consuming_function_class_name = consuming_function.__qualname__.split('.')[0]
            logger_prompt.debug(f''' {self.boost_params.queue_name} booster 配置是 {self.boost_params.json_str_value()}''')
            self.consuming_function = consuming_function
            self.is_decorated_as_consume_function = True

            consumer = get_consumer(self.boost_params)
            self.consumer = consumer

            self.publisher = consumer.publisher_of_same_queue
            # self.publish = self.pub = self.apply_async = consumer.publisher_of_same_queue.publish
            # self.push = self.delay = consumer.publisher_of_same_queue.push
            self.publish = self.pub = self.apply_async = self._safe_publish
            self.push = self.delay = self._safe_push

            self.clear = self.clear_queue = consumer.publisher_of_same_queue.clear
            self.get_message_count = consumer.publisher_of_same_queue.get_message_count

            self.start_consuming_message = self.consume = self.start = consumer.start_consuming_message
            self.clear_filter_tasks = consumer.clear_filter_tasks
            self.wait_for_possible_has_finish_all_tasks = consumer.wait_for_possible_has_finish_all_tasks

            self.pause = self.pause_consume = consumer.pause_consume
            self.continue_consume = consumer.continue_consume

            wraps(consuming_function)(self)
            BoostersManager.regist_booster(self.queue_name, self)  # 这一句是登记
            return self
        else:
            return self.consuming_function(*args, **kwargs)

    def _safe_push(self, *func_args, **func_kwargs) -> AsyncResult:
        """ 多进程安全的,在fork多进程(非spawn多进程)情况下,有的包多进程不能共用一个连接,例如kafka"""
        consumer = BoostersManager.get_or_create_booster_by_queue_name(self.queue_name).consumer
        return consumer.publisher_of_same_queue.push(*func_args, **func_kwargs)

    def _safe_publish(self, msg: typing.Union[str, dict], task_id=None,
                      priority_control_config: PriorityConsumingControlConfig = None) -> AsyncResult:
        """ 多进程安全的,在fork多进程(非spawn多进程)情况下,很多包跨线程/进程不能共享中间件连接,"""
        consumer = BoostersManager.get_or_create_booster_by_queue_name(self.queue_name).consumer
        return consumer.publisher_of_same_queue.publish(msg=msg, task_id=task_id, priority_control_config=priority_control_config)

    async def aio_push(self, *func_args, **func_kwargs) -> AioAsyncResult:
        """asyncio 生态下发布消息,因为同步push只需要消耗不到1毫秒,所以基本上大概可以直接在asyncio异步生态中直接调用同步的push方法,
        但为了更好的防止网络波动(例如发布消息到外网的消息队列耗时达到10毫秒),可以使用aio_push"""
        async_result = await simple_run_in_executor(self.push, *func_args, **func_kwargs)
        return AioAsyncResult(async_result.task_id, )

    async def aio_publish(self, msg: typing.Union[str, dict], task_id=None,
                          priority_control_config: PriorityConsumingControlConfig = None) -> AioAsyncResult:
        """asyncio 生态下发布消息,因为同步push只需要消耗不到1毫秒,所以基本上大概可以直接在asyncio异步生态中直接调用同步的push方法,
        但为了更好的防止网络波动(例如发布消息到外网的消息队列耗时达到10毫秒),可以使用aio_push"""
        async_result = await simple_run_in_executor(self.publish, msg, task_id, priority_control_config)
        return AioAsyncResult(async_result.task_id, )

    # noinspection PyMethodMayBeStatic
    def multi_process_consume(self, process_num=1):
        """超高速多进程消费"""
        from funboost.core.muliti_process_enhance import run_consumer_with_multi_process
        run_consumer_with_multi_process(self, process_num)

    multi_process_start = multi_process_consume

    # noinspection PyMethodMayBeStatic
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
        from funboost.core.muliti_process_enhance import multi_process_pub_params_list
        multi_process_pub_params_list(self, params_list, process_num)

    # noinspection PyDefaultArgument
    # noinspection PyMethodMayBeStatic
    def fabric_deploy(self, host, port, user, password,
                      path_pattern_exluded_tuple=('/.git/', '/.idea/', '/dist/', '/build/'),
                      file_suffix_tuple_exluded=('.pyc', '.log', '.gz'),
                      only_upload_within_the_last_modify_time=3650 * 24 * 60 * 60,
                      file_volume_limit=1000 * 1000, sftp_log_level=20, extra_shell_str='',
                      invoke_runner_kwargs={'hide': None, 'pty': True, 'warn': False},
                      python_interpreter='python3',
                      process_num=1,
                      pkey_file_path=None,
                      ):
        """
        入参见 fabric_deploy 函数。这里重复入参是为了代码在pycharm补全提示。
        """
        params = copy.copy(locals())
        params.pop('self')
        from funboost.core.fabric_deploy_helper import fabric_deploy
        fabric_deploy(self, **params)


boost = Booster  # @boost 后消费函数.  不能自动补全方法就用 Booster就可以。 2024版本的 pycharm抽风了，@boost的消费函数不能自动补全提示 .consume  .push 这些方法。
task_deco = boost  # 两个装饰器名字都可以。task_deco是原来名字，兼容一下。


class BoostersManager:
    """
    消费函数生成Booster对象时候,会自动调用BoostersManager.regist_booster方法,把队列名和入参信息保存到pid_queue_name__booster_map字典中.
    使用这个类,可以创建booster对象,达到无需使用装饰器的目的.
    """

    # pid_queue_name__booster_map字典存放 {(进程id,queue_name):Booster对象}
    pid_queue_name__booster_map = {}  # type: typing.Dict[typing.Tuple[int,str],Booster]

    # queue_name__boost_params_consuming_function_map 字典存放  {queue_name,(@boost的入参字典,@boost装饰的消费函数)}
    queue_name__boost_params_map = {}  # type: typing.Dict[str,BoosterParams]

    pid_queue_name__has_start_consume_set = set()

    @classmethod
    def regist_booster(cls, queue_name: str, booster: Booster):
        """这个是框架在@boost时候自动调用的,无需用户亲自调用"""
        cls.pid_queue_name__booster_map[(os.getpid(), queue_name)] = booster
        cls.queue_name__boost_params_map[queue_name] = booster.boost_params

    @classmethod
    def show_all_boosters(cls):
        queues = []
        for pid_queue_name, booster in cls.pid_queue_name__booster_map.items():
            queues.append(pid_queue_name[1])
            flogger.debug(f'booster: {pid_queue_name[1]}  {booster}')

    @classmethod
    def get_all_queues(cls):
        return cls.queue_name__boost_params_map.keys()

    @classmethod
    def get_booster(cls, queue_name: str) -> Booster:
        """
        当前进程获得booster对象。注意和下面的get_or_create_booster_by_queue_name方法的区别,主要是开了多进程时候有区别.
        :param queue_name:
        :return:
        """
        pid = os.getpid()
        key = (pid, queue_name)
        if key in cls.pid_queue_name__booster_map:
            return cls.pid_queue_name__booster_map[key]
        else:
            err_msg = f'进程 {pid} ，没有 {queue_name} 对应的 booster   , pid_queue_name__booster_map: {cls.pid_queue_name__booster_map}'
            raise ValueError(err_msg)

    @classmethod
    def get_or_create_booster_by_queue_name(cls, queue_name, ) -> Booster:
        """
        当前进程获得booster对象，如果是多进程,会在新的进程内部创建一个新的booster对象,因为多进程操作有些中间件的同一个conn不行.
        :param queue_name: 就是 @boost的入参。
        :return:
        """
        pid = os.getpid()
        key = (pid, queue_name)
        if key in cls.pid_queue_name__booster_map:
            return cls.pid_queue_name__booster_map[key]
        else:
            boost_params = cls.get_boost_params(queue_name)
            return Booster(boost_params)(boost_params.consuming_function)

    @classmethod
    def get_boost_params(cls, queue_name: str) -> (dict, typing.Callable):
        """
        这个函数是为了在别的进程实例化 booster，consumer和publisher,获取queue_name队列对应的booster的当时的入参。
        有些中间件python包的对中间件连接对象不是多进程安全的，不要在进程2中去操作进程1中生成的booster consumer publisher等对象。
        """
        return cls.queue_name__boost_params_map[queue_name]

    @classmethod
    def build_booster(cls, boost_params: BoosterParams) -> Booster:
        """
        当前进程获得或者创建booster对象。方便有的人需要在函数内部临时动态根据队列名创建booster,不会无数次临时生成消费者、生产者、创建消息队列连接。
        :param boost_params: 就是 @boost的入参。
        :param consuming_function: 消费函数
        :return:
        """
        pid = os.getpid()
        key = (pid, boost_params.queue_name)
        if key in cls.pid_queue_name__booster_map:
            booster = cls.pid_queue_name__booster_map[key]
        else:
            if boost_params.consuming_function is None:
                raise ValueError(f' build_booster 方法的 consuming_function 字段不能为None,必须指定一个函数')
            flogger.info(f'创建booster {boost_params} {boost_params.consuming_function}')
            booster = Booster(boost_params)(boost_params.consuming_function)
        return booster

    queue_name__cross_project_publisher_map = {}

    @classmethod
    def get_cross_project_publisher(cls, publisher_params: PublisherParams) -> AbstractPublisher:
        """
        跨不同的项目，发布消息。例如proj1中定义有fun1消费函数，但proj2无法直接到日proj1的函数，无法直接 fun1.push 来发布消息
        可以使用这个方法，获取一个publisher。

        publisher = BoostersManager.get_cross_project_publisher(PublisherParams(queue_name='proj1_queue', broker_kind=publisher_params.broker_kind))
        publisher.publish({'x': aaa})
        """
        pid = os.getpid()
        key = (pid, publisher_params.queue_name)
        if key not in cls.queue_name__cross_project_publisher_map:
            publisher = get_publisher(publisher_params)
            publisher.push = lambda *args, **kwargs: print('跨项目虚拟publisher不支持push方法，请使用publish来发布消息')
            cls.queue_name__cross_project_publisher_map[key] = publisher
        return cls.queue_name__cross_project_publisher_map[key]

    @classmethod
    def push(cls, queue_name, *args, **kwargs):
        """push发布消息到消息队列 ;
        """
        cls.get_or_create_booster_by_queue_name(queue_name).push(*args, **kwargs)

    @classmethod
    def publish(cls, queue_name, msg):
        """publish发布消息到消息队列;
        """
        cls.get_or_create_booster_by_queue_name(queue_name).publish(msg)

    @classmethod
    def consume_queues(cls, *queue_names):
        """
        启动多个消息队列名的消费,多个函数队列在当前同一个进程内启动消费.
        这种方式节约总的内存,但无法利用多核cpu
        """
        for queue_name in queue_names:
            cls.get_booster(queue_name).consume()
        ctrl_c_recv()

    consume = consume_queues

    @classmethod
    def consume_all_queues(cls, block=True):
        """
        启动所有消息队列名的消费,无需一个一个函数亲自 funxx.consume()来启动,多个函数队列在当前同一个进程内启动消费.
        这种方式节约总的内存,但无法利用多核cpu
        """
        for queue_name in cls.get_all_queues():
            cls.get_booster(queue_name).consume()
        if block:
            ctrl_c_recv()

    consume_all = consume_all_queues

    @classmethod
    def multi_process_consume_queues(cls, **queue_name__process_num):
        """
        启动多个消息队列名的消费,传递队列名和进程数,每个队列启动n个单独的消费进程;
        这种方式总的内存使用高,但充分利用多核cpu
        例如 multi_process_consume_queues(queue1=2,queue2=3) 表示启动2个进程消费queue1,启动3个进程消费queue2
        """
        for queue_name, process_num in queue_name__process_num.items():
            cls.get_booster(queue_name).multi_process_consume(process_num)
        ctrl_c_recv()

    m_consume = multi_process_consume_queues

    @classmethod
    def multi_process_consume_all_queues(cls, process_num=1):
        """
        启动所有消息队列名的消费,无需指定队列名,每个队列启动n个单独的消费进程;
        这种方式总的内存使用高,但充分利用多核cpu
        """
        for queue_name in cls.get_all_queues():
            cls.get_booster(queue_name).multi_process_consume(process_num)
        ctrl_c_recv()

    m_consume_all = multi_process_consume_all_queues

```

### 代码文件: funboost\core\current_task.py
```python
import abc
import typing
import contextvars
from dataclasses import dataclass
import logging
import threading
import asyncio

from funboost.core.function_result_status_saver import FunctionResultStatus



""" 用法例子 
    '''
    fct = funboost_current_task()
    print(fct.function_result_status.get_status_dict())
    print(fct.function_result_status.task_id)
    print(fct.function_result_status.run_times)
    print(fct.full_msg)
    '''
import random
import time

from funboost import boost, FunctionResultStatusPersistanceConfig,BoosterParams
from funboost.core.current_task import funboost_current_task

@boost(BoosterParams(queue_name='queue_test_f01', qps=2,concurrent_num=5,
       function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
           is_save_status=True, is_save_result=True, expire_seconds=7 * 24 * 3600)))
def f(a, b):
    fct = funboost_current_task()
    print(fct.function_result_status.get_status_dict())
    print(fct.function_result_status.task_id)
    print(fct.function_result_status.run_times)
    print(fct.full_msg)

    time.sleep(20)
    if random.random() > 0.5:
        raise Exception(f'{a} {b} 模拟出错啦')
    print(a+b)

    return a + b


if __name__ == '__main__':
    # f(5, 6)  # 可以直接调用

    for i in range(0, 200):
        f.push(i, b=i * 2)

    f.consume()

    """


@dataclass
class FctContext:
    """
    fct 是 funboost current task 的简写
    """

    function_params: dict
    full_msg: dict
    function_result_status: FunctionResultStatus
    logger: logging.Logger
    queue_name: str
    asyncio_use_thread_concurrent_mode: bool = False
    

# class FctContext:
#     """
#     fct 是 funboost current task 的简写
#     """
#
#     def __init__(self, function_params: dict,
#                  full_msg: dict,
#                  function_result_status: FunctionResultStatus,
#                  logger: logging.Logger,
#                  asyncio_use_thread_concurrent_mode: bool = False):
#         self.function_params = function_params
#         self.full_msg = full_msg
#         self.function_result_status = function_result_status
#         self.logger = logger
#         self.asyncio_use_thread_concurrent_mode = asyncio_use_thread_concurrent_mode


class _BaseCurrentTask(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def set_fct_context(self, fct_context: FctContext):
        raise NotImplemented

    @abc.abstractmethod
    def get_fct_context(self) -> FctContext:
        raise NotImplemented

    @property
    def function_params(self):
        return self.get_fct_context().function_params

    @property
    def full_msg(self) -> dict:
        return self.get_fct_context().full_msg

    @property
    def function_result_status(self) -> FunctionResultStatus:
        return self.get_fct_context().function_result_status

    @property
    def task_id(self) -> FunctionResultStatus:
        return self.function_result_status.task_id

    @property
    def logger(self) -> logging.Logger:
        return self.get_fct_context().logger
    
    @property
    def queue_name(self) -> str:
        return self.get_fct_context().queue_name
    

    def __str__(self):
        return f'<{self.__class__.__name__} [{self.function_result_status.get_status_dict()}]>'


class __ThreadCurrentTask(_BaseCurrentTask):
    """
    用于在用户自己函数内部去获取 消息的完整体,当前重试次数等.
    """

    _fct_local_data = threading.local()

    def set_fct_context(self, fct_context: FctContext):
        self._fct_local_data.fct_context = fct_context

    def get_fct_context(self) -> FctContext:
        return self._fct_local_data.fct_context


class __AsyncioCurrentTask(_BaseCurrentTask):
    _fct_context = contextvars.ContextVar('fct_context')

    def set_fct_context(self, fct_context: FctContext):
        self._fct_context.set(fct_context)

    def get_fct_context(self) -> FctContext:
        return self._fct_context.get()


thread_current_task = __ThreadCurrentTask()
asyncio_current_task = __AsyncioCurrentTask()


def is_asyncio_environment():
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def funboost_current_task():
    if is_asyncio_environment():
        if hasattr(thread_current_task._fct_local_data,'fct_context') and thread_current_task.get_fct_context().asyncio_use_thread_concurrent_mode is True:
            # 如果用户使用的是默认的ConcurrentModeEnum.THREADING并发模式来运行async def 函数，那么也使用线程获取上下文
            return thread_current_task
        else:
            return asyncio_current_task
    else:
        return thread_current_task

class _FctProxy:
    """后来多新增这个类了，"""
    @property
    def fct_context(self) ->FctContext:
        ct = funboost_current_task()
        return ct.get_fct_context()

    @property
    def function_params(self):
        return self.fct_context.function_params

    @property
    def full_msg(self) -> dict:
        return self.fct_context.full_msg

    @property
    def function_result_status(self) -> FunctionResultStatus:
        return self.fct_context.function_result_status

    @property
    def task_id(self) -> FunctionResultStatus:
        return self.fct_context.function_result_status.task_id

    @property
    def logger(self) -> logging.Logger:
        return self.fct_context.logger
    
    @property
    def queue_name(self) -> str:
        return self.fct_context.queue_name
    



    def __str__(self):
        return f'<{self.__class__.__name__} [{self.function_result_status.get_status_dict()}]>'

"""
可以直接导入这个fct，不需要 手动写 fct = funboost_current_task() 了。 直接 from funboost import fct就完了，不需要先 fct = funboost_current_task()。
funboost的fct 相当于flask的request那种对象 ，自动线程/协程 级别隔离。 多个线程不会互相干扰。
"""
fct = _FctProxy()



def get_current_taskid():
    # return fct.function_result_status.task_id
    try:
        fct = funboost_current_task()
        return fct.task_id  # 不在funboost的消费函数里面或者同个线程、协程就获取不到上下文了
    except (AttributeError, LookupError) as e:
        # print(e,type(e))
        return 'no_task_id'


class FctContextThread(threading.Thread):
    """
    这个类自动把当前线程的 线程上下文 自动传递给新开的线程。
    """
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, *, daemon=None,
                 ):
        threading.Thread.__init__(**locals())
        self.fct_context = thread_current_task.get_fct_context()

    def run(self):
        thread_current_task.set_fct_context(self.fct_context)
        super().run()


if __name__ == '__main__':
    print(is_asyncio_environment())
    print()
    for i in range(2):
        funboost_current_task()
        print(get_current_taskid())
    print()

```

### 代码文件: funboost\core\exceptions.py
```python


class FunboostException(Exception):
    """funboost 异常基类"""


class ExceptionForRetry(FunboostException):
    """为了重试的，抛出错误。只是定义了一个子类，用不用都可以，函数出任何类型错误了框架都会自动重试"""


class ExceptionForRequeue(FunboostException):
    """框架检测到此错误，重新放回当前队列中"""

class FunboostWaitRpcResultTimeout(FunboostException):
    """等待rpc结果超过了指定时间"""

class FunboostRpcResultError(FunboostException):
    """rpc结果是错误状态"""

class ExceptionForPushToDlxqueue(FunboostException):
    """框架检测到ExceptionForPushToDlxqueue错误，发布到死信队列"""


class BoostDecoParamsIsOldVersion(FunboostException):
    new_version_change_hint = """
你的@boost入参是老的方式,建议用新的入参方式,老入参方式不再支持函数入参代码自动补全了。

老版本的@boost装饰器方式是:
@boost('queue_name_xx',qps=3)
def f(x):
    pass
    

用户需要做的改变如下:
@boost(BoosterParams(queue_name='queue_name_xx',qps=3))
def f(x):
    pass

就是把原来函数入参的加个 BoosterParams 就可以了.

@boost这个最重要的funboost核心方法作出改变的原因是:
1/由于开发框架时候,Booster和Consumer多处需要重复声明入参,
2/入参个数较多,需要locals转化,麻烦
    """

    def __str__(self):
        return self.new_version_change_hint



```

### 代码文件: funboost\core\fabric_deploy_helper.py
```python
# noinspection PyDefaultArgument
import sys
import threading
import time
from pathlib import Path
from fabric2 import Connection
from nb_libs.path_helper import PathHelper
from funboost.utils.paramiko_util import ParamikoFolderUploader

from funboost.core.loggers import get_funboost_file_logger
from funboost.core.booster import Booster

logger = get_funboost_file_logger(__name__)


# noinspection PyDefaultArgument
def fabric_deploy(booster: Booster, host, port, user, password,
                  path_pattern_exluded_tuple=('/.git/', '/.idea/', '/dist/', '/build/'),
                  file_suffix_tuple_exluded=('.pyc', '.log', '.gz'),
                  only_upload_within_the_last_modify_time=3650 * 24 * 60 * 60,
                  file_volume_limit=1000 * 1000, sftp_log_level=20, extra_shell_str='',
                  invoke_runner_kwargs={'hide': None, 'pty': True, 'warn': False},
                  python_interpreter='python3',
                  process_num=1,
                  pkey_file_path=None,
                  ):
    """
    不依赖阿里云codepipeline 和任何运维发布管理工具，只需要在python代码层面就能实现多机器远程部署。
    这实现了函数级别的精确部署，而非是部署一个 .py的代码，远程部署一个函数实现难度比远程部署一个脚本更高一点，部署更灵活。

    之前有人问怎么方便的部署在多台机器，一般用阿里云codepipeline  k8s自动部署。被部署的远程机器必须是linux，不能是windwos。
    但是有的人是直接操作多台物理机，有些不方便，现在直接加一个利用python代码本身实现的跨机器自动部署并运行函数任务。

    自动根据任务函数所在文件，转化成python模块路径，实现函数级别的精确部署，比脚本级别的部署更精确到函数。
    例如 test_frame/test_fabric_deploy/test_deploy1.py的fun2函数 自动转化成 from test_frame.test_fabric_deploy.test_deploy1 import f2
    从而自动生成部署语句
    export PYTHONPATH=/home/ydf/codes/distributed_framework:$PYTHONPATH ;cd /home/ydf/codes/distributed_framework;
    python3 -c "from test_frame.test_fabric_deploy.test_deploy1 import f2;f2.multi_process_consume(2)"  -funboostmark funboost_fabric_mark_queue_test30

    这个是可以直接在远程机器上运行函数任务。无需用户亲自部署代码和启动代码。自动上传代码，自动设置环境变量，自动导入函数，自动运行。
    这个原理是使用python -c 实现的精确到函数级别的部署，不是python脚本级别的部署。
    可以很灵活的指定在哪台机器运行什么函数，开几个进程。这个比celery更为强大，celery需要登录到每台机器，手动下载代码并部署在多台机器，celery不支持代码自动运行在别的机器上


    :param booster:被@boost 装饰的函数
    :param host: 需要部署的远程linux机器的 ip
    :param port:需要部署的远程linux机器的 port
    :param user: 需要部署的远程linux机器的用户名
    :param password:需要部署的远程linux机器的密码
    :param path_pattern_exluded_tuple:排除的文件夹或文件路径
    :param file_suffix_tuple_exluded:排除的后缀
    :param only_upload_within_the_last_modify_time:只上传多少秒以内的文件，如果完整运行上传过一次后，之后可以把值改小，避免每次全量上传。
    :param file_volume_limit:大于这个体积的不上传，因为python代码文件很少超过1M
    :param sftp_log_level: 文件上传日志级别  10为logging.DEBUG 20为logging.INFO  30 为logging.WARNING
    :param extra_shell_str :自动部署前额外执行的命令，例如可以设置环境变量什么的
    :param python_interpreter: python解释器路径，如果linux安装了多个python环境可以指定绝对路径。
    :param invoke_runner_kwargs : invoke包的runner.py 模块的 run()方法的所有一切入参,例子只写了几个入参，实际可以传入十几个入参，大家可以自己琢磨fabric包的run方法，按需传入。
                                 hide 是否隐藏远程机器的输出，值可以为 False不隐藏远程主机的输出  “out”为只隐藏远程机器的正常输出，“err”为只隐藏远程机器的错误输出，True，隐藏远程主机的一切输出
                                 pty 的意思是，远程机器的部署的代码进程是否随着当前脚本的结束而结束。如果为True，本机代码结束远程进程就会结束。如果为False，即使本机代码被关闭结束，远程机器还在运行代码。
                                 warn 的意思是如果远程机器控制台返回了异常码本机代码是否立即退出。warn为True这只是警告一下，warn为False,远程机器返回异常code码则本机代码直接终止退出。
    :param process_num:启动几个进程，要达到最大cpu性能就开启cpu核数个进程就可以了。每个进程内部都有任务函数本身指定的并发方式和并发数量，所以是多进程+线程/协程。
    :param pkey_file_path: 私钥文件路径，如果设置了这个参数，则使用ssh私钥登录远程机器，如果没设置，则使用密码登录。
    :return:


    task_fun.fabric_deploy('192.168.6.133', 22, 'ydf', '123456', process_num=2) 只需要这样就可以自动部署在远程机器运行，无需任何额外操作。
    """
    # print(locals())
    python_proj_dir = Path(sys.path[1]).resolve().as_posix() + '/'
    python_proj_dir_short = python_proj_dir.split('/')[-2]
    # 获取被调用函数所在模块文件名
    file_name = Path(sys._getframe(2).f_code.co_filename).resolve().as_posix() # noqa
    relative_file_name = Path(file_name).relative_to(Path(python_proj_dir)).as_posix()
    relative_module = relative_file_name.replace('/', '.')[:-3]  # -3是去掉.py
    func_name = booster.consuming_function.__name__

    """以下这种是为了兼容 函数没有@boost,而是使用 boosterxx = BoostersManager.build_booster() 来创建的booster. 下面的 python_exec_str 中需要用到 func_name 
    也可以远程时候使用 BoostersManager.get_booster(queue_name),然后启动消费.  因为import模块后,就注册booster信息到BoostersManager,所以能启动了.
    """
    module_obj = PathHelper(sys._getframe(2).f_code.co_filename).import_as_module()  # noqa
    for var_name,var_value in module_obj.__dict__.items():
        if isinstance(var_value,Booster) and var_value.queue_name == booster.queue_name:
            func_name = var_name

    logger.debug([file_name, python_proj_dir, python_proj_dir_short,relative_module, func_name])
    # print(relative_module)
    if user == 'root':  # 文件夹会被自动创建，无需用户创建。
        remote_dir = f'/codes/{python_proj_dir_short}'
    else:
        remote_dir = f'/home/{user}/codes/{python_proj_dir_short}'

    def _inner():
        logger.warning(f'将本地文件夹代码 {python_proj_dir}  上传到远程 {host} 的 {remote_dir} 文件夹。')
        t_start = time.perf_counter()
        uploader = ParamikoFolderUploader(host, port, user, password, python_proj_dir, remote_dir,
                                          path_pattern_exluded_tuple, file_suffix_tuple_exluded,
                                          only_upload_within_the_last_modify_time, file_volume_limit, sftp_log_level, pkey_file_path)
        uploader.upload()
        logger.info(f'上传 本地文件夹代码 {python_proj_dir}  上传到远程 {host} 的 {remote_dir} 文件夹耗时 {round(time.perf_counter() - t_start, 3)} 秒')
        # conn.run(f'''export PYTHONPATH={remote_dir}:$PYTHONPATH''')

        queue_name = booster.consumer.queue_name
        process_mark = f'funboost_fabric_mark__{queue_name}__{func_name}'
        conn = Connection(host, port=port, user=user, connect_kwargs={"password": password}, )
        kill_shell = f'''ps -aux|grep {process_mark}|grep -v grep|awk '{{print $2}}' |xargs kill -9'''
        logger.warning(f'使用linux命令 {kill_shell} 命令杀死 {process_mark} 标识的进程')
        # uploader.ssh.exec_command(kill_shell)
        conn.run(kill_shell, encoding='utf-8', warn=True)  # 不想提示，免得烦扰用户以为有什么异常了。所以用上面的paramiko包的ssh.exec_command

        python_exec_str = f'''export is_funboost_remote_run=1;export PYTHONPATH={remote_dir}:$PYTHONPATH ;{python_interpreter} -c "from {relative_module} import {func_name};{func_name}.multi_process_consume({process_num})"  -funboostmark {process_mark} '''
        shell_str = f'''cd {remote_dir}; {python_exec_str}'''
        extra_shell_str2 = extra_shell_str  # 内部函数对外部变量不能直接改。
        if not extra_shell_str2.endswith(';') and extra_shell_str != '':
            extra_shell_str2 += ';'
        shell_str = extra_shell_str2 + shell_str
        logger.warning(f'使用linux命令 {shell_str} 在远程机器 {host} 上启动任务消费')
        conn.run(shell_str, encoding='utf-8', **invoke_runner_kwargs)
        # uploader.ssh.exec_command(shell_str)

    threading.Thread(target=_inner).start()


def kill_all_remote_tasks(host, port, user, password):
    """ 这个要小心用，杀死所有的远程部署的任务,一般不需要使用到"""
    uploader = ParamikoFolderUploader(host, port, user, password, '', '')
    funboost_fabric_mark_all = 'funboost_fabric_mark__'
    kill_shell = f'''ps -aux|grep {funboost_fabric_mark_all}|grep -v grep|awk '{{print $2}}' |xargs kill -9'''
    logger.warning(f'使用linux命令 {kill_shell} 命令杀死 {funboost_fabric_mark_all} 标识的进程')
    uploader.ssh.exec_command(kill_shell)
    logger.warning(f'杀死 {host}  机器所有的 {funboost_fabric_mark_all} 标识的进程')

```

### 代码文件: funboost\core\funboost_config_getter.py
```python
def _try_get_user_funboost_common_config(funboost_common_conf_field:str):
    try:
        import funboost_config  # 第一次启动funboost前还没这个文件,或者还没有初始化配置之前,就要使用使用配置.
        return getattr(funboost_config.FunboostCommonConfig,funboost_common_conf_field)
    except Exception as e:
        # print(e)
        return None
```

### 代码文件: funboost\core\funboost_time.py
```python
import pytz
import time

import datetime

import typing

from nb_time import NbTime
from funboost.funboost_config_deafult import FunboostCommonConfig

class FunboostTime(NbTime):
    default_formatter = NbTime.FORMATTER_DATETIME_NO_ZONE

    def get_time_zone_str(self,time_zone: typing.Union[str, datetime.tzinfo,None] = None):
        return time_zone or self.default_time_zone or  FunboostCommonConfig.TIMEZONE  or self.get_localzone_name()

    @staticmethod
    def _get_tow_digist(num:int)->str:
        if len(str(num)) ==1:
            return f'0{num}'
        return str(num)

    def get_str(self, formatter=None):
        return self.datetime_obj.strftime(formatter or self.datetime_formatter)

    def get_str_fast(self):
        t_str = f'{self.datetime_obj.year}-{self._get_tow_digist(self.datetime_obj.month)}-{self._get_tow_digist(self.datetime_obj.day)} {self._get_tow_digist(self.datetime_obj.hour)}:{self._get_tow_digist(self.datetime_obj.minute)}:{self._get_tow_digist(self.datetime_obj.second)}'
        return t_str


if __name__ == '__main__':
    print(FunboostTime().get_str())
    tz=pytz.timezone(FunboostCommonConfig.TIMEZONE)
    for i in range(1000000):
        pass
        # FunboostTime()#.get_str_fast()

        # datetime.datetime.now().strftime(NbTime.FORMATTER_DATETIME_NO_ZONE)
        tz = pytz.timezone(FunboostCommonConfig.TIMEZONE)
        datetime.datetime.now(tz=tz)
        # datetime.datetime.now(tz=pytz.timezone(FunboostCommonConfig.TIMEZONE))#.strftime(NbTime.FORMATTER_DATETIME_NO_ZONE)
        # datetime.datetime.now(tz=pytz.timezone(FunboostCommonConfig.TIMEZONE)).timestamp()

        # time.strftime(NbTime.FORMATTER_DATETIME_NO_ZONE)
        # time.time()
    print(NbTime())

```

### 代码文件: funboost\core\function_result_status_config.py
```python
# from pydantic import BaseModel, validator, root_validator
#
# import nb_log
# from nb_log import LoggerMixin
#
#
# # class FunctionResultStatusPersistanceConfig(LoggerMixin):
# #     def __init__(self, is_save_status: bool, is_save_result: bool, expire_seconds: int = 7 * 24 * 3600, is_use_bulk_insert=False):
# #         """
# #         :param is_save_status:
# #         :param is_save_result:
# #         :param expire_seconds: 设置统计的过期时间，在mongo里面自动会移除这些过期的执行记录。
# #         :param is_use_bulk_insert : 是否使用批量插入来保存结果，批量插入是每隔0.5秒钟保存一次最近0.5秒内的所有的函数消费状态结果，始终会出现最后0.5秒内的执行结果没及时插入mongo。为False则，每完成一次函数就实时写入一次到mongo。
# #         """
# #
# #         if not is_save_status and is_save_result:
# #             raise ValueError(f'你设置的是不保存函数运行状态但保存函数运行结果。不允许你这么设置')
# #         self.is_save_status = is_save_status
# #         self.is_save_result = is_save_result
# #         if expire_seconds > 10 * 24 * 3600:
# #             self.logger.warning(f'你设置的过期时间为 {expire_seconds} ,设置的时间过长。 ')
# #         self.expire_seconds = expire_seconds
# #         self.is_use_bulk_insert = is_use_bulk_insert
# #
# #     def to_dict(self):
# #         return {"is_save_status": self.is_save_status,
# #
# #                 'is_save_result': self.is_save_result, 'expire_seconds': self.expire_seconds}
# #
# #     def __str__(self):
# #         return f'<FunctionResultStatusPersistanceConfig> {id(self)} {self.to_dict()}'
# #
#
#

```

### 代码文件: funboost\core\function_result_status_saver.py
```python
import copy
import datetime
import json
import os
import socket
import threading
import time
import uuid

import pymongo
import pymongo.errors
import sys

from pymongo import IndexModel, ReplaceOne

from funboost.core.func_params_model import FunctionResultStatusPersistanceConfig
from funboost.core.helper_funs import get_publish_time, delete_keys_and_return_new_dict
from funboost.core.serialization import Serialization
from funboost.utils import time_util, decorators
from funboost.utils.mongo_util import MongoMixin
# from nb_log import LoggerMixin
from funboost.core.loggers import FunboostFileLoggerMixin

class RunStatus:
    running = 'running'
    finish = 'finish'

class FunctionResultStatus():
    host_name = socket.gethostname()

    script_name_long = sys.argv[0]
    script_name = script_name_long.split('/')[-1].split('\\')[-1]

    FUNC_RUN_ERROR = 'FUNC_RUN_ERROR'

    def __init__(self, queue_name: str, fucntion_name: str, msg_dict: dict):
        # print(params)
        self.host_process = f'{self.host_name} - {os.getpid()}'
        self.queue_name = queue_name
        self.function = fucntion_name
        self.msg_dict = msg_dict
        self.task_id = self.msg_dict.get('extra', {}).get('task_id', '')
        self.process_id = os.getpid()
        self.thread_id = threading.get_ident()
        self.publish_time = publish_time = get_publish_time(msg_dict)
        if publish_time:
            self.publish_time_str = time_util.DatetimeConverter(publish_time).datetime_str
        function_params = delete_keys_and_return_new_dict(msg_dict, )
        self.params = function_params
        self.params_str = Serialization.to_json_str(function_params)
        self.result = None
        self.run_times = 0
        self.exception = None
        self.exception_type = None
        self.exception_msg = None
        self.rpc_chain_error_msg_dict:dict  = None
        self.time_start = time.time()
        self.time_cost = None
        self.time_end = None
        self.success = False
        self.run_status = ''
        self.total_thread = threading.active_count()
        self._has_requeue = False
        self._has_to_dlx_queue = False
        self._has_kill_task = False
        self.rpc_result_expire_seconds = None

    @classmethod
    def parse_status_and_result_to_obj(cls,status_dict:dict):
        obj = cls(status_dict['queue_name'],status_dict['function'],status_dict['msg_dict'])
        for k,v in status_dict.items():
            # if k.startswith('_'):
            #     continue
            setattr(obj,k,v)
        return obj

    def get_status_dict(self, without_datetime_obj=False):
        self.time_end = time.time()
        if self.run_status == RunStatus.running:
            self.time_cost = None
        else:
            self.time_cost = round(self.time_end - self.time_start, 3)
        item = {}
        for k, v in self.__dict__.items():
            if not k.startswith('_'):
                item[k] = v
        item['host_name'] = self.host_name
        item['host_process'] = self.host_process
        item['script_name'] = self.script_name
        item['script_name_long'] = self.script_name_long
        # item.pop('time_start')
        datetime_str = time_util.DatetimeConverter().datetime_str
        try:
            Serialization.to_json_str(item['result'])
            # json.dumps(item['result'])  # 不希望存不可json序列化的复杂类型。麻烦。存这种类型的结果是伪需求。
        except TypeError:
            item['result'] = str(item['result'])[:1000]
        item.update({'insert_time_str': datetime_str,
                     'insert_minutes': datetime_str[:-3],
                     })
        if not without_datetime_obj:
            item.update({'insert_time': time_util.DatetimeConverter().datetime_obj,
                         'utime': datetime.datetime.utcnow(),
                         })
        else:
            item = delete_keys_and_return_new_dict(item, ['insert_time', 'utime'])
        # kw['body']['extra']['task_id']
        # item['_id'] = self.task_id.split(':')[-1] or str(uuid.uuid4())
        item['_id'] = self.task_id or str(uuid.uuid4())
        # self.logger.warning(item['_id'])
        # self.logger.warning(item)
        return item

    def __str__(self):
        return f'''{self.__class__}   {Serialization.to_json_str(self.get_status_dict())}'''

    def to_pretty_json_str(self):
        return json.dumps(self.get_status_dict(),indent=4,ensure_ascii=False)


class ResultPersistenceHelper(MongoMixin, FunboostFileLoggerMixin):
    TASK_STATUS_DB = 'task_status'

    def __init__(self, function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig, queue_name):
        self.function_result_status_persistance_conf = function_result_status_persistance_conf
        self._bulk_list = []
        self._bulk_list_lock = threading.Lock()
        self._last_bulk_insert_time = 0
        self._has_start_bulk_insert_thread = False
        self._queue_name = queue_name
        if self.function_result_status_persistance_conf.is_save_status:
            self._create_indexes()
            # self._mongo_bulk_write_helper = MongoBulkWriteHelper(task_status_col, 100, 2)
            self.logger.debug(f"函数运行状态结果将保存至mongo的 {self.TASK_STATUS_DB} 库的 {queue_name} 集合中，请确认 funboost.py文件中配置的 MONGO_CONNECT_URL")

    def _create_indexes(self):
        task_status_col = self.get_mongo_collection(self.TASK_STATUS_DB, self._queue_name)
        try:
            has_creat_index = False
            index_dict = task_status_col.index_information()
            if 'insert_time_str_-1' in index_dict:
                has_creat_index = True
            old_expire_after_seconds = None
            for index_name, v in index_dict.items():
                if index_name == 'utime_1':
                    old_expire_after_seconds = v['expireAfterSeconds']
            if has_creat_index is False:
                # params_str 如果很长，必须使用TEXt或HASHED索引。
                task_status_col.create_indexes([IndexModel([("insert_time_str", -1)]), IndexModel([("insert_time", -1)]),
                                                IndexModel([("params_str", pymongo.TEXT)]), IndexModel([("success", 1)])
                                                ], )
                task_status_col.create_index([("utime", 1)],  # 这个是过期时间索引。
                                             expireAfterSeconds=self.function_result_status_persistance_conf.expire_seconds)  # 只保留7天(用户自定义的)。
            else:
                if old_expire_after_seconds != self.function_result_status_persistance_conf.expire_seconds:
                    self.logger.warning(f'过期时间从 {old_expire_after_seconds} 修改为 {self.function_result_status_persistance_conf.expire_seconds} 。。。')
                    task_status_col.drop_index('utime_1', ),  # 这个不能也设置为True，导致修改过期时间不成功。
                    task_status_col.create_index([("utime", 1)],
                                                 expireAfterSeconds=self.function_result_status_persistance_conf.expire_seconds, background=True)  # 只保留7天(用户自定义的)。
        except pymongo.errors.PyMongoError as e:
            self.logger.warning(e)

    def save_function_result_to_mongo(self, function_result_status: FunctionResultStatus):
        if self.function_result_status_persistance_conf.is_save_status:
            task_status_col = self.get_mongo_collection(self.TASK_STATUS_DB, self._queue_name)  # type: pymongo.collection.Collection
            item = function_result_status.get_status_dict()
            item2 = copy.copy(item)
            if not self.function_result_status_persistance_conf.is_save_result:
                item2['result'] = '不保存结果'
            if item2['result'] is None:
                item2['result'] = ''
            if item2['exception'] is None:
                item2['exception'] = ''
            if self.function_result_status_persistance_conf.is_use_bulk_insert:
                # self._mongo_bulk_write_helper.add_task(InsertOne(item2))  # 自动离散批量聚合方式。
                with self._bulk_list_lock:
                    self._bulk_list.append(ReplaceOne({'_id': item2['_id']}, item2, upsert=True))
                    # if time.time() - self._last_bulk_insert_time > 0.5:
                    #     self.task_status_col.bulk_write(self._bulk_list, ordered=False)
                    #     self._bulk_list.clear()
                    #     self._last_bulk_insert_time = time.time()
                    if not self._has_start_bulk_insert_thread:
                        self._has_start_bulk_insert_thread = True
                        decorators.keep_circulating(time_sleep=0.2, is_display_detail_exception=True, block=False,
                                                    daemon=False)(self._bulk_insert)()
                        self.logger.warning(f'启动批量保存函数消费状态 结果到mongo的 线程')
            else:
                task_status_col.replace_one({'_id': item2['_id']}, item2, upsert=True)  # 立即实时插入。

    def _bulk_insert(self):
        with self._bulk_list_lock:
            if time.time() - self._last_bulk_insert_time > 0.5 and self._bulk_list:
                task_status_col = self.get_mongo_collection(self.TASK_STATUS_DB, self._queue_name)
                task_status_col.bulk_write(self._bulk_list, ordered=False)
                self._bulk_list.clear()
                self._last_bulk_insert_time = time.time()

```

### 代码文件: funboost\core\func_params_model.py
```python
from typing import Any

import asyncio
import datetime
import functools
import json
import logging
import typing

from typing_extensions import Literal
from collections import OrderedDict

from funboost.concurrent_pool import FunboostBaseConcurrentPool, FlexibleThreadPool, ConcurrentPoolBuilder
from funboost.constant import ConcurrentModeEnum, BrokerEnum
from pydantic import BaseModel, validator, root_validator, BaseConfig, Field

from funboost.core.lazy_impoter import funboost_lazy_impoter


def _patch_for_pydantic_field_deepcopy():
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


_patch_for_pydantic_field_deepcopy()


class BaseJsonAbleModel(BaseModel):
    """
    因为model字段包括了 函数和自定义类型的对象,无法直接json序列化,需要自定义json序列化
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
        try:
            return json.dumps(self.get_str_dict(), ensure_ascii=False, )
        except TypeError as e:
            return str(self.get_str_dict())

    def json_pre(self):
        try:
            return json.dumps(self.get_str_dict(), ensure_ascii=False, indent=4)
        except TypeError as e:
            return str(self.get_str_dict())

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

    @staticmethod
    def init_by_another_model(model_type: typing.Type[BaseModel], modelx: BaseModel):
        init_dict = {}
        for k, v in modelx.dict().items():
            if k in model_type.__fields__.keys():
                init_dict[k] = v
        return model_type(**init_dict)


class FunctionResultStatusPersistanceConfig(BaseJsonAbleModel):
    is_save_status: bool  # 是否保存函数的运行状态信息
    is_save_result: bool  # 是否保存函数的运行结果
    expire_seconds: int = 7 * 24 * 3600  # mongo中的函数运行状态保存多久时间,自动过期
    is_use_bulk_insert: bool = False  # 是否使用批量插入来保存结果，批量插入是每隔0.5秒钟保存一次最近0.5秒内的所有的函数消费状态结果，始终会出现最后0.5秒内的执行结果没及时插入mongo。为False则，每完成一次函数就实时写入一次到mongo。

    @validator('expire_seconds',allow_reuse=True)
    def check_expire_seconds(cls, value):
        if value > 10 * 24 * 3600:
            from funboost.core.loggers import flogger  # 这个文件不要提前导入日志,以免互相导入.
            flogger.warning(f'你设置的过期时间为 {value} ,设置的时间过长。 ')
        return value

    @root_validator(skip_on_failure=True)
    def check_values(cls, values: dict):
        if not values['is_save_status'] and values['is_save_result']:
            raise ValueError(f'你设置的是不保存函数运行状态但保存函数运行结果。不允许你这么设置')
        return values





class BoosterParams(BaseJsonAbleModel):
    """
    pydatinc pycharm编程代码补全,请安装 pydantic插件, 在pycharm的  file -> settings -> Plugins -> 输入 pydantic 搜索,点击安装 pydantic 插件.

    @boost的传参必须是此类或者继承此类,如果你不想每个装饰器入参都很多,你可以写一个子类继承BoosterParams, 传参这个子类,例如下面的 BoosterParamsComplete
    """

    queue_name: str  # 队列名字,必传项,每个函数要使用不同的队列名字.
    broker_kind: str = BrokerEnum.SQLITE_QUEUE  # 中间件选型见3.1章节 https://funboost.readthedocs.io/zh-cn/latest/articles/c3.html

    """如果设置了qps，并且cocurrent_num是默认的50，会自动开了500并发，由于是采用的智能线程池任务少时候不会真开那么多线程而且会自动缩小线程数量。具体看ThreadPoolExecutorShrinkAble的说明
    由于有很好用的qps控制运行频率和智能扩大缩小的线程池，此框架建议不需要理会和设置并发数量只需要关心qps就行了，框架的并发是自适应并发数量，这一点很强很好用。"""
    concurrent_mode: str = ConcurrentModeEnum.THREADING  # 并发模式,支持THREADING,GEVENT,EVENTLET,ASYNC,SINGLE_THREAD并发,multi_process_consume 支持协程/线程 叠加多进程并发,性能炸裂.
    concurrent_num: int = 50  # 并发数量，并发种类由concurrent_mode决定
    specify_concurrent_pool: typing.Optional[FunboostBaseConcurrentPool] = None  # 使用指定的线程池/携程池，可以多个消费者共使用一个线程池,节约线程.不为None时候。threads_num失效
    
    specify_async_loop: typing.Optional[asyncio.AbstractEventLoop] = None  # 指定的async的loop循环，设置并发模式为async才能起作用。 有些包例如aiohttp,发送请求和httpclient的实例化不能处在两个不同的loop中,可以传过来.
    is_auto_start_specify_async_loop_in_child_thread: bool = True  # 是否自动在funboost asyncio并发池的子线程中自动启动指定的async的loop循环，设置并发模式为async才能起作用。如果是False,用户自己在自己的代码中去手动启动自己的loop.run_forever() 
    
    """qps:
    强悍的控制功能,指定1秒内的函数执行次数，例如可以是小数0.01代表每100秒执行一次，也可以是50代表1秒执行50次.为None则不控频。 设置qps时候,不需要指定并发数量,funboost的能够自适应智能动态调节并发池大小."""
    qps: typing.Union[float, int, None] = None
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
    retry_interval: typing.Union[float, int] = 0  # 函数出错后间隔多少秒再重试.
    is_push_to_dlx_queue_when_retry_max_times: bool = False  # 函数达到最大重试次数仍然没成功，是否发送到死信队列,死信队列的名字是 队列名字 + _dlx。


    consumin_function_decorator: typing.Optional[typing.Callable] = None  # 函数的装饰器。因为此框架做参数自动转指点，需要获取精准的入参名称，不支持在消费函数上叠加 @ *args  **kwargs的装饰器，如果想用装饰器可以这里指定。
    function_timeout: typing.Union[int, float,None] = None  # 超时秒数，函数运行超过这个时间，则自动杀死函数。为0是不限制。 谨慎使用,非必要别去设置超时时间,设置后性能会降低(因为需要把用户函数包装到另一个线单独的程中去运行),而且突然强制超时杀死运行中函数,可能会造成死锁.(例如用户函数在获得线程锁后突然杀死函数,别的线程再也无法获得锁了)

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

    msg_expire_senconds: typing.Union[float, int,None] = None  # 消息过期时间,可以设置消息是多久之前发布的就丢弃这条消息,不运行. 为None则永不丢弃

    do_task_filtering: bool = False  # 是否对函数入参进行过滤去重.
    task_filtering_expire_seconds: int = 0  # 任务过滤的失效期，为0则永久性过滤任务。例如设置过滤过期时间是1800秒 ， 30分钟前发布过1 + 2 的任务，现在仍然执行，如果是30分钟以内执行过这个任务，则不执行1 + 2

    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = FunctionResultStatusPersistanceConfig(
        is_save_result=False, is_save_status=False, expire_seconds=7 * 24 * 3600, is_use_bulk_insert=False)  # 是否保存函数的入参，运行结果和运行状态到mongodb。这一步用于后续的参数追溯，任务统计和web展示，需要安装mongo。

    user_custom_record_process_info_func: typing.Optional[typing.Callable] = None  # 提供一个用户自定义的保存消息处理记录到某个地方例如mysql数据库的函数，函数仅仅接受一个入参，入参类型是 FunctionResultStatus，用户可以打印参数

    is_using_rpc_mode: bool = False  # 是否使用rpc模式，可以在发布端获取消费端的结果回调，但消耗一定性能，使用async_result.result时候会等待阻塞住当前线程。
    rpc_result_expire_seconds: int = 600  # 保存rpc结果的过期时间.

    delay_task_apscheduler_jobstores_kind :Literal[ 'redis', 'memory'] = 'redis'  # 延时任务的aspcheduler对象使用哪种jobstores ，可以为 redis memory 两种作为jobstore

    is_support_remote_kill_task: bool = False  # 是否支持远程任务杀死功能，如果任务数量少，单个任务耗时长，确实需要远程发送命令来杀死正在运行的函数，才设置为true，否则不建议开启此功能。(是把函数放在单独的线程中实现的,随时准备线程被远程命令杀死,所以性能会降低)

    is_do_not_run_by_specify_time_effect: bool = False  # 是否使不运行的时间段生效
    do_not_run_by_specify_time: tuple = ('10:00:00', '22:00:00')  # 不运行的时间段,在这个时间段自动不运行函数.

    schedule_tasks_on_main_thread: bool = False  # 直接在主线程调度任务，意味着不能直接在当前主线程同时开启两个消费者。

    is_auto_start_consuming_message: bool = False  # 是否在定义后就自动启动消费，无需用户手动写 .consume() 来启动消息消费。

    consuming_function: typing.Optional[typing.Callable] = None  # 消费函数,在@boost时候不用指定,因为装饰器知道下面的函数.
    consuming_function_raw: typing.Optional[typing.Callable] = None  # 不需要传递，自动生成
    consuming_function_name: str = '' # 不需要传递，自动生成

    

    broker_exclusive_config: dict = {}  # 加上一个不同种类中间件非通用的配置,不同中间件自身独有的配置，不是所有中间件都兼容的配置，因为框架支持30种消息队列，消息队列不仅仅是一般的先进先出queue这么简单的概念，
    # 例如kafka支持消费者组，rabbitmq也支持各种独特概念例如各种ack机制 复杂路由机制，有的中间件原生能支持消息优先级有的中间件不支持,每一种消息队列都有独特的配置参数意义，可以通过这里传递。每种中间件能传递的键值对可以看consumer类的 BROKER_EXCLUSIVE_CONFIG_DEFAULT

    should_check_publish_func_params: bool = True  # 消息发布时候是否校验消息发布内容,比如有的人发布消息,函数只接受a,b两个入参,他去传2个入参,或者传参不存在的参数名字; 如果消费函数加了装饰器 ，你非要写*args,**kwargs,那就需要关掉发布消息时候的函数入参检查
    publish_msg_log_use_full_msg: bool = False # 发布到消息队列的消息内容的日志，是否显示消息的完整体，还是只显示函数入参。

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

    auto_generate_info: dict = {}  # 自动生成的信息,不需要用户主动传参.



    @root_validator(skip_on_failure=True, )
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
        if values['broker_kind'] in [BrokerEnum.REDIS_ACK_ABLE, BrokerEnum.REDIS_STREAM, BrokerEnum.REDIS_PRIORITY, 
                                     BrokerEnum.RedisBrpopLpush,BrokerEnum.REDIS,BrokerEnum.REDIS_PUBSUB]:
            values['is_send_consumer_hearbeat_to_redis'] = True  # 需要心跳进程来辅助判断消息是否属于掉线或关闭的进程，需要重回队列
        # if not set(values.keys()).issubset(set(BoosterParams.__fields__.keys())):
        #     raise ValueError(f'{cls.__name__} 的字段包含了父类 BoosterParams 不存在的字段')
        for k in values.keys():
            if k not in BoosterParams.__fields__.keys():
                raise ValueError(f'{cls.__name__} 的字段新增了父类 BoosterParams 不存在的字段 "{k}"')  # 使 BoosterParams的子类,不能增加字段,只能覆盖字段.
        return values

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
    is_send_consumer_hearbeat_to_redis 永远支持发送消费者的心跳到redis,便于统计分布式环境的活跃消费者
    is_using_rpc_mode  永远支持rpc模式
    broker_kind 永远是使用 amqpstorm包 操作 rabbbitmq作为消息队列.
    specify_concurrent_pool 同一个进程的不同booster函数,共用一个线程池,线程资源利用更高.
    """

    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = FunctionResultStatusPersistanceConfig(
        is_save_result=True, is_save_status=True, expire_seconds=7 * 24 * 3600, is_use_bulk_insert=True)  # 开启函数消费状态 结果持久化到 mongo,为True用户必须要安装mongo和多浪费一丝丝性能.
    is_send_consumer_hearbeat_to_redis: bool = True  # 消费者心跳发到redis,为True那么用户必须安装reids
    is_using_rpc_mode: bool = True  # 固定支持rpc模式,不用每次指定 (不需要使用rpc模式的同学,就不要指定为True,必须安装redis和浪费一点性能)
    rpc_result_expire_seconds: int = 3600
    broker_kind: str = BrokerEnum.RABBITMQ_AMQPSTORM  # 固定使用rabbitmq,不用每次指定
    specify_concurrent_pool: FunboostBaseConcurrentPool = Field(default_factory=functools.partial(ConcurrentPoolBuilder.get_pool, FlexibleThreadPool, 500))  # 多个消费函数共享线程池


class PriorityConsumingControlConfig(BaseJsonAbleModel):
    """
    为每个独立的任务设置控制参数，和函数参数一起发布到中间件。可能有少数时候有这种需求。
    例如消费为add函数，可以每个独立的任务设置不同的超时时间，不同的重试次数，是否使用rpc模式。这里的配置优先，可以覆盖生成消费者时候的配置。
    """

    class Config:
        json_encoders = {
            datetime.datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")
        }

    function_timeout: typing.Union[float, int,None] = None

    max_retry_times: typing.Union[int,None] = None

    is_print_detail_exception: typing.Union[bool,None] = None

    msg_expire_senconds: typing.Union[float, int,None] = None

    is_using_rpc_mode: typing.Union[bool,None] = None

    countdown: typing.Union[float, int,None] = None
    eta: typing.Union[datetime.datetime, str,None] = None  # 时间对象， 或 %Y-%m-%d %H:%M:%S 字符串。
    misfire_grace_time: typing.Union[int, None] = None

    other_extra_params: typing.Optional[dict] = None  # 其他参数, 例如消息优先级 , priority_control_config=PriorityConsumingControlConfig(other_extra_params={'priroty': priorityxx})，
    
    """filter_str:
    用户指定过滤字符串， 例如函数入参是 def fun(userid,username,sex，user_description),
    默认是所有入参一起组成json来过滤，但其实只把userid的值来过滤就好了。所以如果需要精准的按照什么过滤，用户来灵活指定一个字符串就好了
    
    用法见文档4.35 
    f3.publish(msg={'a':i,'b':i*2},priority_control_config=PriorityConsumingControlConfig(filter_str=str(i)))
    """
    filter_str :typing.Optional[str] = None 

    can_not_json_serializable_keys: typing.List[str] = None # 不能json序列化的入参名字，反序列化时候需要使用pickle来反序列化这些字段(这个是自动生成的，用户不需要手动指定此入参。)
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
    logger_name: str = ''  # 队列消费者发布者的日志命名空间.
    log_filename: typing.Optional[str] = None
    clear_queue_within_init: bool = False  # with 语法发布时候,先清空消息队列
    consuming_function: typing.Optional[typing.Callable] = None  # consuming_function 作用是 inspect 模块获取函数的入参信息
    broker_kind: typing.Optional[str] = None
    broker_exclusive_config: dict = {}
    should_check_publish_func_params: bool = True  # 消息发布时候是否校验消息发布内容,比如有的人发布消息,函数只接受a,b两个入参,他去传2个入参,或者传参不存在的参数名字,  如果消费函数你非要写*args,**kwargs,那就需要关掉发布消息时候的函数入参检查
    publisher_override_cls: typing.Optional[typing.Type] = None
    # func_params_is_pydantic_model: bool = False  # funboost 兼容支持 函数娼还是 pydantic model类型，funboost在发布之前和取出来时候自己转化。
    publish_msg_log_use_full_msg: bool = False # 发布到消息队列的消息内容的日志，是否显示消息的完整体，还是只显示函数入参。
    consuming_function_kind: typing.Optional[str] = None  # 自动生成的信息,不需要用户主动传参.


if __name__ == '__main__':
    from funboost.concurrent_pool import FlexibleThreadPool

    pass
    # print(FunctionResultStatusPersistanceConfig(is_save_result=True, is_save_status=True, expire_seconds=70 * 24 * 3600).update_from_kwargs(expire_seconds=100).get_str_dict())
    #
    # print(PriorityConsumingControlConfig().get_str_dict())

    print(BoosterParams(queue_name='3213', specify_concurrent_pool=FlexibleThreadPool(100)).json_pre())
    # print(PublisherParams.schema_json())  # 注释掉，因为 PublisherParams 包含 Callable 类型字段，无法生成 JSON Schema

```

### 代码文件: funboost\core\helper_funs.py
```python
import copy
import pytz
import time
import uuid
import datetime
from funboost.core.funboost_time import FunboostTime


def get_publish_time(paramsx: dict):
    """
    :param paramsx:
    :return:
    """
    return paramsx.get('extra', {}).get('publish_time', None)


def delete_keys_and_return_new_dict(dictx: dict, keys: list = None):
    dict_new = copy.deepcopy(dictx)  # 主要是去掉一级键 publish_time，浅拷贝即可。新的消息已经不是这样了。
    keys = ['publish_time', 'publish_time_format', 'extra'] if keys is None else keys
    for dict_key in keys:
        try:
            dict_new.pop(dict_key)
        except KeyError:
            pass
    return dict_new


def block_python_main_thread_exit():
    """

    https://funboost.readthedocs.io/zh-cn/latest/articles/c10.html#runtimeerror-cannot-schedule-new-futures-after-interpreter-shutdown

    主要是用于 python3.9以上 定时任务报错，  定时任务报错 RuntimeError: cannot schedule new futures after interpreter shutdown
    如果主线程结束了，apscheduler就会报这个错，加上这个while 1 ： time.sleep(100) 目的就是阻止主线程退出。
    """
    while 1:
        time.sleep(100)


run_forever = block_python_main_thread_exit


class MsgGenerater:
    @staticmethod
    def generate_task_id(queue_name:str) -> str:
        return f'{queue_name}_result:{uuid.uuid4()}'

    @staticmethod
    def generate_publish_time() -> float:
        return round(time.time(),4)

    @staticmethod
    def generate_publish_time_format() -> str:
        return FunboostTime().get_str()

    @classmethod
    def generate_pulish_time_and_task_id(cls,queue_name:str,task_id=None):
        extra_params = {'task_id': task_id or cls.generate_task_id(queue_name), 'publish_time': cls.generate_publish_time(),
                        'publish_time_format': cls.generate_publish_time_format()}
        return extra_params



if __name__ == '__main__':

    from funboost import FunboostCommonConfig

    print(FunboostTime())
    for i in range(1000000):
        # time.time()
        # MsgGenerater.generate_publish_time_format()

        datetime.datetime.now(tz=pytz.timezone(FunboostCommonConfig.TIMEZONE)).strftime(FunboostTime.FORMATTER_DATETIME_NO_ZONE)

    print(FunboostTime())
```

### 代码文件: funboost\core\kill_remote_task.py
```python
import ctypes
import threading
import time
from funboost.utils.time_util import DatetimeConverter
from funboost.utils.redis_manager import RedisMixin
# import nb_log
from funboost.core.loggers import FunboostFileLoggerMixin
from funboost.core.current_task import FctContextThread

class ThreadKillAble(FctContextThread):
    task_id = None
    killed = False
    event_kill = threading.Event()


def kill_thread(thread_id):
    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.py_object(SystemExit))


class TaskHasKilledError(Exception):
    pass


def kill_fun_deco(task_id):
    def _inner(f):
        def __inner(*args, **kwargs):
            def _new_func(oldfunc, result, oldfunc_args, oldfunc_kwargs):
                result.append(oldfunc(*oldfunc_args, **oldfunc_kwargs))
                threading.current_thread().event_kill.set()  # noqa

            result = []
            new_kwargs = {
                'oldfunc': f,
                'result': result,
                'oldfunc_args': args,
                'oldfunc_kwargs': kwargs
            }

            thd = ThreadKillAble(target=_new_func, args=(), kwargs=new_kwargs)
            thd.task_id = task_id
            thd.event_kill = threading.Event()
            thd.start()
            thd.event_kill.wait()
            if not result and thd.killed is True:
                raise TaskHasKilledError(f'{DatetimeConverter()} 线程已被杀死 {thd.task_id}')
            return result[0]

        return __inner

    return _inner


def kill_thread_by_task_id(task_id):
    for t in threading.enumerate():
        if isinstance(t, ThreadKillAble):
            thread_task_id = getattr(t, 'task_id', None)
            if thread_task_id == task_id:
                t.killed = True
                t.event_kill.set()
                kill_thread(t.ident)


kill_task = kill_thread_by_task_id


class RemoteTaskKillerZset(RedisMixin, FunboostFileLoggerMixin):
    """
    zset实现的，需要zrank 多次。
    """

    def __init__(self, queue_name, task_id):
        self.queue_name = queue_name
        self.task_id = task_id
        self._redis_zset_key = f'funboost_kill_task:{queue_name}'
        self._lsat_kill_task_ts = time.time()

    def send_remote_task_comd(self):
        self.redis_db_frame.zadd(self._redis_zset_key, {self.task_id: time.time()})

    def judge_need_revoke_run(self):
        if self.redis_db_frame.zrank(self._redis_zset_key, self.task_id) is not None:
            self.redis_db_frame.zrem(self._redis_zset_key, self.task_id)
            return True
        return False

    def kill_local_task(self):
        kill_task(self.task_id)

    def start_cycle_kill_task(self):
        def _start_cycle_kill_task():
            while 1:
                for t in threading.enumerate():
                    if isinstance(t, ThreadKillAble):
                        thread_task_id = getattr(t, 'task_id', None)
                        if self.redis_db_frame.zrank(self._redis_zset_key, thread_task_id) is not None:
                            self.redis_db_frame.zrem(self._redis_zset_key, thread_task_id)
                            t.killed = True
                            t.event_kill.set()
                            kill_thread(t.ident)
                            self._lsat_kill_task_ts = time.time()
                            self.logger.warning(f'队列 {self.queue_name} 的 任务 {thread_task_id} 被杀死')
                if time.time() - self._lsat_kill_task_ts < 2:
                    time.sleep(0.001)
                else:
                    time.sleep(5)

        threading.Thread(target=_start_cycle_kill_task).start()


class RemoteTaskKiller(RedisMixin, FunboostFileLoggerMixin):
    """
    hash实现的，只需要 hmget 一次
    """

    def __init__(self, queue_name, task_id):
        self.queue_name = queue_name
        self.task_id = task_id
        # self.redis_zset_key = f'funboost_kill_task:{queue_name}'
        self._redis_hash_key = f'funboost_kill_task_hash:{queue_name}'
        # self._lsat_kill_task_ts = 0  # time.time()
        self._recent_scan_need_kill_task = False

    def send_kill_remote_task_comd(self):
        # self.redis_db_frame.zadd(self.redis_zset_key, {self.task_id: time.time()})
        self.redis_db_frame.hset(self._redis_hash_key, key=self.task_id, value=time.time())

    def judge_need_revoke_run(self):
        if self.redis_db_frame.hexists(self._redis_hash_key, self.task_id):
            self.redis_db_frame.hdel(self._redis_hash_key, self.task_id)
            return True
        return False

    def kill_local_task(self):
        kill_task(self.task_id)

    def start_cycle_kill_task(self):
        def _start_cycle_kill_task():
            while 1:
                if self._recent_scan_need_kill_task:
                    # print(0.0001)
                    time.sleep(0.01)
                else:
                    # print(555)
                    time.sleep(5)
                self._recent_scan_need_kill_task = False
                thread_task_id_list = []
                task_id__thread_map = {}
                for t in threading.enumerate():
                    if isinstance(t, ThreadKillAble):
                        thread_task_id = getattr(t, 'task_id', None)
                        thread_task_id_list.append(thread_task_id)
                        task_id__thread_map[thread_task_id] = t
                if thread_task_id_list:
                    values = self.redis_db_frame.hmget(self._redis_hash_key, keys=thread_task_id_list)
                    for idx, thread_task_id in enumerate(thread_task_id_list):
                        if values[idx] is not None:
                            self.redis_db_frame.hdel(self._redis_hash_key, thread_task_id)
                            t = task_id__thread_map[thread_task_id]
                            t.killed = True
                            t.event_kill.set()
                            kill_thread(t.ident)
                            self._recent_scan_need_kill_task = True
                            self.logger.warning(f'队列 {self.queue_name} 的 任务 {thread_task_id} 被杀死')

        threading.Thread(target=_start_cycle_kill_task).start()


if __name__ == '__main__':

    test_lock = threading.Lock()


    def my_fun(x):
        """
        使用lock.acquire(),强行杀死会一直无法释放锁
        """
        test_lock.acquire()
        print(f'start {x}')
        # resp = requests.get('http://127.0.0.1:5000')  # flask接口里面sleep30秒，
        # print(resp.text)
        for i in range(10):
            time.sleep(2)
        test_lock.release()
        print(f'over {x}')
        return 666


    def my_fun2(x):
        """
        使用with lock,强行杀死会不会出现一直无法释放锁
        """
        with test_lock:
            print(f'start {x}')
            # resp = requests.get('http://127.0.0.1:5000')  # flask接口里面sleep30秒，
            # print(resp.text)
            for i in range(10):
                time.sleep(2)
            print(f'over {x}')
            return 666


    threading.Thread(target=kill_fun_deco(task_id='task1234')(my_fun2), args=(777,)).start()
    threading.Thread(target=kill_fun_deco(task_id='task5678')(my_fun2), args=(888,)).start()
    time.sleep(5)
    # kill_thread_by_task_id('task1234')

    k = RemoteTaskKiller('test_kill_queue', 'task1234')
    k.start_cycle_kill_task()
    k.send_kill_remote_task_comd()

    """
    第一种代码：
    test_lock.acquire()
    执行io耗时代码
    test_lock.release()
    如果使用lock.acquire()获得锁以后，执行耗时代码时候，还没有执行lock.release() 强行杀死线程，会导致锁一直不能释放
    
    第二种代码
    with test_lock:
        执行io耗时代码
    使用with lock 获得锁以后，执行耗时代码时候，强行杀死线程，则不会导致锁一直不能释放
    
    """

```

### 代码文件: funboost\core\lazy_impoter.py
```python
import abc

from funboost.utils.decorators import cached_method_result, singleton, SingletonBaseNew, SingletonBaseCustomInit, singleton_no_lock

"""
延迟导入
或者使用时候再pip安装
"""


class FunboostLazyImpoter(SingletonBaseNew):
    """
    延迟导入,避免需要互相导入.
    """

    @property
    @cached_method_result
    def BoostersManager(self):
        from funboost.core import booster
        return booster.BoostersManager

    @property
    @cached_method_result
    def boost(self):
        from funboost.core import  booster
        return booster.boost

    @property
    @cached_method_result
    def Booster(self):
        from funboost.core import booster
        return booster.Booster



    # @property
    # @cached_method_result
    # def get_current_taskid(self):
    #     from funboost.core.current_task import get_current_taskid
    #     return get_current_taskid


funboost_lazy_impoter = FunboostLazyImpoter()


# noinspection SpellCheckingInspection
@singleton
class GeventImporter:
    """
    避免提前导入
    import gevent
    from gevent import pool as gevent_pool
    from gevent import monkey
    from gevent.queue import JoinableQueue
    """

    def __init__(self):
        import gevent
        print('导入gevent')
        from gevent import pool as gevent_pool
        from gevent import monkey
        from gevent.queue import JoinableQueue
        self.gevent = gevent
        self.gevent_pool = gevent_pool
        self.monkey = monkey
        self.JoinableQueue = JoinableQueue


@singleton_no_lock
class EventletImporter:
    """
    避免提前导入
    from eventlet import greenpool, monkey_patch, patcher, Timeout
    """

    def __init__(self):
        from eventlet import greenpool, monkey_patch, patcher, Timeout
        print('导入eventlet')
        self.greenpool = greenpool
        self.monkey_patch = monkey_patch
        self.patcher = patcher
        self.Timeout = Timeout


@singleton_no_lock
class PeeweeImporter:
    def __init__(self):
        """pip install peewee == 3.17"""
        from peewee import ModelSelect, Model, BigAutoField, CharField, DateTimeField, MySQLDatabase
        from playhouse.shortcuts import model_to_dict, dict_to_model
        self.ModelSelect = ModelSelect
        self.Model = Model
        self.BigAutoField = BigAutoField
        self.CharField = CharField
        self.DateTimeField = DateTimeField
        self.MySQLDatabase = MySQLDatabase
        self.model_to_dict = model_to_dict
        self.dict_to_model = dict_to_model


@singleton_no_lock
class AioHttpImporter:

    def __init__(self):
        """pip install aiohttp==3.8.3"""
        from aiohttp import web
        from aiohttp.web_request import Request
        self.web = web
        self.Request = Request


@singleton_no_lock
class NatsImporter:
    def __init__(self):
        """pip install nats-python """
        from pynats import NATSClient, NATSMessage
        self.NATSClient = NATSClient
        self.NATSMessage = NATSMessage


@singleton_no_lock
class GnsqImporter:
    def __init__(self):
        """pip install  gnsq==1.0.1"""
        from gnsq import Consumer, Message
        from gnsq import Producer, NsqdHTTPClient
        from gnsq.errors import NSQHttpError
        self.Consumer = Consumer
        self.Message = Message
        self.Producer = Producer
        self.NsqdHTTPClient = NsqdHTTPClient
        self.NSQHttpError = NSQHttpError


@singleton_no_lock
class ElasticsearchImporter:
    def __init__(self):
        """pip install elasticsearch """
        from elasticsearch import helpers
        self.helpers = helpers


@singleton_no_lock
class PsutilImporter:
    def __init__(self):
        """pip install  psutil"""
        import psutil
        self.psutil = psutil


@singleton_no_lock
class PahoMqttImporter:
    def __init__(self):
        """pip install paho-mqtt"""
        import paho.mqtt.client as mqtt
        self.mqtt = mqtt


@singleton_no_lock
class ZmqImporter:
    def __init__(self):
        """pip install zmq pyzmq"""
        import zmq
        self.zmq = zmq


@singleton_no_lock
class KafkaPythonImporter:
    def __init__(self):
        """pip install kafka-python==2.0.2"""

        from kafka import KafkaConsumer as OfficialKafkaConsumer, KafkaProducer, KafkaAdminClient
        from kafka.admin import NewTopic
        from kafka.errors import TopicAlreadyExistsError

        self.OfficialKafkaConsumer = OfficialKafkaConsumer
        self.KafkaProducer = KafkaProducer
        self.KafkaAdminClient = KafkaAdminClient
        self.NewTopic = NewTopic
        self.TopicAlreadyExistsError = TopicAlreadyExistsError


if __name__ == '__main__':
    print()
    for i in range(1000000):
        # funboost_lazy_impoter.BoostersManager
        # EventletImporter().greenpool
        # GeventImporter().JoinableQueue
        ZmqImporter().zmq
    print()

```

### 代码文件: funboost\core\loggers.py
```python
import nb_log
from funboost.core.funboost_config_getter import _try_get_user_funboost_common_config

# noinspection PyUnresolvedReferences
from nb_log import get_logger, LoggerLevelSetterMixin, nb_log_config_default
import logging

LOG_FILE_NAME = 'funboost.log'


def get_funboost_file_logger(name, *, log_level_int: int = None, **kwargs) -> logging.Logger:
    """日志自动写入 funboost.log文件中,不需要亲自指定文件名"""
    kwargs['log_filename'] = LOG_FILE_NAME
    kwargs['error_log_filename'] = nb_log.generate_error_file_name(log_filename=LOG_FILE_NAME)
    return nb_log.get_logger(name, log_level_int=log_level_int, **kwargs, )


class FunboostFileLoggerMixin(nb_log.LoggerMixin):
    """给对象添加一个logger树形命名空间是类本身,写入funboost.log"""
    subclass_logger_dict = {}

    @property
    def logger(self) -> logging.Logger:
        logger_name_key = self.logger_full_name + '3'
        if logger_name_key not in self.subclass_logger_dict:
            logger_var = get_funboost_file_logger(self.logger_full_name)
            self.subclass_logger_dict[logger_name_key] = logger_var
            return logger_var
        else:
            return self.subclass_logger_dict[logger_name_key]


class FunboostMetaTypeFileLogger(type):
    """
    给类添加一个属性.名空间是类本身,写入funboost.log
    """

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        cls.logger: logging.Logger = get_funboost_file_logger(name)


nb_log.LogManager('_KeepAliveTimeThread').preset_log_level(_try_get_user_funboost_common_config('KEEPALIVETIMETHREAD_LOG_LEVEL') or logging.DEBUG)

flogger = get_funboost_file_logger('funboost', )
# print(_try_get_user_funboost_common_config('FUNBOOST_PROMPT_LOG_LEVEL'))
logger_prompt = get_funboost_file_logger('funboost.prompt', log_level_int=_try_get_user_funboost_common_config('FUNBOOST_PROMPT_LOG_LEVEL') or logging.DEBUG)

# 开发时候的调试日志，比print方便通过级别一键屏蔽。
develop_logger = get_logger('funboost_develop', log_level_int=logging.WARNING, log_filename='funboost_develop.log')

if __name__ == '__main__':
    logger1 = get_funboost_file_logger('name1')
    logger1.info('啦啦啦啦啦啦啦')
    logger1.error('错错错')
    
```

### 代码文件: funboost\core\msg_result_getter.py
```python
import asyncio
import time

import typing
import json

from funboost.utils.mongo_util import MongoMixin

from funboost.concurrent_pool import CustomThreadPoolExecutor
from funboost.concurrent_pool.flexible_thread_pool import FlexibleThreadPoolMinWorkers0
from funboost.utils.redis_manager import RedisMixin
from funboost.utils.redis_manager import AioRedisMixin
from funboost.core.serialization import Serialization

from funboost.core.function_result_status_saver import FunctionResultStatus

class HasNotAsyncResult(Exception):
    pass


NO_RESULT = 'no_result'

def _judge_rpc_function_result_status_obj(status_and_result_obj:FunctionResultStatus,raise_exception:bool):
    if status_and_result_obj is None:
        raise FunboostWaitRpcResultTimeout(f'等待 {status_and_result_obj.task_id} rpc结果超过了指定时间')
    if status_and_result_obj.success is True:
        return status_and_result_obj
    else:
        raw_erorr = status_and_result_obj.exception
        if status_and_result_obj.exception_type == 'FunboostRpcResultError':
            raw_erorr = json.loads(status_and_result_obj.exception_msg) # 使canvas链式报错json显示更美观
        error_msg_dict = {'task_id':status_and_result_obj.task_id,'raw_error':raw_erorr}
        if raise_exception:
            raise FunboostRpcResultError(json.dumps(error_msg_dict,indent=4,ensure_ascii=False))
        else:
            status_and_result_obj.rpc_chain_error_msg_dict = error_msg_dict
            return status_and_result_obj
class AsyncResult(RedisMixin):
    default_callback_run_executor = FlexibleThreadPoolMinWorkers0(200,work_queue_maxsize=50)

    @property
    def callback_run_executor(self, ):
        return self._callback_run_executor or self.default_callback_run_executor
    @callback_run_executor.setter
    def callback_run_executor(self,thread_pool_executor):
        """
        用户可以 async_result.callback_run_executor = 你自己的线程池
        thread_pool_executor 用户可以传递 FlexibleThreadPool或者 ThreadPoolExecutorShrinkAble 或者官方的 concurrent.futures.ThreadPoolExecutor 类型的对象都可以，任意线程池只要实现了submit方法即可。
        :param thread_pool_executor:
        :return:
        """
        self._callback_run_executor = thread_pool_executor

    def __init__(self, task_id, timeout=120):
        self.task_id = task_id
        self.timeout = timeout
        self._has_pop = False
        self._status_and_result = None
        self._callback_run_executor = None

    def set_timeout(self, timeout=60):
        self.timeout = timeout
        return self

    def is_pending(self):
        return not self.redis_db_filter_and_rpc_result.exists(self.task_id)

    @property
    def status_and_result(self):
        if not self._has_pop:
            # print(f'{self.task_id} 正在等待结果')
            redis_value = self.redis_db_filter_and_rpc_result.blpop(self.task_id, self.timeout)
            self._has_pop = True
            if redis_value is not None:
                status_and_result_str = redis_value[1]
                self._status_and_result = Serialization.to_dict(status_and_result_str)
                self.redis_db_filter_and_rpc_result.lpush(self.task_id, status_and_result_str)
                self.redis_db_filter_and_rpc_result.expire(self.task_id, self._status_and_result['rpc_result_expire_seconds'])
                return self._status_and_result
            return None
        return self._status_and_result
    
    @property
    def status_and_result_obj(self) -> FunctionResultStatus:
        """这个是为了比字典有更好的ide代码补全效果"""
        if self.status_and_result is not None:
            return FunctionResultStatus.parse_status_and_result_to_obj(self.status_and_result)
    
    rpc_data =status_and_result_obj

    def get(self):
        # print(self.status_and_result)
        if self.status_and_result is not None:
            return self.status_and_result['result']
        else:
            raise HasNotAsyncResult

    @property
    def result(self):
        return self.get()

    def is_success(self):
        if self.status_and_result is not None:
            return self.status_and_result['success']
        else:
            raise HasNotAsyncResult

    def _run_callback_func(self, callback_func):
        callback_func(self.status_and_result)

    def set_callback(self, callback_func: typing.Callable):
        """
        :param callback_func: 函数结果回调函数，使回调函数自动在线程池中并发运行。
        :return:
        """

        ''' 用法例如
        from test_frame.test_rpc.test_consume import add
        def show_result(status_and_result: dict):
            """
            :param status_and_result: 一个字典包括了函数入参、函数结果、函数是否运行成功、函数运行异常类型
            """
            print(status_and_result)

        for i in range(100):
            async_result = add.push(i, i * 2)
            # print(async_result.result)   # 执行 .result是获取函数的运行结果，会阻塞当前发布消息的线程直到函数运行完成。
            async_result.set_callback(show_result) # 使用回调函数在线程池中并发的运行函数结果
        '''
        self.callback_run_executor.submit(self._run_callback_func, callback_func)
    
    def wait_rpc_data_or_raise(self,raise_exception:bool=True)->FunctionResultStatus:
        return _judge_rpc_function_result_status_obj(self.status_and_result_obj,raise_exception)
    
    @classmethod
    def batch_wait_rpc_data_or_raise(cls,r_list:typing.List['AsyncResult'],raise_exception:bool=True)->typing.List[FunctionResultStatus]:
        return [ _judge_rpc_function_result_status_obj(r.status_and_result_obj,raise_exception) 
                for r in r_list]


class AioAsyncResult(AioRedisMixin):
    """ 这个是可以用于asyncio的语法环境中。"""
    '''
    用法例子
import asyncio

from funboost import AioAsyncResult
from test_frame.test_rpc.test_consume import add


async def process_result(status_and_result: dict):
    """
    :param status_and_result: 一个字典包括了函数入参、函数结果、函数是否运行成功、函数运行异常类型
    """
    await asyncio.sleep(1)
    print(status_and_result)


async def test_get_result(i):
    async_result = add.push(i, i * 2)
    aio_async_result = AioAsyncResult(task_id=async_result.task_id) # 这里要使用asyncio语法的类，更方便的配合asyncio异步编程生态
    print(await aio_async_result.result) # 注意这里有个await，如果不await就是打印一个协程对象，不会得到结果。这是asyncio的基本语法，需要用户精通asyncio。
    print(await aio_async_result.status_and_result)
    await aio_async_result.set_callback(process_result)  #  你也可以编排任务到loop中


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    for j in range(100):
        loop.create_task(test_get_result(j))
    loop.run_forever()

    '''

    def __init__(self, task_id, timeout=120):
        self.task_id = task_id
        self.timeout = timeout
        self._has_pop = False
        self._status_and_result = None

    def set_timeout(self, timeout=60):
        self.timeout = timeout
        return self

    async def is_pending(self):
        is_exists = await self.aioredis_db_filter_and_rpc_result.exists(self.task_id)
        return not is_exists

    @property
    async def status_and_result(self):
        if not self._has_pop:
            t1 = time.time()
            redis_value = await self.aioredis_db_filter_and_rpc_result.blpop(self.task_id, self.timeout)
            self._has_pop = True
            if redis_value is not None:
                status_and_result_str = redis_value[1]
                self._status_and_result = Serialization.to_dict(status_and_result_str)
                await self.aioredis_db_filter_and_rpc_result.lpush(self.task_id, status_and_result_str)
                await self.aioredis_db_filter_and_rpc_result.expire(self.task_id, self._status_and_result['rpc_result_expire_seconds'])
                return self._status_and_result
            return None
        return self._status_and_result

    @property
    async def status_and_result_obj(self) -> FunctionResultStatus:
        """这个是为了比字典有更好的ide代码补全效果"""
        sr = await self.status_and_result
        if sr is not None:
            return FunctionResultStatus.parse_status_and_result_to_obj(sr)

    rpc_data =status_and_result_obj
    async def get(self):
        # print(self.status_and_result)
        if (await self.status_and_result) is not None:
            return (await self.status_and_result)['result']
        else:
            raise HasNotAsyncResult

    @property
    async def result(self):
        return await self.get()

    async def is_success(self):
        if (await self.status_and_result) is not None:
            return (await self.status_and_result)['success']
        else:
            raise HasNotAsyncResult

    async def _run_callback_func(self, callback_func):
        await callback_func(await self.status_and_result)

    async def set_callback(self, aio_callback_func: typing.Callable):
        asyncio.create_task(self._run_callback_func(callback_func=aio_callback_func))

    async def wait_rpc_data_or_raise(self,raise_exception:bool=True)->FunctionResultStatus:
        return _judge_rpc_function_result_status_obj(await self.status_and_result_obj,raise_exception)

    @classmethod
    async def batch_wait_rpc_data_or_raise(cls,r_list:typing.List['AioAsyncResult'],raise_exception:bool=True)->typing.List[FunctionResultStatus]:
        return [ _judge_rpc_function_result_status_obj(await r.status_and_result_obj,raise_exception) 
                for r in r_list]
    



class ResultFromMongo(MongoMixin):
    """
    以非阻塞等待的方式从funboost的状态结果持久化的mongodb数据库根据taskid获取结果

    async_result = add.push(i, i * 2)
    task_id=async_result.task_id
    print(ResultFromMongo(task_id).get_status_and_result())


    print(ResultFromMongo('test_queue77h6_result:764a1ba2-14eb-49e2-9209-ac83fc5db1e8').get_status_and_result())
    print(ResultFromMongo('test_queue77h6_result:5cdb4386-44cc-452f-97f4-9e5d2882a7c1').get_result())
    """

    def __init__(self, task_id: str, ):
        self.task_id = task_id
        self.col_name = task_id.split('_result:')[0]
        self.mongo_row = None
        self._has_query = False

    def query_result(self):
        col = self.get_mongo_collection('task_status', self.col_name)
        self.mongo_row = col.find_one({'_id': self.task_id})
        self._has_query = True

    def get_status_and_result(self):
        self.query_result()
        return self.mongo_row or NO_RESULT

    def get_result(self):
        """以非阻塞等待的方式从funboost的状态结果持久化的mongodb数据库根据taskid获取结果"""
        self.query_result()
        return (self.mongo_row or {}).get('result', NO_RESULT)


if __name__ == '__main__':
    print(ResultFromMongo('test_queue77h6_result:764a1ba2-14eb-49e2-9209-ac83fc5db1e8').get_status_and_result())
    print(ResultFromMongo('test_queue77h6_result:5cdb4386-44cc-452f-97f4-9e5d2882a7c1').get_result())

```

### 代码文件: funboost\core\muliti_process_enhance.py
```python
import os
import signal
from multiprocessing import Process
import time
from typing import List
from concurrent.futures import ProcessPoolExecutor
from funboost.core.booster import Booster
from funboost.core.helper_funs import run_forever
from funboost.core.loggers import flogger
from funboost.core.lazy_impoter import funboost_lazy_impoter


def _run_consumer_in_new_process(queue_name, ):
    booster_current_pid = funboost_lazy_impoter.BoostersManager.get_or_create_booster_by_queue_name(queue_name)
    # booster_current_pid = boost(**boost_params)(consuming_function)
    booster_current_pid.consume()
    # ConsumersManager.join_all_consumer_shedual_task_thread()
    run_forever()


def run_consumer_with_multi_process(booster: Booster, process_num=1):
    """
    :param booster:被 boost 装饰器装饰的消费函数
    :param process_num:开启多个进程。  主要是 多进程并发  + 4种细粒度并发(threading gevent eventlet asyncio)。叠加并发。
    这种是多进程方式，一次编写能够兼容win和linux的运行。一次性启动6个进程 叠加 多线程 并发。
    """
    '''
       from funboost import boost, BrokerEnum, ConcurrentModeEnum, run_consumer_with_multi_process
       import os

       @boost('test_multi_process_queue',broker_kind=BrokerEnum.REDIS_ACK_ABLE,concurrent_mode=ConcurrentModeEnum.THREADING,)
       def fff(x):
           print(x * 10,os.getpid())

       if __name__ == '__main__':
           # fff.consume()
           run_consumer_with_multi_process(fff,6) # 一次性启动6个进程 叠加 多线程 并发。
           fff.multi_process_conusme(6)    # 这也是一次性启动6个进程 叠加 多线程 并发。
    '''
    if not isinstance(booster, Booster):
        raise ValueError(f'{booster} 参数必须是一个被 boost 装饰的函数')
    if process_num == 1 and False:
        booster.consume()
    else:
        for i in range(process_num):
            # print(i)
            Process(target=_run_consumer_in_new_process,
                    args=(booster.queue_name,)).start()


def _multi_process_pub_params_list_in_new_process(queue_name, msgs: List[dict]):
    booster_current_pid = funboost_lazy_impoter.BoostersManager.get_or_create_booster_by_queue_name(queue_name)
    publisher = booster_current_pid.publisher
    publisher.set_log_level(20)  # 超高速发布，如果打印详细debug日志会卡死屏幕和严重降低代码速度。
    for msg in msgs:
        publisher.publish(msg)


def multi_process_pub_params_list(booster: Booster, params_list, process_num=16):
    """超高速多进程发布任务，充分利用多核"""
    if not isinstance(booster, Booster):
        raise ValueError(f'{booster} 参数必须是一个被 boost 装饰的函数')
    params_list_len = len(params_list)
    if params_list_len < 1000 * 100:
        raise ValueError(f'要要发布的任务数量是 {params_list_len} 个,要求必须至少发布10万任务才使用此方法')
    ava_len = params_list_len // process_num + 1
    with ProcessPoolExecutor(process_num) as pool:
        t0 = time.time()
        for i in range(process_num):
            msgs = params_list[i * ava_len: (i + 1) * ava_len]
            # print(msgs)
            pool.submit(_multi_process_pub_params_list_in_new_process, booster.queue_name,
                        msgs)
    flogger.info(f'\n 通过 multi_process_pub_params_list 多进程子进程的发布方式，发布了 {params_list_len} 个任务。耗时 {time.time() - t0} 秒')

```

### 代码文件: funboost\core\serialization.py
```python
import typing
import json
import orjson
import pickle
import ast

class Serialization:
    @staticmethod
    def to_json_str(dic:typing.Union[dict,str]):
        if isinstance(dic,str):
            return dic
        str1 =orjson.dumps(dic)
        return str1.decode('utf8')

    @staticmethod
    def to_dict(strx:typing.Union[str,dict]):
        if isinstance(strx,dict):
            return strx
        return orjson.loads(strx)
    
    @staticmethod
    def find_can_not_json_serializable_keys(dic:dict)->typing.List[str]:
        can_not_json_serializable_keys = []
        dic = Serialization.to_dict(dic)
        for k,v in dic.items():
            if not isinstance(v,str):
                try:
                    json.dumps(v)
                except:
                    can_not_json_serializable_keys.append(k)
        return can_not_json_serializable_keys
    

class PickleHelper:
    @staticmethod
    def to_str(obj_x:typing.Any):
        return str(pickle.dumps(obj_x)) # 对象pickle,转成字符串
    
    @staticmethod
    def to_obj(str_x:str):
        return pickle.loads(ast.literal_eval(str_x)) # 不是从字节转成对象,是从字符串转,所以需要这样.
    


```

### 代码文件: funboost\core\task_id_logger.py
```python
import functools

from nb_log import CompatibleLogger
from funboost.core.current_task import get_current_taskid


class TaskIdLogger(CompatibleLogger):
    """
    如果你要使用带taskid的日志模板,一定要使用
     LogManager('namexx',logger_cls=TaskIdLogger).get_logger_and_add_handlers(....)
     的方式来创建logger, 就是需要指定logger_cls=TaskIdLogger ,否则的话你需要在打印日志时候 手动传递extra logger.info(msg,extra={'task_id':task_idxxx})
     """
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False):
        extra = extra or {}
        if 'task_id' not in extra:
            extra['task_id'] = get_current_taskid()
        if 'sys_getframe_n' not in extra:
            extra['sys_getframe_n'] = 3
        super()._log(level, msg, args, exc_info, extra, stack_info)

```

### 代码文件: funboost\core\__init__.py
```python

```

### 代码文件: funboost\core\cli\discovery_boosters.py
```python
import re
import sys
import typing
from os import PathLike
from pathlib import Path
import importlib.util
# import nb_log
from funboost.core.loggers import FunboostFileLoggerMixin
from funboost.utils.decorators import flyweight
from funboost.core.lazy_impoter import funboost_lazy_impoter

@flyweight
class BoosterDiscovery(FunboostFileLoggerMixin):
    def __init__(self, project_root_path: typing.Union[PathLike, str],
                 booster_dirs: typing.List[typing.Union[PathLike, str]],
                 max_depth=1, py_file_re_str: str = None):
        """
        :param project_root_path 项目根目录
        :param booster_dirs: @boost装饰器函数所在的模块的文件夹,不用包含项目根目录长路径
        :param max_depth: 查找多少深层级子目录
        :param py_file_re_str: 文件名匹配过滤. 例如你所有的消费函数都在xxx_task.py yyy_task.py这样的,  你可以传参 task.py , 避免自动import了不需要导入的模块
        """

        self.booster__full_path_dirs = [Path(project_root_path) / Path(boost_dir) for boost_dir in booster_dirs]
        self.max_depth = max_depth
        self.py_file_re_str = py_file_re_str

        self.py_files = []
        self._has_discovery_import = False

    def get_py_files_recursively(self, current_folder_path: Path, current_depth=0, ):
        """先找到所有py文件"""
        if current_depth > self.max_depth:
            return
        for item in current_folder_path.iterdir():
            if item.is_dir():
                self.get_py_files_recursively(item, current_depth + 1)
            elif item.suffix == '.py':
                if self.py_file_re_str:
                    if re.search(self.py_file_re_str, str(item), ):
                        self.py_files.append(str(item))
                else:
                    self.py_files.append(str(item))
        self.py_files = list(set(self.py_files))

    def auto_discovery(self, ):
        """把所有py文件自动执行import,主要是把 所有的@boost函数装饰器注册到 pid_queue_name__booster_map 中
        这个auto_discovery方法最好放到main里面,如果要扫描自身文件夹,没写正则排除文件本身,会无限懵逼死循环导入,无无限懵逼死循环导入
        """
        if self._has_discovery_import is False:
            self._has_discovery_import = True
        else:
            pass
            return  # 这一个判断是避免用户执行BoosterDiscovery.auto_discovery没有放到 if __name__ == '__main__'中,导致无限懵逼死循环.
        self.logger.info(self.booster__full_path_dirs)
        for dir in self.booster__full_path_dirs:
            if not Path(dir).exists():
                raise Exception(f'没有这个文件夹 ->  {dir}')

            self.get_py_files_recursively(Path(dir))
            for file_path in self.py_files:
                self.logger.debug(f'导入模块 {file_path}')
                if Path(file_path) == Path(sys._getframe(1).f_code.co_filename):
                    self.logger.warning(f'排除导入调用auto_discovery的模块自身 {file_path}')  # 否则下面的import这个文件,会造成无限懵逼死循环
                    continue

                module_name = Path(file_path).as_posix().replace('/', '.') + '.' + Path(file_path).stem
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
        funboost_lazy_impoter.BoostersManager.show_all_boosters()


if __name__ == '__main__':
    # 指定文件夹路径
    BoosterDiscovery(project_root_path='/codes/funboost',
                     booster_dirs=['test_frame/test_funboost_cli/test_find_boosters'],
                     max_depth=2, py_file_re_str='task').auto_discovery()

```

### 代码文件: funboost\core\cli\funboost_cli_user_templ.py
```python
"""
funboost现在 新增 命令行启动消费 发布  和清空消息


"""
import sys
from pathlib import Path
import fire

project_root_path = Path(__file__).absolute().parent
print(f'project_root_path is : {project_root_path}  ,请确认是否正确')
sys.path.insert(1, str(project_root_path))  # 这个是为了方便命令行不用用户手动先 export PYTHONPATTH=项目根目录

# $$$$$$$$$$$$
# 以上的sys.path代码需要放在最上面,先设置好pythonpath再导入funboost相关的模块
# $$$$$$$$$$$$


from funboost.core.cli.funboost_fire import BoosterFire, env_dict
from funboost.core.cli.discovery_boosters import BoosterDiscovery

# 需要启动的函数,那么该模块或函数建议建议要被import到这来, 否则需要要在 --import_modules_str 或 booster_dirs 中指定用户项目中有哪些模块包括了booster
'''
有4种方式,自动找到有@boost装饰器,注册booster

1. 用户亲自把要启动的消费函数所在模块或函数 手动 import 一下到此模块来
2. 用户在使用命令行时候 --import_modules_str 指定导入哪些模块路径,就能启动那些队列名来消费和发布了.
3. 用户使用BoosterDiscovery.auto_discovery_boosters  自动 import 指定文件夹下的 .py 文件来实现.
4  用户在使用命令行时候传参 project_root_path booster_dirs ,自动扫描模块,自动import
'''
env_dict['project_root_path'] = project_root_path

if __name__ == '__main__':
    # booster_dirs 用户可以自己增加扫描的文件夹,这样可以命令行少传了 --booster_dirs_str
    # BoosterDiscovery 可以多次调用
    BoosterDiscovery(project_root_path, booster_dirs=[], max_depth=1, py_file_re_str=None).auto_discovery()  # 这个最好放到main里面,如果要扫描自身文件夹,没写正则排除文件本身,会无限懵逼死循环导入
    fire.Fire(BoosterFire, )

'''

python /codes/funboost/funboost_cli_user.py   --booster_dirs_str=test_frame/test_funboost_cli/test_find_boosters --max_depth=2  push test_find_queue1 --x=1 --y=2

python /codes/funboost/funboost_cli_user.py   --booster_dirs_str=test_frame/test_funboost_cli/test_find_boosters --max_depth=2  consume test_find_queue1 

'''

```

### 代码文件: funboost\core\cli\funboost_fire.py
```python
import copy
import importlib
import sys
import typing
from os import PathLike

from funboost.core.booster import BoostersManager
from funboost.core.cli.discovery_boosters import BoosterDiscovery
from funboost.utils.ctrl_c_end import ctrl_c_recv

env_dict = {'project_root_path': None}


# noinspection PyMethodMayBeStatic
class BoosterFire(object):
    def __init__(self, import_modules_str: str = None,
                 booster_dirs_str: str = None, max_depth=1, py_file_re_str: str = None, project_root_path=None):
        """
        :param project_root_path : 用户项目根目录
        :param import_modules_str:
        :param booster_dirs_str: 扫描@boost函数所在的目录，如果多个目录用,隔开
        :param max_depth: 扫描目录代码层级
        :param py_file_re_str: python文件的正则， 例如  tasks.py那么就不自动import其他名字的python模块
        """
        project_root_path = env_dict['project_root_path'] or project_root_path
        print(f'project_root_path is :{project_root_path} ,请确认')
        if project_root_path is None:
            raise Exception('project_root_path is none')
        loc = copy.copy(locals())
        for k, v in loc.items():
            print(f'{k} : {v}')
        sys.path.insert(1, str(project_root_path))
        self.import_modules_str = import_modules_str
        if import_modules_str:
            for m in self.import_modules_str.split(','):
                importlib.import_module(m)  # 发现@boost函数
        if booster_dirs_str and project_root_path:
            boost_dirs = booster_dirs_str.split(',')
            BoosterDiscovery(project_root_path=str(project_root_path), booster_dirs=boost_dirs,
                             max_depth=max_depth, py_file_re_str=py_file_re_str).auto_discovery()  # 发现@boost函数

    def show_all_queues(self):
        """显示扫描到的所有queue name"""
        print(f'get_all_queues: {BoostersManager.get_all_queues()}')
        return self

    def clear(self, *queue_names: str):
        """
        清空多个queue ; 例子: clear test_cli1_queue1  test_cli1_queue2   # 清空2个消息队列消息队列
        """

        for queue_name in queue_names:
            BoostersManager.get_booster(queue_name).clear()
        return self

    def push(self, queue_name, *args, **kwargs):
        """push发布消息到消息队列 ;
        例子: 假设函数是 def  add(x,y)  队列名是 add_queue , 发布 1 + 2求和;
        push add_queue 1 2;
        或者 push add_queue --x=1 --y=2;
        或者 push add_queue -x 1 -y 2;
        """
        BoostersManager.push(queue_name,*args, **kwargs)
        return self

    def __str__(self):
        # print('over')  # 这行重要,否则命令行链式调用无法自动结束
        return ''

    def publish(self, queue_name, msg):
        """publish发布消息到消息队列;
           假设函数是 def  add(x,y)  队列名是 add_queue , 发布 1 + 2求和;
           publish add_queue "{'x':1,'y':2}"
        """

        BoostersManager.publish(queue_name,msg)
        return self

    def consume_queues(self, *queue_names: str):
        """
        启动多个消息队列名的消费;
        例子: consume queue1 queue2
        """
        BoostersManager.consume_queues(*queue_names)

    consume = consume_queues

    def consume_all_queues(self, ):
        """
        启动所有消息队列名的消费,无需指定队列名;
        例子: consume_all_queues
        """
        BoostersManager.consume_all_queues()

    consume_all = consume_all_queues

    def multi_process_consume_queues(self, **queue_name__process_num):
        """
        使用多进程启动消费,每个队列开启多个单独的进程消费;
        例子:  m_consume --queue1=2 --queue2=3    # queue1启动两个单独进程消费  queue2 启动3个单独进程消费
        """
        BoostersManager.multi_process_consume_queues(**queue_name__process_num)

    m_consume = multi_process_consume_queues

    def multi_process_consume_all_queues(self, process_num=1):
        """
        启动所有消息队列名的消费,无需指定队列名,每个队列启动n个单独的消费进程;
        例子: multi_process_consume_all_queues 2
        """
        BoostersManager.multi_process_consume_all_queues(process_num)

    m_consume_all = multi_process_consume_all_queues

    def pause(self, *queue_names: str):
        """
        暂停多个消息队列名的消费;
        例子: pause queue1 queue2
        """
        for queue_name in queue_names:
            BoostersManager.get_booster(queue_name).pause()

    def continue_consume(self, *queue_names: str):
        """
        继续多个消息队列名的消费;
        例子: continue_consume queue1 queue2
        """
        for queue_name in queue_names:
            BoostersManager.get_booster(queue_name).continue_consume()
    
    def start_funboost_web_manager(self):
        """
        启动funboost web管理器;
        例子: start_funboost_web_manager
        """
        from funboost.function_result_web.app import start_funboost_web_manager
        start_funboost_web_manager()

    start_web = start_funboost_web_manager

```

### 代码文件: funboost\core\cli\__init__.py
```python

```

### 代码文件: funboost\factories\broker_kind__publsiher_consumer_type_map.py
```python
import typing

from funboost.publishers.empty_publisher import EmptyPublisher
from funboost.publishers.http_publisher import HTTPPublisher
from funboost.publishers.nats_publisher import NatsPublisher
from funboost.publishers.peewee_publisher import PeeweePublisher
from funboost.publishers.redis_publisher_lpush import RedisPublisherLpush
from funboost.publishers.redis_publisher_priority import RedisPriorityPublisher
from funboost.publishers.redis_pubsub_publisher import RedisPubSubPublisher
from funboost.publishers.tcp_publisher import TCPPublisher
from funboost.publishers.txt_file_publisher import TxtFilePublisher
from funboost.publishers.udp_publisher import UDPPublisher
from funboost.publishers.zeromq_publisher import ZeroMqPublisher
from funboost.publishers.kafka_publisher import KafkaPublisher
from funboost.publishers.local_python_queue_publisher import LocalPythonQueuePublisher
from funboost.publishers.mongomq_publisher import MongoMqPublisher

from funboost.publishers.persist_queue_publisher import PersistQueuePublisher

from funboost.publishers.rabbitmq_pika_publisher import RabbitmqPublisher

from funboost.publishers.redis_publisher import RedisPublisher
from funboost.publishers.rocketmq_publisher import RocketmqPublisher
from funboost.publishers.redis_stream_publisher import RedisStreamPublisher
from funboost.publishers.mqtt_publisher import MqttPublisher
from funboost.publishers.httpsqs_publisher import HttpsqsPublisher

from funboost.consumers.empty_consumer import EmptyConsumer
from funboost.consumers.redis_consumer_priority import RedisPriorityConsumer
from funboost.consumers.redis_pubsub_consumer import RedisPbSubConsumer
from funboost.consumers.http_consumer import HTTPConsumer
from funboost.consumers.kafka_consumer import KafkaConsumer
from funboost.consumers.local_python_queue_consumer import LocalPythonQueueConsumer
from funboost.consumers.mongomq_consumer import MongoMqConsumer
from funboost.consumers.nats_consumer import NatsConsumer

from funboost.consumers.peewee_conusmer import PeeweeConsumer
from funboost.consumers.persist_queue_consumer import PersistQueueConsumer
from funboost.consumers.rabbitmq_pika_consumer import RabbitmqConsumer

from funboost.consumers.redis_brpoplpush_consumer import RedisBrpopLpushConsumer
from funboost.consumers.redis_consumer import RedisConsumer
from funboost.consumers.redis_consumer_ack_able import RedisConsumerAckAble
from funboost.consumers.rocketmq_consumer import RocketmqConsumer
from funboost.consumers.redis_stream_consumer import RedisStreamConsumer
from funboost.consumers.tcp_consumer import TCPConsumer
from funboost.consumers.txt_file_consumer import TxtFileConsumer
from funboost.consumers.udp_consumer import UDPConsumer
from funboost.consumers.zeromq_consumer import ZeroMqConsumer
from funboost.consumers.mqtt_consumer import MqttConsumer
from funboost.consumers.httpsqs_consumer import HttpsqsConsumer
from funboost.consumers.redis_consumer_ack_using_timeout import RedisConsumerAckUsingTimeout

from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.constant import BrokerEnum

broker_kind__publsiher_consumer_type_map = {


    BrokerEnum.REDIS: (RedisPublisher, RedisConsumer),
    BrokerEnum.MEMORY_QUEUE: (LocalPythonQueuePublisher, LocalPythonQueueConsumer),
    BrokerEnum.RABBITMQ_PIKA: (RabbitmqPublisher, RabbitmqConsumer),
    BrokerEnum.MONGOMQ: (MongoMqPublisher, MongoMqConsumer),
    BrokerEnum.PERSISTQUEUE: (PersistQueuePublisher, PersistQueueConsumer),
    BrokerEnum.KAFKA: (KafkaPublisher, KafkaConsumer),
    BrokerEnum.REDIS_ACK_ABLE: (RedisPublisher, RedisConsumerAckAble),
    BrokerEnum.REDIS_PRIORITY: (RedisPriorityPublisher, RedisPriorityConsumer),
    BrokerEnum.ROCKETMQ: (RocketmqPublisher, RocketmqConsumer),
    BrokerEnum.REDIS_STREAM: (RedisStreamPublisher, RedisStreamConsumer),
    BrokerEnum.ZEROMQ: (ZeroMqPublisher, ZeroMqConsumer),
    BrokerEnum.RedisBrpopLpush: (RedisPublisherLpush, RedisBrpopLpushConsumer),
    BrokerEnum.MQTT: (MqttPublisher, MqttConsumer),
    BrokerEnum.HTTPSQS: (HttpsqsPublisher, HttpsqsConsumer),
    BrokerEnum.UDP: (UDPPublisher, UDPConsumer),
    BrokerEnum.TCP: (TCPPublisher, TCPConsumer),
    BrokerEnum.HTTP: (HTTPPublisher, HTTPConsumer),
    BrokerEnum.NATS: (NatsPublisher, NatsConsumer),
    BrokerEnum.TXT_FILE: (TxtFilePublisher, TxtFileConsumer),
    BrokerEnum.PEEWEE: (PeeweePublisher, PeeweeConsumer),
    BrokerEnum.REDIS_PUBSUB: (RedisPubSubPublisher, RedisPbSubConsumer),
    BrokerEnum.REIDS_ACK_USING_TIMEOUT: (RedisPublisher, RedisConsumerAckUsingTimeout),
    BrokerEnum.EMPTY:(EmptyPublisher,EmptyConsumer),

}

for broker_kindx, cls_tuple in broker_kind__publsiher_consumer_type_map.items():
    cls_tuple[1].BROKER_KIND = broker_kindx


def register_custom_broker(broker_kind, publisher_class: typing.Type[AbstractPublisher], consumer_class: typing.Type[AbstractConsumer]):
    """
    动态注册中间件到框架中， 方便的增加中间件类型或者修改是自定义消费者逻辑。
    :param broker_kind:
    :param publisher_class:
    :param consumer_class:
    :return:
    """
    if not issubclass(publisher_class, AbstractPublisher):
        raise TypeError(f'publisher_class 必须是 AbstractPublisher 的子或孙类')
    if not issubclass(consumer_class, AbstractConsumer):
        raise TypeError(f'consumer_class 必须是 AbstractConsumer 的子或孙类')
    broker_kind__publsiher_consumer_type_map[broker_kind] = (publisher_class, consumer_class)
    consumer_class.BROKER_KIND = broker_kind


def regist_to_funboost(broker_kind: str):
    """
    延迟导入是因为funboost没有pip自动安装这些三方包，防止一启动就报错。
    这样当用户需要使用某些三方包中间件作为消息队列时候，按照import报错信息，用户自己去pip安装好。或者 pip install funboost[all] 一次性安装所有中间件。
    建议按照 https://github.com/ydf0509/funboost/blob/master/setup.py 中的 extra_brokers 和 install_requires 里面的版本号来安装三方包版本.
    """
    if broker_kind == BrokerEnum.RABBITMQ_AMQPSTORM:
        from funboost.publishers.rabbitmq_amqpstorm_publisher import RabbitmqPublisherUsingAmqpStorm
        from funboost.consumers.rabbitmq_amqpstorm_consumer import RabbitmqConsumerAmqpStorm
        register_custom_broker(BrokerEnum.RABBITMQ_AMQPSTORM, RabbitmqPublisherUsingAmqpStorm, RabbitmqConsumerAmqpStorm)

    if broker_kind == BrokerEnum.RABBITMQ_RABBITPY:
        from funboost.publishers.rabbitmq_rabbitpy_publisher import RabbitmqPublisherUsingRabbitpy
        from funboost.consumers.rabbitmq_rabbitpy_consumer import RabbitmqConsumerRabbitpy
        register_custom_broker(BrokerEnum.RABBITMQ_RABBITPY, RabbitmqPublisherUsingRabbitpy, RabbitmqConsumerRabbitpy)

    if broker_kind == BrokerEnum.PULSAR:
        from funboost.consumers.pulsar_consumer import PulsarConsumer
        from funboost.publishers.pulsar_publisher import PulsarPublisher
        register_custom_broker(BrokerEnum.PULSAR, PulsarPublisher, PulsarConsumer)

    if broker_kind == BrokerEnum.CELERY:
        from funboost.consumers.celery_consumer import CeleryConsumer
        from funboost.publishers.celery_publisher import CeleryPublisher
        register_custom_broker(BrokerEnum.CELERY, CeleryPublisher, CeleryConsumer)

    if broker_kind == BrokerEnum.NAMEKO:
        from funboost.consumers.nameko_consumer import NamekoConsumer
        from funboost.publishers.nameko_publisher import NamekoPublisher
        register_custom_broker(BrokerEnum.NAMEKO, NamekoPublisher, NamekoConsumer)

    if broker_kind == BrokerEnum.SQLACHEMY:
        from funboost.consumers.sqlachemy_consumer import SqlachemyConsumer
        from funboost.publishers.sqla_queue_publisher import SqlachemyQueuePublisher
        register_custom_broker(BrokerEnum.SQLACHEMY, SqlachemyQueuePublisher, SqlachemyConsumer)

    if broker_kind == BrokerEnum.DRAMATIQ:
        from funboost.consumers.dramatiq_consumer import DramatiqConsumer
        from funboost.publishers.dramatiq_publisher import DramatiqPublisher
        register_custom_broker(BrokerEnum.DRAMATIQ, DramatiqPublisher, DramatiqConsumer)

    if broker_kind == BrokerEnum.HUEY:
        from funboost.consumers.huey_consumer import HueyConsumer
        from funboost.publishers.huey_publisher import HueyPublisher
        register_custom_broker(BrokerEnum.HUEY, HueyPublisher, HueyConsumer)

    if broker_kind == BrokerEnum.KAFKA_CONFLUENT:
        from funboost.consumers.kafka_consumer_manually_commit import KafkaConsumerManuallyCommit
        from funboost.publishers.confluent_kafka_publisher import ConfluentKafkaPublisher
        register_custom_broker(BrokerEnum.KAFKA_CONFLUENT, ConfluentKafkaPublisher, KafkaConsumerManuallyCommit)

    if broker_kind == BrokerEnum.KAFKA_CONFLUENT_SASlPlAIN:
        from funboost.consumers.kafka_consumer_manually_commit import SaslPlainKafkaConsumer
        from funboost.publishers.confluent_kafka_publisher import SaslPlainKafkaPublisher
        register_custom_broker(broker_kind, SaslPlainKafkaPublisher, SaslPlainKafkaConsumer)

    if broker_kind == BrokerEnum.RQ:
        from funboost.consumers.rq_consumer import RqConsumer
        from funboost.publishers.rq_publisher import RqPublisher
        register_custom_broker(broker_kind, RqPublisher, RqConsumer)

    if broker_kind == BrokerEnum.KOMBU:
        from funboost.consumers.kombu_consumer import KombuConsumer
        from funboost.publishers.kombu_publisher import KombuPublisher
        register_custom_broker(broker_kind, KombuPublisher, KombuConsumer)

    if broker_kind == BrokerEnum.NSQ:
        from funboost.publishers.nsq_publisher import NsqPublisher
        from funboost.consumers.nsq_consumer import NsqConsumer
        register_custom_broker(broker_kind, NsqPublisher, NsqConsumer)


if __name__ == '__main__':
    import sys

    print(sys.modules)

```

### 代码文件: funboost\factories\consumer_factory.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:19


from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.func_params_model import BoosterParams


def get_consumer(boost_params: BoosterParams) -> AbstractConsumer:
    """
    :param args: 入参是AbstractConsumer的入参
    :param broker_kind:
    :param kwargs:
    :return:
    """
    from funboost.factories.broker_kind__publsiher_consumer_type_map import broker_kind__publsiher_consumer_type_map, regist_to_funboost
    regist_to_funboost(boost_params.broker_kind)  # 动态注册中间件到框架是为了延迟导入，用户没安装不需要的第三方包不报错。

    if boost_params.broker_kind not in broker_kind__publsiher_consumer_type_map:
        raise ValueError(f'设置的中间件种类不正确,你设置的值是 {boost_params.broker_kind} ')
    consumer_cls = broker_kind__publsiher_consumer_type_map[boost_params.broker_kind][1]
    if not boost_params.consumer_override_cls:
        return consumer_cls(boost_params)
    else:
        ConsumerClsOverride = type(f'{consumer_cls.__name__}__{boost_params.consumer_override_cls.__name__}', (boost_params.consumer_override_cls, consumer_cls, AbstractConsumer), {})
        # class ConsumerClsOverride(boost_params.consumer_override_cls, consumer_cls, AbstractConsumer):
        #     pass

        return ConsumerClsOverride(boost_params)

```

### 代码文件: funboost\factories\publisher_factotry.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:16
import copy

from typing import Callable
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.core.func_params_model import PublisherParams


# broker_kind__publisher_type_map

def get_publisher(publisher_params: PublisherParams) -> AbstractPublisher:
    """
    :param queue_name:
    :param log_level_int:
    :param logger_prefix:
    :param is_add_file_handler:
    :param clear_queue_within_init:
    :param is_add_publish_time:是否添加发布时间，以后废弃，都添加。
    :param consuming_function:消费函数，为了做发布时候的函数入参校验用的，如果不传则不做发布任务的校验，
               例如add 函数接收x，y入参，你推送{"x":1,"z":3}就是不正确的，函数不接受z参数。
    :param broker_kind: 中间件或使用包的种类。
    :param broker_exclusive_config 加上一个不同种类中间件非通用的配置,不同中间件自身独有的配置，不是所有中间件都兼容的配置，因为框架支持30种消息队列，消息队列不仅仅是一般的先进先出queue这么简单的概念，
           例如kafka支持消费者组，rabbitmq也支持各种独特概念例如各种ack机制 复杂路由机制，每一种消息队列都有独特的配置参数意义，可以通过这里传递。

    :return:
    """

    from funboost.factories.broker_kind__publsiher_consumer_type_map import broker_kind__publsiher_consumer_type_map, regist_to_funboost
    broker_kind = publisher_params.broker_kind
    regist_to_funboost(broker_kind)  # 动态注册中间件到框架是为了延迟导入，用户没安装不需要的第三方包不报错。
    if broker_kind not in broker_kind__publsiher_consumer_type_map:
        raise ValueError(f'设置的中间件种类不正确,你设置的值是 {broker_kind} ')
    publisher_cls = broker_kind__publsiher_consumer_type_map[broker_kind][0]
    if not publisher_params.publisher_override_cls:
        return publisher_cls(publisher_params)
    else:
        PublsiherClsOverride = type(f'{publisher_cls.__name__}__{publisher_params.publisher_override_cls.__name__}', (publisher_params.publisher_override_cls, publisher_cls, AbstractPublisher), {})
        # class PublsiherClsOverride(publisher_params.publisher_override_cls, publisher_cls, AbstractPublisher):
        #     pass

        return PublsiherClsOverride(publisher_params)


```

### 代码文件: funboost\factories\__init__.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:17

"""
工厂模式，通过broker_kind来生成不同中间件类型的消费者和发布者。
"""
```

### 代码文件: funboost\function_result_web\app.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/9/18 0018 14:46
import threading

import sys


import os
# print("PYTHONPATH:", os.environ.get('PYTHONPATH'))


import datetime
import json
import traceback

from funboost.core.func_params_model import PriorityConsumingControlConfig

"""
pip install Flask flask_bootstrap  flask_wtf  wtforms flask_login       
"""
from flask import render_template, Flask, request, url_for, jsonify, flash, redirect
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_login import login_user, logout_user, login_required, LoginManager, UserMixin

import nb_log
from funboost import nb_print,ActiveCousumerProcessInfoGetter,BoostersManager,PublisherParams,RedisMixin
from funboost.function_result_web.functions import get_cols, query_result, get_speed, Statistic
from funboost.function_result_web import functions as app_functions
from funboost.core.active_cousumer_info_getter import QueueConusmerParamsGetter
from funboost.constant import RedisKeys

app = Flask(__name__)
app.secret_key = 'mtfy54321'
app.config['JSON_AS_ASCII'] = False
bootstrap = Bootstrap(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.login_message = 'Access denied.'
login_manager.init_app(app)



class User(UserMixin):
    pass


users = [
    {'id': 'Tom', 'user_name': 'Tom', 'password': '111111'},
    {'id': 'user', 'user_name': 'user', 'password': 'mtfy123'},
    {'id': 'admin', 'user_name': 'admin', 'password': '123456'}
]


nb_log.get_logger('flask',log_filename='flask.log')
nb_log.get_logger('werkzeug',log_filename='werkzeug.log')

def query_user(user_name):
    for user in users:
        if user_name == user['user_name']:
            return user


@login_manager.user_loader
def load_user(user_id):
    if query_user(user_id) is not None:
        curr_user = User()
        curr_user.id = user_id
        return curr_user


class LoginForm(FlaskForm):
    user_name = StringField(u'用户名', validators=[DataRequired(), Length(3, 64)])
    password = PasswordField(u'密码', validators=[DataRequired(), Length(3, 64)])
    remember_me = BooleanField(u'记住我')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':

        # nb_print(form.validate())
        # nb_print(form.password.data)
        # nb_print(form.user_name.data)
        # nb_print(form.user_name.errors)
        # nb_print(form.password.errors)
        if form.validate_on_submit():
            user = query_user(form.user_name.data)
            if user is not None and request.form['password'] == user['password']:
                curr_user = User()
                curr_user.id = form.user_name.data

                # 通过Flask-Login的login_user方法登录用户
                nb_print(form.remember_me.data)
                login_user(curr_user, remember=form.remember_me.data, duration=datetime.timedelta(days=7))

                return redirect(url_for('index'))

            flash('用户名或密码错误', category='error')

            # if form.user_name.data == 'user' and form.password.data == 'mtfy123':
            #     login_user(form.user_name.data, form.remember_me.data)
            #     return redirect(url_for('index'))
            # else:
            #     flash('账号或密码错误',category='error')
            #     return render_template('login4.html', form=form)

    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    page = request.args.get('page')
    return render_template('index.html', page=page)


@app.route('/query_cols')
@login_required
def query_cols_view():
    nb_print(request.args)
    return jsonify(get_cols(request.args.get('col_name_search')))


@app.route('/query_result')
@login_required
def query_result_view():

    return jsonify(query_result(**request.values.to_dict()))


@app.route('/speed_stats')
@login_required
def speed_stats():
    return jsonify(get_speed(**request.values.to_dict()))


@app.route('/speed_statistic_for_echarts')
@login_required
def speed_statistic_for_echarts():
    stat = Statistic(request.args.get('col_name'))
    stat.build_result()
    return jsonify(stat.result)

@app.route('/tpl/<template>')
@login_required
def serve_template(template):
    # 安全检查：确保只能访问templates目录下的html文件
    if not template.endswith('.html'):
        return 'Invalid request', 400
    try:
        return render_template(template)
    except Exception as e:
        return f'Template not found: {template}', 404


@app.route('/running_consumer/hearbeat_info_by_queue_name')
def hearbeat_info_by_queue_name():
    if request.args.get('queue_name') in ('所有',None):
        info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name()
        ret_list = []
        for queue_name,dic in info_map.items():
            ret_list.extend(dic)
        return jsonify(ret_list)
    else:
        return jsonify(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_queue_name(request.args.get('queue_name')))
    
        

@app.route('/running_consumer/hearbeat_info_by_ip')
def hearbeat_info_by_ip():
    if request.args.get('ip') in ('所有',None):
        info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_ip()
        ret_list = []
        for queue_name,dic in info_map.items():
            ret_list.extend(dic)
        return jsonify(ret_list)
    else:
        return jsonify(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_ip(request.args.get('ip')))


@app.route('/running_consumer/hearbeat_info_partion_by_queue_name')
def hearbeat_info_partion_by_queue_name():
    info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name()
    ret_list = []
    total_count = 0
    for k,v in info_map.items():
        ret_list.append({'collection_name':k,'count':len(v)})
        total_count +=len(v)
    ret_list = sorted(ret_list, key=lambda x: x['collection_name'])
    ret_list.insert(0,{'collection_name':'所有','count':total_count})
    return jsonify(ret_list)

@app.route('/running_consumer/hearbeat_info_partion_by_ip')
def hearbeat_info_partion_by_ip():
    info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_ip()
    ret_list = []
    total_count = 0
    for k,v in info_map.items():
        ret_list.append({'collection_name':k,'count':len(v)})
        total_count +=len(v)
    ret_list = sorted(ret_list, key=lambda x: x['collection_name'])
    ret_list.insert(0,{'collection_name':'所有','count':total_count})
    print(ret_list)
    return jsonify(ret_list)


@app.route('/queue/params_and_active_consumers')
def get_queue_params_and_active_consumers():
    return jsonify(QueueConusmerParamsGetter().get_queue_params_and_active_consumers())




@app.route('/queue/clear/<broker_kind>/<queue_name>',methods=['POST'])
def clear_queue(broker_kind,queue_name):
    publisher = BoostersManager.get_cross_project_publisher(PublisherParams(queue_name=queue_name, broker_kind=broker_kind, publish_msg_log_use_full_msg=True))
    publisher.clear()
    return jsonify({'success':True})

@app.route('/queue/pause/<queue_name>', methods=['POST'])
def pause_cousume(queue_name):
    RedisMixin().redis_db_frame.hset(RedisKeys.REDIS_KEY_PAUSE_FLAG, queue_name,'1')
    return jsonify({'success':True})

@app.route('/queue/resume/<queue_name>',methods=['POST'])
def resume_consume(queue_name):
    RedisMixin().redis_db_frame.hset(RedisKeys.REDIS_KEY_PAUSE_FLAG, queue_name,'0')
    return jsonify({'success':True})

@app.route('/queue/get_msg_num_all_queues',methods=['GET'])
def get_msg_num_all_queues():
    """这个是通过消费者周期每隔10秒上报到redis的，性能好。不需要实时获取每个消息队列，直接从redis读取所有队列的消息数量"""
    return jsonify(QueueConusmerParamsGetter().get_msg_num(ignore_report_ts=True))

@app.route('/queue/message_count/<broker_kind>/<queue_name>')
def get_message_count(broker_kind,queue_name):
    """这个是实时获取每个消息队列的消息数量，性能差，但是可以实时获取每个消息队列的消息数量"""
    queue_params = QueueConusmerParamsGetter().get_queue_params()
    for queue_namex,params in queue_params.items():
        if params['broker_kind'] == broker_kind and queue_namex == queue_name:
            publisher = BoostersManager.get_cross_project_publisher(
                PublisherParams(queue_name=queue_name, 
                                 broker_kind=broker_kind,
                                 broker_exclusive_config=params['broker_exclusive_config'],
                                 publish_msg_log_use_full_msg=True))
            return jsonify({'count':publisher.get_message_count(),'success':True})
    return jsonify({'success':False,'msg':f'队列{queue_name}不存在'})

@app.route('/queue/get_time_series_data/<queue_name>',methods=['GET'])
def get_time_series_data_by_queue_name(queue_name,):
    """_summary_

    Args:
        queue_name (_type_): _description_

    Returns:
        _type_: _description_
    
    返回例如  [{'report_data': {'pause_flag': -1, 'msg_num_in_broker': 936748, 'history_run_count': '150180', 'history_run_fail_count': '46511', 'all_consumers_last_x_s_execute_count': 7, 'all_consumers_last_x_s_execute_count_fail': 0, 'all_consumers_last_x_s_avarage_function_spend_time': 3.441, 'all_consumers_avarage_function_spend_time_from_start': 4.598, 'all_consumers_total_consume_count_from_start': 1296, 'all_consumers_total_consume_count_from_start_fail': 314, 'report_ts': 1749617360.597841}, 'report_ts': 1749617360.597841}, {'report_data': {'pause_flag': -1, 'msg_num_in_broker': 936748, 'history_run_count': '150184', 'history_run_fail_count': '46514', 'all_consumers_last_x_s_execute_count': 7, 'all_consumers_last_x_s_execute_count_fail': 0, 'all_consumers_last_x_s_avarage_function_spend_time': 3.441, 'all_consumers_avarage_function_spend_time_from_start': 4.599, 'all_consumers_total_consume_count_from_start': 1299, 'all_consumers_total_consume_count_from_start_fail': 316, 'report_ts': 1749617370.628166}, 'report_ts': 1749617370.628166}] 
    """
    return jsonify(QueueConusmerParamsGetter().get_time_series_data_by_queue_name(
        queue_name,request.args.get('start_ts'),request.args.get('end_ts')))
        
@app.route('/rpc/rpc_call',methods=['POST'])
def rpc_call():
    """
    class MsgItem(BaseModel):
        queue_name: str  # 队列名
        msg_body: dict  # 消息体,就是boost函数的入参字典,例如 {"x":1,"y":2}
        need_result: bool = False  # 发布消息后,是否需要返回结果
        timeout: int = 60  # 等待结果返回的最大等待时间.


    class PublishResponse(BaseModel):
        succ: bool
        msg: str
        status_and_result: typing.Optional[dict] = None  # 消费函数的消费状态和结果.
        task_id:str
    """
    
    msg_item = request.get_json()
    return jsonify(app_functions.rpc_call(**msg_item))
    
@app.route('/rpc/get_result_by_task_id',methods=['GET'])
def get_result_by_task_id():
    res = app_functions.get_result_by_task_id(task_id=request.args.get('task_id'),
                                                          timeout=request.args.get('timeout') or 60)
    if res['status_and_result'] is None:
        return jsonify({'succ':False,'msg':'task_id不存在或者超时或者结果已经过期'})
    return jsonify(res)
   

def start_funboost_web_manager(host='0.0.0.0', port=27018,block=False):
    print('start_funboost_web_manager , sys.path :', sys.path)
    def _start_funboost_web_manager():
        app.run(debug=False, threaded=True, host=host, port=port)
    QueueConusmerParamsGetter().cycle_get_queue_params_and_active_consumers_and_report()
    if block is  True:
        _start_funboost_web_manager()
    else:
        threading.Thread(target=_start_funboost_web_manager).start()
        
        
        
if __name__ == '__main__':
    # app.jinja_env.auto_reload = True
    # with app.test_request_context():
    #     print(url_for('query_cols_view'))
    QueueConusmerParamsGetter().cycle_get_queue_params_and_active_consumers_and_report(daemon=True)
    app.run(debug=False, threaded=True, host='0.0.0.0', port=27018)

    
    '''
    funboost web manager 启动方式：

    web代码在funboost包里面，所以可以直接使用命令行运行起来，不需要用户现亲自下载web代码就可以直接运行。
    
    第一步： 设置 PYTHONPATH 为你的项目根目录
    export PYTHONPATH=你的项目根目录 (这么做是为了这个web可以读取到你项目根目录下的 funboost_config.py里面的配置)
    (怎么设置环境变量应该不需要我来教，环境变量都没听说过太low了)
      例如 export PYTHONPATH=/home/ydf/codes/ydfhome
      或者 export PYTHONPATH=./   (./是相对路径，前提是已近cd到你的项目根目录了，也可以写绝对路径全路径)
      win cmd 设置环境变量语法是 set PYTHONPATH=/home/ydf/codes/ydfhome   
      win powershell 语法是  $env:PYTHONPATH = "/home/ydf/codes/ydfhome"   

    第二步： 启动flask app   
    win上这么做 python3 -m funboost.function_result_web.app 

    linux上可以这么做性能好一些，也可以按win的做。
    gunicorn -w 4 --threads=30 --bind 0.0.0.0:27018 funboost.function_result_web.app:app
    '''

```

### 代码文件: funboost\function_result_web\app_debug_start.py
```python


from funboost.core.active_cousumer_info_getter import QueueConusmerParamsGetter
from funboost.function_result_web.app import app


if __name__ == '__main__':
    QueueConusmerParamsGetter().cycle_get_queue_params_and_active_consumers_and_report(daemon=True)
    app.run(debug=True, threaded=True, host='0.0.0.0', port=27019)


```

### 代码文件: funboost\function_result_web\functions.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/9/19 0019 9:48
import datetime
import json
from pprint import pprint
import time
import copy
import traceback
from funboost import nb_print
from funboost.constant import RedisKeys
from funboost.core.booster import BoostersManager
from funboost.core.func_params_model import PriorityConsumingControlConfig, PublisherParams
from funboost.core.msg_result_getter import AsyncResult
from funboost.core.serialization import Serialization
from funboost.utils import time_util, decorators, LoggerMixin
from funboost.utils.mongo_util import MongoMixin
from funboost.utils.redis_manager import RedisMixin

# from test_frame.my_patch_frame_config import do_patch_frame_config
#
# do_patch_frame_config()




# print(db)
# print(type(db))
# print(db.list_collection_names())

def get_cols(col_name_search: str):
    db = MongoMixin().mongo_db_task_status
    if not col_name_search:
        collection_name_list = db.list_collection_names()
    else:
        collection_name_list = [collection_name for collection_name in db.list_collection_names() if col_name_search in collection_name]
    # return [{'collection_name': collection_name, 'count': db.get_collection(collection_name).find().count()} for collection_name in collection_name_list]
    return [{'collection_name': collection_name, 'count': db.get_collection(collection_name).count_documents({})} for collection_name in collection_name_list]
    # for collection_name in collection_list:
    #     if col_name_search in collection_name:
    #     print (collection,db[collection].find().count())


def query_result(col_name, start_time, end_time, is_success, function_params: str, page, ):
    query_kw = copy.copy(locals())
    t0 = time.time()
    if not col_name:
        return []
    db = MongoMixin().mongo_db_task_status
    condition = {
        'insert_time': {'$gt': time_util.DatetimeConverter(start_time).datetime_obj,
                        '$lt': time_util.DatetimeConverter(end_time).datetime_obj},
    }
    # condition = {
    #     'insert_time_str': {'$gt': start_time,
    #                     '$lt': end_time},
    # }
    if is_success in ('2', 2, True):
        condition.update({"success": True})
    elif is_success in ('3', 3, False):
        condition.update({"success": False})
    if function_params.strip():
        condition.update({'params_str': {'$regex': function_params.strip()}})
    # nb_print(col_name)
    # nb_print(condition)
    # results = list(db.get_collection(col_name).find(condition, ).sort([('insert_time', -1)]).skip(int(page) * 100).limit(100))
    # with decorators.TimerContextManager():
    results = list(db.get_collection(col_name).find(condition, {'insert_time': 0, 'utime': 0}).skip(int(page) * 100).limit(100))
    # nb_print(results)
    nb_print(time.time() -t0, query_kw)
    return results


def get_speed(col_name, start_time, end_time):
    db = MongoMixin().mongo_db_task_status
    condition = {
        'insert_time': {'$gt': time_util.DatetimeConverter(start_time).datetime_obj,
                        '$lt': time_util.DatetimeConverter(end_time).datetime_obj},
    }
    # condition = {
    #     'insert_time_str': {'$gt': time_util.DatetimeConverter(time.time() - 60).datetime_str},
    # }
    # nb_print(condition)
    with decorators.TimerContextManager():
        # success_num = db.get_collection(col_name).count({**{'success': True}, **condition})
        # fail_num = db.get_collection(col_name).count({**{'success': False}, **condition})
        success_num = db.get_collection(col_name).count_documents({**{'success': True,'run_status':'finish'}, **condition})
        fail_num = db.get_collection(col_name).count_documents({**{'success': False,'run_status':'finish'}, **condition})
        qps = (success_num + fail_num) / (time_util.DatetimeConverter(end_time).timestamp - time_util.DatetimeConverter(start_time).timestamp)
        return {'success_num': success_num, 'fail_num': fail_num, 'qps': round(qps, 1)}


class Statistic(LoggerMixin):
    def __init__(self, col_name):
        db = MongoMixin().mongo_db_task_status
        self.col = db.get_collection(col_name)
        self.result = {'recent_10_days': {'time_arr': [], 'count_arr': []},
                       'recent_24_hours': {'time_arr': [], 'count_arr': []},
                       'recent_60_minutes': {'time_arr': [], 'count_arr': []},
                       'recent_60_seconds': {'time_arr': [], 'count_arr': []}}

    def statistic_by_period(self, t_start: str, t_end: str):
        condition = {'insert_time': {'$gt': time_util.DatetimeConverter(t_start).datetime_obj,
                                                         '$lt': time_util.DatetimeConverter(t_end).datetime_obj}}
        
        # now = datetime.datetime.now()
        # start_time = now - datetime.timedelta(hours=1)
        # end_time = now
        # condition = {
        #     'insert_time': {
        #         '$gt': start_time,
        #         '$lt': end_time
        #     }
        # }
        count =  self.col.count_documents(condition)
        print(count,t_start,t_end,time_util.DatetimeConverter(t_start).datetime_obj.timestamp(),condition)
        return count

    def build_result(self):
        with decorators.TimerContextManager():
            for i in range(10):
                t1 = datetime.datetime.now() + datetime.timedelta(days=-(9 - i))
                t2 = datetime.datetime.now() + datetime.timedelta(days=-(8 - i))
                self.result['recent_10_days']['time_arr'].append(time_util.DatetimeConverter(t1).date_str)
                count = self.statistic_by_period(time_util.DatetimeConverter(t1).date_str + ' 00:00:00',
                                                 time_util.DatetimeConverter(t2).date_str + ' 00:00:00')
                self.result['recent_10_days']['count_arr'].append(count)

            for i in range(0, 24):
                t1 = datetime.datetime.now() + datetime.timedelta(hours=-(23 - i))
                t2 = datetime.datetime.now() + datetime.timedelta(hours=-(22 - i))
                self.result['recent_24_hours']['time_arr'].append(t1.strftime('%Y-%m-%d %H:00:00'))
                # hour1_str = f'0{i}' if i < 10 else i
                count = self.statistic_by_period(t1.strftime('%Y-%m-%d %H:00:00'),
                                                 t2.strftime('%Y-%m-%d %H:00:00'))
                self.result['recent_24_hours']['count_arr'].append(count)

            for i in range(0, 60):
                t1 = datetime.datetime.now() + datetime.timedelta(minutes=-(59 - i))
                t2 = datetime.datetime.now() + datetime.timedelta(minutes=-(58 - i))
                self.result['recent_60_minutes']['time_arr'].append(t1.strftime('%Y-%m-%d %H:%M:00'))
                count = self.statistic_by_period(t1.strftime('%Y-%m-%d %H:%M:00'),
                                                 t2.strftime('%Y-%m-%d %H:%M:00'))
                self.result['recent_60_minutes']['count_arr'].append(count)

            for i in range(0, 60):
                t1 = datetime.datetime.now() + datetime.timedelta(seconds=-(59 - i))
                t2 = datetime.datetime.now() + datetime.timedelta(seconds=-(58 - i))
                self.result['recent_60_seconds']['time_arr'].append(t1.strftime('%Y-%m-%d %H:%M:%S'))
                count = self.statistic_by_period(t1.strftime('%Y-%m-%d %H:%M:%S'),
                                                 t2.strftime('%Y-%m-%d %H:%M:%S'))
                self.result['recent_60_seconds']['count_arr'].append(count)

def rpc_call(queue_name, msg_body, need_result, timeout):
  
    status_and_result = None
    task_id = None
    try:
        boost_params_json = RedisMixin().redis_db_frame.hget(RedisKeys.FUNBOOST_QUEUE__CONSUMER_PARAMS,queue_name)
        boost_params_dict = Serialization.to_dict(boost_params_json)
        broker_kind = boost_params_dict['broker_kind']
        publisher = BoostersManager.get_cross_project_publisher(PublisherParams(queue_name=queue_name,
                                                                            broker_kind=broker_kind, 
                                                                            publish_msg_log_use_full_msg=True))
    
        if need_result:
            # if booster.boost_params.is_using_rpc_mode is False:
            #     raise ValueError(f' need_result 为true,{booster.queue_name} 队列消费者 需要@boost设置支持rpc模式')
            
            async_result: AsyncResult =  publisher.publish(msg_body,priority_control_config=PriorityConsumingControlConfig(is_using_rpc_mode=True))
            async_result.set_timeout(timeout)
            status_and_result = async_result.status_and_result
            # print(status_and_result)
            task_id = async_result.task_id
        else:
            async_result =publisher.publish(msg_body)
            task_id = async_result.task_id
        if status_and_result['success'] is False:
            return dict(succ=False, msg=f'{queue_name} 队列,消息发布成功,但是函数执行失败', 
                            status_and_result=status_and_result,task_id=task_id)
        return dict(succ=True, msg=f'{queue_name} 队列,消息发布成功', 
                            status_and_result=status_and_result,task_id=task_id)
    except Exception as e:
        return dict(succ=False, msg=f'{queue_name} 队列,消息发布失败 {type(e)} {e} {traceback.format_exc()}',
                               status_and_result=status_and_result,task_id=task_id)
    

def get_result_by_task_id(task_id,timeout):
    async_result = AsyncResult(task_id)
    async_result.set_timeout(timeout)
    status_and_result = async_result.status_and_result
    if status_and_result is None:
        return dict(succ=False, msg=f'{task_id} 不存在 或 超时 或 结果已过期', 
                        status_and_result=status_and_result,task_id=task_id)
    if status_and_result['success'] is False:
        return dict(succ=False, msg=f'{task_id} 执行失败', 
                        status_and_result=status_and_result,task_id=task_id)
    return dict(succ=True, msg=f'task_id:{task_id} 获取结果成功', 
                            status_and_result=status_and_result,task_id=task_id)
        
    
     

if __name__ == '__main__':
    # print(get_cols('4'))
    # pprint(query_result('queue_test54_task_status', '2019-09-15 00:00:00', '2019-09-25 00:00:00', True, '999', 0))
    # print(json.dumps(query_result(**{'col_name': 'queue_test56', 'start_time': '2019-09-18 16:03:29', 'end_time': '2019-09-21 16:03:29', 'is_success': '1', 'function_params': '', 'page': '0'}))[:1000])
    # nb_print(get_speed_last_minute('queue_test54'))

    # nb_print(get_speed('queue_test56', '2019-09-18 16:03:29', '2019-09-23 16:03:29'))
    # stat = Statistic('queue_test_f01t')
    # stat.build_result()
    # nb_print(stat.result)
    
    # res = rpc_call('queue_test_g02t',{'x':1,'y':2},True,60)
    
    res = get_result_by_task_id('3232',60)
    print(res)
    
    

```

### 代码文件: funboost\function_result_web\templates\about.html
```python
<!DOCTYPE html>
<html lang="en">
<head>
    <link href="{{ url_for('static',filename='css_cdn/twitter-bootstrap/3.3.7/css/bootstrap.min.css') }}" rel="stylesheet">
    <style>
        body {
            background-color: #f5f5f5;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 30px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }
        .info-block {
            background-color: #fff;
            border-left: 4px solid #3498db;
            border-radius: 4px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .highlight {
            background-color: #f8f9fa;
            padding: 3px 6px;
            border-radius: 3px;
            color: #e74c3c;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>funboost web manager 说明</h1>
        <div class="info-block">
            <h4>1. 函数结果 和 消费速率</h4>
            <p>
                数据是从 MongoDB 中获取的。<br>
                用户需要设置 <span class="highlight">@boost</span> 的 <span class="highlight">function_result_status_persistance_conf</span>，
                保存消费结果到 mongo 后，网页才能获取到对应的 queue 的消费结果。
            </p>
        </div>
        
        <div class="info-block">
            <h4>2. 运行中消费者 和 队列操作</h4>
            <p>
                数据是从 Redis 消费者心跳获取的。<br>
                用户需要设置 <span class="highlight">@boost</span> 的 <span class="highlight">is_send_consumer_hearbeat_to_redis = True</span>，
                消费者心跳发送到 Redis 后，网页才能获取到对应的 queue 是否正在消费，在哪些机器消费。<br><br>

                <span style="color:#FFA500"> 请不要在 <span class="highlight"> funboost_config.py </span> 配置文件的 <span class="highlight"> BrokerConnConfig.REDIS_DB </span> 的 db 中放太多其他用途的缓存key，因为有redis scan命令操作。 </span>
            </p>
        </div>
    </div>
</body>
</html>
```

### 代码文件: funboost\function_result_web\templates\conusme_speed.html
```python
<!DOCTYPE html>
<html lang="zh">

<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>pytho万能分布式函数调度框架</title>
    <link href="{{ url_for('static',filename='css_cdn/twitter-bootstrap/3.3.7/css/bootstrap.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static',filename='css_cdn/font-awesome/4.7.0/css/font-awesome.min.css') }}" rel="stylesheet">
    <link rel="stylesheet"
        href="{{ url_for('static',filename='css_cdn/bootstrap-datetimepicker/4.17.47/css/bootstrap-datetimepicker.min.css') }}">
    <link rel="stylesheet" href="{{ url_for('static',filename='assets/css/jquery.mCustomScrollbar.min.css') }}">
    <link rel="stylesheet" href="{{ url_for('static',filename='assets/css/custom.css') }}">

    <!-- 在其他 link 标签后添加 -->
    <link href="{{ url_for('static',filename='css_cdn/select2/4.0.13/css/select2.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static',filename='css/content_page_style.css') }}" rel="stylesheet">


    <script src="{{ url_for('static',filename='js/jquery-1.11.0.min.js') }}" type="text/javascript"></script>
    <!-- <script src="https://cdn.bootcdn.net/ajax/libs/jquery/1.11.0/jquery.min.js"></script> -->
    <!-- 在其他 script 标签后添加 -->
    <!-- <script src="https://cdn.bootcdn.net/ajax/libs/select2/4.0.13/js/select2.min.js"></script> -->
    <script src="{{ url_for('static',filename='/js/select2.min.js') }}"></script>
    <script src="{{ url_for('static',filename='js_cdn/bootstrap/3.3.7/js/bootstrap.min.js') }}"></script>


    <script src="{{ url_for('static',filename='js/moment-with-locales.min.js') }}"></script>
    <script src="{{ url_for('static',filename='js/bootstrap-datetimepicker.min.js') }}"></script>
    <!-- <script src="https://cdn.bootcss.com/bootstrap-datetimepicker/4.17.47/js/bootstrap-datetimepicker.min.js"></script> -->
    <!-- <script type="text/javascript" src="https://cdn.bootcss.com/echarts/3.3.0/echarts.js"></script> -->
    <script type="text/javascript" src="{{ url_for('static',filename='js/echarts.min.js') }}"></script>

    <script src="{{ url_for('static',filename='assets/js/jquery.mCustomScrollbar.concat.min.js') }}"></script>
    <script src="{{ url_for('static',filename='assets/js/custom.js') }}"></script>


    </style>
</head>

<body>





    <!-- <li><a href="{{url_for('logout')}}">退出</a></li> -->

    <!-- 添加固定导航栏
    <nav class="navbar navbar-default navbar-fixed-top" style="min-height: 40px;">
        <div class="container-fluid">
            <div class="navbar-header pull-right">
                <a href="{{url_for('logout')}}" class="btn btn-danger" style="margin: 4px 15px;">
                    <i class="fa fa-sign-out"></i> 退出
                </a>
            </div>
        </div>
    </nav> -->

    <!-- 删除原来的退出按钮 -->
    <!-- 调整主容器的上边距 -->
    <div class="container-fluid" style="margin-top: 5px;">
        <div style="margin-top: 5px;">
            <form class="form-inline" role="form" style="float: left">
                <div class="form-group ">
                    <label for="col_name_search">队列名称：</label>
                    <select class="form-control" id="col_name_search">
                        <option value="">请选择队列...</option>
                    </select>
                </div>
                <button type="button" class="btn btn-default marginLeft20" onclick="statistic()">生成消费速率统计图</button>
            </form>
        </div>
        <div id=echartsArea style="display: block">
            <div id="st4" style="width: 100%;height:600px;margin-top:60px;"></div>
            <div id="st3" style="width: 100%;height:600px;margin-top:60px;"></div>
            <div id="st2" style="width: 100%;height:600px;margin-top:60px;"></div>
            <div id="st1" style="width: 100%;height:600px;margin-top:60px;"></div>
        </div>
    </div>






    <script>

        // 在现有的变量声明后添加
        var allQueues = [];  // 存储所有队列数据
        var currentColName;

        // 页面加载完成后立即获取所有队列
        $(document).ready(function () {
            $.ajax({
                url: "{{ url_for('query_cols_view')}}",
                data: { col_name_search: '' },
                async: true,
                success: function (result) {
                    allQueues = result;
                    var html = '<option value="">请选择队列...</option>';
                    for (var item of result) {
                        html += '<option value="' + item.collection_name + '">' +
                            item.collection_name + '&nbsp;&nbsp;&nbsp;&nbsp;(result_count:' + item.count + ')</option>';
                    }
                    $("#col_name_search").html(html);

                    // 初始化选择框的搜索功能
                    $("#col_name_search").select2({
                        placeholder: "请输入队列名称搜索...",
                        allowClear: true,
                        width: '500px'
                    });

                    // 监听选择变化
                    $("#col_name_search").on('change', function () {
                        var selectedQueue = $(this).val();
                        console.log("Selected queue:", selectedQueue);
                        currentColName = selectedQueue;
                        // if(selectedQueue) {
                        //     queryResult(selectedQueue, 0, true);
                        // }
                    });
                }
            });
        });




        function statistic() {
            if (currentColName === undefined) {
                return;
            }

            $('#echartsInfoTex').html('生成统计表中，需要一段时间。。。。');
            $("#echartsInfoTex").css('display', 'block');
            $("#echartsArea").css('display', 'block');
            // stopRun();
            $.ajax({
                url: "{{ url_for('speed_statistic_for_echarts')}}", data: {
                    col_name: currentColName
                }, async: true, success: function (result, status) {
                    // var msg = '{0}队列,最近一分钟内运行成功了{1}次,失败了{2}次'.format(currentColName, result.success_num, result.fail_num);
                    console.info(result);
                    _buildOneChart('st1', '最近10天的消费情况', '运行次数', result['recent_10_days']['time_arr'], result['recent_10_days']['count_arr']);
                    _buildOneChart('st2', '最近24小时的消费情况', '运行次数', result['recent_24_hours']['time_arr'], result['recent_24_hours']['count_arr']);
                    _buildOneChart('st3', '最近60分钟的消费情况', '运行次数', result['recent_60_minutes']['time_arr'], result['recent_60_minutes']['count_arr']);
                    _buildOneChart('st4', '最近60秒的消费情况', '运行次数', result['recent_60_seconds']['time_arr'], result['recent_60_seconds']['count_arr']);
                    $("#echartsInfoTex").css('display', 'none');

                    // $('#top_text').text(msg);
                }
            });


        }

        function _buildOneChart(elementId, titelText, legendData, xData, yData) {

            var myChart = echarts.init(document.getElementById(elementId));



            // 指定图表的配置项和数据
            var option = {
                title: {
                    text: titelText
                },
                tooltip: {},
                legend: {
                    data: [legendData]
                },

                xAxis: {
                    type: 'category',
                    data: xData,
                    axisLabel: {
                        rotate: 90,

                        interval: 0,

                        // formatter: function (value) {
                        //
                        //     console.info(value);
                        //     var v =  value.split("").join("\n");
                        //     console.info(v);
                        //     return v;
                        // },

                        // show: true, interval: 'auto', inside: false, rotate: 90, margin: 8, formatter: null, showMinLabel: null, showMaxLabel: null,

                    },

                },

                yAxis: {},
                series: [{
                    name: legendData,
                    type: 'bar',
                    data: yData
                }]
            };

            // 使用刚指定的配置项和数据显示图表。
            myChart.setOption(option);
            console.info(elementId);


        }


    </script>
</body>

</html>
```

### 代码文件: funboost\function_result_web\templates\fun_result_table.html
```python
<!DOCTYPE html>
<html lang="zh">

<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>pytho万能分布式函数调度框架</title>
    <link href="{{ url_for('static',filename='css_cdn/twitter-bootstrap/3.3.7/css/bootstrap.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static',filename='css_cdn/font-awesome/4.7.0/css/font-awesome.min.css') }}" rel="stylesheet">
    <link rel="stylesheet"
        href="{{ url_for('static',filename='css_cdn/bootstrap-datetimepicker/4.17.47/css/bootstrap-datetimepicker.min.css') }}">
    <link rel="stylesheet" href="{{ url_for('static',filename='assets/css/jquery.mCustomScrollbar.min.css') }}">
    <link rel="stylesheet" href="{{ url_for('static',filename='assets/css/custom.css') }}">
    <!-- 在其他 link 标签后添加 -->
    <link href="{{ url_for('static',filename='css_cdn/select2/4.0.13/css/select2.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static',filename='css/content_page_style.css') }}" rel="stylesheet">


    <script src="{{ url_for('static',filename='js/jquery-1.11.0.min.js') }}" type="text/javascript"></script>
    <!-- <script src="https://cdn.bootcdn.net/ajax/libs/jquery/1.11.0/jquery.min.js"></script> -->
    <!-- 在其他 script 标签后添加 -->
    <!-- <script src="https://cdn.bootcdn.net/ajax/libs/select2/4.0.13/js/select2.min.js"></script> -->
    <script src="{{ url_for('static',filename='/js/select2.min.js') }}"></script>
    <script src="{{ url_for('static',filename='js_cdn/bootstrap/3.3.7/js/bootstrap.min.js') }}"></script>


    <script src="{{ url_for('static',filename='js/moment-with-locales.min.js') }}"></script>
    <script src="{{ url_for('static',filename='js/bootstrap-datetimepicker.min.js') }}"></script>
    <!-- <script src="https://cdn.bootcss.com/bootstrap-datetimepicker/4.17.47/js/bootstrap-datetimepicker.min.js"></script> -->
    <!-- <script type="text/javascript" src="https://cdn.bootcss.com/echarts/3.3.0/echarts.js"></script> -->
    <script type="text/javascript" src="{{ url_for('static',filename='js/echarts.min.js') }}"></script>

    <script src="{{ url_for('static',filename='assets/js/jquery.mCustomScrollbar.concat.min.js') }}"></script>
    <script src="{{ url_for('static',filename='assets/js/custom.js') }}"></script>
    <style>

    </style>
</head>

<body>





    <!-- <li><a href="{{url_for('logout')}}">退出</a></li> -->

    <!-- 添加固定导航栏
    <nav class="navbar navbar-default navbar-fixed-top" style="min-height: 40px;">
        <div class="container-fluid">
            <div class="navbar-header pull-right">
                <a href="{{url_for('logout')}}" class="btn btn-danger" style="margin: 4px 15px;">
                    <i class="fa fa-sign-out"></i> 退出
                </a>
            </div>
        </div>
    </nav> -->

    <!-- 删除原来的退出按钮 -->
    <!-- 调整主容器的上边距 -->
    <div class="container-fluid" style="margin-top: 5px;">
        <div style="margin-top: 5px;">
            <!-- {# <h1 style="text-align:center;">Pro sidebar template</h1>#} -->


            <form class="form-inline" role="form" style="float: left">
                <div class="form-group ">
                    <label for="col_name_search">队列名称：</label>
                    <select class="form-control" id="col_name_search">
                        <option value="">请选择队列...</option>
                    </select>
                </div>
                <div class="form-group marginLeft20">
                    <label for="start_time">起始时间：</label>
                    <input type="text" class="form-control" id="start_time">
                </div>
                <div class="form-group marginLeft20">
                    <label for="end_time">截止时间：</label>
                    <input type="text" class="form-control" id="end_time">
                </div>
                <label for="sucess_status" class="marginLeft20">函数运行状态：</label>
                <select class="form-control" id="sucess_status">
                    <option value="1">全部</option>
                    <option value="2">成功</option>
                    <option value="3">失败</option>

                </select>
                <div class="form-group marginLeft20">
                    <label for="params">函数参数：</label>
                    <input type="text" class="form-control" id="params" placeholder="请输入参数。。">
                </div>
                <button type="button" class="btn btn-default marginLeft20"
                    onclick="document.getElementById('table').style.display = 'block';$('#echartsArea').css('display','none');startRun();queryResult(currentColName,0,true)">查询</button>
            </form>

            <!-- <button id="statistic" type="button" class="btn btn-info btn-sm marginLeft20" onclick="statistic()">生成统计表</button> -->

            <button id="autoFresh" type="button" class="btn btn-success btn-sm marginLeft20" style="float2: right"
                onclick="startOrStop()">自动刷新中</button>
            <!-- <p id="echartsInfoTex" style="clear: both;margin-top: 30px;background-color:yellowgreen ;width:600px;color: white;text-shadow: 0 0 10px black;font-size: 16px;display: none"></p>
            <p id="Last1minInfoTex" style="clear: both;margin-top: 10px;background-color:#00ccff;width:600px;color: white;text-shadow: 0 0 10px black;font-size: 16px;"></p>
            <p id="resultInfoTex" style="clear: both;margin-top: 10px;background-color:green;width:600px;color: white;text-shadow: 0 0 10px black;font-size: 16px;"></p>
             -->
            <p id="echartsInfoTex"
                style="clear: both;margin-top: 30px;background-color:yellowgreen ;width:600px;color: white;text-shadow: 0 0 10px black;font-size: 16px;display: none">
            </p>
            <div style="display: flex; gap: 20px; margin-top: 10px;">
                <p id="resultInfoTex"
                    style="margin: 0; background-color:green;width:600px;color: white;text-shadow: 0 0 10px black;font-size: 16px;">
                </p>
                <p id="Last1minInfoTex"
                    style="margin: 0; background-color:#00ccff;width:600px;color: white;text-shadow: 0 0 10px black;font-size: 16px;">
                </p>
            </div>


            <div class="table-responsive" style="margin-top: 10px;">
                <table id="table" class="table table-striped">

                </table>
            </div>
        </div>
    </div>





    <script>

        // 在现有的变量声明后添加
        var allQueues = [];  // 存储所有队列数据
        var currentColName;
        var runStatus = 1;

        $(document).ready(function () {
            // ... 现有的代码 ...

            // 初始化日期时间选择器
            $('#start_time, #end_time').datetimepicker({
                format: 'YYYY-MM-DD HH:mm:ss',
                locale: 'zh-cn',
                sideBySide: true,  // 日期和时间选择器并排显示
                showClear: true,   // 显示清除按钮
                showClose: true,   // 显示关闭按钮
                showTodayButton: true,  // 显示今天按钮
                icons: {
                    time: 'fa fa-clock-o',
                    date: 'fa fa-calendar',
                    up: 'fa fa-chevron-up',
                    down: 'fa fa-chevron-down',
                    previous: 'fa fa-chevron-left',
                    next: 'fa fa-chevron-right',
                    today: 'fa fa-crosshairs',
                    clear: 'fa fa-trash',
                    close: 'fa fa-times'
                }
            });

            // ... 现有的代码 ...
        });

        // 页面加载完成后立即获取所有队列
        $(document).ready(function () {
            $.ajax({
                url: "{{ url_for('query_cols_view')}}",
                data: { col_name_search: '' },
                async: true,
                success: function (result) {
                    allQueues = result;
                    var html = '<option value="">请选择队列...</option>';
                    for (var item of result) {
                        html += '<option value="' + item.collection_name + '">' +
                            item.collection_name + '&nbsp;&nbsp;&nbsp;&nbsp;(result_count:' + item.count + ')</option>';
                    }
                    $("#col_name_search").html(html);

                    // 初始化选择框的搜索功能
                    $("#col_name_search").select2({
                        placeholder: "请输入队列名称搜索...",
                        allowClear: true,
                        width: '300px'
                    });

                    // 监听选择变化
                    $("#col_name_search").on('change', function () {
                        var selectedQueue = $(this).val();
                        console.log("Selected queue:", selectedQueue);
                        currentColName = selectedQueue;
                        // if(selectedQueue) {
                        //     queryResult(selectedQueue, 0, true);
                        // }
                    });
                }
            });
        });


        String.prototype.format = function () {
            var values = arguments;
            return this.replace(/\{(\d+)\}/g, function (match, index) {
                if (values.length > index) {
                    return values[index];
                } else {
                    return "";
                }
            });
        };

        function dateToString(date) {
            const year = date.getFullYear();
            let month = date.getMonth() + 1;
            let day = date.getDate();
            let hour = date.getHours();
            let minute = date.getMinutes();
            let second = date.getSeconds();
            month = month > 9 ? month : ('0' + month);
            day = day > 9 ? day : ('0' + day);
            hour = hour > 9 ? hour : ('0' + hour);
            minute = minute > 9 ? minute : ('0' + minute);
            second = second > 9 ? second : ('0' + second);
            return year + "-" + month + "-" + day + " " + hour + ":" + minute + ":" + second;
        }


        //昨天的时间
        var day1 = new Date();
        day1.setDate(day1.getDate() - 2);

        //明天的时间
        var day2 = new Date();
        day2.setDate(day2.getDate() + 1);

        $("#start_time").val(dateToString(day1));
        $("#end_time").val(dateToString(day2));
        useAsync = false;


        //searchCols();
        useAsync = true;

        function queryResult(col_name, page, manualOperate) {
            if (currentColName === undefined) {
                return;
            }

            $('#echartsArea').css('display', 'none');
            // currentColName = col_name;
            if (manualOperate === true) {
                document.getElementById('table').style.display = 'block';
                updateTopText();
                updateQueryText();
            }

            if (runStatus === 0) {
                return;
            }


            $.ajax({
                url: "{{ url_for('query_result_view')}}", data: {
                    col_name: col_name, start_time: $("#start_time").val(),
                    end_time: $("#end_time").val(), is_success: $("#sucess_status").val(), function_params: $("#params").val(), page: page
                }, async: useAsync, success: function (result, status) {
                    // console.info(result);

                    var html = '  <thead>\n' +
                        '                    <tr>\n' +
                        '                        <th>执行机器-进程-脚本</th>\n' +

                        '                        <th>函数名称</th>\n' +
                        '                        <th>函数入参</th>\n' +
                        '                        <th>函数结果</th>\n' +
                        '                        <th>消息发布时间</th>\n' +
                        '                        <th>开始执行时间</th>\n' +
                        '                        <th>消耗时间(秒)</th>\n' +
                        '                        <th>执行次数(重试)</th>\n' +
                        '                        <th>运行状态</th>\n' +
                        '                        <th>是否成功</th>\n' +
                        '                        <th>错误原因</th>\n' +


                        '                        <th>线程(协程)数</th>\n' +
                        '                    </tr>\n' +
                        '                    </thead>' +
                        '<tbody>';
                    for (var item of result) {
                        // console.info(item);
                        var displayLevel = "success";
                        if (item.run_times > 1) {
                            displayLevel = "warning";
                        }

                        if (item.success === false) {
                            displayLevel = "danger";
                        }
                        var tr = ' <tr class="{0}">\n' +

                            '                        <td>{1}</td>\n' +
                            '                        <td>{2}</td>\n' +
                            '                        <td>{3}</td>\n' +
                            '                        <td>{4}</td>\n' +
                            '                        <td>{5}</td>\n' +
                            '                        <td>{6}</td>\n' +
                            '                        <td>{7}</td>\n' +
                            '                        <td>{8}</td>\n' +
                            '                        <td>{9}</td>\n' +
                            '                        <td>{10}</td>\n' +
                            '                        <td>{11}</td>\n' +
                            '                        <td>{12}</td>\n' +

                            '                    </tr>';
                        var successText = item.success === true ? "成功" : "失败";
                        <!--                    console.info(item.run_status);-->
                        var run_status_text = item.run_status;
                        if (item.run_status === "running") {
                            successText = "未完成";
                            displayLevel = "info";
                            if (Date.now() / 1000 - item.time_start > 600) {
                                run_status_text = "running?";
                            }
                        }

                        var time_start_obj = new Date(item.time_start * 1000);
                        var time_start_str = dateToString(time_start_obj);

                        tr = tr.format(displayLevel, item.host_process + ' - ' + item.script_name, item.function, item.params_str, item.result, item.publish_time_str,
                            time_start_str, item.time_cost, item.run_times, run_status_text, successText, item.exception, item.total_thread);
                        html += tr;
                    }
                    html += '</tbody>';
                    $("#table").html(html);

                    // document.getElementById('echartsArea').style.display = 'none';


                }
            });
            // if (manualOperate === true) {
            //     updateQueryText()
            // }
        }

        function updateQueryText() {
            if (currentColName === undefined) {
                return;
            }

            $.ajax({
                url: "{{ url_for('speed_stats')}}", data: {
                    col_name: currentColName, start_time: $("#start_time").val(),
                    end_time: $("#end_time").val()
                }, async: useAsync, success: function (result, status) {
                    var msg = ' {0} 队列,所选查询时间范围内运行成功了{1}次,失败了{2}次'.format(currentColName, result.success_num, result.fail_num);
                    console.info(msg);
                    $('#resultInfoTex').html(msg);
                }
            })
        }

        // queryResult(currentColName, 0, true);


        function updateTopText() {
            if (currentColName === undefined) {
                return;
            }
            var t1 = new Date(new Date().getTime() - 60000);
            var t2 = new Date();
            $.ajax({
                url: "{{ url_for('speed_stats')}}", data: {
                    col_name: currentColName, start_time: dateToString(t1), end_time: dateToString(t2)
                }, async: useAsync, success: function (result, status) {
                    var msg = ' {0} 队列,最近一分钟内运行成功了{1}次,失败了{2}次'.format(currentColName, result.success_num, result.fail_num);
                    console.info(msg);
                    $('#Last1minInfoTex').text(msg);
                }
            })
        }

        updateTopText();
        updateQueryText();
        setInterval(updateQueryText, 30000);
        setInterval(updateTopText, 30000);

        function autoFreshResult() {
            if (currentColName === undefined) {
                return;
            }
            queryResult(currentColName, 0, false);
        }

        // setInterval(autoFreshResult, 30000);

        iid = setInterval(autoFreshResult, 5000);
        

        function startRun() {
            $("#autoFresh").text("自动刷新中");
            $("#autoFresh").removeClass("btn-danger");
            $("#autoFresh").addClass("btn-success");
            iid = setInterval(autoFreshResult, 5000);
            runStatus = 1;
        }

        function stopRun() {
            $("#autoFresh").text("暂停刷新了");
            $("#autoFresh").removeClass("btn-success");
            $("#autoFresh").addClass("btn-danger");
            clearInterval(iid);
            runStatus = 0;
        }

        function startOrStop() {
            if (runStatus === 1) {
                stopRun();
            } else {
                startRun();
            }
        }

       

        

       


    </script>
</body>

</html>
```

### 代码文件: funboost\function_result_web\templates\index.html
```python
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <link rel="icon" href="{{ url_for('static',filename='images/favicon.ico') }}">
    <!-- 引入 Bootstrap CSS -->
    <link href="{{ url_for('static',filename='css_cdn/twitter-bootstrap/3.3.7/css/bootstrap.min.css') }}" rel="stylesheet">
    <!-- 引入 jQuery -->
    <script src="{{ url_for('static',filename='js/jquery-1.11.0.min.js') }}" type="text/javascript"></script>
    <!-- 引入 Bootstrap JS -->
    <script src="{{ url_for('static',filename='js_cdn/bootstrap/3.3.7/js/bootstrap.min.js') }}"></script>
     <link href="{{ url_for('static',filename='css_cdn/font-awesome/4.7.0/css/font-awesome.min.css') }}" rel="stylesheet">
    <title>funboost web manager</title>
    <style>
        body {
            overflow-x: hidden;
        }

        .sidebar {
            position: fixed;
        top: 0;
        left: 0;
        bottom: 0;
        width: 180px;
        background-color: #296074;
        padding-top: 20px;
        overflow-y: auto;
        transition: all 0.3s ease;  /* 添加过渡效果 */
        }
        .sidebar.collapsed {
        width: 50px;
    }


        .sidebar .nav-link {
            color: white;
            background-color: #296074; /* 导航栏链接默认灰色背景 */
            margin-bottom: 5px;
            border-radius: 5px;
        }

        .sidebar .nav-link.active {
            background-color: #0BBAF8; /* 激活状态蓝色背景 */
            color: white;
        }

        .main-content {
            margin-left: 180px;
            transition: all 0.3s ease;  /* 添加过渡效果 */
        }
        
        .main-content.expanded {
        margin-left: 50px;
    }

    .toggle-btn {
        position: fixed;
        left: 180px;
        top: 10px;
        z-index: 1000;
        background: #296074;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 0 5px 5px 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .toggle-btn.collapsed {
        left: 50px;
    }

    .sidebar.collapsed .nav-link span {
        display: none;
    }

    .nav-link i {
        margin-right: 10px;
        width: 20px;
        text-align: center;
    }



        .main-content iframe {
            width: 100%;
            height: calc(100vh - 40px);  /* 视窗高度减去padding */
            padding: 20px;
            border: none;
            overflow: auto;
        }

        .sidebar .nav-item {
        padding: 5px 10px;
        position: relative;
    }

    .sidebar .nav-item:not(:last-child)::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 10%;
        width: 80%;
        height: 2px;
        background: linear-gradient(to right, transparent, #ffffff80, transparent);
    }

    .sidebar .nav-link {
        padding: 8px 15px;
        transition: all 0.3s ease;
        font-weight: 500;
    }

    .sidebar .nav-link:hover {
        transform: translateX(5px);
        background-color: #1e4d61;
    }

    </style>
</head>

<body>
        <!-- 添加折叠按钮 -->
        <button class="toggle-btn">
            <i class="fa fa-angle-left"></i>
        </button>
    
    <!-- 左侧导航栏 -->
    <div class="sidebar">
        <ul class="nav flex-column">
            <li class="nav-item">
                <a class="nav-link " href="/?page=fun_result_table" data-target="/tpl/fun_result_table.html">
                    <i class="fa fa-table"></i><span>函数结果表</span>
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="/?page=conusme_speed" data-target="/tpl/conusme_speed.html">
                    <i class="fa fa-tachometer"></i><span>消费速率图</span>
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="/?page=running_consumer_by_ip" data-target="/tpl/running_consumer_by_ip.html">
                    <i class="fa fa-server"></i><span>运行中消费者(by ip)</span>
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="/?page=running_consumer_by_queue_name" data-target="/tpl/running_consumer_by_queue_name.html">
                    <i class="fa fa-list"></i><span>运行中消费者(by queue)</span>
                </a>
            </li>
            <li class="nav-item ">
                <a class="nav-link active" href="/?page=queue_op" data-target="/tpl/queue_op.html">
                    <i class="fa fa-cogs"></i><span>队列操作</span>
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="/?page=rpc_call" data-target="/tpl/rpc_call.html">
                    <i class="fa fa-cogs"></i><span>rpc调用</span>
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="/?page=about" data-target="/tpl/about.html">
                    <i class="fa fa-info-circle"></i><span>说明</span>
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="javascript:void(0)" id="logoutBtn">
                    <i class="fa fa-sign-out"></i><span>退出登录</span>
                </a>
            </li>
        </ul>
    </div>

    <!-- 右侧内容区域 -->
    <div class="main-content" id="content000">
        <!-- 初始加载 Home 页面内容 -->
         <!-- 右侧内容区域 -->
    <iframe id="content" frameborder="0">
        <!-- 初始加载 Home 页面内容 -->
    </iframe >
    </div>

    

    <!-- 添加退出确认模态框 -->
    <div class="modal fade" id="logoutModal" tabindex="-1" role="dialog" aria-labelledby="logoutModalLabel">
      <div class="modal-dialog modal-sm" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
            <h4 class="modal-title" id="logoutModalLabel">确认退出</h4>
          </div>
          <div class="modal-body">
            确定要退出登录吗？
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-default" data-dismiss="modal">取消</button>
            <button type="button" class="btn btn-primary" id="confirmLogout">确认退出</button>
          </div>
        </div>
      </div>
    </div>

    <script src="{{ url_for('static',filename='js/form-memory.js') }}"></script>
    <script>
            $(document).ready(function () {
        // ... 现有代码 ...

        // 添加折叠功能
        $('.toggle-btn').click(function() {
            $('.sidebar').toggleClass('collapsed');
            $('.main-content').toggleClass('expanded');
            $('.toggle-btn').toggleClass('collapsed');
            
            // 切换箭头方向
            var icon = $(this).find('i');
            if (icon.hasClass('fa-angle-left')) {
                icon.removeClass('fa-angle-left').addClass('fa-angle-right');
            } else {
                icon.removeClass('fa-angle-right').addClass('fa-angle-left');
            }
        });
    });

        $(document).ready(function () {
            // 检查URL参数是否指定了页面
            var urlParams = new URLSearchParams(window.location.search);
            var pageName = urlParams.get('page');
            
            // 初始加载页面
            if (pageName) {
                // 根据URL参数加载页面
                loadPage('/tpl/' + pageName + '.html');
                // 设置对应导航为active
                $('.sidebar .nav-link').removeClass('active');
                $('.sidebar .nav-link[href="/?page=' + pageName + '"]').addClass('active');
            } else {
                // 默认加载队列操作页面
                loadPage('/tpl/queue_op.html');
            }

            // 导航栏点击事件
            $('.sidebar .nav-link').click(function (e) {
                // 不阻止默认行为，允许页面跳转
                // e.preventDefault();
                
                // 移除所有导航项的 active 类
                $('.sidebar .nav-link').removeClass('active');
                // 为当前点击的导航项添加 active 类
                $(this).addClass('active');
                // 获取要加载的页面文件名
                const targetPage = $(this).data('target');
                // 加载页面内容
                loadPage(targetPage);
            });

            // 加载页面内容的函数
            function loadPage(page) {
                $.ajax({
                    url: page,
                    method: 'GET',
                    success: function (data) {
                        $('#content').attr('src', page);
                    },
                    error: function () {
                        $('#content').html('<p>Error loading page.</p>');
                    }
                });
            }

            // 退出登录确认
            $('#logoutBtn').click(function(e) {
                e.preventDefault();
                $('#logoutModal').modal('show');
            });
            
            $('#confirmLogout').click(function() {
                window.location.href = '/logout';
            });
        });
    </script>
</body>

</html>
```

### 代码文件: funboost\function_result_web\templates\index_backup.html
```python
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>pytho万能分布式函数调度框架</title>
    <link href="{{ url_for('static',filename='css_cdn/twitter-bootstrap/3.3.7/css/bootstrap.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static',filename='css_cdn/font-awesome/4.7.0/css/font-awesome.min.css') }}" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static',filename='css_cdn/bootstrap-datetimepicker/4.17.47/css/bootstrap-datetimepicker.min.css') }}">
    <link rel="stylesheet" href="{{ url_for('static',filename='assets/css/jquery.mCustomScrollbar.min.css') }}">
    <link rel="stylesheet" href="{{ url_for('static',filename='assets/css/custom.css') }}">

        <!-- 在其他 link 标签后添加 -->
        <link href="{{ url_for('static',filename='css_cdn/select2/4.0.13/css/select2.min.css') }}" rel="stylesheet">
        <script src="{{ url_for('static',filename='js/jquery-1.11.0.min.js') }}" type="text/javascript"></script>
<!-- <script src="https://cdn.bootcdn.net/ajax/libs/jquery/1.11.0/jquery.min.js"></script> -->
        <!-- 在其他 script 标签后添加 -->
        <script src="https://cdn.bootcdn.net/ajax/libs/select2/4.0.13/js/select2.min.js"></script>
    <style>
        .marginLeft20 {
            margin-left: 20px;
        }

        .liActive {
            background: #FFFF66;
        }

    </style>
</head>
<body>

  



    <!-- <li><a href="{{url_for('logout')}}">退出</a></li> -->

    <!-- 添加固定导航栏 -->
    <nav class="navbar navbar-default navbar-fixed-top" style="min-height: 40px;">
        <div class="container-fluid">
            <div class="navbar-header pull-right">
                <a href="{{url_for('logout')}}" class="btn btn-danger" style="margin: 4px 15px;">
                    <i class="fa fa-sign-out"></i> 退出
                </a>
            </div>
        </div>
    </nav>

    <!-- 删除原来的退出按钮 -->
    <!-- 调整主容器的上边距 -->
    <div class="container-fluid" style="margin-top: 10px;">



   

        <div style="margin-top: 70px;">
            {# <h1 style="text-align:center;">Pro sidebar template</h1>#}


            <form class="form-inline" role="form" style="float: left">
                <div class="form-group marginLeft20">
                    <label for="col_name_search">队列名称：</label>
                    <select class="form-control" id="col_name_search">
                        <option value="">请选择队列...</option>
                    </select>
                </div>
                <div class="form-group marginLeft20">
                    <label for="start_time">起始时间：</label>
                    <input type="text" class="form-control" id="start_time">
                </div>
                <div class="form-group marginLeft20">
                    <label for="end_time">截止时间：</label>
                    <input type="text" class="form-control" id="end_time">
                </div>
                <label for="sucess_status" class="marginLeft20">函数运行状态：</label>
                <select class="form-control" id="sucess_status">
                    <option value="1">全部</option>
                    <option value="2">成功</option>
                    <option value="3">失败</option>

                </select>
                <div class="form-group marginLeft20">
                    <label for="params">函数参数：</label>
                    <input type="text" class="form-control" id="params" placeholder="请输入参数。。">
                </div>
                <button type="button" class="btn btn-default marginLeft20" onclick="document.getElementById('table').style.display = 'block';$('#echartsArea').css('display','none');startRun();queryResult(currentColName,0,true)">查询</button>
            </form>

            <button id="statistic" type="button" class="btn btn-info btn-sm marginLeft20" onclick="statistic()">生成统计表</button>

            <button id="autoFresh" type="button" class="btn btn-success btn-sm marginLeft20" style="float2: right" onclick="startOrStop()">自动刷新中</button>
            <!-- <p id="echartsInfoTex" style="clear: both;margin-top: 30px;background-color:yellowgreen ;width:600px;color: white;text-shadow: 0 0 10px black;font-size: 16px;display: none"></p>
            <p id="Last1minInfoTex" style="clear: both;margin-top: 10px;background-color:#00ccff;width:600px;color: white;text-shadow: 0 0 10px black;font-size: 16px;"></p>
            <p id="resultInfoTex" style="clear: both;margin-top: 10px;background-color:green;width:600px;color: white;text-shadow: 0 0 10px black;font-size: 16px;"></p>
             -->
            <p id="echartsInfoTex" style="clear: both;margin-top: 30px;background-color:yellowgreen ;width:600px;color: white;text-shadow: 0 0 10px black;font-size: 16px;display: none"></p>
            <div style="display: flex; gap: 20px; margin-top: 10px;">
                <p id="Last1minInfoTex" style="margin: 0; background-color:#00ccff;width:600px;color: white;text-shadow: 0 0 10px black;font-size: 16px;"></p>
                <p id="resultInfoTex" style="margin: 0; background-color:green;width:600px;color: white;text-shadow: 0 0 10px black;font-size: 16px;"></p>
            </div>

            <div id = echartsArea style="display: None">
            <div id="st4" style="width: 100%;height:600px;margin-top:60px;"></div>
            <div id="st3" style="width: 100%;height:600px;margin-top:60px;"></div>
            <div id="st2" style="width: 100%;height:600px;margin-top:60px;"></div>
            <div id="st1" style="width: 100%;height:600px;margin-top:60px;"></div>
            </div>
            <div class="table-responsive">
                <table id="table" class="table table-striped">

                </table>
            </div>
        </div>




<script src="{{ url_for('static',filename='js_cdn/bootstrap/3.3.7/js/bootstrap.min.js') }}"></script>


<script src="https://cdn.bootcss.com/moment.js/2.24.0/moment-with-locales.js"></script>
<script src="https://cdn.bootcss.com/bootstrap-datetimepicker/4.17.47/js/bootstrap-datetimepicker.min.js"></script>
<script type="text/javascript" src="https://cdn.bootcss.com/echarts/3.3.0/echarts.js"></script>

<script src="{{ url_for('static',filename='assets/js/jquery.mCustomScrollbar.concat.min.js') }}"></script>
<script src="{{ url_for('static',filename='assets/js/custom.js') }}"></script>

<script>

    // 在现有的变量声明后添加
    var allQueues = [];  // 存储所有队列数据
    var currentColName;
    
    // 页面加载完成后立即获取所有队列
    $(document).ready(function() {
        $.ajax({
            url: "{{ url_for('query_cols_view')}}", 
            data: {col_name_search: ''}, 
            async: true, 
            success: function (result) {
                allQueues = result;
                var html = '<option value="">请选择队列...</option>';
                for (var item of result) {
                    html += '<option value="' + item.collection_name + '">' + 
                           item.collection_name + ' (' + item.count + ')</option>';
                }
                $("#col_name_search").html(html);
                
                // 初始化选择框的搜索功能
                $("#col_name_search").select2({
                    placeholder: "请输入队列名称搜索...",
                    allowClear: true,
                    width: '300px'
                });
                
                // 监听选择变化
                $("#col_name_search").on('change', function() {
                    var selectedQueue = $(this).val();
                    console.log("Selected queue:", selectedQueue);
                    currentColName = selectedQueue;
                    // if(selectedQueue) {
                    //     queryResult(selectedQueue, 0, true);
                    // }
                });
            }
        });
    });


    String.prototype.format = function () {
        var values = arguments;
        return this.replace(/\{(\d+)\}/g, function (match, index) {
            if (values.length > index) {
                return values[index];
            } else {
                return "";
            }
        });
    };

    function dateToString(date) {
        const year = date.getFullYear();
        let month = date.getMonth() + 1;
        let day = date.getDate();
        let hour = date.getHours();
        let minute = date.getMinutes();
        let second = date.getSeconds();
        month = month > 9 ? month : ('0' + month);
        day = day > 9 ? day : ('0' + day);
        hour = hour > 9 ? hour : ('0' + hour);
        minute = minute > 9 ? minute : ('0' + minute);
        second = second > 9 ? second : ('0' + second);
        return year + "-" + month + "-" + day + " " + hour + ":" + minute + ":" + second;
    }


    //昨天的时间
    var day1 = new Date();
    day1.setDate(day1.getDate() - 2);

    //明天的时间
    var day2 = new Date();
    day2.setDate(day2.getDate() + 1);

    $("#start_time").val(dateToString(day1));
    $("#end_time").val(dateToString(day2));
    useAsync = false;

   
    //searchCols();
    useAsync = true;

    function queryResult(col_name, page, manualOperate) {
        $('#echartsArea').css('display','none');
        currentColName = col_name;
        if (manualOperate === true){
            document.getElementById('table').style.display = 'block';
        }

        $.ajax({
            url: "{{ url_for('query_result_view')}}", data: {
                col_name: col_name, start_time: $("#start_time").val(),
                end_time: $("#end_time").val(), is_success: $("#sucess_status").val(), function_params: $("#params").val(), page: page
            }, async: useAsync, success: function (result, status) {
                // console.info(result);

                var html = '  <thead>\n' +
                    '                    <tr>\n' +
                    '                        <th>执行机器-进程-脚本</th>\n' +

                    '                        <th>函数名称</th>\n' +
                    '                        <th>函数入参</th>\n' +
                    '                        <th>函数结果</th>\n' +
                    '                        <th>消息发布时间</th>\n' +
                    '                        <th>开始执行时间</th>\n' +
                    '                        <th>消耗时间(秒)</th>\n' +
                    '                        <th>执行次数(重试)</th>\n' +
                    '                        <th>运行状态</th>\n' +
                    '                        <th>是否成功</th>\n' +
                    '                        <th>错误原因</th>\n' +


                    '                        <th>线程(协程)数</th>\n' +
                    '                    </tr>\n' +
                    '                    </thead>' +
                    '<tbody>';
                for (var item of result) {
                    // console.info(item);
                    var displayLevel = "success";
                    if (item.run_times > 1) {
                        displayLevel = "warning";
                    }

                    if (item.success === false) {
                        displayLevel = "danger";
                    }
                    var tr = ' <tr class="{0}">\n' +

                        '                        <td>{1}</td>\n' +
                        '                        <td>{2}</td>\n' +
                        '                        <td>{3}</td>\n' +
                        '                        <td>{4}</td>\n' +
                        '                        <td>{5}</td>\n' +
                        '                        <td>{6}</td>\n' +
                        '                        <td>{7}</td>\n' +
                        '                        <td>{8}</td>\n' +
                        '                        <td>{9}</td>\n' +
                        '                        <td>{10}</td>\n' +
                        '                        <td>{11}</td>\n' +
                        '                        <td>{12}</td>\n' +

                        '                    </tr>';
                    var successText = item.success === true ? "成功" : "失败";
<!--                    console.info(item.run_status);-->
                    var run_status_text = item.run_status;
                    if (item.run_status==="running"){
                        successText = "未完成";
                        displayLevel = "info";
                        if ( Date.now() /1000 - item.time_start > 600) {
                            run_status_text = "running?";
                        }
                    }

                    var time_start_obj = new Date(item.time_start * 1000);
                    var time_start_str = dateToString(time_start_obj);

                    tr = tr.format(displayLevel, item.host_process + ' - ' + item.script_name,  item.function, item.params_str, item.result,item.publish_time_str,
                        time_start_str,item.time_cost, item.run_times, run_status_text,successText, item.exception, item.total_thread);
                    html += tr;
                }
                html += '</tbody>';
                $("#table").html(html);

                // document.getElementById('echartsArea').style.display = 'none';


            }
        });
        if (manualOperate === true) {
            updateQueryText()
        }
    }

    function updateQueryText() {

        $.ajax({
            url: "{{ url_for('speed_stats')}}", data: {
                col_name: currentColName, start_time: $("#start_time").val(),
                end_time: $("#end_time").val()
            }, async: useAsync, success: function (result, status) {
                var msg = '{0}队列,所选查询时间范围内运行成功了{1}次,失败了{2}次'.format(currentColName,result.success_num, result.fail_num);
                console.info(msg);
                $('#resultInfoTex').html(msg);
            }
        })
    }

    // queryResult(currentColName, 0, true);
    setInterval(updateQueryText, 30000);

    function updateTopText() {
        if (currentColName===undefined) {
            return;
        }
        var t1 = new Date(new Date().getTime() - 60000);
        var t2 = new Date();
        $.ajax({
            url: "{{ url_for('speed_stats')}}", data: {
                col_name: currentColName, start_time: dateToString(t1), end_time: dateToString(t2)
            }, async: useAsync, success: function (result, status) {
                var msg = '{0}队列,最近一分钟内运行成功了{1}次,失败了{2}次'.format(currentColName, result.success_num, result.fail_num);
                console.info(msg);
                $('#Last1minInfoTex').text(msg);
            }
        })
    }

    updateTopText();

    setInterval(updateTopText, 30000);

    function autoFreshResult() {
        if (currentColName===undefined) {
            return;
        }
        queryResult(currentColName, 0, false);
    }

    // setInterval(autoFreshResult, 30000);

    iid = setInterval(autoFreshResult, 5000);
    runStatus = 1;

    function startRun() {
        $("#autoFresh").text("自动刷新中");
        $("#autoFresh").removeClass("btn-danger");
        $("#autoFresh").addClass("btn-success");
        iid = setInterval(autoFreshResult, 5000);
        runStatus = 1;
    }

    function stopRun() {
        $("#autoFresh").text("暂停刷新了");
        $("#autoFresh").removeClass("btn-success");
        $("#autoFresh").addClass("btn-danger");
        clearInterval(iid);
        runStatus = 0;
    }

    function startOrStop() {
        if (runStatus === 1) {
            stopRun();
        } else {
            startRun();
        }
    }

    class Person {//定义了一个名字为Person的类
        constructor(name, age) {//constructor是一个构造方法，用来接收参数
            this.name = name;//this代表的是实例对象
            this.age = age;
        }

        say() {//这是一个类的方法，注意千万不要加上function
            return "我的名字叫" + this.name + "今年" + this.age + "岁了";
        }
    }

    var obj = new Person("laotie", 88);
    console.log(obj.say());//我的名字叫laotie今年88岁了

    function statistic() {
        $('#echartsInfoTex').html('生成统计表中，需要一段时间。。。。');
        $("#echartsInfoTex").css('display','block');
        $("#echartsArea").css('display','block');
        stopRun();
        document.getElementById('table').style.display = "none";
        $.ajax({
            url: "{{ url_for('speed_statistic_for_echarts')}}", data: {
                col_name: currentColName
            }, async: useAsync, success: function (result, status) {
                // var msg = '{0}队列,最近一分钟内运行成功了{1}次,失败了{2}次'.format(currentColName, result.success_num, result.fail_num);
                console.info(result);
                _buildOneChart('st1', '最近10天的消费情况', '运行次数', result['recent_10_days']['time_arr'], result['recent_10_days']['count_arr']);
                _buildOneChart('st2', '最近24小时的消费情况', '运行次数', result['recent_24_hours']['time_arr'], result['recent_24_hours']['count_arr']);
                _buildOneChart('st3', '最近60分钟的消费情况', '运行次数', result['recent_60_minutes']['time_arr'], result['recent_60_minutes']['count_arr']);
                _buildOneChart('st4', '最近60秒的消费情况', '运行次数', result['recent_60_seconds']['time_arr'], result['recent_60_seconds']['count_arr']);
                $("#echartsInfoTex").css('display','none');

                // $('#top_text').text(msg);
            }
        });


    }

    function _buildOneChart(elementId, titelText, legendData, xData, yData) {

        var myChart = echarts.init(document.getElementById(elementId));



        // 指定图表的配置项和数据
        var option = {
            title: {
                text: titelText
            },
            tooltip: {},
            legend: {
                data: [legendData]
            },

            xAxis: {
                type: 'category',
                data: xData,
                axisLabel: {
                    rotate: 90,

                    interval: 0,

                    // formatter: function (value) {
                    //
                    //     console.info(value);
                    //     var v =  value.split("").join("\n");
                    //     console.info(v);
                    //     return v;
                    // },

                    // show: true, interval: 'auto', inside: false, rotate: 90, margin: 8, formatter: null, showMinLabel: null, showMaxLabel: null,

                },

            },

            yAxis: {},
            series: [{
                name: legendData,
                type: 'bar',
                data: yData
            }]
        };

        // 使用刚指定的配置项和数据显示图表。
        myChart.setOption(option);
        console.info(elementId);


    }


</script>
</body>
</html>
```

### 代码文件: funboost\function_result_web\templates\login.html
```python
﻿<!DOCTYPE html>
<html>
<head>
    <title>python分布式函数调度框架</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <meta name="keywords" content="python 分布式 高并发 消息队列 框架"/>

</head>
<body>
<h1>python分布式函数调度框架</h1>
<div class="main-agileinfo">
    <h2>立即登录</h2>
    <form action="login" method="post">
		{{ form.csrf_token }}
        <input type="text" name="user_name" class="name" placeholder="用户名" required="">
        <input type="password" name="password" class="password" placeholder="密码" required="">
        <ul>
            <li>
<!--                <input type="checkbox" id="remember_me" name="remember_me" value="">-->
<!--                <label for="remember_me"><span></span>记住我</label>-->
<!--                <input name="remember_me" type="hidden" value="false">-->

<input name="remember_me" type="checkbox" value="false" id="remember_me">
                <label for="remember_me"><span></span>记住我</label>


            </li>
        </ul>
        <!--            <a href="#">忘记密码?</a><br>-->
        <div class="clear"></div>
        {% with messages = get_flashed_messages(category_filter=["error"]) %}
        {% if messages %}
        <span style="color:red;">
            {% for message in messages %}
                {{ message }}
            <!-- <div class="alert alert-warning">{{ message }} </div> -->
            {% endfor %}
            </span>
        {% endif %}
        {% endwith %}
        <input type="submit" value="登录" onclick="document.getElementById('remember_me').value=document.getElementById('remember_me').checked;">


    </form>
</div>
<div class="footer-w3l">
    <p class="agile"> &copy; 2019 分布式函数调度框架</p>
</div>
</body>
</html>

```

### 代码文件: funboost\function_result_web\templates\queue_op.html
```python
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>队列操作</title>
    <!-- Bootstrap CSS -->
    <link href="{{ url_for('static',filename='css_cdn/twitter-bootstrap/3.3.7/css/bootstrap.min.css') }}" rel="stylesheet">
    <!-- Tabulator CSS -->
    <link href="{{ url_for('static',filename='css_cdn/tabulator-tables@5.5.0/tabulator.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static',filename='css_cdn/tabulator-tables@5.5.0/tabulator_bootstrap3.min.css') }}" rel="stylesheet">


     <!-- jQuery -->
     <script src="{{ url_for('static',filename='js/jquery-1.11.0.min.js') }}" type="text/javascript"></script>
     <!-- <script src="https://cdn.bootcdn.net/ajax/libs/jquery/3.6.4/jquery.min.js"></script> -->
     <!-- Bootstrap JS -->
     <script src="{{ url_for('static',filename='js_cdn/bootstrap/3.3.7/js/bootstrap.min.js') }}"></script>
     <!-- <script src="https://cdn.bootcdn.net/ajax/libs/twitter-bootstrap/3.3.7/js/bootstrap.min.js"></script> -->
     <!-- Tabulator JS -->
     <script type="text/javascript" src="{{ url_for('static',filename='js_cdn/tabulator-tables@5.5.0/dist/js/tabulator.min.js') }}"></script>
     <!-- <script src="https://cdn.bootcdn.net/ajax/libs/tabulator/5.5.0/js/tabulator.min.js"></script> -->
     <script src="{{ url_for('static',filename='js_cdn/chart.js') }}"></script>

    <style>
        .action-btn {
            margin: 2px;
        }
        .search-container {
            margin-bottom: 15px;
        }
        #searchInput {
            width: 500px;
            display: inline-block;
        }
        /* .frozen-column-background { background-color: #FFFFFF !important; } */ /* 移除或注释掉这里 */
        .tabulator-cell {
            padding-left: 20px !important;
            padding-right: 20px !important;
            padding-top: 10px !important;
            border: 1px solid #555 !important; 
            background-color: #000000; /* 移除 !important */
            color: #FFFFFF; /* 移除 !important */
        }
        /* 新增: 自定义超大模态框样式 */
        .modal-xl-custom {
            width: 80%; /* 宽度占屏幕的80% */
            max-width: 1400px; /* 最大宽度限制 */
        }
    </style>
</head>
<body>
    <div class="container-fluid" style="margin-top: 5px;">
        <div class="search-container" style="display: flex; align-items: center; margin-bottom: 10px;">
            <div class="input-group" style="width: 400px;">
                <input type="text" id="searchInput" class="form-control" placeholder="输入队列名称进行过滤..." style="width: 100%;">
                <span class="input-group-btn">
                    <button class="btn btn-default" type="button" onclick="clearSearch()">
                        <i class="glyphicon glyphicon-remove"></i>
                    </button>
                </span>
            </div>
            <button id="refresh-all-msg-counts" class="btn btn-info" style="margin-left: 30px;">更新所有队列的消息数量</button>
            <button id="toggle-auto-refresh" class="btn btn-success" style="margin-left: 10px;">启动自动刷新</button>
            <button id="show-explanation-btn" class="btn btn-default" style="margin-left: 10px;">说明</button>
        </div>
        <div id="queue-table"></div>
    </div>

    <!-- Chart Modal -->
    <div class="modal fade" id="chartModal" tabindex="-1" role="dialog" aria-labelledby="chartModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg modal-xl-custom" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 class="modal-title" id="chartModalLabel">队列数据曲线图: <span id="chartQueueName"></span></h4>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                </div>
                <div class="modal-body">
                    <!-- 新增：时间范围筛选控件 -->
                    <div style="margin-bottom: 10px; display: flex; align-items: center;">
                        <label style="margin-right:5px;">起始时间：</label>
                        <input type="datetime-local" id="chartStartTime" style="margin-right: 10px;">
                        <label style="margin-right:5px;">结束时间：</label>
                        <input type="datetime-local" id="chartEndTime" style="margin-right: 10px;">
                        <button class="btn btn-primary btn-sm" onclick="reloadQueueChartWithTimeRange()">查询</button>
                    </div>
                    <canvas id="queueDataChart" style="height:600px;max-height:600px;"></canvas>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-default" data-dismiss="modal">关闭</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Explanation Modal -->
    <div class="modal fade" id="explanationModal" tabindex="-1" role="dialog" aria-labelledby="explanationModalLabel" aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 class="modal-title" id="explanationModalLabel">说明</h4>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                </div>
                <div class="modal-body">
                    <ul id="explanation-text">
                        {# Content will be added by JavaScript #}
                    </ul>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-default" data-dismiss="modal">关闭</button>
                </div>
            </div>
        </div>
    </div>

   
    <script>
        // 创建表格实例
        var table = new Tabulator("#queue-table", {
            theme: "bootstrap3",
            ajaxURL: "/queue/params_and_active_consumers",
            layout: "fitDataFill",
            responsiveLayout: false,
            pagination: true,
            paginationSize: 1000,
            height: "auto",
            locale: true,
            rowFormatter: function(row) {
                var data = row.getData();
                var cell = row.getCell("queue_name"); 

                if (cell && cell.getElement()) { 
                    var element = cell.getElement();
                    if (data.consumer_count > 0) {
                        element.style.backgroundColor = "#4CAF50"; // 恢复绿色背景
                        element.style.color = "white";
                    } else {
                        element.style.backgroundColor = "#F44336"; // 恢复红色背景
                        element.style.color = "white";
                    }
                }
            },
            langs: {
                "zh-cn": {
                    "pagination": {
                        "first": "首页",
                        "first_title": "首页",
                        "last": "末页",
                        "last_title": "末页",
                        "prev": "上一页",
                        "prev_title": "上一页",
                        "next": "下一页",
                        "next_title": "下一页",
                    }
                }
            },
            columns: [
                {
                    title: "<br><br>队列名字",
                    field: "queue_name",
                    sorter: "string",
                    headerSort: true,
                    headerHozAlign: "center",
                    hozAlign: "left",
                    minWidth: 320, // 增加宽度以容纳按钮
                    headerWordWrap: true,
                    frozen: true,
                    formatter: function(cell, formatterParams, onRendered) {
                        const queueName = cell.getValue();
                        // 让按钮始终显示，不再依赖 isAutoRefreshing
                        return `<div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span>${queueName}</span>
                                    <button class="btn btn-xs btn-info view-chart-btn"
                                            data-queue-name="${queueName}"
                                            style="margin-left: 10px; display: inline-block;"
                                            onclick="showQueueChart('${queueName}')">
                                        <i class="glyphicon glyphicon-stats"></i> 查看曲线图
                                    </button>
                                </div>`;
                    }
                },
                { title: "<br><br>consumer数量", field: "consumer_count", sorter: "number", width: 200,
                formatter: function(cell) {
                    const row = cell.getRow().getData();
                    var consumers = row.active_consumers;
                    return `
                        <div style="display: flex; align-items: center; justify-content: space-between; width: 100%; padding-right: 10px;">
                            <span style="min-width: 50px; text-align: right; padding-right: 15px;">${cell.getValue() || ''}</span>
                            <button class="btn btn-primary btn-sm" onclick='showConsumerDetails(${JSON.stringify(consumers)}, "${row.queue_name}")'>
                                查看消费者详情
                            </button>
                        </div>
                    `;
                }
            },
                
                { title: "<br>broker<br>类型", field: "broker_kind", sorter: "string"  },
                { title: "<br>消费<br>函数", field: "consuming_function_name", sorter: "string"  },
              
                { title: "<br>历史运<br>行次数", field: "history_run_count", sorter: "number", width: 150 },
                { title: "<br>历史运<br>行失败<br>次数", field: "history_run_fail_count", sorter: "number", width: 150 },
                { title: "<br>近10秒<br>完成", field: "all_consumers_last_x_s_execute_count", sorter: "number", width: 100 },
                { title: "<br>近10秒<br>失败", field: "all_consumers_last_x_s_execute_count_fail", sorter: "number", width: 100 },

                { title: "近10秒<br>函数运行<br>平均耗时", field: "all_consumers_last_x_s_avarage_function_spend_time", sorter: "number", width: 100 },
                { title: "累计<br>函数运行<br>平均耗时", field: "all_consumers_avarage_function_spend_time_from_start", sorter: "number", width: 100 },

                { title: "<br><br>消息数量", field: "msg_count", sorter: "number", width: 250,
                    formatter: function(cell) {
                        const row = cell.getRow().getData();
                        const initialCount = cell.getValue() === null ? '' : cell.getValue();
                        const initialCountStr = initialCount === '' ? '0' : String(initialCount); // Ensure '0' for empty initial
                        return `
                            <div style="display: flex; align-items: center; justify-content: space-between; width: 100%; padding-right: 10px;">
                                <span id="msg-count-${row.queue_name}" data-last-count="${initialCountStr}" style="min-width: 70px; text-align: right; padding-right: 25px;">${initialCount}</span>
                                <button class="btn btn-primary btn-sm" onclick="getMessageCount('${row.queue_name}')">获取</button>
                            </div>
                        `;
                    }
                },

                { 
                    title: "暂停<br>消费<br>状态",
                    field: "pause_flag",
                    width: 100,
                    formatter: function(cell) {
                        return cell.getValue()===1 ? '<span style="color: red;">已暂停</span>' : "";
                    }
                },
                {
                    title: "<br><br>操作",
                    width: 500,
                    formatter: function(cell) {
                        const row = cell.getRow().getData();
                        const btnId = 'showParamsBtn_' + Math.random().toString(36).substr(2, 9);
                        setTimeout(() => {
                            document.getElementById(btnId)?.addEventListener('click', () => showParams(row.queue_params));
                        }, 0);
                        return `
                            <button id="${btnId}" class="btn btn-info btn-sm action-btn">查看消费者配置</button>
                            <button class="btn btn-danger btn-sm action-btn" onclick="clearQueue('${row.queue_name}')">清空队列消息</button>
                            <button class="btn btn-warning btn-sm action-btn" onclick="pauseConsume('${row.queue_name}')">暂停消费</button>
                            <button class="btn btn-success btn-sm action-btn" onclick="resumeConsume('${row.queue_name}')">恢复消费</button>
                        `;
                    }
                },
            ],
            ajaxResponse: function(url, params, response) {
                // 转换API响应为表格数据
                const tableData = Object.entries(response).map(([queue_name, data]) => ({
                    queue_name: queue_name,
                    
                    broker_kind: data.queue_params.broker_kind,
                    consuming_function_name: data.queue_params.consuming_function_name,
                    history_run_count: data.history_run_count,
                    history_run_fail_count: data.history_run_fail_count,
                    all_consumers_last_x_s_execute_count: data.all_consumers_last_x_s_execute_count,
                    all_consumers_last_x_s_execute_count_fail: data.all_consumers_last_x_s_execute_count_fail,
                    msg_count: data.msg_num_in_broker, 
                    consumer_count: data.active_consumers.length,
                    active_consumers: data.active_consumers,
                    queue_params: data.queue_params,
                    pause_flag: data.pause_flag ,
                    all_consumers_last_x_s_avarage_function_spend_time:data.all_consumers_last_x_s_avarage_function_spend_time,
                    all_consumers_avarage_function_spend_time_from_start:data.all_consumers_avarage_function_spend_time_from_start
                }));

                return tableData;
            },
        });

        // 搜索功能实现
        document.getElementById("searchInput").addEventListener("keyup", function() {
            table.setFilter("queue_name", "like", this.value);
        });

        // 清除搜索
        function clearSearch() {
            document.getElementById("searchInput").value = "";
            table.clearFilter();
        }

        // 显示参数的模态框
        function showParams(params) {
            // 如果已存在模态框，先移除
            if ($("#paramsModal").length) {
                $("#paramsModal").remove();
            }

            const modalHtml = `
                <div class="modal" id="paramsModal" tabindex="-1" role="dialog">
                    <div class="modal-dialog" role="document">
                        <div class="modal-content">
                            <div class="modal-header">
                                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                                <h4 class="modal-title">消费者配置详情</h4>
                            </div>
                            <div class="modal-body" style="max-height: 80vh; overflow-y: auto;">
                                <pre style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6; font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;">${JSON.stringify(params, null, 2)}</pre>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-default" data-dismiss="modal">关闭</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // 添加模态框到body
            $("body").append(modalHtml);
            
            // 初始化并显示模态框
            $("#paramsModal").modal({
                backdrop: "static",
                keyboard: false
            });
        }
        // 操作函数
        function getMessageCount(queueName) {
            const row = table.getRows().find(row => row.getData().queue_name === queueName);
            if (!row) {
                alert('找不到对应的队列数据');
                return;
            }
            const broker_kind = row.getData().broker_kind;
            
            let countSpan = document.getElementById(`msg-count-${queueName}`);
            let previous_count_str = countSpan.getAttribute('data-last-count') || '0';
            let previous_count = parseInt(previous_count_str);
            if (isNaN(previous_count)) previous_count = 0; // Fallback

            countSpan.innerHTML = '正在获取...'; // Add a loading indicator

            // 获取消息数量的API调用
            $.get(`/queue/message_count/${broker_kind}/${queueName}`, function(response) {
                if (response.success) {
                    const new_count = parseInt(response.count);
                    if (isNaN(new_count)) {
                        countSpan.innerHTML = 'get_msg_num_error';
                        countSpan.setAttribute('data-last-count', '0'); // Reset last count on error
                        return;
                    } 

                    const difference = new_count - previous_count;
                    let diff_display_html = '';
                    if (countSpan.getAttribute('data-last-count') !== '0' || previous_count_str !== '') { // Only show diff if not initial load or previous was not error
                        if (difference > 0) {
                            diff_display_html = ` <span style="color: red;">↑ +${difference}</span>`;
                        } else if (difference < 0) {
                            diff_display_html = ` <span style="color: green;">↓ ${difference}</span>`;
                        }
                    }

                    countSpan.innerHTML = `${new_count}${diff_display_html}`;
                    countSpan.setAttribute('data-last-count', new_count.toString());
                } else {
                    countSpan.innerHTML = 'get_msg_num_error';
                    countSpan.setAttribute('data-last-count', '0'); // Reset last count on error
                }
            }).fail(function() {
                countSpan.innerHTML = 'get_msg_num_error';
                countSpan.setAttribute('data-last-count', '0'); // Reset last count on error
            });
        }

        function clearQueue(queueName) {
            const row = table.getRows().find(row => row.getData().queue_name === queueName);
            if (!row) {
                alert('找不到对应的队列数据');
                return;
            }
            const broker_kind = row.getData().broker_kind;
            if (confirm(`确定要清空队列 ${queueName} 的所有消息吗？`)) {
                $.post(`/queue/clear/${broker_kind}/${queueName}`, function(response) {
                    alert(`清空 ${queueName} 队列成功`);
                    // table.replaceData();
                    getMessageCount(queueName); // 自动获取最新的消息数量
                });
            }
        }

        function pauseConsume(queueName) {
            $.post(`/queue/pause/${queueName}`, function(response) {
                if (response.success) {
                    alert("暂停消费成功");
                    const row = table.getRows().find(row => row.getData().queue_name === queueName);
                    if (row) {
                        row.update({pause_flag: 1});
                    }
                }
            });
        }

        function resumeConsume(queueName) {
            $.post(`/queue/resume/${queueName}`, function(response) {
                if (response.success) {
                    alert("恢复消费成功");
                    const row = table.getRows().find(row => row.getData().queue_name === queueName);
                    if (row) {
                        row.update({pause_flag: 0});
                    }
                }
            });
        }

        // 显示消费者详情的模态框
        function showConsumerDetails(consumers, queueName) {
            $.ajax({
                url: '/running_consumer/hearbeat_info_by_queue_name',
                data: { queue_name: queueName },
                success: function(consumers) {
                    let consumerRows = '';
                    consumers.forEach(consumer => {
                        consumerRows += `
                            <tr>
                                <td>${consumer.computer_ip}</td>
                                <td>${consumer.computer_name}</td>
                                <td>${consumer.process_id}</td>
                                <td>${consumer.hearbeat_datetime_str}</td>
                                
                                <td>${consumer.start_datetime_str}</td>
                                
                                <td>${consumer.last_x_s_execute_count}</td>
                                <td>${consumer.last_x_s_execute_count_fail}</td>
                                <td>${consumer.last_x_s_avarage_function_spend_time}</td>
                                <td>${consumer.total_consume_count_from_start}</td>
                                <td>${consumer.total_consume_count_from_start_fail}</td>
                                <td>${consumer.avarage_function_spend_time_from_start}</td>
                                <td>${consumer.code_filename}</td>,
                                <td>${consumer.consumer_uuid}</td>
                            </tr>
                        `;
                    });
                
                    const modalHtml = `
                        <div class="modal" id="consumerDetailsModal" tabindex="-1" role="dialog">
                            <div class="modal-dialog" style="width: 90%;" role="document">
                                <div class="modal-content">
                                    <div class="modal-header">
                                        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                                        <h4 class="modal-title">${queueName}队列的消费者详情信息</h4>
                                    </div>
                                    <div class="modal-body">
                                        <div class="table-responsive">
                                            <table class="table table-striped">
                                                <thead>
                                                    <tr>
                                                        <th>计算机IP</th>
                                                        <th>计算机名称</th>
                                                        <th>进程ID</th>
                                                        <th>最后心跳时间</th>
                                                        
                                                        <th>启动时间</th>
                                                        
                                                        <th>近10秒<br>运行完成<br>消息个数</th>
                                                        <th>近10秒<br>运行失败<br>消息个数</th>
                                                        <th>近10秒<br>函数运行<br>平均耗时</th>
                                                        <th>累计<br>运行完成<br>消息个数</th>
                                                        <th>累计<br>运行失败<br>消息个数</th>
                                                        <th>累计<br>函数运行<br>平均耗时</th>
                                                        <th>代码文件名</th>
                                                        <th>消费者UUID</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    ${consumerRows}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                    <div class="modal-footer">
                                        <button type="button" class="btn btn-default" data-dismiss="modal">关闭</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                
                    // 移除已存在的模态框
                    $('#consumerDetailsModal').remove();
                    // 添加新的模态框到body
                    $('body').append(modalHtml);
                    // 显示模态框
                    $('#consumerDetailsModal').modal('show');
                },
                error: function(xhr, status, error) {
                    console.error('获取消费者详情失败:', error);
                    alert('获取消费者详情失败');
                }
            });
        }

        document.getElementById("refresh-all-msg-counts").onclick = function() {
            table.getRows().forEach(row => {
                const queueName = row.getData().queue_name;
                getMessageCount(queueName);
            });
        };

        // --- BEGIN NEW SCRIPT LOGIC ---
        let isAutoRefreshing = false;
        let autoRefreshIntervalId = null;
        const AUTO_REFRESH_INTERVAL = 10000; // 10 秒
        let chartInstance = null; // 用于存储Chart.js的实例

        // 定义需要记录并展示在图表中的列字段及其显示名称
        const CHARTABLE_FIELDS_MAP = {
            "history_run_count": "历史运行次数",
            "history_run_fail_count": "历史运行失败次数",
            "all_consumers_last_x_s_execute_count": "近10秒完成",
            "all_consumers_last_x_s_execute_count_fail": "近10秒失败",
            "all_consumers_last_x_s_avarage_function_spend_time": "近10秒函数运行平均耗时",
            "all_consumers_avarage_function_spend_time_from_start": "累计函数运行平均耗时",
            "msg_num_in_broker": "消息数量"
        };
        // 预定义颜色
        const PREDEFINED_COLORS = [
            '#E60012', '#005AC8', '#00A600', '#FF9900', '#8B28B7', '#9A6324', '#5E8C78', '#F58231', '#42D4F4', '#BF6131', '#3CB44B', '#4363D8', '#F032E6', '#BCF60C', '#FABEBE', '#AAFFC3', '#E6BEFF', '#FFFAC8'
        ];

        function refreshTableData() {
            table.replaceData()
                .then(() => {
                    console.log("Auto-refresh: table data refreshed successfully.");
                })
                .catch(error => {
                    console.error("Auto-refresh: error refreshing table data:", error);
                });
        }

        function toggleAutoRefresh() {
            const button = document.getElementById("toggle-auto-refresh");
            if (isAutoRefreshing) {
                clearInterval(autoRefreshIntervalId);
                isAutoRefreshing = false;
                button.textContent = "启动自动刷新";
                button.classList.remove("btn-danger");
                button.classList.add("btn-success");
                if (table) {
                    table.redraw(true);
                }
            } else {
                isAutoRefreshing = true;
                button.textContent = "暂停自动刷新";
                button.classList.remove("btn-success");
                button.classList.add("btn-danger");
                refreshTableData();
                autoRefreshIntervalId = setInterval(refreshTableData, AUTO_REFRESH_INTERVAL);
            }
        }

        document.getElementById("toggle-auto-refresh").addEventListener("click", toggleAutoRefresh);

        let currentChartQueueName = null;
        let endTimeUserChanged = false;
        document.getElementById("chartEndTime").addEventListener("input", function() {
            endTimeUserChanged = true;
        });
        // 工具函数：将Date对象转为input[type=datetime-local]需要的本地时间字符串
        function toDatetimeLocalString(date) {
            const pad = n => n < 10 ? '0' + n : n;
            return date.getFullYear() + '-' +
                pad(date.getMonth() + 1) + '-' +
                pad(date.getDate()) + 'T' +
                pad(date.getHours()) + ':' +
                pad(date.getMinutes());
        }
        function showQueueChart(queueName) {
            currentChartQueueName = queueName;
            document.getElementById("chartQueueName").textContent = queueName;
            // 设置默认时间范围：最近1小时（本地时区字符串）
            const now = new Date();
            const start = new Date(now.getTime() - 60 * 60 * 1000); // 1小时
            const startStr = toDatetimeLocalString(start);
            const endStr = toDatetimeLocalString(now);
            const minStart = toDatetimeLocalString(new Date(now.getTime() - 24 * 60 * 60 * 1000)); // 24小时
            document.getElementById("chartStartTime").value = startStr;
            document.getElementById("chartEndTime").value = endStr;
            document.getElementById("chartStartTime").setAttribute('max', endStr);
            document.getElementById("chartStartTime").setAttribute('min', minStart);
            document.getElementById("chartEndTime").removeAttribute('max');
            document.getElementById("chartEndTime").setAttribute('min', minStart);
            endTimeUserChanged = false; // 重置
            loadQueueChartData(queueName, Math.floor(start.getTime() / 1000), Math.floor(now.getTime() / 1000));
        }
        function reloadQueueChartWithTimeRange() {
            const start = document.getElementById("chartStartTime").value;
            const end = document.getElementById("chartEndTime").value;
            let start_ts = start ? (new Date(start).getTime() / 1000) : null;
            let end_ts = end ? (new Date(end).getTime() / 1000) : null;
            if (endTimeUserChanged) {
                console.log('用户手动填写了结束时间:', end);
            } else {
                console.log('结束时间为默认值:', end);
            }
            loadQueueChartData(currentChartQueueName, start_ts, end_ts);
        }
        function loadQueueChartData(queueName, start_ts, end_ts) {
            if (chartInstance) chartInstance.destroy();
            const chartCanvas = document.getElementById('queueDataChart');
            const ctx = chartCanvas.getContext('2d');
            ctx.clearRect(0, 0, chartCanvas.width, chartCanvas.height);
            ctx.font = "16px Arial";
            ctx.textAlign = "center";
            ctx.fillText("正在加载数据...", chartCanvas.width / 2, chartCanvas.height / 2);
            let url = `/queue/get_time_series_data/${queueName}`;
            let params = [];
            if (start_ts) params.push(`start_ts=${start_ts}`);
            if (end_ts) params.push(`end_ts=${end_ts}`);
            if (params.length > 0) url += '?' + params.join('&');
            $.get(url, function(response) {
                if (!response || response.length === 0) {
                    ctx.clearRect(0, 0, chartCanvas.width, chartCanvas.height);
                    ctx.fillText("暂无历史数据", chartCanvas.width / 2, chartCanvas.height / 2);
                    $('#chartModal').modal('show');
                    return;
                }
                // 横坐标用本地时间字符串显示
                const labels = response.map(dp => {
                    const d = new Date(dp.report_ts * 1000);
                    return d.toLocaleString('zh-CN', { hour12: false });
                });
                const datasets = Object.keys(CHARTABLE_FIELDS_MAP).map((fieldKey, index) => {
                    const displayName = CHARTABLE_FIELDS_MAP[fieldKey];
                    const isDefaultVisible = fieldKey === 'all_consumers_last_x_s_execute_count' || fieldKey === 'all_consumers_last_x_s_execute_count_fail';
                    return {
                        label: displayName,
                        data: response.map(dp => {
                            let v = dp.report_data[fieldKey];
                            if (typeof v === 'string') v = parseFloat(v);
                            return v === undefined || v === null ? NaN : v;
                        }),
                        fill: false,
                        borderColor: PREDEFINED_COLORS[index % PREDEFINED_COLORS.length],
                        backgroundColor: PREDEFINED_COLORS[index % PREDEFINED_COLORS.length] + '33',
                        tension: 0.4,
                        pointRadius: 1,
                        pointHoverRadius: 3,
                        borderWidth: 2,
                        hidden: !isDefaultVisible
                    };
                });
                chartInstance = new Chart(ctx, {
                    type: 'line',
                    data: { labels, datasets },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            x: {
                                title: { display: true, text: '时间' },
                                ticks: {
                                    autoSkip: true,
                                    maxTicksLimit: 20
                                }
                            },
                            y: { beginAtZero: false, title: { display: true, text: '数值' } }
                        },
                        plugins: {
                            legend: { position: 'top' },
                            title: { display: true, text: `队列 [${queueName}] 各项指标变化趋势` },
                            tooltip: { mode: 'index', intersect: false }
                        },
                        interaction: { mode: 'nearest', axis: 'x', intersect: false }
                    }
                });
                $('#chartModal').modal('show');
            }).fail(function() {
                ctx.clearRect(0, 0, chartCanvas.width, chartCanvas.height);
                ctx.fillText("获取数据失败", chartCanvas.width / 2, chartCanvas.height / 2);
                $('#chartModal').modal('show');
            });
        }

        // 新增：模态框关闭时的处理
        $('#chartModal').on('hidden.bs.modal', function () {
            if (chartInstance) {
                chartInstance.destroy();
                chartInstance = null;
            }
            console.log("Chart modal closed and instance destroyed.");
        });

        // 新增：显示说明模态框的函数
        function showExplanationModal() {
            const explanationTextHtml = `
                <li>消息队列的各项指标数据是 funboost 消费者每隔10秒周期上报到 redis 的，所以不是毫秒级实时，而是10秒级实时。</li>
                <li>"更新所有队列消息数量"按钮和表格"消息数量"列的获取按钮，是实时查询 broker 的消息数量，不是基于消费者上报到 redis 的数据。（因为有的队列可能没有启动相应的消费者，也就没有上报方）</li>
                
            `;
            document.getElementById('explanation-text').innerHTML = explanationTextHtml;
            $('#explanationModal').modal('show');
        }

        // 绑定说明按钮的点击事件
        document.getElementById('show-explanation-btn').addEventListener('click', showExplanationModal);
    </script>
</body>
</html>


<!-- 
 队列名字  broker_kind  消息数量  consumer数量 消费者参数   是否暂停消费状态     操作(这一列都是按钮)
                                                                            获取消息数量、清空队列消息、 暂停消费 、恢复消费
                                                                        
          
                                                                            
     接口   /queue/params_and_active_consumers 返回的是如下字典,字典中的key是队列名字，
     value是一个字典，字典中有两个key，一个是active_consumers，一个是 queue_params ，
     queue_params的broker_kind 是队列的类型，active_consumers 数组长度是 consumer数量
     
     
     显示到表格中

     {
    "queue_test_g01t": {
        "active_consumers": [
            {
                "code_filename": "d:/codes/funboost/test_frame/test_function_status_result_persist/test_persist.py",
                "computer_ip": "10.0.133.57",
                "computer_name": "LAPTOP-7V78BBO2",
                "consumer_id": 2642746547464,
                "consumer_uuid": "5ba1aa04-1067-4173-8ee6-0c1e29f8b015",
                "consuming_function": "f",
                "hearbeat_datetime_str": "2025-02-26 20:29:40",
                "hearbeat_timestamp": 1740572980.216993,
                "process_id": 51852,
                "queue_name": "queue_test_g01t",
                "start_datetime_str": "2025-02-26 20:03:06",
                "start_timestamp": 1740571386.7500842,
                 "execute_task_times_every_unit_time_temp": 2
            }
        ],
        "queue_params": {
            "auto_generate_info": {
                "where_to_instantiate": "d:/codes/funboost/test_frame/test_function_status_result_persist/test_persist.py:10"
            },
            "broker_exclusive_config": {
                "pull_msg_batch_size": 100,
                "redis_bulk_push": 1
            },
            "broker_kind": "REDIS",
            "concurrent_mode": "threading",
            "concurrent_num": 50,
            "consuming_function": "<function f at 0x000002674C8A1708>",
            "consuming_function_kind": "COMMON_FUNCTION",
            "consuming_function_raw": "<function f at 0x000002674C8A1708>",
            "create_logger_file": true,
            "delay_task_apscheduler_jobstores_kind": "redis",
            "do_not_run_by_specify_time": [
                "10:00:00",
                "22:00:00"
            ],
            "do_task_filtering": false,
            "function_result_status_persistance_conf": {
                "expire_seconds": 604800,
                "is_save_result": true,
                "is_save_status": true,
                "is_use_bulk_insert": false
            },
            "is_auto_start_consuming_message": false,
            "is_do_not_run_by_specify_time_effect": false,
            "is_print_detail_exception": true,
            "is_push_to_dlx_queue_when_retry_max_times": false,
            "is_send_consumer_hearbeat_to_redis": true,
            "is_show_message_get_from_broker": false,
            "is_support_remote_kill_task": false,
            "is_using_distributed_frequency_control": false,
            "is_using_rpc_mode": false,
            "log_level": 10,
            "logger_name": "",
            "logger_prefix": "",
            "max_retry_times": 3,
            "publish_msg_log_use_full_msg": false,
            "queue_name": "queue_test_g01t",
            "retry_interval": 0,
            "rpc_result_expire_seconds": 600,
            "schedule_tasks_on_main_thread": false,
            "should_check_publish_func_params": true,
            "task_filtering_expire_seconds": 0
        }
    },
    "queue_test_g02t": {
        "active_consumers": [
            {
                "code_filename": "d:/codes/funboost/test_frame/test_function_status_result_persist/test_persist.py",
                "computer_ip": "10.0.133.57",
                "computer_name": "LAPTOP-7V78BBO2",
                "consumer_id": 2642746605384,
                "consumer_uuid": "a5528e66-2949-47ca-9aea-bbf920165c53",
                "consuming_function": "f2",
                "hearbeat_datetime_str": "2025-02-26 20:29:40",
                "hearbeat_timestamp": 1740572980.13895,
                "process_id": 51852,
                "queue_name": "queue_test_g02t",
                "start_datetime_str": "2025-02-26 20:03:06",
                "start_timestamp": 1740571386.7650468,
                 "execute_task_times_every_unit_time_temp": 2
            }
        ],
        "queue_params": {
            "auto_generate_info": {
                "where_to_instantiate": "d:/codes/funboost/test_frame/test_function_status_result_persist/test_persist.py:18"
            },
            "broker_exclusive_config": {
                "pull_msg_batch_size": 100,
                "redis_bulk_push": 1
            },
            "broker_kind": "REDIS",
            "concurrent_mode": "threading",
            "concurrent_num": 50,
            "consuming_function": "<function f2 at 0x000002674FF5DE58>",
            "consuming_function_kind": "COMMON_FUNCTION",
            "consuming_function_raw": "<function f2 at 0x000002674FF5DE58>",
            "create_logger_file": true,
            "delay_task_apscheduler_jobstores_kind": "redis",
            "do_not_run_by_specify_time": [
                "10:00:00",
                "22:00:00"
            ],
            "do_task_filtering": false,
            "function_result_status_persistance_conf": {
                "expire_seconds": 604800,
                "is_save_result": true,
                "is_save_status": true,
                "is_use_bulk_insert": false
            },
            "is_auto_start_consuming_message": false,
            "is_do_not_run_by_specify_time_effect": false,
            "is_print_detail_exception": true,
            "is_push_to_dlx_queue_when_retry_max_times": false,
            "is_send_consumer_hearbeat_to_redis": true,
            "is_show_message_get_from_broker": false,
            "is_support_remote_kill_task": false,
            "is_using_distributed_frequency_control": false,
            "is_using_rpc_mode": false,
            "log_level": 10,
            "logger_name": "",
            "logger_prefix": "",
            "max_retry_times": 3,
            "publish_msg_log_use_full_msg": false,
            "queue_name": "queue_test_g02t",
            "retry_interval": 0,
            "rpc_result_expire_seconds": 600,
            "schedule_tasks_on_main_thread": false,
            "should_check_publish_func_params": true,
            "task_filtering_expire_seconds": 0
        }
    }
}

-->
```

### 代码文件: funboost\function_result_web\templates\rpc_call.html
```python
<!DOCTYPE html>
<html lang="zh">

<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>pytho万能分布式函数调度框架</title>
    <link href="{{ url_for('static',filename='css_cdn/twitter-bootstrap/3.3.7/css/bootstrap.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static',filename='css_cdn/font-awesome/4.7.0/css/font-awesome.min.css') }}" rel="stylesheet">
    <link rel="stylesheet"
        href="{{ url_for('static',filename='css_cdn/bootstrap-datetimepicker/4.17.47/css/bootstrap-datetimepicker.min.css') }}">
    <link rel="stylesheet" href="{{ url_for('static',filename='assets/css/jquery.mCustomScrollbar.min.css') }}">
    <link rel="stylesheet" href="{{ url_for('static',filename='assets/css/custom.css') }}">

    <!-- 在其他 link 标签后添加 -->
    <link href="{{ url_for('static',filename='css_cdn/select2/4.0.13/css/select2.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static',filename='css/content_page_style.css') }}" rel="stylesheet">


    <script src="{{ url_for('static',filename='js/jquery-1.11.0.min.js') }}" type="text/javascript"></script>
    <!-- <script src="https://cdn.bootcdn.net/ajax/libs/jquery/1.11.0/jquery.min.js"></script> -->
    <!-- 在其他 script 标签后添加 -->
    <!-- <script src="https://cdn.bootcdn.net/ajax/libs/select2/4.0.13/js/select2.min.js"></script> -->
    <script src="{{ url_for('static',filename='/js/select2.min.js') }}"></script>
    <script src="{{ url_for('static',filename='js_cdn/bootstrap/3.3.7/js/bootstrap.min.js') }}"></script>


    <script src="{{ url_for('static',filename='js/moment-with-locales.min.js') }}"></script>
    <script src="{{ url_for('static',filename='js/bootstrap-datetimepicker.min.js') }}"></script>
    <!-- <script src="https://cdn.bootcss.com/bootstrap-datetimepicker/4.17.47/js/bootstrap-datetimepicker.min.js"></script> -->
    <!-- <script type="text/javascript" src="https://cdn.bootcss.com/echarts/3.3.0/echarts.js"></script> -->
    <script type="text/javascript" src="{{ url_for('static',filename='js/echarts.min.js') }}"></script>

    <script src="{{ url_for('static',filename='assets/js/jquery.mCustomScrollbar.concat.min.js') }}"></script>
    <script src="{{ url_for('static',filename='assets/js/custom.js') }}"></script>

        
    <!-- 添加 Tabulator 样式和脚本 -->
    <link href="{{ url_for('static',filename='css_cdn/tabulator-tables@5.5.0/tabulator.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static',filename='css_cdn/tabulator-tables@5.5.0/tabulator_bootstrap3.min.css') }}" rel="stylesheet">
    <script type="text/javascript" src="{{ url_for('static',filename='js_cdn/tabulator-tables@5.5.0/dist/js/tabulator.min.js') }}"></script>

    <style>

    </style>
</head>

<body>

    <div class="container-fluid" style="margin-top: 5px;">
        <!-- 添加发布消息和RPC结果区域 -->
        <div class="row" style="margin-top: 20px;">
            <div class="col-md-6">
                <div style="background-color: #f9f9f9; border-radius: 8px; padding: 20px; border-left: 5px solid #3498db; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h1 style="margin-bottom: 20px;color: red;">发送rpc请求:</h1>
                    <div class="form-group">
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                         
                            <label for="col_name_search" style="margin-right: 5px; white-space: nowrap;">队列名字:</label>
                            <select class="form-control" id="col_name_search" style="width: 500px;">
                                <option value="">请选择队列名字...</option>
                            </select>
                        </div>
                        <textarea class="form-control" id="message_content" rows="7" placeholder="请输入消息体JSON格式，如：{&quot;x&quot;:1,&quot;y&quot;:2}"></textarea>
                    </div>
                    <div class="form-inline" style="margin-bottom: 15px;">
                        <div class="checkbox" style="margin-right: 20px;">
                            <label>
                                <input type="checkbox" id="need_result" checked> 需要返回结果
                            </label>
                        </div>
                        <div class="form-group" style="margin-right: 20px;">
                            <label for="timeout" style="margin-right: 5px;">超时时间(秒)：</label>
                            <input type="number" class="form-control" id="timeout" value="60" style="width: 80px;">
                        </div>
                        <button type="button" class="btn btn-primary" id="send_btn">发送RPC请求</button>
                    </div>
                    <div class="alert alert-info" id="status_display" style="margin-top: 10px;">
                        准备发送RPC请求，请选择队列名称并输入消息内容
                    </div>
                </div>

                <hr style="border-top: 2px dashed #3498db; margin: 40px 0;">

                <div style="background-color: #f9f9f9; border-radius: 8px; padding: 20px; border-left: 5px solid #e74c3c; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h1 style="margin-bottom: 20px;color: red;">获取task_id结果:</h1>
                    <div class="form-group">
                        <div style="display: flex; align-items: center;">
                            <label for="task_id" style="margin-right: 5px; white-space: nowrap;">task_id:</label>
                            <input type="text" class="form-control" id="task_id" style="width: 500px; margin-right: 15px;">
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 15px;">
                        <div style="margin-right: 20px; display: flex; align-items: center;">
                            <label for="task_timeout" style="margin-right: 5px; white-space: nowrap;">超时时间(秒):</label>
                            <input type="number" class="form-control" id="task_timeout" value="30" style="width: 80px;">
                        </div>
                        <button type="button" class="btn btn-primary" id="get_result_btn">获取结果</button>
                    </div>
                    <div class="alert alert-info" id="task_status_display" style="margin-top: 10px;">
                        准备获取结果，请输入task_id
                    </div>
                </div>
                    

            </div>


            <div class="col-md-6">
                <div class="form-group">
                    <label for="rpc_result">RPC结果：</label>
                    <textarea class="form-control" id="rpc_result" rows="39" readonly style="background-color: #1e1e1e; color: #ffffff; font-family: Consolas, Monaco, 'Courier New', monospace; border: 1px solid #333;"></textarea>
                </div>
            </div>
        </div>


        <div id="result-table" style="margin-top: 20px;"></div>
    </div>

    






    <script>

        // 在现有的变量声明后添加
        var allQueues = [];  // 存储所有队列数据
        var currentColName;

        // 页面加载完成后立即获取所有队列
        $(document).ready(function () {
            $.ajax({
                url: "{{ url_for('get_msg_num_all_queues')}}",
                data: {},
                async: true,
                success: function (result) {
                    var html = '<option value="">请选择队列名字...</option>';
                    for (var queueName in result) {
                        var msgCount = result[queueName];
                        html += '<option value="' + queueName + '">' +
                            queueName + '&nbsp;&nbsp;&nbsp;&nbsp;(msg_count:' + msgCount + ')</option>';
                    }
                    $("#col_name_search").html(html);

                    // 初始化选择框的搜索功能
                    $("#col_name_search").select2({
                        placeholder: "请输入队列名称搜索...",
                        allowClear: true,
                        width: '500px',
                        minimumResultsForSearch: 0
                    });

                    // 监听选择变化
                    $("#col_name_search").on('change', function () {
                        var selectedQueue = $(this).val();
                        console.log("Selected queue:", selectedQueue);
                        currentColName = selectedQueue;
                        // if(selectedQueue) {
                        //     queryResult(selectedQueue, 0, true);
                        // }
                    });
                }
            });
        });

        // 添加发送RPC请求的功能
        $(document).ready(function() {
            // 已有的队列加载代码...
            
            // 发送RPC请求按钮点击事件
            $("#send_btn").click(function() {
                var queueName = $("#col_name_search").val();
                var messageContent = $("#message_content").val();
                
                if (!queueName) {
                    alert("请先选择队列名称");
                    return;
                }
                
                if (!messageContent) {
                    alert("请输入消息内容");
                    return;
                }
                
                try {
                    // 尝试解析JSON，确保内容有效
                    JSON.parse(messageContent);
                } catch (e) {
                    alert("消息内容必须是有效的JSON格式");
                    return;
                }
                
                // 更新状态显示
                $("#status_display").removeClass("alert-info alert-success alert-danger").addClass("alert-warning");
                $("#status_display").text("正在发送RPC请求，请稍候...");
                
                // 清空结果框
                $("#rpc_result").val("");
                $("#rpc_result").css({"background-color": "#1e1e1e", "color": "#ffffff"});
                
                // 发送RPC请求
                $.ajax({
                    url: "{{ url_for('rpc_call') }}",
                    type: "POST",
                    contentType: "application/json",
                    data: JSON.stringify({
                        queue_name: queueName,
                        msg_body: JSON.parse(messageContent),
                        need_result: $("#need_result").is(":checked"),
                        timeout: parseInt($("#timeout").val())
                    }),
                    success: function(result) {
                       
                        console.log(result)

                        $("#rpc_result").val(JSON.stringify(result, null, 2));
                        
                        // 更新状态显示
                        if (result.succ) {
                            $("#status_display").removeClass("alert-warning alert-danger").addClass("alert-success");
                            $("#status_display").text("RPC请求成功: " + result.msg);
                            $("#rpc_result").css({"background-color": "#5cb85c", "color": "#ffffff"});
                        } else {
                            $("#status_display").removeClass("alert-warning alert-success").addClass("alert-danger");
                            $("#status_display").text("RPC请求失败: " + result.msg);
                            $("#rpc_result").css({"background-color": "#d9534f", "color": "#ffffff"});
                        }
                    },
                    error: function(xhr, status, error) {
                        $("#rpc_result").val("请求失败: " + error);
                        $("#rpc_result").css({"background-color": "#d9534f", "color": "#ffffff"});
                        
                        // 更新状态显示
                        $("#status_display").removeClass("alert-warning alert-success").addClass("alert-danger");
                        $("#status_display").text("RPC请求发送失败: " + error);
                    }
                });
            });
        });

        // 添加获取结果功能
        $(document).ready(function() {
            // 获取结果按钮点击事件
            $("#get_result_btn").click(function() {
                var taskId = $("#task_id").val();
                
                if (!taskId) {
                    alert("请先输入task_id");
                    return;
                }
                
                // 更新状态显示
                $("#task_status_display").removeClass("alert-info alert-success alert-danger").addClass("alert-warning");
                $("#task_status_display").text("正在获取结果，请稍候...");
                
                // 清空结果框
                $("#rpc_result").val("");
                $("#rpc_result").css({"background-color": "#1e1e1e", "color": "#ffffff"});
                
                // 获取结果
                $.ajax({
                    url: "{{ url_for('get_result_by_task_id') }}",
                    type: "GET",
                    data: {
                        task_id: taskId,
                        timeout: parseInt($("#task_timeout").val())
                    },
                    success: function(result) {
                        console.log(result);
                        $("#rpc_result").val(JSON.stringify(result, null, 2));
                        
                        // 更新状态显示
                        if (result.succ) {
                            $("#task_status_display").removeClass("alert-warning alert-danger").addClass("alert-success");
                            $("#task_status_display").text("获取结果成功");
                            $("#rpc_result").css({"background-color": "#5cb85c", "color": "#ffffff"});
                        } else {
                            $("#task_status_display").removeClass("alert-warning alert-success").addClass("alert-danger");
                            $("#task_status_display").text("获取结果失败: " + result.msg);
                            $("#rpc_result").css({"background-color": "#d9534f", "color": "#ffffff"});
                        }
                    },
                    error: function(xhr, status, error) {
                        $("#rpc_result").val("请求失败: " + error);
                        $("#rpc_result").css({"background-color": "#d9534f", "color": "#ffffff"});
                        
                        // 更新状态显示
                        $("#task_status_display").removeClass("alert-warning alert-success").addClass("alert-danger");
                        $("#task_status_display").text("获取结果失败: " + error);
                    }
                });
            });
        });

            








    </script>
</body>

</html>
```

### 代码文件: funboost\function_result_web\templates\running_consumer_by_ip.html
```python
<!DOCTYPE html>
<html lang="zh">

<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>pytho万能分布式函数调度框架</title>
    <link href="{{ url_for('static',filename='css_cdn/twitter-bootstrap/3.3.7/css/bootstrap.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static',filename='css_cdn/font-awesome/4.7.0/css/font-awesome.min.css') }}" rel="stylesheet">
    <link rel="stylesheet"
        href="{{ url_for('static',filename='css_cdn/bootstrap-datetimepicker/4.17.47/css/bootstrap-datetimepicker.min.css') }}">
    <link rel="stylesheet" href="{{ url_for('static',filename='assets/css/jquery.mCustomScrollbar.min.css') }}">
    <link rel="stylesheet" href="{{ url_for('static',filename='assets/css/custom.css') }}">

    <!-- 在其他 link 标签后添加 -->
    <link href="{{ url_for('static',filename='css_cdn/select2/4.0.13/css/select2.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static',filename='css/content_page_style.css') }}" rel="stylesheet">


    <script src="{{ url_for('static',filename='js/jquery-1.11.0.min.js') }}" type="text/javascript"></script>
    <!-- <script src="https://cdn.bootcdn.net/ajax/libs/jquery/1.11.0/jquery.min.js"></script> -->
    <!-- 在其他 script 标签后添加 -->
    <!-- <script src="https://cdn.bootcdn.net/ajax/libs/select2/4.0.13/js/select2.min.js"></script> -->
    <script src="{{ url_for('static',filename='/js/select2.min.js') }}"></script>
    <script src="{{ url_for('static',filename='js_cdn/bootstrap/3.3.7/js/bootstrap.min.js') }}"></script>


    <script src="{{ url_for('static',filename='js/moment-with-locales.min.js') }}"></script>
    <script src="{{ url_for('static',filename='js/bootstrap-datetimepicker.min.js') }}"></script>
    <!-- <script src="https://cdn.bootcss.com/bootstrap-datetimepicker/4.17.47/js/bootstrap-datetimepicker.min.js"></script> -->
    <!-- <script type="text/javascript" src="https://cdn.bootcss.com/echarts/3.3.0/echarts.js"></script> -->
    <script type="text/javascript" src="{{ url_for('static',filename='js/echarts.min.js') }}"></script>

    <script src="{{ url_for('static',filename='assets/js/jquery.mCustomScrollbar.concat.min.js') }}"></script>
    <script src="{{ url_for('static',filename='assets/js/custom.js') }}"></script>

        
    <!-- 添加 Tabulator 样式和脚本 -->
    <link href="{{ url_for('static',filename='css_cdn/tabulator-tables@5.5.0/tabulator.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static',filename='css_cdn/tabulator-tables@5.5.0/tabulator_bootstrap3.min.css') }}" rel="stylesheet">
    <script type="text/javascript" src="{{ url_for('static',filename='js_cdn/tabulator-tables@5.5.0/dist/js/tabulator.min.js') }}"></script>

    <style>

    </style>
</head>

<body>

    <div class="container-fluid" style="margin-top: 5px;">
        <div style="margin-top: 5px;">
            <form class="form-inline" role="form" style="">
                <div class="form-group ">
                    <label for="col_name_search">host：</label>
                    <select class="form-control" id="col_name_search">
                        <option value="">请选择ip...</option>
                    </select>
                </div>
                <button type="button" class="btn btn-default marginLeft20" onclick="query()">查询</button>
            </form>
        </div>

        <div id="result-table" style="margin-top: 20px;"></div>

    </div>






    <script>

        // 在现有的变量声明后添加
        var allQueues = [];  // 存储所有队列数据
        var currentColName;

        // 页面加载完成后立即获取所有队列
        $(document).ready(function () {
            $.ajax({
                url: "{{ url_for('hearbeat_info_partion_by_ip')}}",
                data: { col_name_search: '' },
                async: true,
                success: function (result) {
                    allQueues = result;
                    var html = '<option value="">请选择ip...</option>';
                    for (var item of result) {
                        html += '<option value="' + item.collection_name + '">' +
                            item.collection_name + '&nbsp;&nbsp;&nbsp;&nbsp;(consumer_count:' + item.count + ')</option>';
                    }
                    $("#col_name_search").html(html);

                    // 初始化选择框的搜索功能
                    $("#col_name_search").select2({
                        placeholder: "请输入ip名称搜索...",
                        allowClear: true,
                        width: '500px'
                    });

                    // 监听选择变化
                    $("#col_name_search").on('change', function () {
                        var selectedQueue = $(this).val();
                        console.log("Selected queue:", selectedQueue);
                        currentColName = selectedQueue;
                        // if(selectedQueue) {
                        //     queryResult(selectedQueue, 0, true);
                        // }
                    });
                }
            });
        });

        $(document).ready(function (){
            query()
        });


        function query() {
            $.ajax({
                url: "{{ url_for('hearbeat_info_by_ip')}}",
                data: { ip: currentColName },
                async: true,
                success: function (result) {
                    console.info(result);

                                      // 创建表格
                        var table = new Tabulator("#result-table", {
                        theme: "bootstrap3",
                        data: result,
                        // layout: "fitColumns",
                        layout: "fitDataTable",  // 改为 fitDataTable
        responsiveLayout: false, // 禁用响应式布局
                        columns: [
                        {title: "<br><br>队列名称", field: "queue_name"},
                            {title: "<br><br>消费函数", field: "consuming_function"},
                            {title: "<br><br>主机名", field: "computer_name"},
                            {title: "<br><br>IP地址", field: "computer_ip"},
                            {title: "<br><br>进程ID", field: "process_id"},
                            {title: "<br><br>启动时间", field: "start_datetime_str","width":200},
                            {title: "<br><br>最近心跳时间", field: "hearbeat_datetime_str","width":200},
                           
                            {title:"近10秒<br>运行完成<br>消息个数",field:"last_x_s_execute_count", formatter:"html","width":100},
                            {title:"近10秒<br>运行失败<br>消息个数",field:"last_x_s_execute_count_fail", formatter:"html","width":100},
                            {title:"近10秒<br>函数运行<br>平均耗时",field:"last_x_s_avarage_function_spend_time", formatter:"html","width":100},
                            
                            {title:"累计<br>运行完成<br>消息个数",field:"total_consume_count_from_start", formatter:"html","width":100},
                            {title:"累计<br>运行失败<br>消息个数",field:"total_consume_count_from_start_fail", formatter:"html","width":100},
                            {title:"累计<br>函数运行<br>平均耗时",field:"avarage_function_spend_time_from_start", formatter:"html","width":100},
                             
                            {title: "<br><br>代码文件", field: "code_filename"},
                            // {title: "<br><br>consumer_id", field: "consumer_id"},
                            {title: "<br><br>consumer_uuid", field: "consumer_uuid"},
                        ],
                        pagination: true,
                        paginationSize: 1000,
                        locale: true,
                        langs: {
                            "zh-cn": {
                                "pagination": {
                                    "first": "首页",
                                    "first_title": "首页",
                                    "last": "末页",
                                    "last_title": "末页",
                                    "prev": "上一页",
                                    "prev_title": "上一页",
                                    "next": "下一页",
                                    "next_title": "下一页",
                                }
                            }
                        }
                    });
                    /* result 例如 [
  {
    "code_filename": "d:/codes/funboost/test_frame/test_function_status_result_persist/test_persist.py", 
    "computer_ip": "10.0.133.57", 
    "computer_name": "LAPTOP-7V78BBO2", 
    "consumer_id": 1462882757512, 
    "consumer_uuid": "88f568f7-9723-48ef-9cac-0370b2333a49", 
    "consuming_function": "f2", 
    "hearbeat_datetime_str": "2025-02-25 17:28:36", 
    "hearbeat_timestamp": 1740475716.783474, 
    "process_id": 34788, 
    "queue_name": "queue_test_f02t", 
    "start_datetime_str": "2025-02-25 16:33:19", 
    "start_timestamp": 1740472399.4628778
  }, 
  {
    "code_filename": "d:/codes/funboost/test_frame/test_function_status_result_persist/test_persist.py", 
    "computer_ip": "10.0.133.57", 
    "computer_name": "LAPTOP-7V78BBO2", 
    "consumer_id": 1462882671944, 
    "consumer_uuid": "c52a8596-d632-4bac-a797-80375288f381", 
    "consuming_function": "f", 
    "hearbeat_datetime_str": "2025-02-25 17:28:36", 
    "hearbeat_timestamp": 1740475716.783336, 
    "process_id": 34788, 
    "queue_name": "queue_test_f01t", 
    "start_datetime_str": "2025-02-25 16:33:19", 
    "start_timestamp": 1740472399.4503505
  }
]
  */

                }
            });
        }








    </script>
</body>

</html>
```

### 代码文件: funboost\function_result_web\templates\running_consumer_by_queue_name.html
```python
<!DOCTYPE html>
<html lang="zh">

<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>pytho万能分布式函数调度框架</title>
    <link href="{{ url_for('static',filename='css_cdn/twitter-bootstrap/3.3.7/css/bootstrap.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static',filename='css_cdn/font-awesome/4.7.0/css/font-awesome.min.css') }}" rel="stylesheet">
    <link rel="stylesheet"
        href="{{ url_for('static',filename='css_cdn/bootstrap-datetimepicker/4.17.47/css/bootstrap-datetimepicker.min.css') }}">
    <link rel="stylesheet" href="{{ url_for('static',filename='assets/css/jquery.mCustomScrollbar.min.css') }}">
    <link rel="stylesheet" href="{{ url_for('static',filename='assets/css/custom.css') }}">

    <!-- 在其他 link 标签后添加 -->
    <link href="{{ url_for('static',filename='css_cdn/select2/4.0.13/css/select2.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static',filename='css/content_page_style.css') }}" rel="stylesheet">


    <script src="{{ url_for('static',filename='js/jquery-1.11.0.min.js') }}" type="text/javascript"></script>
    <!-- <script src="https://cdn.bootcdn.net/ajax/libs/jquery/1.11.0/jquery.min.js"></script> -->
    <!-- 在其他 script 标签后添加 -->
    <!-- <script src="https://cdn.bootcdn.net/ajax/libs/select2/4.0.13/js/select2.min.js"></script> -->
    <script src="{{ url_for('static',filename='/js/select2.min.js') }}"></script>
    <script src="{{ url_for('static',filename='js_cdn/bootstrap/3.3.7/js/bootstrap.min.js') }}"></script>


    <script src="{{ url_for('static',filename='js/moment-with-locales.min.js') }}"></script>
    <script src="{{ url_for('static',filename='js/bootstrap-datetimepicker.min.js') }}"></script>
    <!-- <script src="https://cdn.bootcss.com/bootstrap-datetimepicker/4.17.47/js/bootstrap-datetimepicker.min.js"></script> -->
    <!-- <script type="text/javascript" src="https://cdn.bootcss.com/echarts/3.3.0/echarts.js"></script> -->
    <script type="text/javascript" src="{{ url_for('static',filename='js/echarts.min.js') }}"></script>

    <script src="{{ url_for('static',filename='assets/js/jquery.mCustomScrollbar.concat.min.js') }}"></script>
    <script src="{{ url_for('static',filename='assets/js/custom.js') }}"></script>

        
    <!-- 添加 Tabulator 样式和脚本 -->
    <link href="{{ url_for('static',filename='css_cdn/tabulator-tables@5.5.0/tabulator.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static',filename='css_cdn/tabulator-tables@5.5.0/tabulator_bootstrap3.min.css') }}" rel="stylesheet">
    <script type="text/javascript" src="{{ url_for('static',filename='js_cdn/tabulator-tables@5.5.0/dist/js/tabulator.min.js') }}"></script>

    <style>

    </style>
</head>

<body>

    <div class="container-fluid" style="margin-top: 5px;">
        <div style="margin-top: 5px;">
            <form class="form-inline" role="form" style="">
                <div class="form-group ">
                    <label for="col_name_search">队列名字：</label>
                    <select class="form-control" id="col_name_search">
                        <option value="">请选择队列名字...</option>
                    </select>
                </div>
                <button type="button" class="btn btn-default marginLeft20" onclick="query()">查询</button>
            </form>
        </div>

        <div id="result-table" style="margin-top: 20px;"></div>

    </div>






    <script>

        // 在现有的变量声明后添加
        var allQueues = [];  // 存储所有队列数据
        var currentColName;

        // 页面加载完成后立即获取所有队列
        $(document).ready(function () {
            $.ajax({
                url: "{{ url_for('hearbeat_info_partion_by_queue_name')}}",
                data: { col_name_search: '' },
                async: true,
                success: function (result) {
                    allQueues = result;
                    var html = '<option value="">请选择队列名字...</option>';
                    for (var item of result) {
                        html += '<option value="' + item.collection_name + '">' +
                            item.collection_name + '&nbsp;&nbsp;&nbsp;&nbsp;(consumer_count:' + item.count + ')</option>';
                    }
                    $("#col_name_search").html(html);

                    // 初始化选择框的搜索功能
                    $("#col_name_search").select2({
                        placeholder: "请输入队列名称搜索...",
                        allowClear: true,
                        width: '500px'
                    });

                    // 监听选择变化
                    $("#col_name_search").on('change', function () {
                        var selectedQueue = $(this).val();
                        console.log("Selected queue:", selectedQueue);
                        currentColName = selectedQueue;
                        // if(selectedQueue) {
                        //     queryResult(selectedQueue, 0, true);
                        // }
                    });
                }
            });
        });

        $(document).ready(function (){
            query()
        });

        function query() {
            $.ajax({
                url: "{{ url_for('hearbeat_info_by_queue_name')}}",
                data: { queue_name: currentColName },
                async: true,
                success: function (result) {
                    console.info(result);

                                      // 创建表格
                        var table = new Tabulator("#result-table", {
                        theme: "bootstrap3",
                        data: result,
                     
                         // layout: "fitColumns",
                         layout: "fitDataTable",  // 改为 fitDataTable
        responsiveLayout: false, // 禁用响应式布局
                        columns: [
                        {title: "<br><br>队列名称", field: "queue_name"},
                            {title: "<br><br>消费函数", field: "consuming_function"},
                            {title: "<br><br>主机名", field: "computer_name"},
                            {title: "<br><br>IP地址", field: "computer_ip"},
                            {title: "<br><br>进程ID", field: "process_id"},
                            {title: "<br><br>启动时间", field: "start_datetime_str","width":200},
                            {title: "<br><br>最近心跳时间", field: "hearbeat_datetime_str","width":200},
                            
                            {title:"近10秒<br>运行完成<br>消息个数",field:"last_x_s_execute_count", formatter:"html","width":100},
                            {title:"近10秒<br>运行失败<br>消息个数",field:"last_x_s_execute_count_fail", formatter:"html","width":100},
                            {title:"近10秒<br>函数运行<br>平均耗时",field:"last_x_s_avarage_function_spend_time", formatter:"html","width":100},
                            
                            {title:"累计<br>运行完成<br>消息个数",field:"total_consume_count_from_start", formatter:"html","width":100},
                            {title:"累计<br>运行失败<br>消息个数",field:"total_consume_count_from_start_fail", formatter:"html","width":100},
                            {title:"累计<br>函数运行<br>平均耗时",field:"avarage_function_spend_time_from_start", formatter:"html","width":100},

                            {title: "<br><br>代码文件", field: "code_filename"},
                            // {title: "<br><br>consumer_id", field: "consumer_id"},
                            {title: "<br><br>consumer_uuid", field: "consumer_uuid"},
                        ],
                        pagination: true,
                        paginationSize: 1000,
                        locale: true,
                        langs: {
                            "zh-cn": {
                                "pagination": {
                                    "first": "首页",
                                    "first_title": "首页",
                                    "last": "末页",
                                    "last_title": "末页",
                                    "prev": "上一页",
                                    "prev_title": "上一页",
                                    "next": "下一页",
                                    "next_title": "下一页",
                                }
                            }
                        }
                    });

                    /* result 例如 [
  {
    "code_filename": "d:/codes/funboost/test_frame/test_function_status_result_persist/test_persist.py", 
    "computer_ip": "10.0.133.57", 
    "computer_name": "LAPTOP-7V78BBO2", 
    "consumer_id": 1462882757512, 
    "consumer_uuid": "88f568f7-9723-48ef-9cac-0370b2333a49", 
    "consuming_function": "f2", 
    "hearbeat_datetime_str": "2025-02-25 17:28:36", 
    "hearbeat_timestamp": 1740475716.783474, 
    "process_id": 34788, 
    "queue_name": "queue_test_f02t", 
    "start_datetime_str": "2025-02-25 16:33:19", 
    "start_timestamp": 1740472399.4628778
  }, 
  {
    "code_filename": "d:/codes/funboost/test_frame/test_function_status_result_persist/test_persist.py", 
    "computer_ip": "10.0.133.57", 
    "computer_name": "LAPTOP-7V78BBO2", 
    "consumer_id": 1462882671944, 
    "consumer_uuid": "c52a8596-d632-4bac-a797-80375288f381", 
    "consuming_function": "f", 
    "hearbeat_datetime_str": "2025-02-25 17:28:36", 
    "hearbeat_timestamp": 1740475716.783336, 
    "process_id": 34788, 
    "queue_name": "queue_test_f01t", 
    "start_datetime_str": "2025-02-25 16:33:19", 
    "start_timestamp": 1740472399.4503505
  }
]
  */

                }
            });
        }








    </script>
</body>

</html>
```

### 代码文件: funboost\publishers\base_publisher.py
```python
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
from re import S
import sys
import threading
import time
import typing
from functools import wraps
from threading import Lock

import nb_log
from funboost.constant import ConstStrForClassMethod, FunctionKind
from funboost.core.func_params_model import PublisherParams, PriorityConsumingControlConfig
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

RedisAsyncResult = AsyncResult  # 别名
RedisAioAsyncResult = AioAsyncResult  # 别名


# class PriorityConsumingControlConfig:
#     """
#     为每个独立的任务设置控制参数，和函数参数一起发布到中间件。可能有少数时候有这种需求。
#     例如消费为add函数，可以每个独立的任务设置不同的超时时间，不同的重试次数，是否使用rpc模式。这里的配置优先，可以覆盖生成消费者时候的配置。
#     """
#
#     def __init__(self, function_timeout: float = None, max_retry_times: int = None,
#                  is_print_detail_exception: bool = None,
#                  msg_expire_senconds: int = None,
#                  is_using_rpc_mode: bool = None,
#
#                  countdown: typing.Union[float, int] = None,
#                  eta: datetime.datetime = None,
#                  misfire_grace_time: typing.Union[int, None] = None,
#
#                  other_extra_params: dict = None,
#
#                  ):
#         """
#
#         :param function_timeout: 超时杀死
#         :param max_retry_times:
#         :param is_print_detail_exception:
#         :param msg_expire_senconds:
#         :param is_using_rpc_mode: rpc模式才能在发布端获取结果
#         :param eta: 规定什么时候运行
#         :param countdown: 规定多少秒后运行
#         # execute_delay_task_even_if_when_task_is_expired
#         :param misfire_grace_time: 单位为秒。这个参数是配合 eta 或 countdown 使用的。是延时任务专用配置.
#
#                一个延时任务，例如规定发布10秒后才运行，但由于消费速度慢导致任务积压，导致任务还没轮到开始消费就已经过了30秒，
#                如果 misfire_grace_time 配置的值是大于20则会依旧运行。如果配置的值是5，那么由于10 + 5 < 30,所以不会执行。
#
#                例如规定18点运行，但由于消费速度慢导致任务积压，导致任务还没轮到开始消费就已经过了18点10分
#                ，如果 misfire_grace_time设置为700，则这个任务会被执行，如果设置为300，忧郁18点10分超过了18点5分，就不会执行。
#
#                misfire_grace_time 如果设置为None，则任务永远不会过期，一定会被执行。
#                misfire_grace_time 的值要么是大于1的整数， 要么等于None
#
#                此含义也可以百度 apscheduler包的 misfire_grace_time 参数的含义。
#
#         """
#         self.function_timeout = function_timeout
#         self.max_retry_times = max_retry_times
#         self.is_print_detail_exception = is_print_detail_exception
#         self.msg_expire_senconds = msg_expire_senconds
#         self.is_using_rpc_mode = is_using_rpc_mode
#
#         if countdown and eta:
#             raise ValueError('不能同时设置eta和countdown')
#         self.eta = eta
#         self.countdown = countdown
#         self.misfire_grace_time = misfire_grace_time
#         if misfire_grace_time is not None and misfire_grace_time < 1:
#             raise ValueError(f'misfire_grace_time 的值要么是大于1的整数， 要么等于None')
#
#         self.other_extra_params = other_extra_params
#
#     def to_dict(self):
#         if isinstance(self.countdown, datetime.datetime):
#             self.countdown = time_util.DatetimeConverter(self.countdown).datetime_str
#         priority_consuming_control_config_dict = {k: v for k, v in self.__dict__.items() if v is not None}  # 使中间件消息不要太长，框架默认的值不发到中间件。
#         return priority_consuming_control_config_dict


class PublishParamsChecker(FunboostFileLoggerMixin):
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
        self.logger.debug(f'{func} 函数的入参要求是 全字段 {self.all_arg_name_set} ,必须字段为 {self.position_arg_name_set} ')

    def check_params(self, publish_params: dict):
        publish_params_keys_set = set(publish_params.keys())
        if publish_params_keys_set.issubset(self.all_arg_name_set) and publish_params_keys_set.issuperset(
                self.position_arg_name_set):
            return True
        else:
            raise ValueError(f'你发布的参数不正确，你发布的任务的所有键是 {publish_params_keys_set}， '
                             f'必须是 {self.all_arg_name_set} 的子集， 必须是 {self.position_arg_name_set} 的超集')


class AbstractPublisher(LoggerLevelSetterMixin, metaclass=abc.ABCMeta, ):
    def __init__(self, publisher_params: PublisherParams, ):
        self.publisher_params = publisher_params
        self.queue_name = self._queue_name = publisher_params.queue_name
        self.logger: logging.Logger
        self._build_logger()
        self.publish_params_checker = PublishParamsChecker(publisher_params.consuming_function) if publisher_params.consuming_function else None

        self.has_init_broker = 0
        self._lock_for_count = Lock()
        self._current_time = None
        self.count_per_minute = None
        self._init_count()
        self.custom_init()
        self.logger.info(f'{self.__class__} 被实例化了')
        self.publish_msg_num_total = 0

        self.__init_time = time.time()
        atexit.register(self._at_exit)
        if publisher_params.clear_queue_within_init:
            self.clear()

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
                     priority_control_config: PriorityConsumingControlConfig = None) -> (typing.Dict, typing.Dict, typing.Dict, str):
        msg = Serialization.to_dict(msg)
        msg_function_kw = copy.deepcopy(msg)
        raw_extra = {}
        if 'extra' in msg:
            msg_function_kw.pop('extra')
            raw_extra = msg['extra']
        if self.publish_params_checker and self.publisher_params.should_check_publish_func_params:
            self.publish_params_checker.check_params(msg_function_kw)
        task_id = task_id or MsgGenerater.generate_task_id(self._queue_name)
        extra_params = MsgGenerater.generate_pulish_time_and_task_id(self._queue_name, task_id=task_id)
        if priority_control_config:
            extra_params.update(Serialization.to_dict(priority_control_config.json(exclude_none=True))) # priority_control_config.json 是为了充分使用 pydantic的自定义时间格式化字符串
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
        msg = copy.deepcopy(msg)  # 字典是可变对象,不要改变影响用户自身的传参字典. 用户可能继续使用这个传参字典.
        msg, msg_function_kw, extra_params, task_id = self._convert_msg(msg, task_id, priority_control_config)
        t_start = time.time()

        can_not_json_serializable_keys = Serialization.find_can_not_json_serializable_keys(msg)
        if can_not_json_serializable_keys:
            pass
            self.logger.warning(f'msg 中包含不能序列化的键: {can_not_json_serializable_keys}')
            # raise ValueError(f'msg 中包含不能序列化的键: {can_not_json_serializable_keys}')
            new_msg = copy.deepcopy(Serialization.to_dict(msg))
            for key in can_not_json_serializable_keys:
                new_msg[key] = PickleHelper.to_str(new_msg[key])
            new_msg['extra']['can_not_json_serializable_keys'] = can_not_json_serializable_keys
            msg_json = Serialization.to_json_str(new_msg)
        else:
            msg_json = Serialization.to_json_str(msg)
        # print(msg_json)
        decorators.handle_exception(retry_times=10, is_throw_error=True, time_sleep=0.1)(
            self.concrete_realization_of_publish)(msg_json)

        self.logger.debug(f'向{self._queue_name} 队列，推送消息 耗时{round(time.time() - t_start, 4)}秒  {msg_json if self.publisher_params.publish_msg_log_use_full_msg else msg_function_kw}',
                          extra={'task_id': task_id})  # 显示msg太长了。
        with self._lock_for_count:
            self.count_per_minute += 1
            self.publish_msg_num_total += 1
            if time.time() - self._current_time > 10:
                self.logger.info(
                    f'10秒内推送了 {self.count_per_minute} 条消息,累计推送了 {self.publish_msg_num_total} 条消息到 {self._queue_name} 队列中')
                self._init_count()
        return AsyncResult(task_id)

    def send_msg(self, msg: typing.Union[dict, str]):
        """直接发送任意消息内容到消息队列,不生成辅助参数,无视函数入参名字,不校验入参个数和键名"""
        decorators.handle_exception(retry_times=10, is_throw_error=True, time_sleep=0.1)(
            self.concrete_realization_of_publish)(Serialization.to_json_str(msg))

    @staticmethod
    def __get_cls_file(cls: type):
        if cls.__module__ == '__main__':
            cls_file = Path(sys.argv[0]).resolve().as_posix()
        else:
            cls_file = Path(sys.modules[cls.__module__].__file__).resolve().as_posix()
        return cls_file

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

            func_args_list[0] = {ConstStrForClassMethod.FIRST_PARAM_NAME: self.publish_params_checker.all_arg_name[0],
                                 ConstStrForClassMethod.CLS_NAME: cls.__name__,
                                 ConstStrForClassMethod.CLS_FILE: self.__get_cls_file(cls),
                                 ConstStrForClassMethod.CLS_MODULE: PathHelper(self.__get_cls_file(cls)).get_module_name(),
                                 }
        elif self.publisher_params.consuming_function_kind == FunctionKind.INSTANCE_METHOD:
            obj = func_args[0]
            cls = type(obj)
            if not hasattr(obj, ConstStrForClassMethod.OBJ_INIT_PARAMS):
                raise ValueError(f'消费函数 {self.publisher_params.consuming_function} 是实例方法，实例必须有 {ConstStrForClassMethod.OBJ_INIT_PARAMS} 属性')
            func_args_list[0] = {ConstStrForClassMethod.FIRST_PARAM_NAME: self.publish_params_checker.all_arg_name[0],
                                 ConstStrForClassMethod.CLS_NAME: cls.__name__,
                                 ConstStrForClassMethod.CLS_FILE: self.__get_cls_file(cls),
                                 ConstStrForClassMethod.CLS_MODULE: PathHelper(self.__get_cls_file(cls)).get_module_name(),
                                 ConstStrForClassMethod.OBJ_INIT_PARAMS: getattr(obj, ConstStrForClassMethod.OBJ_INIT_PARAMS),

                                 }

        for index, arg in enumerate(func_args_list):
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
            except Exception as e:
                import amqpstorm
                from pikav1.exceptions import AMQPError as PikaAMQPError
                if isinstance(e, (PikaAMQPError, amqpstorm.AMQPError)):
                    # except (PikaAMQPError, amqpstorm.AMQPError,) as e:  # except BaseException as e:   # 现在装饰器用到了绝大多出地方，单个异常类型不行。ex
                    self.logger.error(f'中间件链接出错   ,方法 {f.__name__}  出错 ，{e}')
                    self.init_broker()
                    return f(self, *args, **kwargs)
            except BaseException as e:
                self.logger.critical(e, exc_info=True)

    return _deco_mq_conn_error

```

### 代码文件: funboost\publishers\celery_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import os
import sys
import time
import celery
import celery.result
import typing

from funboost.assist.celery_helper import celery_app
from funboost.publishers.base_publisher import AbstractPublisher, PriorityConsumingControlConfig


class CeleryPublisher(AbstractPublisher, ):
    """
    使用celery作为中间件
    """

    def publish(self, msg: typing.Union[str, dict], task_id=None,
                priority_control_config: PriorityConsumingControlConfig = None) -> celery.result.AsyncResult:
        msg, msg_function_kw, extra_params,task_id = self._convert_msg(msg, task_id, priority_control_config)
        t_start = time.time()
        celery_result = celery_app.send_task(name=self.queue_name, kwargs=msg_function_kw, task_id=extra_params['task_id'])  # type: celery.result.AsyncResult
        self.logger.debug(f'向{self._queue_name} 队列，推送消息 耗时{round(time.time() - t_start, 4)}秒  {msg_function_kw}')  # 显示msg太长了。
        with self._lock_for_count:
            self.count_per_minute += 1
            self.publish_msg_num_total += 1
            if time.time() - self._current_time > 10:
                self.logger.info(
                    f'10秒内推送了 {self.count_per_minute} 条消息,累计推送了 {self.publish_msg_num_total} 条消息到 {self._queue_name} 队列中')
                self._init_count()
        # return AsyncResult(task_id)
        return celery_result  # 这里返回celery结果原生对象，类型是 celery.result.AsyncResult。

    def concrete_realization_of_publish(self, msg):
        pass

    def clear(self):
        python_executable = sys.executable
        cmd = f''' {python_executable} -m celery -A funboost.publishers.celery_publisher purge -Q {self.queue_name} -f'''
        self.logger.warning(f'刪除celery {self.queue_name} 隊列中的消息  {cmd}')
        os.system(cmd)

    def get_message_count(self):
        # return -1
        with celery_app.connection_or_acquire() as conn:
            msg_cnt = conn.default_channel.queue_declare(
                queue=self.queue_name, passive=False,durable=True,auto_delete=False).message_count

        return msg_cnt

    def close(self):
        pass

```

### 代码文件: funboost\publishers\celery_publisher000.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import uuid
import copy
import time
import threading
import json
import celery
import celery.result
import typing

from funboost.publishers.base_publisher import AbstractPublisher, PriorityConsumingControlConfig
from funboost.funboost_config_deafult import BrokerConnConfig,FunboostCommonConfig


# celery_app = celery.Celery(broker='redis://192.168.64.151:6378/11',task_routes={})


class CeleryPublisher(AbstractPublisher, ):
    """
    使用celery作为中间件
    """
    celery_conf_lock = threading.Lock()

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        # self.consumer_params.broker_exclusive_config['task_routes'] = {self.queue_name: {"queue": self.queue_name}}
        # celery_app.config_from_object(self.consumer_params.broker_exclusive_config)
        pass

        # celery_app.conf.task_routes.update({self.queue_name: {"queue": self.queue_name}})
        #
        # @celery_app.task(name=self.queue_name)
        # def f(*args, **kwargs):
        #     pass
        #
        # self._celery_app = celery_app
        # self._celery_fun = f

        self._has_build_celery_app = False

    def _build_celery_app(self):
        celery_app = celery.Celery(broker=BrokerConnConfig.CELERY_BROKER_URL,
                                   backend=BrokerConnConfig.CELERY_RESULT_BACKEND,
                                   task_routes={}, timezone=FunboostCommonConfig.TIMEZONE, enable_utc=False)
        celery_app.config_from_object(self.consumer_params.broker_exclusive_config['celery_app_config'])
        celery_app.conf.task_routes.update({self.queue_name: {"queue": self.queue_name}})

        @celery_app.task(name=self.queue_name)
        def f(*args, **kwargs):
            pass

        self._celery_app = celery_app
        self._celery_fun = f

        self._has_build_celery_app = True

    def publish(self, msg: typing.Union[str, dict], task_id=None,
                priority_control_config: PriorityConsumingControlConfig = None) -> celery.result.AsyncResult:
        if isinstance(msg, str):
            msg = json.loads(msg)
        msg_function_kw = copy.copy(msg)
        if self.publish_params_checker:
            self.publish_params_checker.check_params(msg)
        task_id = task_id or f'{self._queue_name}_result:{uuid.uuid4()}'
        msg['extra'] = extra_params = {'task_id': task_id, 'publish_time': round(time.time(), 4),
                                       'publish_time_format': time.strftime('%Y-%m-%d %H:%M:%S')}
        if priority_control_config:
            extra_params.update(priority_control_config.to_dict())
        with self.celery_conf_lock:
            if not self._has_build_celery_app:
                self._build_celery_app()
        t_start = time.time()
        celery_result = self._celery_fun.apply_async(kwargs=msg_function_kw, task_id=extra_params['task_id'])  # type: celery.result.AsyncResult
        self.logger.debug(f'向{self._queue_name} 队列，推送消息 耗时{round(time.time() - t_start, 4)}秒  {msg_function_kw}')  # 显示msg太长了。
        with self._lock_for_count:
            self.count_per_minute += 1
            self.publish_msg_num_total += 1
            if time.time() - self._current_time > 10:
                self.logger.info(
                    f'10秒内推送了 {self.count_per_minute} 条消息,累计推送了 {self.publish_msg_num_total} 条消息到 {self._queue_name} 队列中')
                self._init_count()
        # return AsyncResult(task_id)
        return celery_result  # 这里返回celery结果原生对象，类型是 celery.result.AsyncResult。

    def concrete_realization_of_publish(self, msg):
        pass

    def clear(self):
        pass

    def get_message_count(self):
        return -1

    def close(self):
        pass

```

### 代码文件: funboost\publishers\confluent_kafka_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/20 0008 12:12

import os

from funboost.core.lazy_impoter import KafkaPythonImporter

if os.name == 'nt':
    """
    为了保险起见，这样做一下,设置一下path，否则anaconda安装的python可能出现 ImportError: DLL load failed while importing cimpl: 找不到指定的模块。
    多设置没事，少设置了才麻烦。
    """
    from pathlib import Path
    import sys

    # print(sys.executable)  #F:\minicondadir\Miniconda2\envs\py38\python.exe
    # print(os.getenv('path'))
    python_install_path = Path(sys.executable).parent.absolute()
    kafka_libs_path = python_install_path / Path(r'.\Lib\site-packages\confluent_kafka.libs')
    dlls_path = python_install_path / Path(r'.\DLLs')
    library_bin_path = python_install_path / Path(r'.\Library\bin')
    # print(library_bin_path)
    path_env = os.getenv('path')
    os.environ['path'] = f'''{path_env};{kafka_libs_path};{dlls_path};{library_bin_path};'''

import atexit
import time

from confluent_kafka import Producer as ConfluentProducer
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher


class ConfluentKafkaPublisher(AbstractPublisher, ):
    """
    使用kafka作为中间件，这个confluent_kafka包的性能远强于 kafka-pyhton
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):

        # self._producer = KafkaProducer(bootstrap_servers=funboost_config_deafult.KAFKA_BOOTSTRAP_SERVERS)
        try:
            admin_client = KafkaPythonImporter().KafkaAdminClient(bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS)
            admin_client.create_topics([KafkaPythonImporter().NewTopic(self._queue_name, 10, 1)])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except KafkaPythonImporter().TopicAlreadyExistsError:
            pass
        except BaseException as e:
            self.logger.exception(e)
        atexit.register(self.close)  # 程序退出前不主动关闭，会报错。
        self._confluent_producer = ConfluentProducer({'bootstrap.servers': ','.join(BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS)})
        self._recent_produce_time = time.time()

    # noinspection PyAttributeOutsideInit
    def concrete_realization_of_publish(self, msg):
        # noinspection PyTypeChecker
        # self.logger.debug(msg)
        self._confluent_producer.produce(self._queue_name, msg.encode(), )
        if time.time() - self._recent_produce_time > 1:
            self._confluent_producer.flush()
            self._recent_produce_time = time.time()

    def clear(self):
        self.logger.warning('还没开始实现 kafka 清空 消息')
        # self._consumer.seek_to_end()
        # self.logger.warning(f'将kafka offset 重置到最后位置')

    def get_message_count(self):
        return -1  # 还没找到获取所有分区未消费数量的方法。

    def close(self):
        pass
        # self._confluent_producer.

    def _at_exit(self):
        # self._producer.flush()
        self._confluent_producer.flush()
        super()._at_exit()


class SaslPlainKafkaPublisher(ConfluentKafkaPublisher):
    """
    使用kafka作为中间件，这个confluent_kafka包的性能远强于 kafka-pyhton
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        # self._producer = KafkaProducer(bootstrap_servers=funboost_config_deafult.KAFKA_BOOTSTRAP_SERVERS)
        try:
            admin_client = KafkaPythonImporter().KafkaAdminClient(**BrokerConnConfig.KFFKA_SASL_CONFIG)
            admin_client.create_topics([KafkaPythonImporter().NewTopic(self._queue_name, 10, 1)])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except KafkaPythonImporter().TopicAlreadyExistsError:
            pass
        except BaseException as e:
            self.logger.exception(e)
        atexit.register(self.close)  # 程序退出前不主动关闭，会报错。
        self._confluent_producer = ConfluentProducer({
            'bootstrap.servers': ','.join(BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS),
            'security.protocol': BrokerConnConfig.KFFKA_SASL_CONFIG['security_protocol'],
            'sasl.mechanisms': BrokerConnConfig.KFFKA_SASL_CONFIG['sasl_mechanism'],
            'sasl.username': BrokerConnConfig.KFFKA_SASL_CONFIG['sasl_plain_username'],
            'sasl.password': BrokerConnConfig.KFFKA_SASL_CONFIG['sasl_plain_password']
        })
        self._recent_produce_time = time.time()

```

### 代码文件: funboost\publishers\dramatiq_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf

import copy
import json

from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.assist.dramatiq_helper import DramatiqHelper
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.utils.redis_manager import RedisMixin


class DramatiqPublisher(AbstractPublisher, ):
    """
    使用dramatiq框架作为中间件
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        pass

    def concrete_realization_of_publish(self, msg):
        if isinstance(msg, str):
            msg = json.loads(msg)
        msg_function_kw = copy.deepcopy(msg)
        if 'extra' in msg:
            msg_function_kw.pop('extra')
        DramatiqHelper.queue_name__actor_map[self.queue_name].send(**msg_function_kw)

    def clear(self):
        DramatiqHelper.broker.flush(self.queue_name)

    def get_message_count(self):
        # pass
        # return -1
        if BrokerConnConfig.DRAMATIQ_URL.startswith('redis'):
            return RedisMixin().redis_db_frame.llen(self.queue_name)  # redis 无，需要自己实现
        if BrokerConnConfig.DRAMATIQ_URL.startswith('amqp'):
            cnts = DramatiqHelper.broker.get_queue_message_counts(self.queue_name)
            return cnts[0]
        return -1

    def close(self):
        DramatiqHelper.broker.close()

```

### 代码文件: funboost\publishers\empty_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/8 0008 12:12

import abc
from funboost.publishers.base_publisher import AbstractPublisher


class EmptyPublisher(AbstractPublisher, metaclass=abc.ABCMeta):
    """
    空的发布者，空的实现，需要搭配 boost入参的 consumer_override_cls 和 publisher_override_cls使用，或者被继承。
    """

    def custom_init(self):
        pass

    @abc.abstractmethod
    def concrete_realization_of_publish(self, msg: str):
        raise NotImplemented('not realization')

    @abc.abstractmethod
    def clear(self):
        raise NotImplemented('not realization')

    @abc.abstractmethod
    def get_message_count(self):
        raise NotImplemented('not realization')

    @abc.abstractmethod
    def close(self):
        raise NotImplemented('not realization')

```

### 代码文件: funboost\publishers\faststream_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/8 0008 12:12

import abc
import asyncio
import json
import time
import typing

from funboost import PriorityConsumingControlConfig
from funboost.concurrent_pool.async_helper import get_or_create_event_loop
from funboost.core.serialization import Serialization
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.assist.faststream_helper import app,get_broker
from faststream import FastStream,Context
from faststream.annotations import Logger

class FastStreamPublisher(AbstractPublisher, metaclass=abc.ABCMeta):
    """
    空的发布者，空的实现，需要搭配 boost入参的 consumer_override_cls 和 publisher_override_cls使用，或者被继承。
    """
    def custom_init(self):
        pass
        # asyncio.get_event_loop().run_until_complete(broker.start())
        self.broker = get_broker()
        get_or_create_event_loop().run_until_complete(self.broker.connect())

    def publish(self, msg: typing.Union[str, dict], task_id=None,
                priority_control_config: PriorityConsumingControlConfig = None) :
        msg, msg_function_kw, extra_params, task_id = self._convert_msg(msg, task_id, priority_control_config)
        t_start = time.time()
        faststream_result =  get_or_create_event_loop().run_until_complete(self.broker.publish(Serialization.to_json_str(msg), self.queue_name))
        self.logger.debug(f'向{self._queue_name} 队列，推送消息 耗时{round(time.time() - t_start, 4)}秒  {msg_function_kw}')  # 显示msg太长了。
        with self._lock_for_count:
            self.count_per_minute += 1
            self.publish_msg_num_total += 1
            if time.time() - self._current_time > 10:
                self.logger.info(
                    f'10秒内推送了 {self.count_per_minute} 条消息,累计推送了 {self.publish_msg_num_total} 条消息到 {self._queue_name} 队列中')
                self._init_count()
        # return AsyncResult(task_id)
        return faststream_result  #

    def concrete_realization_of_publish(self, msg):
        pass


    def clear(self):
        pass


    def get_message_count(self):
        return -1


    def close(self):
        pass

```

### 代码文件: funboost\publishers\httpsqs_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import json
from funboost.publishers.base_publisher import AbstractPublisher
import http.client
from urllib.parse import quote
from funboost.funboost_config_deafult import BrokerConnConfig
import urllib3

"""
http://blog.zyan.cc/httpsqs/
"""


class HttpsqsPublisher(AbstractPublisher):
    """
    使用httpsqs作为中间件
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        conn = http.client.HTTPConnection(host=BrokerConnConfig.HTTPSQS_HOST, port=BrokerConnConfig.HTTPSQS_PORT)
        url = f"/?name={self._queue_name}&opt=maxqueue&num=1000000000&auth={BrokerConnConfig.HTTPSQS_AUTH}&charset=utf-8"
        conn.request("GET", url)
        self.logger.info(conn.getresponse().read(1000))

        self.http = urllib3.PoolManager(20)

    def opt_httpsqs000(self, opt=None, data=''):
        data_url_encode = quote(data)
        resp = self.http.request('get', url=f'http://{BrokerConnConfig.HTTPSQS_HOST}:{BrokerConnConfig.HTTPSQS_PORT}' +
                                            f"/?name={self._queue_name}&opt={opt}&data={data_url_encode}&auth={BrokerConnConfig.HTTPSQS_AUTH}&charset=utf-8")
        return resp.data.decode()

    def opt_httpsqs(self, opt=None, data=''):
        conn = http.client.HTTPConnection(host=BrokerConnConfig.HTTPSQS_HOST, port=BrokerConnConfig.HTTPSQS_PORT)
        data_url_encode = quote(data)
        url = f"/?name={self._queue_name}&opt={opt}&data={data_url_encode}&auth={BrokerConnConfig.HTTPSQS_AUTH}&charset=utf-8"
        conn.request("GET", url)
        r = conn.getresponse()
        resp_text = r.read(1000000).decode()
        # print(url,r.status, resp_text)
        conn.close()
        return resp_text

    def concrete_realization_of_publish(self, msg):
        # curl "http://host:port/?name=your_queue_name&opt=put&data=经过URL编码的文本消息&auth=mypass123"
        text = self.opt_httpsqs('put', msg)
        if text != 'HTTPSQS_PUT_OK':
            self.logger.critical(text)

    def clear(self):
        # curl "http://host:port/?name=your_queue_name&opt=reset&auth=mypass123"
        # HTTPSQS_RESET_OK
        text = self.opt_httpsqs('reset')
        if text != 'HTTPSQS_RESET_OK':
            self.logger.critical(text)
        else:
            self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    def get_message_count(self):
        text = self.opt_httpsqs('status_json')
        status_dict = json.loads(text)
        # print(status_dict)
        return status_dict['putpos'] - status_dict['getpos']

    def close(self):
        self.http.clear()

```

### 代码文件: funboost\publishers\http_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12

from funboost.publishers.base_publisher import AbstractPublisher
from urllib3 import PoolManager


class HTTPPublisher(AbstractPublisher, ):
    """
    http实现的，不支持持久化。
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._http = PoolManager(10)
        self._ip = self.publisher_params.broker_exclusive_config['host']
        self._port = self.publisher_params.broker_exclusive_config['port']
        self._ip_port_str = f'{self._ip}:{self._port}'
        if self._port is None:
            raise ValueError('please specify port')


    def concrete_realization_of_publish(self, msg):
        url = self._ip_port_str + '/queue'
        self._http.request('post', url, fields={'msg': msg})

    def clear(self):
        pass  # udp没有保存消息

    def get_message_count(self):
        return -1  # http模式没有持久化保存消息

    def close(self):
        pass

```

### 代码文件: funboost\publishers\huey_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf

import copy
import json

from huey import RedisHuey

from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.assist.huey_helper import HueyHelper
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.utils.redis_manager import RedisMixin


class HueyPublisher(AbstractPublisher, ):
    """
    使用huey框架作为中间件
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._huey_task_fun = HueyHelper.queue_name__huey_task_fun_map[self.queue_name]
        self._huey_obj = HueyHelper.huey_obj # type: RedisHuey

    def concrete_realization_of_publish(self, msg):
        if isinstance(msg, str):
            msg = json.loads(msg)
        msg_function_kw = copy.deepcopy(msg)
        if 'extra' in msg:
            msg_function_kw.pop('extra')
        self._huey_task_fun(**msg_function_kw)

    def clear(self):
        self._huey_obj.flush()

    def get_message_count(self):
        pass
        return -1


    def close(self):
        pass

```

### 代码文件: funboost\publishers\kafka_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/20 0008 12:12

# noinspection PyPackageRequirements
import atexit

from funboost.core.lazy_impoter import KafkaPythonImporter
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher


class KafkaPublisher(AbstractPublisher, ):
    """
    使用kafka作为中间件
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._producer = KafkaPythonImporter().KafkaProducer(bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS)
        self._admin_client = KafkaPythonImporter().KafkaAdminClient(bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS)
        try:
            self._admin_client.create_topics([KafkaPythonImporter().NewTopic(self._queue_name, 10, 2)])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except KafkaPythonImporter().TopicAlreadyExistsError:
            pass
        except BaseException as e:
            self.logger.exception(e)
        atexit.register(self.close)  # 程序退出前不主动关闭，会报错。

    def concrete_realization_of_publish(self, msg):
        # noinspection PyTypeChecker
        # self.logger.debug(msg)
        # print(msg)
        self._producer.send(self._queue_name, msg.encode(), )

    def clear(self):
        self.logger.warning('还没开始实现 kafka 清空 消息')
        # self._consumer.seek_to_end()
        # self.logger.warning(f'将kafka offset 重置到最后位置')

    def get_message_count(self):
        # return -1 # 还没找到获取所有分区未消费数量的方法 。
        # print(self._admin_client.list_consumer_group_offsets('frame_group'))
        # print(self._admin_client.describe_consumer_groups('frame_group'))
        return -1

    def close(self):
        self._producer.close()

    def _at_exit(self):
        self._producer.flush()
        super()._at_exit()

```

### 代码文件: funboost\publishers\kombu_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2021-04-15 0008 12:12
import os

import json

# noinspection PyUnresolvedReferences
from kombu.transport.virtual.base import Channel
from kombu.entity import Exchange, Queue
from kombu.connection import Connection

from funboost.publishers.base_publisher import AbstractPublisher, deco_mq_conn_error
from funboost.funboost_config_deafult import BrokerConnConfig, FunboostCommonConfig

# nb_log.get_logger(name=None,log_level_int=10)
"""
https://www.cnblogs.com/shenh/p/10497244.html

rabbitmq  交换机知识。

https://docs.celeryproject.org/projects/kombu/en/stable/introduction.html
kombu 教程
"""


# noinspection PyMethodMayBeStatic,PyRedundantParentheses
class NoEncode():
    def encode(self, s):
        # return bytes_to_str(base64.b64encode(str_to_bytes(s)))
        return s

    def decode(self, s):
        # return base64.b64decode(str_to_bytes(s))
        return s


Channel.codecs['no_encode'] = NoEncode()  # 不使用base64更分方便查看内容


# noinspection PyAttributeOutsideInit
class KombuPublisher(AbstractPublisher, ):
    """
    使用kombu作为中间件,这个能直接一次性支持很多种小众中间件，但性能很差，除非是分布式函数调度框架没实现的中间件种类用户才可以用这种，用户也可以自己对比性能。
    """

    def custom_init(self):
        self.kombu_url = self.publisher_params.broker_exclusive_config['kombu_url'] or BrokerConnConfig.KOMBU_URL
        self._kombu_broker_url_prefix = self.kombu_url.split(":")[0]
        # logger_name = f'{self._logger_prefix}{self.__class__.__name__}--{self._kombu_broker_url_prefix}--{self._queue_name}'
        # self.logger = get_logger(logger_name, log_level_int=self._log_level_int,
        #                          _log_filename=f'{logger_name}.log' if self._is_add_file_handler else None,
        #                          formatter_template=FunboostCommonConfig.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER,
        #                          )  #
        if self.kombu_url.startswith('filesystem://'):
            self._create_msg_file_dir()

    def _create_msg_file_dir(self):
        os.makedirs(self.publisher_params.broker_exclusive_config['transport_options']['data_folder_in'], exist_ok=True)
        os.makedirs(self.publisher_params.broker_exclusive_config['transport_options']['data_folder_out'], exist_ok=True)
        processed_folder = self.publisher_params.broker_exclusive_config['transport_options'].get('processed_folder', None)
        if processed_folder:
            os.makedirs(processed_folder, exist_ok=True)

    def init_broker(self):
        self.exchange = Exchange('funboost_exchange', 'direct', durable=True)
        self.queue = Queue(self._queue_name, exchange=self.exchange, routing_key=self._queue_name, auto_delete=False)
        self.conn = Connection(self.kombu_url, transport_options=self.publisher_params.broker_exclusive_config['transport_options'])
        self.queue(self.conn).declare()
        self.producer = self.conn.Producer(serializer='json')
        self.channel = self.producer.channel  # type: Channel
        self.channel.body_encoding = 'no_encode'  # 这里改了编码，存到中间件的参数默认把消息base64了，我觉得没必要不方便查看消息明文。
        # self.channel = self.conn.channel()  # type: Channel
        # # self.channel.exchange_declare(exchange='distributed_framework_exchange', durable=True, type='direct')
        # self.queue = self.channel.queue_declare(queue=self._queue_name, durable=True)
        self.logger.warning(f'使用 kombu 库 连接 {self._kombu_broker_url_prefix} 中间件')

    @deco_mq_conn_error
    def concrete_realization_of_publish(self, msg):
        self.producer.publish(json.loads(msg), exchange=self.exchange, routing_key=self._queue_name, declare=[self.queue])

    @deco_mq_conn_error
    def clear(self):
        self.logger.warning(f'kombu清空消息队列 {self.queue_name}')
        self.channel.queue_purge(self._queue_name)

    @deco_mq_conn_error
    def get_message_count(self):
        # queue = self.channel.queue_declare(queue=self._queue_name, durable=True)
        # return queue.method.message_count
        # self.logger.warning(self.channel._size(self._queue_name))
        queue_declare_ok_t_named_tuple = self.channel.queue_declare(queue=self._queue_name, durable=True, auto_delete=False)
        # print(queue_declare_ok_t_named_tuple)
        return queue_declare_ok_t_named_tuple.message_count
        # if self._kombu_broker_url_prefix == 'amqp' or True:
        #     '''amqp tries to use librabbitmq but falls back to pyamqp.'''
        #     queue_declare_ok_t_named_tuple = self.channel.queue_declare(queue=self._queue_name, durable=True, auto_delete=False)
        #     # queue_declare_ok_t(queue='test_rabbit_queue2', message_count=100000, consumer_count=0)
        #     # print(type(queue_declare_ok_t_named_tuple),queue_declare_ok_t_named_tuple)
        #     return queue_declare_ok_t_named_tuple.message_count
        # # noinspection PyProtectedMember
        # return self.channel._size(self._queue_name)

    def close(self):
        self.channel.close()
        self.conn.close()
        self.logger.warning('关闭 kombu 包 链接')

```

### 代码文件: funboost\publishers\local_python_queue_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:07
from collections import deque
from queue import Queue, SimpleQueue

from funboost.publishers.base_publisher import AbstractPublisher
from funboost.queues.memory_queues_map import PythonQueues

local_pyhton_queue_name__local_pyhton_queue_obj_map = dict()  # 使local queue和其他中间件完全一样的使用方式，使用映射保存队列的名字，使消费和发布通过队列名字能找到队列对象。


class LocalPythonQueuePublisher(AbstractPublisher):
    """
    使用python内置queue对象作为中间件。方便测试，每个中间件的消费者类是鸭子类，多态可以互相替换。
    """

    # noinspection PyAttributeOutsideInit

    @property
    def local_python_queue(self) -> Queue:
        return PythonQueues.get_queue(self._queue_name)

    def concrete_realization_of_publish(self, msg):
        # noinspection PyTypeChecker
        pass
        self.local_python_queue.put(msg)

    def clear(self):
        # noinspection PyUnresolvedReferences
        self.local_python_queue.queue.clear()
        self.logger.warning(f'清除 本地队列中的消息成功')

    def get_message_count(self):
        return self.local_python_queue.qsize()

    def close(self):
        pass


class LocalPythonQueuePublisherSimpleQueue(AbstractPublisher):
    """
    使用python内置SimpleQueue对象作为中间件。方便测试，每个中间件的消费者类是鸭子类，多态可以互相替换。
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        if self._queue_name not in local_pyhton_queue_name__local_pyhton_queue_obj_map:
            local_pyhton_queue_name__local_pyhton_queue_obj_map[self._queue_name] = SimpleQueue()
        self.queue = local_pyhton_queue_name__local_pyhton_queue_obj_map[self._queue_name]  # type: SimpleQueue

    def concrete_realization_of_publish(self, msg):
        # noinspection PyTypeChecker
        self.queue.put(msg)

    def clear(self):
        pass
        # noinspection PyUnresolvedReferences
        # self.queue._queue.clear()
        # self.logger.warning(f'清除 本地队列中的消息成功')

    def get_message_count(self):
        return self.queue.qsize()

    def close(self):
        pass


class LocalPythonQueuePublisherDeque(AbstractPublisher):
    """
    使用python内置 Dequeu 对象作为中间件。方便测试，每个中间件的消费者类是鸭子类，多态可以互相替换。
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        if self._queue_name not in local_pyhton_queue_name__local_pyhton_queue_obj_map:
            local_pyhton_queue_name__local_pyhton_queue_obj_map[self._queue_name] = deque()
        self.queue = local_pyhton_queue_name__local_pyhton_queue_obj_map[self._queue_name]  # type: deque
        # deque.get = deque.pop
        # # setattr(self.queue,'get',self.queue.pop)

    def concrete_realization_of_publish(self, msg):
        # noinspection PyTypeChecker
        print(msg)
        self.queue.append(msg)

    def clear(self):
        pass
        # noinspection PyUnresolvedReferences
        self.queue.clear()
        self.logger.warning(f'清除 本地队列中的消息成功')

    def get_message_count(self):
        return len(self.queue)

    def close(self):
        pass

```

### 代码文件: funboost\publishers\meomory_deque_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:07
from collections import deque

from funboost.publishers.base_publisher import AbstractPublisher

deque_queue_name__deque_obj_map = dict()  # 使local queue和其他中间件完全一样的使用方式，使用映射保存队列的名字，使消费和发布通过队列名字能找到队列对象。


class DequePublisher(AbstractPublisher):
    """
    使用python内置queue对象作为中间件。方便测试，每个中间件的消费者类是鸭子类，多态可以互相替换。
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        if self._queue_name not in deque_queue_name__deque_obj_map:
            deque_queue_name__deque_obj_map[self._queue_name] = deque()
        self.queue = deque_queue_name__deque_obj_map[self._queue_name]  # type: deque

    def concrete_realization_of_publish(self, msg):
        # noinspection PyTypeChecker
        self.queue.append(msg)

    def clear(self):
        pass
        # noinspection PyUnresolvedReferences
        self.queue.clear()
        self.logger.warning(f'清除 本地队列中的消息成功')

    def get_message_count(self):
        return len(self.queue)

    def close(self):
        pass

```

### 代码文件: funboost\publishers\mongomq_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:23
import os

import json
from funboost.utils.dependency_packages.mongomq import MongoQueue
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.utils import time_util
from funboost.utils.mongo_util import MongoMixin


class MongoMqPublisher(AbstractPublisher, MongoMixin):
    # 使用mongo-queue包实现的基于mongodb的队列。 队列是一个col，自动存放在consume_queues库中。
    # noinspection PyAttributeOutsideInit

    pid__queue_map = {}

    def custom_init(self):
        pass

    @property
    def queue(self):
        ''' 不能提前实例化，mongo fork进程不安全，这样是动态生成queue'''
        pid = os.getpid()
        key = (pid, 'consume_queues', self._queue_name)
        if key not in MongoMqPublisher.pid__queue_map:
            queuex = MongoQueue(
                # self.mongo_client.get_database('consume_queues').get_collection(self._queue_name),
                self.get_mongo_collection('consume_queues', self._queue_name),
                consumer_id=f"consumer-{time_util.DatetimeConverter().datetime_str}",
                timeout=600,
                max_attempts=3,
                ttl=24 * 3600 * 365)
            MongoMqPublisher.pid__queue_map[key] = queuex
        return MongoMqPublisher.pid__queue_map[key]


    def concrete_realization_of_publish(self, msg):
        # noinspection PyTypeChecker
        self.queue.put(json.loads(msg))

    def clear(self):
        self.queue.clear()
        self.logger.warning(f'清除 mongo队列 {self._queue_name} 中的消息成功')

    def get_message_count(self):
        # return self.queue.size()
        return self.queue.collection.count_documents({'status': 'queued'})

    def close(self):
        pass

```

### 代码文件: funboost\publishers\mqtt_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
from funboost.core.lazy_impoter import PahoMqttImporter
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.funboost_config_deafult import BrokerConnConfig

"""
首先安装mqtt模块：


pip install paho-mqtt
写一个发布客户端pub.py：

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code: " + str(rc))

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect('127.0.0.1', 1883, 600) # 600为keepalive的时间间隔
client.publish('fifa', payload='amazing', qos=0)






再写一个接受客户端sub.py：

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code: " + str(rc))

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect('127.0.0.1', 1883, 600) # 600为keepalive的时间间隔
client.subscribe('fifa', qos=0)
client.loop_forever() # 保持连接

作者：赤色要塞满了
链接：https://www.jianshu.com/p/0ed4e59b1e8f
来源：简书
著作权归作者所有。商业转载请联系作者获得授权，非商业转载请注明出处。
"""

# import paho.mqtt.client as mqtt


# def on_connect(client, userdata, flags, rc):
#     print("Connected with result code: " + str(rc))
#
#
# def on_message(client, userdata, msg):
#     print(msg.topic + " " + str(msg.payload))


class MqttPublisher(AbstractPublisher, ):
    """
    使用 emq 作为中间件
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        client = PahoMqttImporter().mqtt.Client()
        # client.username_pw_set('admin', password='public')
        client.on_connect = self._on_connect
        client.on_socket_close = self._on_socket_close
        # client.on_message = on_message
        # print(frame_config.MQTT_HOST)
        client.connect(BrokerConnConfig.MQTT_HOST, BrokerConnConfig.MQTT_TCP_PORT, 600)  # 600为keepalive的时间间隔
        self._client = client

    def _on_socket_close(self, client, userdata, socket):
        self.logger.critical(f'{client, userdata, socket}')
        self.custom_init()

    def _on_connect(self, client, userdata, flags, rc):
        self.logger.info(f'连接mqtt服务端成功, {client, userdata, flags, rc}')

    def concrete_realization_of_publish(self, msg):
        self._client.publish(self._queue_name, payload=msg, qos=0, retain=False)

    def clear(self):
        pass
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    def get_message_count(self):
        # nb_print(self.redis_db7,self._queue_name)
        return -1

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass

```

### 代码文件: funboost\publishers\nameko_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/8 0008 12:12
import copy
import json
import time
import typing
import uuid

from nameko.standalone.rpc import ClusterRpcProxy

from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher, PriorityConsumingControlConfig


def get_nameko_config():
    return {'AMQP_URI': f'amqp://{BrokerConnConfig.RABBITMQ_USER}:{BrokerConnConfig.RABBITMQ_PASS}@{BrokerConnConfig.RABBITMQ_HOST}:{BrokerConnConfig.RABBITMQ_PORT}/{BrokerConnConfig.RABBITMQ_VIRTUAL_HOST}'}


class NamekoPublisher(AbstractPublisher, ):
    """
    使用nameko作为中间件
    """

    def custom_init(self):
        self._rpc = ClusterRpcProxy(get_nameko_config())

    def publish(self, msg: typing.Union[str, dict], task_id=None,
                priority_control_config: PriorityConsumingControlConfig = None):
        msg, msg_function_kw, extra_params, task_id = self._convert_msg(msg, task_id, priority_control_config)
        t_start = time.time()
        with self._rpc as rpc:
            res = getattr(rpc, self.queue_name).call(**msg_function_kw)
        self.logger.debug(f'调用nameko的 {self.queue_name} service 的 call方法 耗时{round(time.time() - t_start, 4)}秒，入参  {msg_function_kw}')  # 显示msg太长了。
        return res

    def concrete_realization_of_publish(self, msg):
        pass

    def clear(self):
        self.logger.warning('還沒開始實現')

    def get_message_count(self):
        return -1

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass

```

### 代码文件: funboost\publishers\nats_publisher.py
```python
﻿from funboost.core.lazy_impoter import NatsImporter
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.funboost_config_deafult import BrokerConnConfig


class NatsPublisher(AbstractPublisher, ):
    """
    使用nats作为中间件
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self.nats_client = NatsImporter().NATSClient(BrokerConnConfig.NATS_URL)
        self.nats_client.connect()

    def concrete_realization_of_publish(self, msg):
        # print(msg)
        self.nats_client.publish(subject=self.queue_name, payload=msg.encode())

    def clear(self):
        pass

    def get_message_count(self):
        return -1

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass

```

### 代码文件: funboost\publishers\nsq_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/19 0008 12:12
from funboost.core.lazy_impoter import GnsqImporter
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.funboost_config_deafult import BrokerConnConfig


class NsqPublisher(AbstractPublisher, ):
    """
    使用nsq作为中间件
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._nsqd_cleint = GnsqImporter().NsqdHTTPClient(BrokerConnConfig.NSQD_HTTP_CLIENT_HOST, BrokerConnConfig.NSQD_HTTP_CLIENT_PORT)
        self._producer = GnsqImporter().Producer(BrokerConnConfig.NSQD_TCP_ADDRESSES)
        self._producer.start()

    def concrete_realization_of_publish(self, msg):
        # noinspection PyTypeChecker
        self._producer.publish(self._queue_name, msg.encode())

    def clear(self):
        try:
            self._nsqd_cleint.empty_topic(self._queue_name)
        except GnsqImporter().NSQHttpError as e:
            self.logger.exception(e)  # 不能清除一个不存在的topoc会报错，和其他消息队列中间件不同。
        self.logger.warning(f'清除 {self._queue_name} topic中的消息成功')

    def get_message_count(self):
        return -1

    def close(self):
        self._producer.close()

```

### 代码文件: funboost\publishers\peewee_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:05
from funboost.queues.peewee_queue import PeeweeQueue
from funboost.publishers.base_publisher import AbstractPublisher


# noinspection PyProtectedMember
class PeeweePublisher(AbstractPublisher):
    """
    使用Sqlachemy 操作数据库 ，实现的5种sql 数据库服务器作为 消息队列。包括sqlite mydql microsoftsqlserver postgre oracle
    这个是使用数据库表模拟的消息队列。这不是突发奇想一意孤行，很多包库都实现了这。
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self.queue = PeeweeQueue(self._queue_name, )

    def concrete_realization_of_publish(self, msg):
        # print(msg)
        self.queue.push(body=msg, )

    def clear(self):
        self.queue.clear_queue()
        self.logger.warning(f'清除 sqlalchemy 数据库队列 {self._queue_name} 中的消息成功')

    def get_message_count(self):
        return self.queue.to_be_consumed_count

    def close(self):
        pass

```

### 代码文件: funboost\publishers\persist_queue_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:05
import json
import sqlite3

import persistqueue
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher
# from funboost.utils import LogManager
from funboost.core.loggers import get_funboost_file_logger

get_funboost_file_logger('persistqueue')


# noinspection PyProtectedMember
class PersistQueuePublisher(AbstractPublisher):
    """
    使用persistqueue实现的本地持久化队列。
    这个是本地持久化，支持本地多个启动的python脚本共享队列任务。与LocalPythonQueuePublisher相比，不会随着python解释器退出，导致任务丢失。
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        # noinspection PyShadowingNames
        def _my_new_db_connection(self, path, multithreading, timeout):  # 主要是改了sqlite文件后缀，方便pycharm识别和打开。
            # noinspection PyUnusedLocal
            conn = None
            if path == self._MEMORY:
                conn = sqlite3.connect(path,
                                       check_same_thread=not multithreading)
            else:
                conn = sqlite3.connect('{}/data.sqlite'.format(path),
                                       timeout=timeout,
                                       check_same_thread=not multithreading)
            conn.execute('PRAGMA journal_mode=WAL;')
            return conn

        persistqueue.SQLiteAckQueue._new_db_connection = _my_new_db_connection  # 打猴子补丁。
        # REMIND 官方测试基于sqlite的本地持久化，比基于纯文件的持久化，使用相同固态硬盘和操作系统情况下，速度快3倍以上，所以这里选用sqlite方式。

        self.queue = persistqueue.SQLiteAckQueue(path=BrokerConnConfig.SQLLITE_QUEUES_PATH, name=self._queue_name, auto_commit=True, serializer=json, multithreading=True)

    def concrete_realization_of_publish(self, msg):
        # noinspection PyTypeChecker
        self.queue.put(msg)

    def clear(self):
        sql = f'{"DELETE"}  {"FROM"} ack_queue_{self._queue_name}'
        self.logger.info(sql)
        self.queue._getter.execute(sql)
        self.queue._getter.commit()
        self.logger.warning(f'清除 本地持久化队列 {self._queue_name} 中的消息成功')

    def get_message_count(self):
        return self.queue._count()
        # return self.queue.qsize()

    def close(self):
        pass

```

### 代码文件: funboost\publishers\pulsar_publisher.py
```python
'''

import pulsar

client = pulsar.Client('pulsar://localhost:6650')

producer = client.create_producer('my-topic36')

for i in range(10):
    producer.send(('Hello-%d' % i).encode('utf-8'))

client.close()

'''

# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import os

from pulsar.schema import schema

from funboost.publishers.base_publisher import AbstractPublisher
from funboost.funboost_config_deafult import BrokerConnConfig


class PulsarPublisher(AbstractPublisher, ):
    """
    使用pulsar作为中间件
    """

    def custom_init(self):
        import pulsar
        self._client = pulsar.Client(BrokerConnConfig.PULSAR_URL, )
        self._producer = self._client.create_producer(self._queue_name, schema=schema.StringSchema(), producer_name=f'funboost_publisher_{os.getpid()}')

    def concrete_realization_of_publish(self, msg):
        self._producer.send(msg)

    def clear(self):
        """用户换个 subscription_name 就可以重新消费了，不需要清空消息"""
        pass


    def get_message_count(self):
        return -1

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        self._client.close()

```

### 代码文件: funboost\publishers\rabbitmq_amqpstorm_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:06
import amqpstorm
from amqpstorm.basic import Basic as AmqpStormBasic
from amqpstorm.queue import Queue as AmqpStormQueue
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher, deco_mq_conn_error
from funboost.utils import decorators


class RabbitmqPublisherUsingAmqpStorm(AbstractPublisher):
    # 使用amqpstorm包实现的mq操作。
    # 实例属性没在__init__里面写，造成代码补全很麻烦，写在这里做类属性，方便pycharm补全
    connection = amqpstorm.UriConnection
    channel = amqpstorm.Channel
    channel_wrapper_by_ampqstormbaic = AmqpStormBasic
    queue = AmqpStormQueue
    DURABLE = True

    def custom_init(self):
        arguments = {}     #  {'x-queue-type':'classic'} classic stream lazy quorum
        if self.publisher_params.broker_exclusive_config.get('x-max-priority'):
            arguments['x-max-priority'] = self.publisher_params.broker_exclusive_config['x-max-priority']
        self.queue_declare_params = dict(queue=self._queue_name, durable=self.DURABLE, arguments=arguments,auto_delete=False)

    # noinspection PyAttributeOutsideInit
    # @decorators.synchronized
    def init_broker(self):
        # username=app_config.RABBITMQ_USER, password=app_config.RABBITMQ_PASS, host=app_config.RABBITMQ_HOST, port=app_config.RABBITMQ_PORT, virtual_host=app_config.RABBITMQ_VIRTUAL_HOST, heartbeat=60 * 10
        self.logger.warning(f'使用AmqpStorm包 链接mq')
        self.connection = amqpstorm.UriConnection(
            f'amqp://{BrokerConnConfig.RABBITMQ_USER}:{BrokerConnConfig.RABBITMQ_PASS}@{BrokerConnConfig.RABBITMQ_HOST}:{BrokerConnConfig.RABBITMQ_PORT}/{BrokerConnConfig.RABBITMQ_VIRTUAL_HOST}?heartbeat={60 * 10}&timeout=20000'
        )
        self.channel = self.connection.channel()  # type:amqpstorm.Channel
        self.channel_wrapper_by_ampqstormbaic = AmqpStormBasic(self.channel)
        self.queue = AmqpStormQueue(self.channel)
        self.queue.declare(**self.queue_declare_params)

    # @decorators.tomorrow_threads(10)
    @deco_mq_conn_error
    def concrete_realization_of_publish(self, msg: str):
        self.channel_wrapper_by_ampqstormbaic.publish(exchange='',
                                                      routing_key=self._queue_name,
                                                      body=msg,
                                                      properties={'delivery_mode': 2, 'priority': self._get_from_other_extra_params('priroty', msg)}, )
        # nb_print(msg)

    @deco_mq_conn_error
    def clear(self):
        self.queue.purge(self._queue_name)
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    @deco_mq_conn_error
    def get_message_count(self):
        # noinspection PyUnresolvedReferences
        return self.queue.declare(**self.queue_declare_params)['message_count']

    # @deco_mq_conn_error
    def close(self):
        self.channel.close()
        self.connection.close()
        self.logger.warning('关闭amqpstorm包 链接mq')

```

### 代码文件: funboost\publishers\rabbitmq_pika_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:03
from threading import Lock
from pikav1 import BasicProperties
import pikav1
from funboost.publishers.base_publisher import AbstractPublisher, deco_mq_conn_error
from funboost.funboost_config_deafult import BrokerConnConfig


class RabbitmqPublisher(AbstractPublisher):
    """
    使用pika实现的。
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._lock_for_pika = Lock()

    # noinspection PyAttributeOutsideInit
    def init_broker(self):
        self.logger.warning(f'使用pika 链接mq')
        credentials = pikav1.PlainCredentials(BrokerConnConfig.RABBITMQ_USER, BrokerConnConfig.RABBITMQ_PASS)
        self.connection = pikav1.BlockingConnection(pikav1.ConnectionParameters(
            BrokerConnConfig.RABBITMQ_HOST, BrokerConnConfig.RABBITMQ_PORT, BrokerConnConfig.RABBITMQ_VIRTUAL_HOST, credentials, heartbeat=60))
        self.channel = self.connection.channel()
        self.queue = self.channel.queue_declare(queue=self._queue_name, durable=True)

    # noinspection PyAttributeOutsideInit
    @deco_mq_conn_error
    def concrete_realization_of_publish(self, msg):
        with self._lock_for_pika:  # 亲测pika多线程publish会出错
            self.channel.basic_publish(exchange='',
                                       routing_key=self._queue_name,
                                       body=msg,
                                       properties=BasicProperties(
                                           delivery_mode=2,  # make message persistent   2(1是非持久化)
                                       )
                                       )

    @deco_mq_conn_error
    def clear(self):
        self.channel.queue_purge(self._queue_name)
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    @deco_mq_conn_error
    def get_message_count(self):
        with self._lock_for_pika:
            queue = self.channel.queue_declare(queue=self._queue_name, durable=True)
            return queue.method.message_count

    # @deco_mq_conn_error
    def close(self):
        self.channel.close()
        self.connection.close()
        self.logger.warning('关闭pika包 链接')

```

### 代码文件: funboost\publishers\rabbitmq_rabbitpy_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:04
import os
import rabbitpy

from funboost.publishers.base_publisher import AbstractPublisher, deco_mq_conn_error
from funboost.utils.rabbitmq_factory import RabbitMqFactory


class RabbitmqPublisherUsingRabbitpy(AbstractPublisher):
    """
    使用rabbitpy包实现的。
    """

    # noinspection PyAttributeOutsideInit
    def init_broker(self):
        self.logger.warning(f'使用rabbitpy包 链接mq')
        self.rabbit_client = RabbitMqFactory(is_use_rabbitpy=1).get_rabbit_cleint()
        self.channel = self.rabbit_client.creat_a_channel()
        self.queue = self.channel.queue_declare(queue=self._queue_name, durable=True)
        self.logger.critical('rabbitpy 快速发布 有问题会丢失大量任务，如果使用 rabbitmq 建议设置中间件为 BrokerEnum.RABBITMQ_AMQPSTORM')
        os._exit(444) # noqa

    # @decorators.tomorrow_threads(10)
    @deco_mq_conn_error
    def concrete_realization_of_publish(self, msg):
        # noinspection PyTypeChecker
        import time
        # time.sleep(0.1)
        print(self.channel.basic_publish(
            exchange='',
            routing_key=self._queue_name,
            body=msg,
            properties={'delivery_mode': 2},
        ))


    @deco_mq_conn_error
    def clear(self):
        self.channel.queue_purge(self._queue_name)
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    @deco_mq_conn_error
    def get_message_count(self):
        # noinspection PyUnresolvedReferences
        ch_raw_rabbity = self.channel.channel
        return len(rabbitpy.amqp_queue.Queue(ch_raw_rabbity, self._queue_name, durable=True))

    # @deco_mq_conn_error
    def close(self):
        self.channel.close()
        self.rabbit_client.connection.close()
        self.logger.warning('关闭rabbitpy包 链接mq')

```

### 代码文件: funboost\publishers\redis_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import os
import time
# noinspection PyUnresolvedReferences
from queue import Queue, Empty
from threading import Lock

from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.publishers.redis_queue_flush_mixin import FlushRedisQueueMixin
from funboost.utils import decorators
from funboost.utils.redis_manager import RedisMixin


class RedisPublisher(FlushRedisQueueMixin, AbstractPublisher, RedisMixin, ):
    """
    使用redis作为中间件,这个是大幅优化了发布速度的方式。简单的发布是 redis_publisher_0000.py 中的代码方式。

    这个是复杂版，批量推送，简单版在 funboost/publishers/redis_publisher_simple.py
    """
    _push_method = 'rpush'

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._temp_msg_queue = Queue()
        self._temp_msg_list = list()
        self._lock_for_bulk_push = Lock()
        self._last_push_time = time.time()
        decorators.keep_circulating(time_sleep=0.1, is_display_detail_exception=True, block=False,
                                    daemon=True)(self._initiative_bulk_push_to_broker, )()

    def __bulk_push_and_init(self):
        if len(self._temp_msg_list) > 0:
            getattr(self.redis_db_frame, self._push_method)(self._queue_name, *self._temp_msg_list)
            self._temp_msg_list = []

    def _initiative_bulk_push_to_broker(self):  # 主动触发。concrete_realization_of_publish防止发布最后一条后没达到2000但sleep很久，无法触发at_exit，不能自动触发进入消息队列。
        with self._lock_for_bulk_push:
            self.__bulk_push_and_init()

    def concrete_realization_of_publish(self, msg):
        # print(getattr(frame_config,'has_start_a_consumer_flag',0))
        # 这里的 has_start_a_consumer_flag 是一个标志，借用此模块设置的一个标识变量而已，框架运行时候自动设定的，不要把这个变量写到模块里面。
        # if getattr(funboost_config_deafult, 'has_start_a_consumer_flag', 0) == 0:  # 加快速度推送，否则每秒只能推送4000次。如果是独立脚本推送，使用批量推送，如果是消费者中发布任务，为了保持原子性，用原来的单个推送。
        if self.publisher_params.broker_exclusive_config.get('redis_bulk_push', 0) == 1:  # RedisConsumer传了,  RedisAckAble  没传
            # self._temp_msg_queue.put(msg)
            with self._lock_for_bulk_push:
                self._temp_msg_list.append(msg)
                if len(self._temp_msg_list) >= 1000:
                    # print(len(self._temp_msg_list))
                    self.__bulk_push_and_init()
        else:
            getattr(self.redis_db_frame, self._push_method)(self._queue_name, msg)
            # print(msg)

    def get_message_count(self):
        # print(self.redis_db7,self._queue_name)
        return self.redis_db_frame.llen(self._queue_name)

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass

    def _at_exit(self):
        # time.sleep(2) # 不需要
        # self._real_bulk_push_to_broker()
        with self._lock_for_bulk_push:
            self.__bulk_push_and_init()
        super()._at_exit()

```

### 代码文件: funboost\publishers\redis_publisher_lpush.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12


from funboost.publishers.redis_publisher import RedisPublisher


class RedisPublisherLpush(RedisPublisher):
    """
    使用redis作为中间件,
    """

    _push_method = 'lpush'



```

### 代码文件: funboost\publishers\redis_publisher_priority.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12

from funboost.publishers.base_publisher import AbstractPublisher
from funboost.publishers.redis_queue_flush_mixin import FlushRedisQueueMixin
from funboost.utils.redis_manager import RedisMixin


class RedisPriorityPublisher(FlushRedisQueueMixin,AbstractPublisher, RedisMixin,):
    """
    redis队列，支持任务优先级。
    """

    def custom_init(self):
        queue_list = [self._queue_name]
        x_max_priority = self.publisher_params.broker_exclusive_config.get('x-max-priority')
        if x_max_priority:
            for i in range(1, x_max_priority + 1):
                queue_list.append(f'{self.queue_name}:{i}')
        queue_list.sort(reverse=True)
        self.queue_list = queue_list

    def build_queue_name_by_msg(self, msg):
        """
        根据消息的other_extra_params的 priority ，自动生成子队列名。例如 queue_name:1   queue_name:2  queue_name:3 queue_name:4
        :param msg:
        :return:
        """
        priority = self._get_from_other_extra_params('priroty', msg)
        x_max_priority = self.publisher_params.broker_exclusive_config['x-max-priority']
        queue_name = self.queue_name
        if x_max_priority and priority:
            priority = min(priority, x_max_priority)  # 防止有傻瓜发布消息的优先级priroty比最大支持的优先级还高。
            queue_name = f'{self.queue_name}:{priority}'
        return queue_name

    def concrete_realization_of_publish(self, msg):
        queue_name = self.build_queue_name_by_msg(msg)
        # self.logger.debug([queue_name, msg])
        self.redis_db_frame.rpush(queue_name, msg)


    def get_message_count(self):
        count = 0
        for queue_name in self.queue_list:
            count += self.redis_db_frame.llen(queue_name)
        return count

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass

    def clear(self):
        self.logger.warning(f'清除 {self.queue_list} 中的消息')
        self.redis_db_frame.delete(*self.queue_list)
        FlushRedisQueueMixin.clear(self)

```

### 代码文件: funboost\publishers\redis_publisher_simple.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/8 0008 12:12
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.publishers.redis_queue_flush_mixin import FlushRedisQueueMixin
from funboost.utils.redis_manager import RedisMixin


class RedisPublisher(FlushRedisQueueMixin, AbstractPublisher, RedisMixin, ):
    """
    使用redis作为中间件
    """

    def concrete_realization_of_publish(self, msg):
        self.redis_db_frame.rpush(self._queue_name, msg)

    def get_message_count(self):
        # nb_print(self.redis_db7,self._queue_name)
        return self.redis_db_frame.llen(self._queue_name)

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass

```

### 代码文件: funboost\publishers\redis_pubsub_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.utils.redis_manager import RedisMixin


class RedisPubSubPublisher(AbstractPublisher, RedisMixin, ):
    """
    使用redis作为中间件
    """

    def concrete_realization_of_publish(self, msg):
        self.redis_db_frame.publish(self._queue_name, msg)

    def clear(self):
        self.redis_db_frame.delete(self._queue_name)
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    def get_message_count(self):
        return -1

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass

```

### 代码文件: funboost\publishers\redis_queue_flush_mixin.py
```python
class FlushRedisQueueMixin:
    # noinspection PyUnresolvedReferences
    def clear(self):
        self.redis_db_frame.delete(self._queue_name)
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')
        # self.redis_db_frame.delete(f'{self._queue_name}__unack')
        unack_queue_name_list = self.redis_db_frame.scan(match=f'{self._queue_name}__unack_id_*', count=100000)[1] + \
                                self.redis_db_frame.scan(match=f'unack_{self._queue_name}_*', count=100000)[1]  # noqa
        if unack_queue_name_list:
            self.redis_db_frame.delete(*unack_queue_name_list)
            self.logger.warning(f'清除 {unack_queue_name_list} 队列中的消息成功')

```

### 代码文件: funboost\publishers\redis_stream_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2021/4/3 0008 13:32
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.utils.redis_manager import RedisMixin


class RedisStreamPublisher(AbstractPublisher, RedisMixin):
    """
    redis 的 stream 结构 作为中间件实现的。需要redis 5.0以上，redis stream结构 是redis的消息队列，功能远超 list结构。
    """

    _has__check_redis_version = False

    def _check_redis_version(self):
        redis_server_info_dict = self.redis_db_frame.info()
        if float(redis_server_info_dict['redis_version'][0]) < 5:
            raise EnvironmentError('必须是5.0版本以上redis服务端才能支持  stream 数据结构，'
                                   '请升级服务端，否则使用 REDIS_ACK_ABLE 方式使用redis 的 list 结构')
        if self.redis_db_frame.type(self._queue_name) == 'list':
            raise EnvironmentError(f'检测到已存在 {self._queue_name} 这个键，且类型是list， 必须换个队列名字或者删除这个'
                                   f' list 类型的键。'
                                   f'RedisStreamConsumer 使用的是 stream数据结构')
        self._has__check_redis_version = True

    def concrete_realization_of_publish(self, msg):
        # redis服务端必须是5.0以上，并且确保这个键的类型是stream不能是list数据结构。
        if not self._has__check_redis_version:
            self._check_redis_version()
        self.redis_db_frame.xadd(self._queue_name, {"": msg})

    def clear(self):
        self.redis_db_frame.delete(self._queue_name)
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    def get_message_count(self):
        # nb_print(self.redis_db7,self._queue_name)
        return self.redis_db_frame.xlen(self._queue_name)

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass

```

### 代码文件: funboost\publishers\rocketmq_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/7/9 0008 12:12
import threading
import time
from funboost.funboost_config_deafult import BrokerConnConfig

from funboost.publishers.base_publisher import AbstractPublisher



class RocketmqPublisher(AbstractPublisher, ):
    _group_id__rocketmq_producer = {}
    _lock_for_create_producer = threading.Lock()

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        try:
            from rocketmq.client import Producer
        except BaseException as e:
            # print(traceback.format_exc())
            raise ImportError(f'rocketmq包 只支持linux和mac {str(e)}')

        group_id = f'g-{self._queue_name}'
        with self._lock_for_create_producer:
            if group_id not in self.__class__._group_id__rocketmq_producer:  # 同一个进程中创建多个同组消费者会报错。
                producer = Producer(group_id)
                producer.set_namesrv_addr(BrokerConnConfig.ROCKETMQ_NAMESRV_ADDR)
                producer.start()
                self.__class__._group_id__rocketmq_producer[group_id] = producer
            else:
                producer = self.__class__._group_id__rocketmq_producer[group_id]
            self._producer = producer

    def concrete_realization_of_publish(self, msg):
        try:
            from rocketmq.client import Message
        except BaseException as e:
            # print(traceback.format_exc())
            raise ImportError(f'rocketmq包 只支持linux和mac {str(e)}')
        rocket_msg = Message(self._queue_name)
        # rocket_msg.set_keys(msg)  # 利于检索
        # rocket_msg.set_tags('XXX')
        rocket_msg.set_body(msg)
        # print(msg)
        self._producer.send_sync(rocket_msg)

    def clear(self):
        self.logger.error('清除队列，python版的rocket包太弱了，没有方法设置偏移量或者删除主题。java才能做到')

    def get_message_count(self):
        if time.time() - getattr(self, '_last_warning_count', 0) > 300:
            setattr(self, '_last_warning_count', time.time())
            self.logger.warning('获取消息数量，python版的rocket包太弱了，没找到方法。java才能做到。')
        return -1

    def close(self):
        self._producer.shutdown()

```

### 代码文件: funboost\publishers\rq_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import json

from funboost.assist.rq_helper import RqHelper
from funboost.publishers.base_publisher import AbstractPublisher


class RqPublisher(AbstractPublisher):
    """
    使用redis作为中间件,这个是大幅优化了发布速度的方式。简单的发布是 redis_publisher_0000.py 中的代码方式。

    这个是复杂版，批量推送，简单版在 funboost/publishers/redis_publisher_simple.py
    """

    def concrete_realization_of_publish(self, msg):
        func_kwargs = json.loads(msg)
        func_kwargs.pop('extra')
        RqHelper.queue_name__rq_job_map[self.queue_name].delay(**func_kwargs)

    def clear(self):
        pass

    def get_message_count(self):
        return -1

    def close(self):
        pass

    def _at_exit(self):
        pass

```

### 代码文件: funboost\publishers\sqla_queue_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:05
from funboost.queues import sqla_queue
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher


# noinspection PyProtectedMember
class SqlachemyQueuePublisher(AbstractPublisher):
    """
    使用Sqlachemy 操作数据库 ，实现的5种sql 数据库服务器作为 消息队列。包括sqlite mydql microsoftsqlserver postgre oracle
    这个是使用数据库表模拟的消息队列。这不是突发奇想一意孤行，很多包库都实现了这。
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self.queue = sqla_queue.SqlaQueue(self._queue_name, BrokerConnConfig.SQLACHEMY_ENGINE_URL)

    def concrete_realization_of_publish(self, msg):
        self.queue.push(dict(body=msg, status=sqla_queue.TaskStatus.TO_BE_CONSUMED))

    def clear(self):
        self.queue.clear_queue()
        self.logger.warning(f'清除 sqlalchemy 数据库队列 {self._queue_name} 中的消息成功')

    def get_message_count(self):
        return self.queue.to_be_consumed_count

    def close(self):
        pass

```

### 代码文件: funboost\publishers\tcp_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import socket
from funboost.publishers.base_publisher import AbstractPublisher


class TCPPublisher(AbstractPublisher, ):
    """
    使用tcp作为中间件,不支持持久化，支持分布式
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._bufsize = self.publisher_params.broker_exclusive_config['bufsize']

    # noinspection PyAttributeOutsideInit
    def concrete_realization_of_publish(self, msg):
        if not hasattr(self, '_tcp_cli_sock'):
            # ip__port_str = self.queue_name.split(':')
            # ip_port = (ip__port_str[0], int(ip__port_str[1]))
            self._ip = self.publisher_params.broker_exclusive_config['host']
            self._port = self.publisher_params.broker_exclusive_config['port']
            self.__ip_port = (self._ip, self._port)
            if self._port is None:
                raise ValueError('please specify port')
            tcp_cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_cli_sock.connect(self.__ip_port)
            self._tcp_cli_sock = tcp_cli_sock

        self._tcp_cli_sock.send(msg.encode())
        self._tcp_cli_sock.recv(self._bufsize)

    def clear(self):
        pass  # udp没有保存消息

    def get_message_count(self):
        # nb_print(self.redis_db7,self._queue_name)
        return -1  # udp没有保存消息

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        self._tcp_cli_sock.close()

```

### 代码文件: funboost\publishers\txt_file_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import shutil
from pathlib import Path

from nb_filelock import FileLock
from persistqueue import Queue
from persistqueue.serializers import json as json_serializer

from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher


class TxtFilePublisher(AbstractPublisher, ):
    """
    使用txt文件作为中间件
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._file_queue_path = str((Path(BrokerConnConfig.TXT_FILE_PATH) / self.queue_name).absolute())
        # Path(self._file_queue_path).mkdir(exist_ok=True)
        self.file_queue = Queue(self._file_queue_path,
                                autosave=True, serializer=json_serializer)
        self._file_lock = FileLock(Path(self._file_queue_path) / f'_funboost_txtfile_{self.queue_name}.lock')

    def concrete_realization_of_publish(self, msg):
        with self._file_lock:
            self.file_queue.put(msg)

    def clear(self):
        shutil.rmtree(self._file_queue_path, ignore_errors=True)
        self.logger.warning(f'清除 {Path(self._file_queue_path).absolute()} 文件夹成功')

    def get_message_count(self):
        return self.file_queue.qsize()

    def close(self):
        pass

```

### 代码文件: funboost\publishers\udp_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import socket
from funboost.publishers.base_publisher import AbstractPublisher


class UDPPublisher(AbstractPublisher, ):
    """
    使用udp作为中间件,不支持持久化，支持分布式
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._bufsize = self.publisher_params.broker_exclusive_config['bufsize']
        self.__udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._ip = self.publisher_params.broker_exclusive_config['host']
        self._port = self.publisher_params.broker_exclusive_config['port']
        self.__ip_port = (self._ip, self._port)
        if self._port is None:
            raise ValueError('please specify port')
        self.__udp_client.connect(self.__ip_port)

    # noinspection PyAttributeOutsideInit
    def concrete_realization_of_publish(self, msg):
        self.__udp_client.send(msg.encode('utf-8'), )
        self.__udp_client.recv(self._bufsize)

    def clear(self):
        pass  # udp没有保存消息

    def get_message_count(self):
        # nb_print(self.redis_db7,self._queue_name)
        return -1  # udp没有保存消息

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        self.__udp_client.close()

```

### 代码文件: funboost\publishers\zeromq_publisher.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
from funboost.core.lazy_impoter import ZmqImporter
from funboost.publishers.base_publisher import AbstractPublisher


# noinspection PyProtectedMember
class ZeroMqPublisher(AbstractPublisher):
    """
    zeromq 中间件的发布者，zeromq基于socket代码，不会持久化，且不需要安装软件。
    """
    def custom_init(self):
        self._port = self.publisher_params.broker_exclusive_config['port']
        if self._port is None:
            raise ValueError('please specify port')

        context = ZmqImporter().zmq.Context()
        socket = context.socket(ZmqImporter().zmq.REQ)
        socket.connect(f"tcp://localhost:{int(self._port)}")
        self.socket =socket
        self.logger.warning('框架使用 zeromq 中间件方式，必须先启动消费者(消费者会顺便启动broker) ,只有启动了服务端才能发布任务')

    def concrete_realization_of_publish(self, msg):
        self.socket.send(msg.encode())
        self.socket.recv()

    def clear(self):
        pass

    def get_message_count(self):
        return -1

    def close(self):
        pass


```

### 代码文件: funboost\publishers\__init__.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 11:50

"""
实现各种中间件类型的发布者。
"""
```

### 代码文件: funboost\queues\memory_queues_map.py
```python
import queue


class PythonQueues:
    local_pyhton_queue_name__local_pyhton_queue_obj_map  = {}

    @classmethod
    def get_queue(cls,queue_name):
        if queue_name not in cls.local_pyhton_queue_name__local_pyhton_queue_obj_map:
            cls.local_pyhton_queue_name__local_pyhton_queue_obj_map[queue_name] = queue.Queue()
        return cls.local_pyhton_queue_name__local_pyhton_queue_obj_map[queue_name]
```

### 代码文件: funboost\queues\peewee_queue.py
```python
import datetime
import time
#
# from peewee import ModelSelect, Model, BigAutoField, CharField, DateTimeField, MySQLDatabase
# from playhouse.shortcuts import model_to_dict, dict_to_model

# from nb_log import LoggerMixin, LoggerLevelSetterMixin
from funboost.core.loggers import LoggerLevelSetterMixin,FunboostFileLoggerMixin
from funboost.funboost_config_deafult import BrokerConnConfig
# from peewee import *
from funboost.core.lazy_impoter import PeeweeImporter


class TaskStatus:
    TO_BE_CONSUMED = 'to_be_consumed'
    PENGDING = 'pengding'
    FAILED = 'failed'
    SUCCESS = 'success'
    REQUEUE = 'requeue'


class PeeweeQueue(FunboostFileLoggerMixin, LoggerLevelSetterMixin):
    """
    使用peewee操作数据库模拟消息队列
    """

    def __init__(self, queue_name):
        self.queue_name = queue_name
        self.FunboostMessage = None
        self._create_table()

    def _create_table(self):
        class FunboostMessage(PeeweeImporter().Model):
            """数据库的一行模拟一条消息"""
            job_id = PeeweeImporter().BigAutoField(primary_key=True, )
            body = PeeweeImporter().CharField(max_length=10240, null=False)
            publish_timestamp = PeeweeImporter().DateTimeField(default=datetime.datetime.now)
            status = PeeweeImporter().CharField(max_length=40, null=False)
            consume_start_timestamp = PeeweeImporter().DateTimeField(default=None, null=True)

            class Meta:
                db_table = self.queue_name
                conn_params = dict(
                    host=BrokerConnConfig.MYSQL_HOST,
                    port=BrokerConnConfig.MYSQL_PORT,
                    user=BrokerConnConfig.MYSQL_USER,
                    passwd=BrokerConnConfig.MYSQL_PASSWORD,
                    database=BrokerConnConfig.MYSQL_DATABASE,
                )
                database = PeeweeImporter().MySQLDatabase(**conn_params)

        FunboostMessage.create_table()
        self.FunboostMessage = FunboostMessage

    def push(self, body):
        msg = self.FunboostMessage(body=body, status=TaskStatus.TO_BE_CONSUMED, consume_start_timestamp=None)
        msg.save()

    def get(self):
        while True:
            ten_minitues_ago_datetime = datetime.datetime.now() + datetime.timedelta(minutes=-10)
            ret = self.FunboostMessage.select().where(self.FunboostMessage.status.in_([TaskStatus.TO_BE_CONSUMED, TaskStatus.REQUEUE])
                                                      | (
                                                              (self.FunboostMessage.status == TaskStatus.PENGDING) &
                                                              (self.FunboostMessage.consume_start_timestamp < ten_minitues_ago_datetime)
                                                      )).limit(1)
            # ret = self.FunboostMessage.select().where(self.FunboostMessage.status=='dsadsad').limit(1)
            # print(ret)
            if len(ret) == 1:
                row_obj = ret[0]
                row = PeeweeImporter().model_to_dict(row_obj)
                self.FunboostMessage.update(status=TaskStatus.PENGDING, consume_start_timestamp=datetime.datetime.now()
                                            ).where(self.FunboostMessage.job_id == row['job_id']).execute()
                return row
            else:
                time.sleep(0.2)

    def set_success(self, job_id, is_delete_the_task=False):
        if is_delete_the_task:
            self.FunboostMessage.delete_by_id(job_id)
        else:
            # ModelSelect.for_update()
            # print(self.FunboostMessage.update(status=TaskStatus.SUCCESS).where(self.FunboostMessage.job_id==job_id))
            self.FunboostMessage.update(status=TaskStatus.SUCCESS).where(self.FunboostMessage.job_id == job_id).execute()

    def set_failed(self, job_id, ):
        self.set_task_status(job_id, status=TaskStatus.FAILED)

    def set_task_status(self, job_id, status: str):
        self.FunboostMessage.update(status=status).where(self.FunboostMessage.job_id == job_id).execute()

    def requeue_task(self, job_id):
        self.set_task_status(job_id, TaskStatus.REQUEUE)

    def clear_queue(self):
        self.FunboostMessage.truncate_table()

    def get_count_by_status(self, status):
        return self.FunboostMessage.select().where(self.FunboostMessage.status == status).count()

    @property
    def total_count(self):
        return self.FunboostMessage.select().count()

    @property
    def to_be_consumed_count(self):
        return self.get_count_by_status(TaskStatus.TO_BE_CONSUMED)


if __name__ == '__main__':
    from threadpool_executor_shrink_able import ThreadPoolExecutorShrinkAble
    q = PeeweeQueue('peewee_queue')
    q.set_success(1)

    pool = ThreadPoolExecutorShrinkAble(200)
    # q.clear_queue()
    # t1 = time.time()
    #
    for i in range(10000):
        # q.push(body=f'{{"a":{i}}}',status=TaskStatus.TO_BE_CONSUMED)
        pool.submit(q.push, body=f'{{"a":{i}}}',)
    # # q.get()
    # # q.set_success(3,is_delete_the_task=False)
    # pool.shutdown()
    # print(time.time() - t1)
    # print(q.total_count)

```

### 代码文件: funboost\queues\sqla_queue.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/1/10 0010 18:42
"""
使用sqlachemy来使5种关系型数据库模拟消息队列。
"""
import datetime
import json
import time
from pathlib import Path


import sqlalchemy
from sqlalchemy import Column, func, or_, and_, Table, MetaData
from sqlalchemy import Integer
from sqlalchemy import String, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from sqlalchemy_utils import database_exists, create_database

from funboost.utils import  decorators
from funboost.core.loggers import FunboostFileLoggerMixin,LoggerLevelSetterMixin

class TaskStatus:
    TO_BE_CONSUMED = 'to_be_consumed'
    PENGDING = 'pengding'
    FAILED = 'failed'
    SUCCESS = 'success'
    REQUEUE = 'requeue'


"""
class SqlaBase(Base):
    __abstract__ = True
    job_id = Column(Integer, primary_key=True, autoincrement=True)
    body = Column(String(10240))
    publish_timestamp = Column(DateTime, default=datetime.datetime.now, comment='发布时间')
    status = Column(String(20), index=True, nullable=True)
    consume_start_timestamp = Column(DateTime, default=None, comment='消费时间', index=True)

    def __init__(self, job_id=None, body=None, publish_timestamp=None, status=None, consume_start_timestamp=None):
        self.job_id = job_id
        self.body = body
        self.publish_timestamp = publish_timestamp
        self.status = status
        self.consume_start_timestamp = consume_start_timestamp

    def __str__(self):
        return f'{self.__class__} {self.__dict__}'

    def to_dict(self):
        # return {'job_id':self.job_id,'body':self.body,'publish_timestamp':self.publish_timestamp,'status':self.status}
        # noinspection PyUnresolvedReferences
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
"""





class SessionContext:
    # def __init__(self, session: sqlalchemy.orm.session.Session):
    def __init__(self, session):
        self.ss = session

    def __enter__(self):
        return self.ss

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ss.commit()
        self.ss.close()


@decorators.flyweight
class SqlaQueue(FunboostFileLoggerMixin, LoggerLevelSetterMixin):
    # noinspection PyPep8Naming
    @decorators.where_is_it_called
    def __init__(self, queue_name: str, sqla_conn_url: str):
        class SqlaBaseMixin:
            # __abstract__ = True
            job_id = Column(Integer, primary_key=True, autoincrement=True)
            body = Column(String(10240))
            publish_timestamp = Column(DateTime, default=datetime.datetime.now, comment='发布时间')
            status = Column(String(20), index=False, nullable=True)
            consume_start_timestamp = Column(DateTime, default=None, comment='消费时间', index=False)

            def __init__(self, job_id=None, body=None, publish_timestamp=None, status=None, consume_start_timestamp=None):
                self.job_id = job_id
                self.body = body
                self.publish_timestamp = publish_timestamp
                self.status = status
                self.consume_start_timestamp = consume_start_timestamp

            def __str__(self):
                return f'{self.__class__} {self.to_dict()}'

            def to_dict(self):
                # return {'job_id':self.job_id,'body':self.body,'publish_timestamp':self.publish_timestamp,'status':self.status}
                # noinspection PyUnresolvedReferences
                return {c.name: getattr(self, c.name) for c in self.__table__.columns}

        self.logger.setLevel(20)
        self.queue_name = queue_name
        self._sqla_conn_url = sqla_conn_url
        self.__auto_create_database()

        if sqla_conn_url.startswith('sqlite'):
            engine = create_engine(sqla_conn_url,
                                   connect_args={'check_same_thread': False},
                                   # poolclass=StaticPool
                                   )
        else:
            engine = create_engine(sqla_conn_url, echo=False,
                                   max_overflow=30,  # 超过连接池大小外最多创建的连接
                                   pool_size=20,  # 连接池大小
                                   pool_timeout=300,  # 池中没有线程最多等待的时间，否则报错
                                   pool_recycle=-1  # 多久之后对线程池中的线程进行一次连接的回收（重置）
                                   )

        try:
            Base = declarative_base()  # type: sqlalchemy.ext.declarative.api.Base

            class SqlaQueueModel(SqlaBaseMixin, Base, ):
                __tablename__ = self.queue_name
                # __table_args__ = {'extend_existing': True， "mysql_engine": "MyISAM",
                #                     "mysql_charset": "utf8"}  # "useexisting": True

            SqlaQueueModel.metadata.create_all(engine, )
            self.Session = sessionmaker(bind=engine, expire_on_commit=False)
            self.SqlaQueueModel = SqlaQueueModel
        except BaseException as e:
            self.logger.warning(e)
            Base = automap_base()

            class SqlaQueueModel(SqlaBaseMixin, Base, ):
                __tablename__ = self.queue_name
                # __table_args__ = {'extend_existing': True}  # "useexisting": True

            Base.prepare(engine, reflect=True)
            self.Session = sessionmaker(bind=engine, expire_on_commit=False)
            self.SqlaQueueModel = SqlaQueueModel

        self._to_be_publish_task_list = []

    def __auto_create_database(self):
        # 'sqlite:////sqlachemy_queues/queues.db'
        if self._sqla_conn_url.startswith('sqlite:'):
            if not Path('/sqlachemy_queues').exists():
                Path('/sqlachemy_queues').mkdir()
        else:
            if not database_exists(self._sqla_conn_url):
                create_database(self._sqla_conn_url)

    def push(self, sqla_task_dict):
        with SessionContext(self.Session()) as ss:
            # sqla_task = ss.merge(sqla_task)
            self.logger.debug(sqla_task_dict)
            ss.add(self.SqlaQueueModel(**sqla_task_dict))

    def bulk_push(self, sqla_task_dict_list: list):
        """
        queue = SqlaQueue('queue37', 'sqlite:////sqlachemy_queues/queues.db')
        queue.bulk_push([queue.SqlaQueueModel(body=json.dumps({'a': i, 'b': 2 * i}), status=TaskStatus.TO_BE_CONSUMED) for i in range(10000)])
        :param sqla_task_dict_list:
        :return:
        """
        with SessionContext(self.Session()) as ss:
            self.logger.debug(sqla_task_dict_list)
            sqla_task_list = [self.SqlaQueueModel(**sqla_task_dict) for sqla_task_dict in sqla_task_dict_list]
            ss.add_all(sqla_task_list)

    def get(self):
        # print(ss)
        while True:
            with SessionContext(self.Session()) as ss:
                ten_minitues_ago_datetime = datetime.datetime.now() + datetime.timedelta(minutes=-10)
                # task = ss.query(self.SqlaQueueModel).filter_by(status=TaskStatus.TO_BE_CONSUMED).first()
                # query = ss.query(self.SqlaQueueModel).filter(self.SqlaQueueModel.status.in_([TaskStatus.TO_BE_CONSUMED, TaskStatus.REQUEUE]))
                # noinspection PyUnresolvedReferences
                query = ss.query(self.SqlaQueueModel).filter(or_(self.SqlaQueueModel.status.in_([TaskStatus.TO_BE_CONSUMED, TaskStatus.REQUEUE]),
                                                                 and_(self.SqlaQueueModel.status == TaskStatus.PENGDING,
                                                                      self.SqlaQueueModel.consume_start_timestamp < ten_minitues_ago_datetime)))
                # print(str(query))  # 打印原始语句。
                task = query.first()
                if task:
                    task.status = task.status = TaskStatus.PENGDING
                    task.consume_start_timestamp = datetime.datetime.now()
                    return task.to_dict()
                else:
                    time.sleep(0.2)

    def set_success(self, sqla_task_dict, is_delete_the_task=True):
        with SessionContext(self.Session()) as ss:
            # sqla_task = ss.merge(sqla_task)
            # print(sqla_task_dict)
            if is_delete_the_task:
                sqla_task = ss.query(self.SqlaQueueModel).filter_by(job_id=sqla_task_dict['job_id']).first()
                # print(sqla_task)
                if sqla_task:  # REMIND 如果中途把表清空了，则不会查找到。
                    ss.delete(sqla_task)
            else:
                sqla_task = ss.query(self.SqlaQueueModel).filter(self.SqlaQueueModel.job_id == sqla_task_dict['job_id']).first()
                if sqla_task:
                    sqla_task.status = TaskStatus.SUCCESS

    def set_failed(self, sqla_task_dict):
        with SessionContext(self.Session()) as ss:
            # sqla_task = ss.merge(sqla_task)
            task = ss.query(self.SqlaQueueModel).filter_by(job_id=sqla_task_dict['job_id']).first()
            task.status = TaskStatus.FAILED

    def set_task_status(self, sqla_task_dict, status: str):
        with SessionContext(self.Session()) as ss:
            # sqla_task = ss.merge(sqla_task)
            task = ss.query(self.SqlaQueueModel).filter(self.SqlaQueueModel.job_id == sqla_task_dict['job_id']).first()
            task.status = status

    def requeue_task(self, sqla_task_dict):
        self.set_task_status(sqla_task_dict, TaskStatus.REQUEUE)

    def clear_queue(self):
        with SessionContext(self.Session()) as ss:
            ss.query(self.SqlaQueueModel).delete(synchronize_session=False)

    def get_count_by_status(self, status):
        with SessionContext(self.Session()) as ss:
            return ss.query(func.count(self.SqlaQueueModel.job_id)).filter(self.SqlaQueueModel.status == status).scalar()

    @property
    def total_count(self):
        with SessionContext(self.Session()) as ss:
            return ss.query(func.count(self.SqlaQueueModel.job_id)).scalar()

    @property
    def to_be_consumed_count(self):
        return self.get_count_by_status(TaskStatus.TO_BE_CONSUMED)


if __name__ == '__main__':
    queue = SqlaQueue('queue37', 'sqlite:////sqlachemy_queues/queues.db').set_log_level(10)
    print()
    queue.bulk_push([dict(body=json.dumps({'a': i, 'b': 2 * i}), status=TaskStatus.TO_BE_CONSUMED) for i in range(10000)])
    print()
    for i in range(1000):
        queue.push(dict(body=json.dumps({'a': i, 'b': 2 * i}), status=TaskStatus.TO_BE_CONSUMED))
    task_dictx = queue.get()
    print(task_dictx)

```

### 代码文件: funboost\queues\__init__.py
```python

```

### 代码文件: funboost\timing_job\apscheduler_use_mysql_store.py
```python
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore


from funboost.timing_job import FsdfBackgroundScheduler


"""
这个是使用mysql作为定时任务持久化，支持动态修改 添加定时任务,用户完全可以自己按照 funboost/timing_job/apscheduler_use_redis_store.py 中的代码实现，因为apscheduler支持SQLAlchemyJobStore
只是scheduler改个jobstores类型，和funboost知识毫无关系，是apscheduler的知识。
"""
```

### 代码文件: funboost\timing_job\apscheduler_use_redis_store.py
```python
from apscheduler.jobstores.redis import RedisJobStore
from funboost.utils.redis_manager import RedisMixin,get_redis_conn_kwargs

from funboost.timing_job import FunboostBackgroundScheduler
from funboost.funboost_config_deafult import BrokerConnConfig, FunboostCommonConfig
from funboost.utils.decorators import RedisDistributedBlockLockContextManager


"""
这个是使用redis作为定时任务持久化，支持跨机器好跨进程，外部远程 动态修改/添加/删除定时任务
"""


class FunboostBackgroundSchedulerProcessJobsWithinRedisLock(FunboostBackgroundScheduler):
    """
    分布式或多进程都启动某个apscheduler实例，如果都使用的同一个数据库类型的jobstores ，_process_jobs有很大概率会造成报错， 因为_process_jobs使用的是线程锁，管不了其他进程和分布式机器。

    https://groups.google.com/g/apscheduler/c/Gjc_JQMPePc 问题也提到了这个bug

    继承 Custom schedulers https://apscheduler.readthedocs.io/en/3.x/extending.html   可以重写 _create_lock
    """

    process_jobs_redis_lock_key = None

    def set_process_jobs_redis_lock_key(self, lock_key):
        self.process_jobs_redis_lock_key = lock_key
        return self

    # def  _create_lock(self):
    #     return RedisDistributedBlockLockContextManager(RedisMixin().redis_db_frame,self.process_jobs_redis_lock_key,) 这个类的写法不适合固定的单例，
    #     RedisDistributedBlockLockContextManager的写法不适合 永远用一个 对象，所以还是放到 def  _process_jobs 里面运行

    # def _process_jobs(self):
    #     for i in range(10) :
    #         with RedisDistributedLockContextManager(RedisMixin().redis_db_frame, self.process_jobs_redis_lock_key, ) as lock:
    #             if lock.has_aquire_lock:
    #                 wait_seconds = super()._process_jobs()
    #                 return wait_seconds
    #             else:
    #                 time.sleep(0.1)
    #     return 0.1

    def _process_jobs(self):
        """
        funboost 的做法是 在任务取出阶段就加锁，从根本上防止了重复执行。
        这个很关键，防止多个apscheduler 实例同时扫描取出同一个定时任务，间接导致重复执行,
        在apscheduler 3.xx版本这样写来防止多个apscheduler实例 重复执行定时任务的问题,简直是神操作.

        _process_jobs 功能是扫描取出需要运行的定时任务,而不是直接运行定时任务
        只要扫描取出任务不会取出相同的任务,就间接的决定了不可能重复执行相同的定时任务了.
        

        不要以为随便在你自己的消费函数加个redis分布式锁就不会重复执行任务了,redis分布式锁是解决相同代码块不会并发执行,而不是解决重复执行.
        但funboost是神级别骚操作,把分布式锁加到_process_jobs里面,
        _process_jobs是获取一个即将运行的定时任务,是扫描并删除这个即将运行的定时任务,
        所以这里加分布式锁能间接解决不重复运行定时任务,一旦任务被取出，就会从 jobstore 中删除,其他实例就无法再取到这个任务了.

        """
        if self.process_jobs_redis_lock_key is None:
            raise ValueError('process_jobs_redis_lock_key is not set')
        with RedisDistributedBlockLockContextManager(RedisMixin().redis_db_frame, self.process_jobs_redis_lock_key, ):
            return super()._process_jobs()


jobstores = {
    "default": RedisJobStore(**get_redis_conn_kwargs(),
                             jobs_key='funboost.apscheduler.jobs',run_times_key="funboost.apscheduler.run_times")
}

"""
建议不要亲自使用这个 funboost_background_scheduler_redis_store 对象，而是 ApsJobAdder来添加定时任务，自动多个apscheduler对象实例，
尤其是redis作为jobstores时候，使用不同的jobstores，每个消费函数使用各自单独的jobs_key和 run_times_key
"""
funboost_background_scheduler_redis_store = FunboostBackgroundSchedulerProcessJobsWithinRedisLock(timezone=FunboostCommonConfig.TIMEZONE, daemon=False, jobstores=jobstores)






"""
跨python解释器 跨机器动态修改定时任务配置的例子在

test_frame/test_apschedual/test_aps_redis_store.py
test_frame/test_apschedual/test_change_aps_conf.py

"""

```

### 代码文件: funboost\timing_job\timing_job_base.py
```python
"""
集成定时任务。
"""
import atexit

import time
from apscheduler.executors.pool import BasePoolExecutor

from typing import Union
import threading

from apscheduler.schedulers.background import BackgroundScheduler
# noinspection PyProtectedMember
from apscheduler.schedulers.base import STATE_STOPPED, STATE_RUNNING
from apscheduler.util import undefined
from threading import TIMEOUT_MAX
import deprecated
from funboost.utils.redis_manager import RedisMixin

from funboost.funboost_config_deafult import FunboostCommonConfig

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.booster import BoostersManager, Booster

from funboost import BoosterParams
from funboost.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAble


@deprecated.deprecated(reason='以后不要再使用这种方式，对于job_store为数据库时候需要序列化不好。使用内存和数据库都兼容的添加任务方式: add_push_job')
def timing_publish_deco(consuming_func_decorated_or_consumer: Union[callable, AbstractConsumer]):
    def _deco(*args, **kwargs):
        if getattr(consuming_func_decorated_or_consumer, 'is_decorated_as_consume_function', False) is True:
            consuming_func_decorated_or_consumer.push(*args, **kwargs)
        elif isinstance(consuming_func_decorated_or_consumer, AbstractConsumer):
            consuming_func_decorated_or_consumer.publisher_of_same_queue.push(*args, **kwargs)
        else:
            raise TypeError('consuming_func_decorated_or_consumer 必须是被 boost 装饰的函数或者consumer类型')

    return _deco


def push_fun_params_to_broker(queue_name: str, *args, **kwargs):
    """
    queue_name 队列名字
    *args **kwargs 是消费函数的入参
    """
    
    BoostersManager.get_or_create_booster_by_queue_name(queue_name).push(*args, **kwargs)


class ThreadPoolExecutorForAps(BasePoolExecutor):
    """
    An executor that runs jobs in a concurrent.futures thread pool.

    Plugin alias: ``threadpool``

    :param max_workers: the maximum number of spawned threads.
    :param pool_kwargs: dict of keyword arguments to pass to the underlying
        ThreadPoolExecutor constructor
    """

    def __init__(self, max_workers=100, pool_kwargs=None):
        pool = ThreadPoolExecutorShrinkAble(int(max_workers), )
        super().__init__(pool)


class FunboostBackgroundScheduler(BackgroundScheduler):
    """
    自定义的， 继承了官方BackgroundScheduler，
    通过重写 _main_loop ，使得动态修改增加删除定时任务配置更好。
    """

    _last_wait_seconds = None
    _last_has_task = False

    @deprecated.deprecated(reason='以后不要再使用这种方式，对于job_store为数据库时候需要序列化不好。使用内存和数据库都兼容的添加任务方式: add_push_job')
    def add_timing_publish_job(self, func, trigger=None, args=None, kwargs=None, id=None, name=None,
                               misfire_grace_time=undefined, coalesce=undefined, max_instances=undefined,
                               next_run_time=undefined, jobstore='default', executor='default',
                               replace_existing=False, **trigger_args):
        return self.add_job(timing_publish_deco(func), trigger, args, kwargs, id, name,
                            misfire_grace_time, coalesce, max_instances,
                            next_run_time, jobstore, executor,
                            replace_existing, **trigger_args)

    def add_push_job(self, func: Booster, trigger=None, args=None, kwargs=None, 
                     id=None, name=None,
                     misfire_grace_time=undefined, coalesce=undefined, max_instances=undefined,
                     next_run_time=undefined, jobstore='default', executor='default',
                     replace_existing=False, **trigger_args, ):
        """
        :param func: 被@boost装饰器装饰的函数
        :param trigger:
        :param args:
        :param kwargs:
        :param id:
        :param name:
        :param misfire_grace_time:
        :param coalesce:
        :param max_instances:
        :param next_run_time:
        :param jobstore:
        :param executor:
        :param replace_existing:
        :param trigger_args:
        :return:
        """
        # args = args or {}
        # kwargs['queue_name'] = func.queue_name

        """
        用户如果不使用funboost的 FunboostBackgroundScheduler 类型对象，而是使用原生的apscheduler类型对象，可以scheduler.add_job(push_fun_params_to_broker,args=(,),kwargs={}) 
        push_fun_params_to_broker函数入参是消费函数队列的 queue_name 加上 原消费函数的入参
        """
        if args is None:
            args = tuple()
        args_list = list(args)
        args_list.insert(0, func.queue_name)
        args = tuple(args_list)
        if name is None:
            name = f'push_fun_params_to_broker_for_queue_{func.queue_name}'
        return self.add_job(push_fun_params_to_broker, trigger, args, kwargs, id, name,
                            misfire_grace_time, coalesce, max_instances,
                            next_run_time, jobstore, executor,
                            replace_existing, **trigger_args, )

    def start(self, paused=False, block_exit=True):
        # def _block_exit():
        #     while True:
        #         time.sleep(3600)
        #
        # threading.Thread(target=_block_exit,).start()  # 既不希望用BlockingScheduler阻塞主进程也不希望定时退出。
        # self._daemon = False
        # def _when_exit():
        #     while 1:
        #         # print('阻止退出')
        #         time.sleep(100)

        # if block_exit:
        #     atexit.register(_when_exit)
        self._daemon = False   # 这里强制默认改成非守护线程。默认是守护线程，主线程退出会报错。
        super().start(paused=paused, )
        # _block_exit()   # python3.9 判断守护线程结束必须主线程在运行。你自己在你的运行代碼的最末尾加上 while 1： time.sleep(100)  ,来阻止主线程退出。

    def _main_loop00000(self):
        """
        原来的代码是这，动态添加任务不友好。
        :return:
        """
        wait_seconds = threading.TIMEOUT_MAX
        while self.state != STATE_STOPPED:
            print(6666, self._event.is_set(), wait_seconds)
            self._event.wait(wait_seconds)
            print(7777, self._event.is_set(), wait_seconds)
            self._event.clear()
            wait_seconds = self._process_jobs()

    def _main_loop(self):
        """原来的_main_loop 删除所有任务后wait_seconds 会变成None，无限等待。
        或者下一个需要运行的任务的wait_seconds是3600秒后，此时新加了一个动态任务需要3600秒后，
        现在最多只需要1秒就能扫描到动态新增的定时任务了。
        """
        MAX_WAIT_SECONDS_FOR_NEX_PROCESS_JOBS = 0.5
        wait_seconds = None
        while self.state != STATE_STOPPED:
            if wait_seconds is None:
                wait_seconds = MAX_WAIT_SECONDS_FOR_NEX_PROCESS_JOBS
            self._last_wait_seconds = min(wait_seconds, MAX_WAIT_SECONDS_FOR_NEX_PROCESS_JOBS)
            if wait_seconds in (None, TIMEOUT_MAX):
                self._last_has_task = False
            else:
                self._last_has_task = True
            time.sleep(self._last_wait_seconds)  # 这个要取最小值，不然例如定时间隔0.1秒运行，不取最小值，不会每隔0.1秒运行。
            wait_seconds = self._process_jobs()

    def _create_default_executor(self):
        return ThreadPoolExecutorForAps()  # 必须是apscheduler pool的子类


FsdfBackgroundScheduler = FunboostBackgroundScheduler  # 兼容一下名字，fsdf是 function-scheduling-distributed-framework 老框架名字的缩写
# funboost_aps_scheduler定时配置基于内存的，不可以跨机器远程动态添加/修改/删除定时任务配置。如果需要动态增删改查定时任务，可以使用funboost_background_scheduler_redis_store

"""
建议不要亲自使用这个 funboost_aps_scheduler 对象，而是 ApsJobAdder来添加定时任务，自动多个apscheduler对象实例，
尤其是redis作为jobstores时候，使用不同的jobstores，每个消费函数使用各自单独的jobs_key和 run_times_key
"""
funboost_aps_scheduler = FunboostBackgroundScheduler(timezone=FunboostCommonConfig.TIMEZONE, daemon=False, )
fsdf_background_scheduler = funboost_aps_scheduler  # 兼容一下老名字。



if __name__ == '__main__':

    """
    下面的例子过时了，可以用但不建议，建议统一使用 ApsJobAdder 来添加定时任务。

    """

    # 定时运行消费演示
    import datetime
    from funboost import boost, BrokerEnum, fsdf_background_scheduler, timing_publish_deco, run_forever


    @Booster(boost_params=BoosterParams(queue_name='queue_test_666', broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE))
    def consume_func(x, y):
        print(f'{x} + {y} = {x + y}')


    print(consume_func, type(consume_func))

    # 定时每隔3秒执行一次。
    funboost_aps_scheduler.add_push_job(consume_func,
                                        'interval', id='3_second_job', seconds=3, kwargs={"x": 5, "y": 6})

    # 定时，只执行一次
    funboost_aps_scheduler.add_push_job(consume_func,
                                        'date', run_date=datetime.datetime(2020, 7, 24, 13, 53, 6), args=(5, 6,))

    # 定时，每天的11点32分20秒都执行一次。
    funboost_aps_scheduler.add_push_job(consume_func,
                                        'cron', day_of_week='*', hour=18, minute=22, second=20, args=(5, 6,))

    # 启动定时
    funboost_aps_scheduler.start()

    # 启动消费
    consume_func.consume()
    run_forever()

```

### 代码文件: funboost\timing_job\timing_push.py
```python
from funboost.utils import redis_manager
from funboost.core.booster import BoostersManager, Booster

from apscheduler.jobstores.redis import RedisJobStore
from funboost.timing_job.timing_job_base import funboost_aps_scheduler, undefined
from funboost.timing_job.apscheduler_use_redis_store import FunboostBackgroundSchedulerProcessJobsWithinRedisLock
from funboost.funboost_config_deafult import FunboostCommonConfig
from apscheduler.schedulers.base import BaseScheduler
from funboost.constant import RedisKeys

class ApsJobAdder:
    """
    20250116新增加的统一的新增定时任务的方式，推荐这种方式。
    用户不用像之前再去关心使用哪个apscheduler对象去添加定时任务了。

    例如 add_numbers 是@boost装饰的消费函数
    ApsJobAdder(add_numbers,job_store_kind='memory').add_push_job(
        args=(1, 2),
        trigger='date',  # 使用日期触发器
        run_date='2025-01-16 18:23:50',  # 设置运行时间
        # id='add_numbers_job'  # 任务ID
    )

    """

    queue__redis_aps_map = {}

    def __init__(self, booster: Booster, job_store_kind: str = 'memory',is_auto_start=True,is_auto_paused=False):
        """
        Initialize the ApsJobAdder.

        :param booster: A Booster object representing the function to be scheduled.
        :param job_store_kind: The type of job store to use. Default is 'memory'.
                               Can be 'memory' or 'redis'.
        """
        self.booster = booster
        self.job_store_kind = job_store_kind
        if getattr(self.aps_obj, 'has_started_flag', False) is False:
            if is_auto_start:
                self.aps_obj.has_started_flag = True
                self.aps_obj.start(paused=is_auto_paused)



    @classmethod
    def get_funboost_redis_apscheduler(cls, queue_name):
        """ 
        每个队列名字的定时任务用不同的redis jobstore的 jobs_key 和 run_times_key，防止互相干扰和取出不属于自己的任务
        """
        if queue_name in cls.queue__redis_aps_map:
            return cls.queue__redis_aps_map[queue_name]
        redis_jobstores = {

            "default": RedisJobStore(**redis_manager.get_redis_conn_kwargs(),
                                    jobs_key=RedisKeys.gen_funboost_redis_apscheduler_jobs_key_by_queue_name(queue_name),
                                    run_times_key=RedisKeys.gen_funboost_redis_apscheduler_run_times_key_by_queue_name(queue_name),
                                     )
        }
        redis_aps = FunboostBackgroundSchedulerProcessJobsWithinRedisLock(timezone=FunboostCommonConfig.TIMEZONE,
                                                                          daemon=False, jobstores=redis_jobstores)
        redis_aps.set_process_jobs_redis_lock_key(RedisKeys.gen_funboost_apscheduler_redis_lock_key_by_queue_name(queue_name))
        cls.queue__redis_aps_map[queue_name] = redis_aps
        return redis_aps

    @property
    def aps_obj(self) -> BaseScheduler:
        if self.job_store_kind == 'redis':
            return self.get_funboost_redis_apscheduler(self.booster.queue_name)
        elif self.job_store_kind == 'memory':
            return funboost_aps_scheduler
        else:
            raise ValueError('Unsupported job_store_kind')

    def add_push_job(self, trigger=None, args=None, kwargs=None,
                     id=None, name=None,
                     misfire_grace_time=undefined, coalesce=undefined, max_instances=undefined,
                     next_run_time=undefined, jobstore='default', executor='default',
                     replace_existing=False, **trigger_args, ):
        """
        1. 这里的入参都是和apscheduler的add_job的入参一样的，funboost作者没有创造新的入参。
        但是官方apscheduler的入参第一个入参是函数，
        funboost的ApsJobAdder对象.add_push_job入参去掉了函数，因为类的实例化时候会把函数传进来，不需要再麻烦用户一次了。
        

        2. add_push_job目的是 定时运行 消费函数.push方法发布消息到消费队列， 而不是 定时直接运行 消费函数自身。

        相当于 aps_obj.add_job(消费函数.push, trigger, args, kwargs, id, name, .....)
        那为什么 不直接使用 aps_obj.add_job(消费函数.push, trigger, args, kwargs, id, name, .....) 呢？因为 消费函数.push是实例方法，
        如果redis作为 jobstore， 消费函数.push 会报错，因为 消费函数.push 是实例方法，不能被序列化。只有普通函数和静态方法才能被序列化。
        所以开发了一个 add_push_job方法， 里面再去用 add_job， 使用 push_fun_params_to_broker 这个普通函数作为 add_job 的第一个入参，
        这个普通函数里面再去调用 消费函数.push 方法， 相当于是曲线救国避免 aps_obj.add_job(消费函数.push 不可序列化问题。


        3. 用户也可以自己定义一个普通函数my_push，你这个普通函数my_push 里面去调用消费函数.push方法；然后使用 aps_obj.add_job 使用你自己定义的这个my_push作为第一个入参。
        这种方式更容易你去理解，和apscheduler 官方库的原生写法一模一样。 但是不如 add_push_job 方便，因为 需要你亲自给每个消费函数分别定义一个普通函数my_push。

        """

        # if not getattr(self.aps_obj, 'has_started_flag', False):
        #     self.aps_obj.has_started_flag = True
        #     self.aps_obj.start(paused=False)
        return self.aps_obj.add_push_job(self.booster, trigger, args, kwargs, id, name,
                                         misfire_grace_time, coalesce, max_instances,
                                         next_run_time, jobstore, executor,
                                         replace_existing, **trigger_args, )


if __name__ == '__main__':
    """
    2025年后定时任务现在推荐使用 ApsJobAdder 写法 ，用户不需要亲自选择使用 apscheduler对象来添加定时任务
    特别是使用redis作为jobstores时候，你可以看源码就知道了。
    """
    from funboost import boost, BrokerEnum, ctrl_c_recv, BoosterParams, ApsJobAdder


    # 定义任务处理函数
    @BoosterParams(queue_name='sum_queue3', broker_kind=BrokerEnum.REDIS)
    def sum_two_numbers(x, y):
        result = x + y
        print(f'The sum of {x} and {y} is {result}')

    # 启动消费者
    # sum_two_numbers.consume()

    # 发布任务
    sum_two_numbers.push(3, 5)
    sum_two_numbers.push(10, 20)



    # 使用ApsJobAdder添加定时任务， 里面的定时语法，和apscheduler是一样的，用户需要自己熟悉知名框架apscheduler的add_job定时入参

    # 方式1：指定日期执行一次
    ApsJobAdder(sum_two_numbers, job_store_kind='redis').add_push_job(
        trigger='date',
        run_date='2025-01-17 23:25:40',
        args=(7, 8),
        id='date_job1'
    )

    # 方式2：固定间隔执行
    ApsJobAdder(sum_two_numbers, job_store_kind='memory').add_push_job(
        trigger='interval',
        seconds=5,
        args=(4, 6),
        id='interval_job1'
    )

    # 方式3：使用cron表达式定时执行,周期运行
    ApsJobAdder(sum_two_numbers, job_store_kind='redis').add_push_job(
        trigger='cron',
        day_of_week='*',
        hour=23,
        minute=49,
        second=50,
        kwargs={"x": 50, "y": 60},
        replace_existing=True,
        id='cron_job1')
    


    ctrl_c_recv() # 启动了守护线程的定时器，一定要阻止主线程退出。 你可以代码最末尾加这个 ctrl_c_recv() 或者加个 while 1:time.sleep(10)

```

### 代码文件: funboost\timing_job\__init__.py
```python
from  funboost.timing_job.timing_job_base import (FsdfBackgroundScheduler ,
funboost_aps_scheduler ,fsdf_background_scheduler,timing_publish_deco,FunboostBackgroundScheduler,push_fun_params_to_broker )



from funboost.timing_job.timing_push import ApsJobAdder
```

### 代码文件: funboost\utils\apscheduler_monkey.py
```python
from datetime import datetime, timedelta
from traceback import format_tb
import logging
import sys

from pytz import utc
import six

import apscheduler

from apscheduler.events import (
    JobExecutionEvent, EVENT_JOB_MISSED, EVENT_JOB_ERROR, EVENT_JOB_EXECUTED)


def my_run_job(job, jobstore_alias, run_times, logger_name):
    """
    主要是把函数的入参放到event上，便于listener获取函数对象和函数入参。
    """

    """
    Called by executors to run the job. Returns a list of scheduler events to be dispatched by the
    scheduler.

    """
    events = []
    logger = logging.getLogger(logger_name)
    for run_time in run_times:
        # See if the job missed its run time window, and handle
        # possible misfires accordingly
        # print(job.misfire_grace_time) # add_job不设置时候默认为1秒。
        if job.misfire_grace_time is not None:
            # print(job,dir(job),job.args,job.kwargs)
            difference = datetime.now(utc) - run_time
            grace_time = timedelta(seconds=job.misfire_grace_time)
            if difference > grace_time:
                ev = JobExecutionEvent(EVENT_JOB_MISSED, job.id, jobstore_alias,
                                       run_time)
                ev.function_args = job.args
                ev.function_kwargs = job.kwargs
                ev.function = job.func

                events.append(ev)
                logger.warning('Run time of job "%s" was missed by %s', job, difference)
                continue

        logger.info('Running job "%s" (scheduled at %s)', job, run_time)
        try:
            retval = job.func(*job.args, **job.kwargs)
        except BaseException:
            exc, tb = sys.exc_info()[1:]
            formatted_tb = ''.join(format_tb(tb))

            ev = JobExecutionEvent(EVENT_JOB_ERROR, job.id, jobstore_alias, run_time,
                                   exception=exc, traceback=formatted_tb)
            ev.function_args = job.args
            ev.function_kwargs = job.kwargs
            ev.function = job.func

            events.append(ev)
            logger.exception('Job "%s" raised an exception', job)

            # This is to prevent cyclic references that would lead to memory leaks
            if six.PY2:
                sys.exc_clear()
                del tb
            else:
                import traceback
                traceback.clear_frames(tb)
                del tb
        else:
            ev = JobExecutionEvent(EVENT_JOB_EXECUTED, job.id, jobstore_alias, run_time,
                                   retval=retval)
            ev.function_args = job.args
            ev.function_kwargs = job.kwargs
            ev.function = job.func

            events.append(ev)
            logger.info('Job "%s" executed successfully', job)

    return events





def patch_run_job():
    # from apscheduler.executors import base
    # base.run_job = my_run_job
    apscheduler.executors.base.run_job = my_run_job
    apscheduler.executors.pool.run_job = my_run_job

```

### 代码文件: funboost\utils\block_exit.py
```python



import time

def block_python_main_thread_exit():
    while 1:
        time.sleep(100)
```

### 代码文件: funboost\utils\bulk_operation.py
```python
# coding=utf8
"""
@author:Administrator
@file: bulk_operation.py
@time: 2018/08/27

三大数据库的更简单的批次操作，自动聚合一定时间内的离散任务为批次任务。免除手工数组切片的烦恼。
"""
import atexit
import re
import os
# from elasticsearch import helpers
from threading import Thread
from typing import Union
import abc
import time
from queue import Queue, Empty
import unittest
# noinspection PyUnresolvedReferences
from pymongo import UpdateOne, InsertOne, UpdateMany, collection, MongoClient
import redis

from funboost.core.lazy_impoter import ElasticsearchImporter
from funboost.utils.redis_manager import RedisMixin
from funboost.utils.time_util import DatetimeConverter
from funboost.utils import LoggerMixin, decorators


class RedisOperation:
    """redis的操作，此类作用主要是规范下格式而已"""

    def __init__(self, operation_name: str, key: str, value: str):
        """
        :param operation_name: redis操作名字，例如 sadd lpush等
        :param key: redis的键
        :param value: reids键的值
        """
        self.operation_name = operation_name
        self.key = key
        self.value = value


class BaseBulkHelper(LoggerMixin, metaclass=abc.ABCMeta):
    """批量操纵抽象基类"""
    bulk_helper_map = {}

    def __new__(cls, base_object, *args, **kwargs):
        cls_key = f'{str(base_object)}-{os.getpid()}'
        if cls_key not in cls.bulk_helper_map:  # 加str是由于有一些类型的实例不能被hash作为字典的键
            self = super().__new__(cls)
            return self
        else:
            return cls.bulk_helper_map[cls_key]

    def __init__(self, base_object: Union[collection.Collection, redis.Redis], threshold: int = 100, max_time_interval=10, is_print_log: bool = True):
        cls_key = f'{str(base_object)}-{os.getpid()}'
        if cls_key not in self.bulk_helper_map:
            self._custom_init(base_object, threshold, max_time_interval, is_print_log)
            self.bulk_helper_map[cls_key] = self

    def _custom_init(self, base_object, threshold, max_time_interval, is_print_log):
        self.base_object = base_object
        self._threshold = threshold
        self._max_time_interval = max_time_interval
        self._is_print_log = is_print_log
        self._to_be_request_queue = Queue(threshold * 2)
        self._current_time = time.time()
        self._last_has_task_time = time.time()
        atexit.register(self.__do_something_before_exit)  # 程序自动结束前执行注册的函数
        self._main_thread_has_exit = False
        # Thread(target=self.__excute_bulk_operation_in_other_thread).start()
        # Thread(target=self.__check_queue_size).start()
        self.__excute_bulk_operation_in_other_thread()
        self.__check_queue_size()
        self.logger.debug(f'{self.__class__}被实例化')

    def add_task(self, base_operation: Union[UpdateOne, InsertOne, RedisOperation, tuple, dict]):
        """添加单个需要执行的操作，程序自动聚合陈批次操作"""
        self._to_be_request_queue.put(base_operation)
        # self.logger.debug(base_operation)

    # @decorators.tomorrow_threads(100)
    @decorators.keep_circulating(1, block=False, daemon=True)  # redis异常或网络异常，使其自动恢复。
    def __excute_bulk_operation_in_other_thread(self):
        while True:
            if self._to_be_request_queue.qsize() >= self._threshold or time.time() > self._current_time + self._max_time_interval:
                self._do_bulk_operation()
            if self._main_thread_has_exit and self._to_be_request_queue.qsize() == 0:
                pass
                # break
            time.sleep(10 ** -1)

    @decorators.keep_circulating(60, block=False, daemon=True)
    def __check_queue_size(self):
        if self._to_be_request_queue.qsize() > 0:
            self._last_has_task_time = time.time()
        if time.time() - self._last_has_task_time > 60:
            self.logger.info(f'{self.base_object} 最近一次有任务的时间是 ： {DatetimeConverter(self._last_has_task_time)}')

    @abc.abstractmethod
    def _do_bulk_operation(self):
        raise NotImplementedError

    def __do_something_before_exit(self):
        self._main_thread_has_exit = True
        self.logger.critical(f'程序自动结束前执行  [{str(self.base_object)}]  执行剩余的任务')


class MongoBulkWriteHelper(BaseBulkHelper):
    """
    一个更简单的批量插入,可以直接提交一个操作，自动聚合多个操作为一个批次再插入，速度快了n倍。
    """

    def _do_bulk_operation(self):
        if self._to_be_request_queue.qsize() > 0:
            t_start = time.time()
            count = 0
            request_list = []
            for _ in range(0, self._threshold):
                try:
                    request = self._to_be_request_queue.get_nowait()
                    # print(request)
                    count += 1
                    request_list.append(request)
                except Empty:
                    pass
                    break
            if request_list:
                # print(request_list)
                self.base_object.bulk_write(request_list, ordered=False)
            if self._is_print_log:
                mongo_col_str = re.sub(r"document_class=dict, tz_aware=False, connect=True\),", "", str(self.base_object))
                self.logger.info(f'【{mongo_col_str}】  批量插入的任务数量是 {count} 消耗的时间是 {round(time.time() - t_start, 6)}')
            self._current_time = time.time()


class ElasticBulkHelper(BaseBulkHelper):
    """
    elastic批量插入。
    """

    def _do_bulk_operation(self):
        if self._to_be_request_queue.qsize() > 0:
            t_start = time.time()
            count = 0
            request_list = []
            for _ in range(self._threshold):
                try:
                    request = self._to_be_request_queue.get_nowait()
                    count += 1
                    request_list.append(request)
                except Empty:
                    pass
                    break
            if request_list:
                # self.base_object.bulk_write(request_list, ordered=False)
                ElasticsearchImporter().helpers.bulk(self.base_object, request_list)
            if self._is_print_log:
                self.logger.info(f'【{self.base_object}】  批量插入的任务数量是 {count} 消耗的时间是 {round(time.time() - t_start, 6)}')
            self._current_time = time.time()


class RedisBulkWriteHelper(BaseBulkHelper):
    """redis批量插入，比自带的更方便操作非整除批次"""

    def _do_bulk_operation(self):
        if self._to_be_request_queue.qsize() > 0:
            t_start = time.time()
            count = 0
            pipeline = self.base_object.pipeline()  # type: redis.client.Pipeline
            for _ in range(self._threshold):
                try:
                    request = self._to_be_request_queue.get_nowait()
                    count += 1
                except Empty:
                    break
                    pass
                else:
                    getattr(pipeline, request.operation_name)(request.key, request.value)
            pipeline.execute()
            pipeline.reset()
            if self._is_print_log:
                self.logger.info(f'[{str(self.base_object)}]  批量插入的任务数量是 {count} 消耗的时间是 {round(time.time() - t_start, 6)}')
            self._current_time = time.time()

    def _do_bulk_operation2(self):
        if self._to_be_request_queue.qsize() > 0:
            t_start = time.time()
            count = 0
            with self.base_object.pipeline() as pipeline:  # type: redis.client.Pipeline
                for _ in range(self._threshold):
                    try:
                        request = self._to_be_request_queue.get_nowait()
                        count += 1
                    except Empty:
                        pass
                    else:
                        getattr(pipeline, request.operation_name)(request.key, request.value)
                pipeline.execute()
            if self._is_print_log:
                self.logger.info(f'[{str(self.base_object)}]  批量插入的任务数量是 {count} 消耗的时间是 {round(time.time() - t_start, 6)}')
            self._current_time = time.time()


# noinspection SpellCheckingInspection,PyMethodMayBeStatic
class _Test(unittest.TestCase, LoggerMixin):
    # @unittest.skip
    def test_mongo_bulk_write(self):
        # col = MongoMixin().mongo_16_client.get_database('test').get_collection('ydf_test2')
        col = MongoClient('mongodb://myUserAdmin:8mwTdy1klnSYepNo@192.168.199.202:27016/admin').get_database('test').get_collection('ydf_test3')
        with decorators.TimerContextManager():
            for i in range(5000 + 13):
                # time.sleep(0.01)
                item = {'_id': i, 'field1': i * 2}
                mongo_helper = MongoBulkWriteHelper(col, 100, is_print_log=True)
                # mongo_helper.add_task(UpdateOne({'_id': item['_id']}, {'$set': item}, upsert=True))
                mongo_helper.add_task(InsertOne({'_id': item['_id']}))

    @unittest.skip
    def test_redis_bulk_write(self):

        with decorators.TimerContextManager():
            # r = redis.Redis(password='123456')
            r = RedisMixin().redis_db0
            redis_helper = RedisBulkWriteHelper(r, 200)
            # redis_helper = RedisBulkWriteHelper(r, 100)  # 放在外面可以
            for i in range(1003):
                # time.sleep(0.2)
                # 也可以在这里无限实例化
                redis_helper.add_task(RedisOperation('sadd', 'key1', str(i)))


if __name__ == '__main__':
    unittest.main()

```

### 代码文件: funboost\utils\class_utils.py
```python
import copy
import gc
import inspect
import re
import sys
import typing

import nb_log
from types import MethodType, FunctionType

from funboost.constant import FunctionKind


class ClsHelper:
    @staticmethod
    def get_instncae_method_cls(instncae_method):
        # print(instncae_method)
        # print(instncae_method.__qualname__)
        # print(instncae_method.__module__)
        return getattr(sys.modules[instncae_method.__module__],instncae_method.__qualname__.split('.')[0])
        # return instncae_method.__self__.__class__

    @staticmethod
    def get_classs_method_cls(class_method):
        # print(class_method)
        # print(class_method.__qualname__)
        # print(class_method.__module__)
        return getattr(sys.modules[class_method.__module__],class_method.__qualname__.split('.')[0])

    @staticmethod
    def is_class_method(method):
        # if inspect.ismethod(method):
        #     if hasattr(method, '__self__') and inspect.isclass(method.__self__):
        #         return True
        # return False

        sourcelines = inspect.getsourcelines(method)
        # print(sourcelines)
        line0: str = sourcelines[0][0]
        if line0.replace(' ', '').startswith('@classmethod'):
            return True

    @staticmethod
    def is_static_method(method):
        sourcelines = inspect.getsourcelines(method)
        line0: str = sourcelines[0][0]
        if line0.replace(' ', '').startswith('@staticmethod'):
            return True

    @classmethod
    def is_instance_method(cls, method):
        if cls.is_class_method(method):
            return False
        if cls.is_static_method(method):
            return False
        if isinstance(method, FunctionType):
            sourcelines = inspect.getsourcelines(method)
            for line in sourcelines[0][:50]:
                if not line.replace( ' ','').startswith('#'):
                    if not line.startswith('def') and re.search('\(\s*?self\s*?,',line):
                        return True
        # method_class = getattr(method, '__qualname__', '').rsplit('.', 1)[0]
        # if method_class:  # 如果能找到类名，说明是类的成员
        #     print( f"{method.__name__} 属于类 {method_class} 的成员")
        #
        #     return True

    @classmethod
    def is_common_function(cls, method):
        if cls.is_static_method(method):
            return False
        if cls.is_class_method(method):
            return False
        if cls.is_instance_method(method):
            return False
        if isinstance(method, FunctionType):
            sourcelines = inspect.getsourcelines(method)
            for line in sourcelines[0][:50]:
                if not line.replace(' ', '').startswith('#'):
                    if not re.search('\(\s*?self\s*?,', line):
                        return True

    @classmethod
    def get_method_kind(cls, method: typing.Callable) -> str:
        if cls.is_class_method(method):
            return FunctionKind.CLASS_METHOD
        elif cls.is_static_method(method):
            return FunctionKind.STATIC_METHOD
        elif cls.is_instance_method(method):
            return FunctionKind.INSTANCE_METHOD
        elif cls.is_common_function(method):
            return FunctionKind.COMMON_FUNCTION

    @staticmethod
    def get_obj_init_params_for_funboost(obj_init_params: dict):
        obj_init_params.pop('self')
        return copy.deepcopy(obj_init_params)


if __name__ == '__main__':
    pass
```

### 代码文件: funboost\utils\class_utils2.py
```python
import copy
import gc
import inspect
import re
import sys
import traceback
import typing

import nb_log
from types import MethodType, FunctionType




class ClsHelper:
    @staticmethod
    def is_static_method(func):
        # 获取类名
        class_name = func.__qualname__.split('.')[0]
        # 使用 inspect 获取函数的原始定义
        return isinstance(func, staticmethod) or (inspect.isfunction(func) and func.__qualname__.startswith(f'{class_name}.'))

    # 判断函数是否是实例方法
    @staticmethod
    def is_instance_method(method):
        # 检查方法是否是绑定到类实例上的方法
        return inspect.ismethod(method) or (inspect.isfunction(method) and getattr(method, '__self__', None) is not None)

    @staticmethod
    def is_class_method(method):
        # 检查方法是否是类方法
        return isinstance(method, classmethod) or (inspect.isfunction(method) and method.__self__ is None)



    @classmethod
    def is_common_function(cls, method):
        if cls.is_static_method(method):
            return False
        if cls.is_class_method(method):
            return False
        if cls.is_instance_method(method):
            return False
        if isinstance(method, FunctionType):
            sourcelines = inspect.getsourcelines(method)
            for line in sourcelines[0][:50]:
                if not line.replace(' ', '').startswith('#'):
                    if not re.search('\(\s*?self\s*?,', line):
                        return True

    @classmethod
    def get_method_kind(cls, method: typing.Callable) -> str:
        func =method
        try:
            if cls.is_instance_method(func):
                return "实例方法"
            if cls.is_static_method(func):
                return "静态方法"
            if cls.is_class_method(func):
                return "类方法"
            if inspect.isfunction(func):
                return "模块级函数"
        except Exception as e:
            print(traceback.format_exc())

    @staticmethod
    def get_obj_init_params_for_funboost(obj_init_params: dict):
        obj_init_params.pop('self')
        return copy.deepcopy(obj_init_params)




if __name__ == '__main__':
    def module_function():
        return "I am a module-level function"


    class MyClass:
        @staticmethod
        def static_method():
            return "I am a static method"

        @classmethod
        def class_method(cls):
            return "I am a class method"

        def instance_method(self):
            return "I am a instance method"

    print(ClsHelper.get_method_kind(module_function))  # 输出: 模块级函数
    print(ClsHelper.get_method_kind(MyClass.static_method))  # 输出: 静态方法
    print(ClsHelper.get_method_kind(MyClass.class_method))  # 输出: 类方法
    print(ClsHelper.get_method_kind(MyClass.instance_method))  # 输出: 实例方法

```

### 代码文件: funboost\utils\ctrl_c_end.py
```python
import os
import sys
import time
import signal


def signal_handler(signum, frame):
    print(f'收到信号 {signum}，程序准备退出', flush=True)
    sys.exit(4)
    os._exit(44)


def ctrl_c_recv():
    """ 
    主要目的就是阻止主线程退出而已。 因为funboost为了方便用户连续启动多个consume都是子线程运行循环调度的。
    apscheduler background 类型必须有主线程在运行，否则会很快结束。所以需要阻止主线程退出。
    在代码最最末尾加上 ctrl_c_recv() 就可以阻止主线程退出。
    
    你也可以不用ctrl_c_recv(),  直接在你的启动脚本文件的最末尾加上：
    while 1:
        time.sleep(100) 
    来达到阻止主线程退出的目的。
    """
    # signal.signal(signal.SIGTERM, signal_handler)
    
    for i in range(3):
        while 1:
            try:
                time.sleep(2)
            except (KeyboardInterrupt,) as e:
                # time.sleep(2)
                print(f'{type(e)} 你按了ctrl c ,程序退出, 第 {i + 1} 次', flush=True)
                # time.sleep(2)
                break
    # sys.exit(4)
    os._exit(44)
    # exit(444)

```

### 代码文件: funboost\utils\custom_pysnooper.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
"""
基于0.0.11版本，对其打猴子补丁改进的。现在推荐使用pysnooper_ydf里面的，不需要用这里。
DeBug Python代码全靠print函数？换用这个一天2K+Star的工具吧
对最火热的github库，进行了三点改造。
1、由于部署一般是linux，开发是windows，所以可以自动使其在linux上失效，调试会消耗性能。
2、将代码运行轨迹修改成可以点击的，点击对应行号可以跳转到代码位置。
3、提供一个猴子补丁，使用猴子补丁修改三方包的模块级全局变量MAX_VARIABLE_LENGTH ，最大变量默认是100，但对调试对接方json时候，往往很大，可以加大到最大显示10万个字母。

"""
import datetime
import os
from functools import wraps
import decorator
import pysnooper  # 需要安装 pip install pysnooper==0.0.11
from pysnooper.pysnooper import get_write_function
from pysnooper.tracer import Tracer, get_local_reprs, get_source_from_frame

os_name = os.name


class TracerCanClick(Tracer):
    """
    使代码运行轨迹可点击。
    """

    def trace(self, frame, event, arg):
        if frame.f_code is not self.target_code_object:
            if self.depth == 1:

                return self.trace
            else:
                _frame_candidate = frame
                for i in range(1, self.depth):
                    _frame_candidate = _frame_candidate.f_back
                    if _frame_candidate is None:
                        return self.trace
                    elif _frame_candidate.f_code is self.target_code_object:
                        indent = ' ' * 4 * i
                        break
                else:
                    return self.trace
        else:
            indent = ''

        self.frame_to_old_local_reprs[frame] = old_local_reprs = \
            self.frame_to_local_reprs[frame]
        self.frame_to_local_reprs[frame] = local_reprs = \
            get_local_reprs(frame, variables=self.variables)

        modified_local_reprs = {}
        newish_local_reprs = {}

        for key, value in local_reprs.items():
            if key not in old_local_reprs:
                newish_local_reprs[key] = value
            elif old_local_reprs[key] != value:
                modified_local_reprs[key] = value

        newish_string = ('Starting var:.. ' if event == 'call' else
                         'New var:....... ')
        for name, value_repr in newish_local_reprs.items():
            self.write('{indent}{newish_string}{name} = {value_repr}'.format(
                **locals()))
        for name, value_repr in modified_local_reprs.items():
            self.write('{indent}Modified var:.. {name} = {value_repr}'.format(
                **locals()))

        now_string = datetime.datetime.now().time().isoformat()
        source_line = get_source_from_frame(frame)[frame.f_lineno - 1]
        # print(frame)
        # print(dir(frame.f_code))
        # print(frame.f_code.co_filename)
        file_name_and_line = f'{frame.f_code.co_filename}:{frame.f_lineno}'
        # print(file_name_and_line)

        # self.write('{indent}{now_string} {event:9} '
        #            '{frame.f_lineno:4} {source_line}'.format(**locals()))
        file_name_and_line2 = f'"{file_name_and_line}"'
        self.write('{indent}{now_string} {event:9} '  # REMIND 主要是修改了这一行，使debug可点击。
                   '{file_name_and_line2:100} {source_line}'.format(**locals()))
        return self.trace


def _snoop_can_click(output=None, variables=(), depth=1, prefix=''):
    write = get_write_function(output)

    # noinspection PyShadowingBuiltins
    @decorator.decorator
    def decorate(function, *args, **kwargs):
        target_code_object = function.__code__
        with TracerCanClick(target_code_object=target_code_object,
                            write=write, variables=variables,
                            depth=depth, prefix=prefix):
            return function(*args, **kwargs)

    return decorate


def snoop_deco(output=None, variables: tuple = (), depth=1, prefix='', do_not_effect_on_linux=True, line_can_click=True):
    # REMIND 对装饰器再包装一次，不使用上面的和官方的。
    def _snoop(func):
        nonlocal prefix
        if prefix == '':
            prefix = f'调试 [{func.__name__}] 函数 -->  '

        @wraps(func)
        def __snoop(*args, **kwargs):
            if os_name != 'nt' and do_not_effect_on_linux:  # 不要修改任何代码，自动就会不在linux上debug，一般linux是部署机器。
                return func(*args, **kwargs)
            else:
                if line_can_click:
                    return _snoop_can_click(output, variables, depth, prefix)(func)(*args, **kwargs)
                else:
                    return pysnooper.snoop(output, variables, depth, prefix)(func)(*args, **kwargs)

        return __snoop

    return _snoop


def patch_snooper_max_variable_length(max_lenth=100000):
    """
    提供一个猴子补丁，三方包默认是变量最大显示100个字母，对于我这种经常debug对接方json的，要加到10万才能显示一个josn。
    最好是放在name = main中去执行此补丁，否则由于模块是单例的永远只导入一次，会改变其他地方的运行表现。
    :param max_lenth:
    :return:
    """
    from pysnooper import tracer
    tracer.MAX_VARIABLE_LENGTH = max_lenth


if __name__ == '__main__':
    patch_snooper_max_variable_length(10000)


    @snoop_deco(line_can_click=True, do_not_effect_on_linux=True)
    def fun2():
        x = 1
        x += 2
        y = '6' * 10
        if x == 3:
            print('ttttt')
        else:
            print('ffff')


    fun2()

```

### 代码文件: funboost\utils\decorators.py
```python
# coding=utf-8
import base64
import copy
import abc
import logging
import random
import uuid
from typing import TypeVar
# noinspection PyUnresolvedReferences
from contextlib import contextmanager
import functools
import json
import os
import sys
import threading
import time
import traceback
import unittest
from functools import wraps
# noinspection PyUnresolvedReferences
import pysnooper
from tomorrow3 import threads as tomorrow_threads

from funboost.utils import LogManager, nb_print, LoggerMixin
# noinspection PyUnresolvedReferences
# from funboost.utils.custom_pysnooper import _snoop_can_click, snoop_deco, patch_snooper_max_variable_length
from nb_log import LoggerLevelSetterMixin

os_name = os.name
# nb_print(f' 操作系统类型是  {os_name}')
handle_exception_log = LogManager('function_error').get_logger_and_add_handlers()
run_times_log = LogManager('run_many_times').get_logger_and_add_handlers(20)


class CustomException(Exception):
    def __init__(self, err=''):
        err0 = 'fatal exception\n'
        Exception.__init__(self, err0 + err)


def run_many_times(times=1):
    """把函数运行times次的装饰器
    :param times:运行次数
    没有捕获错误，出错误就中断运行，可以配合handle_exception装饰器不管是否错误都运行n次。
    """

    def _run_many_times(func):
        @wraps(func)
        def __run_many_times(*args, **kwargs):
            for i in range(times):
                run_times_log.debug('* ' * 50 + '当前是第 {} 次运行[ {} ]函数'.format(i + 1, func.__name__))
                func(*args, **kwargs)

        return __run_many_times

    return _run_many_times


# noinspection PyIncorrectDocstring
def handle_exception(retry_times=0, error_detail_level=0, is_throw_error=False, time_sleep=0):
    """捕获函数错误的装饰器,重试并打印日志
    :param retry_times : 重试次数
    :param error_detail_level :为0打印exception提示，为1打印3层深度的错误堆栈，为2打印所有深度层次的错误堆栈
    :param is_throw_error : 在达到最大次数时候是否重新抛出错误
    :type error_detail_level: int
    """

    if error_detail_level not in [0, 1, 2]:
        raise Exception('error_detail_level参数必须设置为0 、1 、2')

    def _handle_exception(func):
        @wraps(func)
        def __handle_exception(*args, **keyargs):
            for i in range(0, retry_times + 1):
                try:
                    result = func(*args, **keyargs)
                    if i:
                        handle_exception_log.debug(
                            u'%s\n调用成功，调用方法--> [  %s  ] 第  %s  次重试成功' % ('# ' * 40, func.__name__, i))
                    return result

                except BaseException as e:
                    error_info = ''
                    if error_detail_level == 0:
                        error_info = '错误类型是：' + str(e.__class__) + '  ' + str(e)
                    elif error_detail_level == 1:
                        error_info = '错误类型是：' + str(e.__class__) + '  ' + traceback.format_exc(limit=3)
                    elif error_detail_level == 2:
                        error_info = '错误类型是：' + str(e.__class__) + '  ' + traceback.format_exc()

                    handle_exception_log.exception(
                        u'%s\n记录错误日志，调用方法--> [  %s  ] 第  %s  次错误重试， %s\n' % ('- ' * 40, func.__name__, i, error_info))
                    if i == retry_times and is_throw_error:  # 达到最大错误次数后，重新抛出错误
                        raise e
                time.sleep(time_sleep)

        return __handle_exception

    return _handle_exception


def keep_circulating(time_sleep=0.001, exit_if_function_run_sucsess=False, is_display_detail_exception=True, block=True, daemon=False):
    """间隔一段时间，一直循环运行某个方法的装饰器
    :param time_sleep :循环的间隔时间
    :param exit_if_function_run_sucsess :如果成功了就退出循环
    :param is_display_detail_exception
    :param block :是否阻塞主主线程，False时候开启一个新的线程运行while 1。
    """
    if not hasattr(keep_circulating, 'keep_circulating_log'):
        keep_circulating.log = LogManager('keep_circulating').get_logger_and_add_handlers()

    def _keep_circulating(func):
        @wraps(func)
        def __keep_circulating(*args, **kwargs):

            # noinspection PyBroadException
            def ___keep_circulating():
                while 1:
                    try:
                        result = func(*args, **kwargs)
                        if exit_if_function_run_sucsess:
                            return result
                    except BaseException as e:
                        msg = func.__name__ + '   运行出错\n ' + traceback.format_exc(limit=10) if is_display_detail_exception else str(e)
                        keep_circulating.log.error(msg)
                    finally:
                        time.sleep(time_sleep)

            if block:
                return ___keep_circulating()
            else:
                threading.Thread(target=___keep_circulating, daemon=daemon).start()

        return __keep_circulating

    return _keep_circulating


def synchronized(func):
    """线程锁装饰器，可以加在单例模式上"""
    func.__lock__ = threading.Lock()

    @wraps(func)
    def lock_func(*args, **kwargs):
        with func.__lock__:
            return func(*args, **kwargs)

    return lock_func

ClSX = TypeVar('CLSX')
def singleton(cls:ClSX)  -> ClSX:
    """
    单例模式装饰器,新加入线程锁，更牢固的单例模式，主要解决多线程如100线程同时实例化情况下可能会出现三例四例的情况,实测。
    """
    _instance = {}
    singleton.__lock = threading.Lock()

    @wraps(cls)
    def _singleton(*args, **kwargs):
        with singleton.__lock:
            if cls not in _instance:
                _instance[cls] = cls(*args, **kwargs)
            return _instance[cls]

    return _singleton

def singleton_no_lock(cls:ClSX)  -> ClSX:
    """
    单例模式装饰器,新加入线程锁，更牢固的单例模式，主要解决多线程如100线程同时实例化情况下可能会出现三例四例的情况,实测。
    """
    _instance = {}


    @wraps(cls)
    def _singleton(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]

    return _singleton

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class SingletonBaseCall(metaclass=SingletonMeta):
    """
    单例基类。任何继承自这个基类的子类都会自动成为单例。

    示例：
    class MyClass(SingletonBase):
        pass

    instance1 = MyClass()
    instance2 = MyClass()

    assert instance1 is instance2  # 实例1和实例2实际上是同一个对象
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # 可以在此处添加对子类的额外处理，比如检查其是否符合单例要求等


class SingletonBaseNew:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # 可以在此处添加对子类的额外处理，比如检查其是否符合单例要求等


class SingletonBaseCustomInit(metaclass=abc.ABCMeta):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._custom_init(*args, **kwargs)
        return cls._instance

    def _custom_init(self, *args, **kwargs):
        raise NotImplemented


def flyweight(cls):
    _instance = {}

    def _make_arguments_to_key(args, kwds):
        key = args
        if kwds:
            sorted_items = sorted(kwds.items())
            for item in sorted_items:
                key += item
        return key

    @synchronized
    @wraps(cls)
    def _flyweight(*args, **kwargs):
        # locals_copy = copy.deepcopy(locals())
        # import inspect
        # nb_print(inspect.getfullargspec(cls.__init__))
        # nb_print(cls.__init__.__defaults__)  # 使用__code__#总参数个数
        #
        # nb_print(cls.__init__.__code__.co_argcount)  # 总参数名
        #
        # nb_print(cls.__init__.__code__.co_varnames)
        #
        #
        # nb_print(locals_copy)
        # cache_param_value_list = [locals_copy.get(param, None) for param in cache_params]

        cache_key = f'{cls}_{_make_arguments_to_key(args, kwargs)}'
        # nb_print(cache_key)
        if cache_key not in _instance:
            _instance[cache_key] = cls(*args, **kwargs)
        return _instance[cache_key]

    return _flyweight


def timer(func):
    """计时器装饰器，只能用来计算函数运行时间"""
    if not hasattr(timer, 'log'):
        timer.log = LogManager(f'timer_{func.__name__}').get_logger_and_add_handlers(log_filename=f'timer_{func.__name__}.log')

    @wraps(func)
    def _timer(*args, **kwargs):
        t1 = time.time()
        result = func(*args, **kwargs)
        t2 = time.time()
        t_spend = round(t2 - t1, 2)
        timer.log.debug('执行[ {} ]方法用时 {} 秒'.format(func.__name__, t_spend))
        return result

    return _timer


# noinspection PyProtectedMember
class TimerContextManager(LoggerMixin):
    """
    用上下文管理器计时，可对代码片段计时
    """

    def __init__(self, is_print_log=True):
        self._is_print_log = is_print_log
        self.t_spend = None
        self._line = None
        self._file_name = None
        self.time_start = None

    def __enter__(self):
        self._line = sys._getframe().f_back.f_lineno  # 调用此方法的代码的函数
        self._file_name = sys._getframe(1).f_code.co_filename  # 哪个文件调了用此方法
        self.time_start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.t_spend = time.time() - self.time_start
        if self._is_print_log:
            self.logger.debug(f'对下面代码片段进行计时:  \n执行"{self._file_name}:{self._line}" 用时 {round(self.t_spend, 2)} 秒')


class RedisDistributedLockContextManager(LoggerMixin, LoggerLevelSetterMixin):
    """
    分布式redis锁上下文管理.
    """
    '''
    redis 官方推荐的 redlock-py
    https://github.com/SPSCommerce/redlock-py/blob/master/redlock/__init__.py
    '''
    unlock_script = """
       if redis.call("get",KEYS[1]) == ARGV[1] then
           return redis.call("del",KEYS[1])
       else
           return 0
       end"""

    def __init__(self, redis_client, redis_lock_key, expire_seconds=30, ):
        self.redis_client = redis_client
        self.redis_lock_key = redis_lock_key
        self._expire_seconds = expire_seconds
        self.identifier = str(uuid.uuid4())
        self.has_aquire_lock = False
        self.logger.setLevel(logging.INFO)

    def __enter__(self):
        self._line = sys._getframe().f_back.f_lineno  # 调用此方法的代码的函数
        self._file_name = sys._getframe(1).f_code.co_filename  # 哪个文件调了用此方法
        ret = self.redis_client.set(self.redis_lock_key, value=self.identifier, ex=self._expire_seconds, nx=True)

        self.has_aquire_lock = False if ret is None else True
        if self.has_aquire_lock:
            log_msg = f'\n"{self._file_name}:{self._line}" 这行代码获得了redis锁 {self.redis_lock_key}'
        else:
            log_msg = f'\n"{self._file_name}:{self._line}" 这行代码此次没有获得redis锁 {self.redis_lock_key}'
        # print(self.logger.level,log_msg)
        self.logger.debug(log_msg)
        return self

    def __bool__(self):
        return self.has_aquire_lock

    def __exit__(self, exc_type, exc_val, exc_tb):
        # self.redis_client.delete(self.redis_lock_key)
        unlock = self.redis_client.register_script(self.unlock_script)
        result = unlock(keys=[self.redis_lock_key], args=[self.identifier])
        if result:
            return True
        else:
            return False


class RedisDistributedBlockLockContextManager(RedisDistributedLockContextManager):
    def __init__(self, redis_client, redis_lock_key, expire_seconds=30, check_interval=0.1):
        super().__init__(redis_client,redis_lock_key,expire_seconds)
        self.check_interval = check_interval
        # self.logger.setLevel(logging.DEBUG)

    def __enter__(self):
        while True:
            self._line = sys._getframe().f_back.f_lineno  # 调用此方法的代码的函数
            self._file_name = sys._getframe(1).f_code.co_filename  # 哪个文件调了用此方法
            ret = self.redis_client.set(self.redis_lock_key, value=self.identifier, ex=self._expire_seconds, nx=True)
            has_aquire_lock = False if ret is None else True
            if has_aquire_lock:
                log_msg = f'\n"{self._file_name}:{self._line}" 这行代码获得了redis锁 {self.redis_lock_key}'
            else:
                log_msg = f'\n"{self._file_name}:{self._line}" 这行代码此次没有获得redis锁 {self.redis_lock_key}'
            # print(self.logger.level,log_msg)
            self.logger.debug(log_msg)
            if has_aquire_lock:
                break
            else:
                time.sleep(self.check_interval)


"""
@contextmanager
        def some_generator(<arguments>):
            <setup>
            try:
                yield <value>
            finally:
                <cleanup>
"""





class ExceptionContextManager:
    """
    用上下文管理器捕获异常，可对代码片段进行错误捕捉，比装饰器更细腻
    """

    def __init__(self, logger_name='ExceptionContextManager', verbose=100, donot_raise__exception=True, ):
        """
        :param verbose: 打印错误的深度,对应traceback对象的limit，为正整数
        :param donot_raise__exception:是否不重新抛出错误，为Fasle则抛出，为True则不抛出
        """
        self.logger = LogManager(logger_name).get_logger_and_add_handlers()
        self._verbose = verbose
        self._donot_raise__exception = donot_raise__exception

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # print(exc_val)
        # print(traceback.format_exc())
        exc_str = str(exc_type) + '  :  ' + str(exc_val)
        exc_str_color = '\033[0;30;45m%s\033[0m' % exc_str
        if self._donot_raise__exception:
            if exc_tb is not None:
                self.logger.error('\n'.join(traceback.format_tb(exc_tb)[:self._verbose]) + exc_str_color)
        return self._donot_raise__exception  # __exit__方法必须retuen True才会不重新抛出错误


def where_is_it_called(func):
    """一个装饰器，被装饰的函数，如果被调用，将记录一条日志,记录函数被什么文件的哪一行代码所调用"""
    if not hasattr(where_is_it_called, 'log'):
        where_is_it_called.log = LogManager('where_is_it_called').get_logger_and_add_handlers()

    # noinspection PyProtectedMember
    @wraps(func)
    def _where_is_it_called(*args, **kwargs):
        # 获取被调用函数名称
        # func_name = sys._getframe().f_code.co_name
        func_name = func.__name__
        # 什么函数调用了此函数
        which_fun_call_this = sys._getframe(1).f_code.co_name  # NOQA

        # 获取被调用函数在被调用时所处代码行数
        line = sys._getframe().f_back.f_lineno

        # 获取被调用函数所在模块文件名
        file_name = sys._getframe(1).f_code.co_filename

        # noinspection PyPep8
        where_is_it_called.log.debug(
            f'文件[{func.__code__.co_filename}]的第[{func.__code__.co_firstlineno}]行即模块 [{func.__module__}] 中的方法 [{func_name}] 正在被文件 [{file_name}] 中的'
            f'方法 [{which_fun_call_this}] 中的第 [{line}] 行处调用，传入的参数为[{args},{kwargs}]')
        try:
            t0 = time.time()
            result = func(*args, **kwargs)
            result_raw = result
            t_spend = round(time.time() - t0, 2)
            if isinstance(result, dict):
                result = json.dumps(result)
            if len(str(result)) > 200:
                result = str(result)[0:200] + '  。。。。。。  '
            where_is_it_called.log.debug('执行函数[{}]消耗的时间是{}秒，返回的结果是 --> '.format(func_name, t_spend) + str(result))
            return result_raw
        except BaseException as e:
            where_is_it_called.log.debug('执行函数{}，发生错误'.format(func_name))
            where_is_it_called.log.exception(e)
            raise e

    return _where_is_it_called


# noinspection PyPep8Naming
class cached_class_property(object):
    """类属性缓存装饰器"""

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = self.func(obj)
        setattr(cls, self.func.__name__, value)
        return value


# noinspection PyPep8Naming
class cached_property(object):
    """实例属性缓存装饰器"""

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        print(obj, cls)
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


def cached_method_result(fun):
    """方法的结果装饰器,不接受self以外的多余参数，主要用于那些属性类的property方法属性上，配合property装饰器，主要是在pycahrm自动补全上比上面的装饰器好"""

    @wraps(fun)
    def inner(self):
        if not hasattr(fun, 'result'):
            result = fun(self)
            fun.result = result
            fun_name = fun.__name__
            setattr(self.__class__, fun_name, result)
            setattr(self, fun_name, result)
            return result
        else:
            return fun.result

    return inner


def cached_method_result_for_instance(fun):
    """方法的结果装饰器,不接受self以外的多余参数，主要用于那些属性类的property方法属性上"""

    @wraps(fun)
    def inner(self):
        if not hasattr(fun, 'result'):
            result = fun(self)
            fun.result = result
            fun_name = fun.__name__
            setattr(self, fun_name, result)
            return result
        else:
            return fun.result

    return inner


class FunctionResultCacher:
    logger = LogManager('FunctionResultChche').get_logger_and_add_handlers(log_level_int=20)
    func_result_dict = {}
    """
    {
        (f1,(1,2,3,4)):(10,1532066199.739),
        (f2,(5,6,7,8)):(26,1532066211.645),
    }
    """

    @classmethod
    def cached_function_result_for_a_time(cls, cache_time: float):
        """
        函数的结果缓存一段时间装饰器,不要装饰在返回结果是超大字符串或者其他占用大内存的数据结构上的函数上面。
        :param cache_time :缓存的时间
        :type cache_time : float
        """

        def _cached_function_result_for_a_time(fun):

            @wraps(fun)
            def __cached_function_result_for_a_time(*args, **kwargs):
                # print(cls.func_result_dict)
                # if len(cls.func_result_dict) > 1024:
                if sys.getsizeof(cls.func_result_dict) > 100 * 1000 * 1000:
                    cls.func_result_dict.clear()

                key = cls._make_arguments_to_key(args, kwargs)
                if (fun, key) in cls.func_result_dict and time.time() - cls.func_result_dict[(fun, key)][1] < cache_time:
                    return cls.func_result_dict[(fun, key)][0]
                else:
                    cls.logger.debug('函数 [{}] 此次不能使用缓存'.format(fun.__name__))
                    result = fun(*args, **kwargs)
                    cls.func_result_dict[(fun, key)] = (result, time.time())
                    return result

            return __cached_function_result_for_a_time

        return _cached_function_result_for_a_time

    @staticmethod
    def _make_arguments_to_key(args, kwds):
        key = args
        if kwds:
            sorted_items = sorted(kwds.items())
            for item in sorted_items:
                key += item
        return key  # 元祖可以相加。


# noinspection PyUnusedLocal
class __KThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.killed = False
        self.__run_backup = None

    # noinspection PyAttributeOutsideInit
    def start(self):
        """Start the thread."""
        self.__run_backup = self.run
        self.run = self.__run  # Force the Thread to install our trace.
        threading.Thread.start(self)

    def __run(self):
        """Hacked run function, which installs the trace."""
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, why, arg):
        if why == 'call':
            return self.localtrace
        return None

    def localtrace(self, frame, why, arg):
        if self.killed:
            if why == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True


# noinspection PyPep8Naming
class TIMEOUT_EXCEPTION(Exception):
    """function run timeout"""
    pass


def timeout(seconds):
    """超时装饰器，指定超时时间

    若被装饰的方法在指定的时间内未返回，则抛出Timeout异常"""

    def timeout_decorator(func):

        def _(*args, **kwargs):
            def _new_func(oldfunc, result, oldfunc_args, oldfunc_kwargs):
                result.append(oldfunc(*oldfunc_args, **oldfunc_kwargs))

            result = []
            new_kwargs = {
                'oldfunc': func,
                'result': result,
                'oldfunc_args': args,
                'oldfunc_kwargs': kwargs
            }

            thd = __KThread(target=_new_func, args=(), kwargs=new_kwargs)
            thd.start()
            thd.join(seconds)
            alive = thd.is_alive()
            thd.kill()  # kill the child thread

            if alive:
                # raise TIMEOUT_EXCEPTION('function run too long, timeout %d seconds.' % seconds)
                raise TIMEOUT_EXCEPTION(f'{func.__name__}运行时间超过{seconds}秒')
            else:
                if result:
                    return result[0]
                return result

        _.__name__ = func.__name__
        _.__doc__ = func.__doc__
        return _

    return timeout_decorator


# noinspection PyMethodMayBeStatic
class _Test(unittest.TestCase):
    @unittest.skip
    def test_superposition(self):
        """测试多次运行和异常重试,测试装饰器叠加"""

        @run_many_times(3)
        @handle_exception(2, 1)
        def f():
            import json
            json.loads('a', ac='ds')

        f()

    @unittest.skip
    def test_run_many_times(self):
        """测试运行5次"""

        @run_many_times(5)
        def f1():
            print('hello')
            time.sleep(1)

        f1()

    @unittest.skip
    def test_tomorrow_threads(self):
        """测试多线程装饰器,每2秒打印5次"""

        @tomorrow_threads(5)
        def f2():
            print(time.strftime('%H:%M:%S'))
            time.sleep(2)

        [f2() for _ in range(9)]

    @unittest.skip
    def test_singleton(self):
        """测试单例模式的装饰器"""

        @singleton
        class A(object):
            def __init__(self, x):
                self.x = x

        a1 = A(3)
        a2 = A(4)
        self.assertEqual(id(a1), id(a2))
        print(a1.x, a2.x)

    @unittest.skip
    def test_flyweight(self):
        @flyweight
        class A:
            def __init__(self, x, y, z, q=4):
                in_param = copy.deepcopy(locals())
                nb_print(f'执行初始化啦, {in_param}')

        @flyweight
        class B:
            def __init__(self, x, y, z):
                in_param = copy.deepcopy(locals())
                nb_print(f'执行初始化啦, {in_param}')

        A(1, 2, 3)
        A(1, 2, 3)
        A(1, 2, 4)
        B(1, 2, 3)

    @unittest.skip
    def test_keep_circulating(self):
        """测试间隔时间，循环运行"""

        @keep_circulating(3)
        def f6():
            print("每隔3秒，一直打印   " + time.strftime('%H:%M:%S'))

        f6()

    @unittest.skip
    def test_timer(self):
        """测试计时器装饰器"""

        @timer
        def f7():
            time.sleep(2)

        f7()

    @unittest.skip
    def test_timer_context(self):
        """
        测试上下文，对代码片段进行计时
        """
        with TimerContextManager(is_print_log=False) as tc:
            time.sleep(2)
        print(tc.t_spend)

    @unittest.skip
    def test_where_is_it_called(self):
        """测试函数被调用的装饰器，被调用2次将会记录2次被调用的日志"""

        @where_is_it_called
        def f9(a, b):
            result = a + b
            print(result)
            time.sleep(0.1)
            return result

        f9(1, 2)

        f9(3, 4)

    # noinspection PyArgumentEqualDefault
    # @unittest.skip
    def test_cached_function_result(self):
        @FunctionResultCacher.cached_function_result_for_a_time(3)
        def f10(a, b, c=3, d=4):
            print('计算中。。。')
            return a + b + c + d

        print(f10(1, 2, 3, d=6))
        print(f10(1, 2, 3, d=4))
        print(f10(1, 2, 3, 4))
        print(f10(1, 2, 3, 4))
        time.sleep(4)
        print(f10(1, 2, 3, 4))

    @unittest.skip
    def test_exception_context_manager(self):
        def f1():
            # noinspection PyStatementEffect,PyTypeChecker
            1 + '2'

        def f2():
            f1()

        def f3():
            f2()

        def f4():
            f3()

        def run():
            f4()

        # noinspection PyUnusedLocal
        with ExceptionContextManager() as ec:
            run()

        print('finish')

    @unittest.skip
    def test_timeout(self):
        """
        测试超时装饰器
        :return:
        """

        @timeout(3)
        def f(time_to_be_sleep):
            time.sleep(time_to_be_sleep)
            print('hello wprld')

        f(5)


if __name__ == '__main__':
    pass
    unittest.main()

```

### 代码文件: funboost\utils\develop_log.py
```python
import nb_log
from funboost.funboost_config_deafult import FunboostCommonConfig

#开发时候的调试日志，比print方便通过级别一键屏蔽。
# develop_logger = nb_log.get_logger('fsdf_develop', log_level_int=FunboostCommonConfig.FSDF_DEVELOP_LOG_LEVEL)

```

### 代码文件: funboost\utils\expire_lock.py
```python
'''
基于程序内存的过期锁。
'''

import copy
from threading import Thread, Event, Lock
import time
import typing
import uuid

from funboost.utils import time_util
from nb_log import get_logger

lock_key__event_is_free_map: typing.Dict[str, Event] = {}


class LockStore:
    lock_for_operate_store = Lock()

    lock_key__info_map: typing.Dict[str, typing.Dict] = {}

    _has_start_delete_expire_lock_key_thread = False

    THREAD_DELETE_DAEMON = False
    DELETE_INTERVAL = 0.01

    logger = get_logger('LockStore')

    @classmethod
    def _auto_delete_expire_lock_key_thread(cls):
        while 1:
            with cls.lock_for_operate_store:
                lock_key__info_map_copy = copy.copy(cls.lock_key__info_map)
                for lock_key, info in lock_key__info_map_copy.items():
                    if time.time() - info['set_time'] > info['ex']:
                        cls.lock_key__info_map.pop(lock_key)
                        cls.logger.warning(f'''自动删除占用耗时长的锁 {lock_key} {time_util.DatetimeConverter(info['set_time'])} {info['ex']}''')
                        lock_key__event_is_free_map[lock_key].set()
            time.sleep(cls.DELETE_INTERVAL)

    @classmethod
    def set(cls, lock_key, value, ex):
        set_succ = False
        with cls.lock_for_operate_store:
            if lock_key not in cls.lock_key__info_map:
                cls.lock_key__info_map[lock_key] = {'value': value, 'ex': ex, 'set_time': time.time()}
                set_succ = True

                event_is_free = Event()
                event_is_free.set()
                lock_key__event_is_free_map[lock_key] = event_is_free

            if cls._has_start_delete_expire_lock_key_thread is False:
                cls._has_start_delete_expire_lock_key_thread = True
                Thread(target=cls._auto_delete_expire_lock_key_thread, daemon=cls.THREAD_DELETE_DAEMON).start()

        return set_succ

    @classmethod
    def delete(cls, lock_key, value):
        with cls.lock_for_operate_store:
            if lock_key in cls.lock_key__info_map:
                if cls.lock_key__info_map[lock_key]['value'] == value:
                    cls.lock_key__info_map.pop(lock_key)
                    lock_key__event_is_free_map[lock_key].set()
                    cls.logger.warning(f'expire delete {lock_key}')
                    return True
            return False


class ExpireLockConf:
    def __init__(self, expire_seconds=30, lock_key=None, ):
        self.expire_seconds = expire_seconds
        self.lock_key = lock_key or uuid.uuid4().hex


class ExpireLockContextManager:
    """
    分布式redis锁上下文管理.
    """

    def __init__(self, lock_expire_conf: ExpireLockConf):
        self.expire_seconds = lock_expire_conf.expire_seconds
        self.lock_key = lock_expire_conf.lock_key
        self.identifier = str(uuid.uuid4())
        self.has_aquire_lock = False

    def acquire(self):
        # self._line = sys._getframe().f_back.f_lineno  # noqa 调用此方法的代码的函数
        # self._file_name = sys._getframe(1).f_code.co_filename  # noqa 哪个文件调了用此方法

        while 1:
            # print(self.lock_key)
            ret = LockStore.set(self.lock_key, value=self.identifier, ex=self.expire_seconds)
            self.has_aquire_lock = ret

            if not self.has_aquire_lock:
                lock_key__event_is_free_map[self.lock_key].wait()
                continue
            else:
                lock_key__event_is_free_map[self.lock_key].clear()
                break

    def realese(self):
        return LockStore.delete(self.lock_key, self.identifier)

    def __enter__(self):
        return self.acquire()

    def __bool__(self):
        return self.has_aquire_lock

    def __exit__(self, exc_type, exc_val, exc_tb):
        result = self.realese()


if __name__ == '__main__':

    lockx1_expire = ExpireLockConf(expire_seconds=4, lock_key='test_lock_name_expire', )


    def f(x):
        with ExpireLockContextManager(lockx1_expire):
            print(x, time.time())
            time.sleep(5)


    test_raw_lock = Lock()


    def test_raw_lock_fun(x):
        try:
            test_raw_lock.acquire(timeout=4)
            print(x, time.time())
            time.sleep(5)
            test_raw_lock.release()
        except Exception as e:
            if 'release unlocked lock' in str(e):
                return
            print(e)


    for i in range(100):
        Thread(target=f, args=[i]).start()
        # Thread(target=test_raw_lock_fun, args=[i]).start()

```

### 代码文件: funboost\utils\json_helper.py
```python
import json
import typing
from datetime import datetime as _datetime
from datetime import date as _date

def dict_to_un_strict_json(dictx: dict, indent=4):
    dict_new = {}
    for k, v in dictx.items():
        # only_print_on_main_process(f'{k} :  {v}')
        if isinstance(v, (bool, tuple, dict, float, int)):
            dict_new[k] = v
        else:
            dict_new[k] = str(v)
    return json.dumps(dict_new, ensure_ascii=False, indent=indent)


class _CustomEncoder(json.JSONEncoder):
    """自定义的json解析器，mongodb返回的字典中的时间格式是datatime，json直接解析出错"""

    def default(self, obj):
        if isinstance(obj, _datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, _date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)


# noinspection PyProtectedMember,PyPep8,PyRedundantParentheses
def _dumps(obj, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, cls=_CustomEncoder, indent=None, separators=None,
           default=None, sort_keys=False, **kw):
    # 全局patch ensure_ascii = False 会引起极少数库不兼容。
    if (not skipkeys and ensure_ascii and check_circular and allow_nan and cls is None and indent is None and separators is None and default is None and not sort_keys and not kw):
        return json._default_encoder.encode(obj)
    if cls is None:
        cls = json.JSONEncoder
    return cls(
        skipkeys=skipkeys, ensure_ascii=ensure_ascii,
        check_circular=check_circular, allow_nan=allow_nan, indent=indent,
        separators=separators, default=default, sort_keys=sort_keys, ).encode(obj)



def monkey_patch_json():
    json.dumps = _dumps


# class JsonUtils:
#     @staticmethod
#     def to_dict(obj:typing.Union[str,dict,list]):
#         if isinstance(obj,str):
#             return json.loads(obj)
#         else:
#             return obj
#
#     @staticmethod
#     def to_json_str(obj:typing.Union[str,dict,list]):
#         if isinstance(obj,str):
#             return obj
#         else:
#             return json.dumps(obj,ensure_ascii=False)

if __name__ == '__main__':
    pass

```

### 代码文件: funboost\utils\mongo_util.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/9/17 0017 15:26
import functools
import os
import pymongo
from pymongo.collection import Collection
from funboost.utils import decorators


@functools.lru_cache()
def _get_mongo_url():
    from funboost.funboost_config_deafult import BrokerConnConfig
    return BrokerConnConfig.MONGO_CONNECT_URL

class MongoMixin0000:
    """
    mixin类被继承，也可以直接实例化。


    这种在 linux运行 + pymongo 版本4.xx  + 多进程子进程中操作会报错。
    /usr/local/lib/python3.8/dist-packages/pymongo/topology.py:172: UserWarning: MongoClient opened before fork. Create MongoClient only after forking.
    See PyMongo's documentation for details: https://pymongo.readthedocs.io/en/stable/faq.html#is-pymongo-fork-safe
    """

    @property
    @decorators.cached_method_result
    def mongo_client(self):
        return pymongo.MongoClient(_get_mongo_url(), connect=False)  # connect等于False原因见注释

    @property
    @decorators.cached_method_result
    def mongo_db_task_status(self):
        return self.mongo_client.get_database('task_status')


class MongoMixin:
    """
    mixin类被继承，也可以直接实例化。

    这个是修改后的，当使用f.multi_process_connsume() + linux +  保存结果到mongo + pymongo.0.2 时候不再报错了。

    在linux上 即使写 connect=False，如果在主进程操作了collection，那么就破坏了 connect=False，在子进程中继续操作这个collection全局变量就会报错。
    设计了多进程+fork 每次都 get_mongo_collection() 是最保险的
    """
    processid__client_map = {}
    processid__db_map = {}
    processid__col_map = {}

    @property
    def mongo_client(self) -> pymongo.MongoClient:
        pid = os.getpid()
        key = pid
        if key not in MongoMixin.processid__client_map:
            MongoMixin.processid__client_map[key] = pymongo.MongoClient(_get_mongo_url(),
                                                                        connect=False, maxIdleTimeMS=60 * 1000, minPoolSize=3, maxPoolSize=20)
        return MongoMixin.processid__client_map[key]

    @property
    def mongo_db_task_status(self):
        pid = os.getpid()
        key = (pid, 'task_status')
        if key not in MongoMixin.processid__db_map:
            MongoMixin.processid__db_map[key] = self.mongo_client.get_database('task_status')
        return MongoMixin.processid__db_map[key]

    def get_mongo_collection(self, database_name, colleciton_name) -> pymongo.collection.Collection:
        pid = os.getpid()
        key = (pid, database_name, colleciton_name)
        if key not in MongoMixin.processid__col_map:
            MongoMixin.processid__col_map[key] = self.mongo_client.get_database(database_name).get_collection(colleciton_name)
        return MongoMixin.processid__col_map[key]


if __name__ == '__main__':
    print(MongoMixin().get_mongo_collection('db2', 'col2'))
    print(MongoMixin().get_mongo_collection('db2', 'col3'))

```

### 代码文件: funboost\utils\monkey_color_log.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/1 0001 17:54
"""
如果老项目没用使用Logmanager,可以打此猴子补丁，自动使项目中的任何日志变彩色和可跳转。

"""

import sys
import os
import logging


class ColorHandler(logging.Handler):
    """
    A handler class which writes logging records, appropriately formatted,
    to a stream. Note that this class does not close the stream, as
    sys.stdout or sys.stderr may be used.
    """
    os_name = os.name
    terminator = '\n'
    bule = 96 if os_name == 'nt' else 36
    yellow = 93 if os_name == 'nt' else 33

    def __init__(self, stream=None, ):
        """
        Initialize the handler.

        If stream is not specified, sys.stderr is used.
        """
        logging.Handler.__init__(self)
        self.formatter = logging.Formatter(
            '%(asctime)s - %(name)s - "%(pathname)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(message)s',
            "%Y-%m-%d %H:%M:%S")
        if stream is None:
            stream = sys.stdout  # stderr无彩。
        self.stream = stream
        self._display_method = 7 if self.os_name == 'posix' else 0

    def setFormatter(self, fmt):
        pass  # 禁止私自设置日志模板。固定使用可跳转的模板。

    def flush(self):
        """
        Flushes the stream.
        """
        self.acquire()
        try:
            if self.stream and hasattr(self.stream, "flush"):
                self.stream.flush()
        finally:
            self.release()

    def emit0(self, record):
        """
        前后彩色不分离的方式
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.
        """
        # noinspection PyBroadException
        try:
            msg = self.format(record)
            stream = self.stream
            if record.levelno == 10:
                # msg_color = ('\033[0;32m%s\033[0m' % msg)  # 绿色
                msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, 32, msg))  # 绿色
            elif record.levelno == 20:
                msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, self.bule, msg))  # 青蓝色 36    96
            elif record.levelno == 30:
                msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, self.yellow, msg))
            elif record.levelno == 40:
                msg_color = ('\033[%s;35m%s\033[0m' % (self._display_method, msg))  # 紫红色
            elif record.levelno == 50:
                msg_color = ('\033[%s;31m%s\033[0m' % (self._display_method, msg))  # 血红色
            else:
                msg_color = msg
            # print(msg_color,'***************')
            stream.write(msg_color)
            stream.write(self.terminator)
            self.flush()
        except BaseException :
            self.handleError(record)

    def emit(self, record):
        """
        前后彩色分离的方式。
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.
        """
        # noinspection PyBroadException
        try:
            msg = self.format(record)
            stream = self.stream
            msg1, msg2 = self.__spilt_msg(record.levelno, msg)
            if record.levelno == 10:
                # msg_color = ('\033[0;32m%s\033[0m' % msg)  # 绿色
                msg_color = f'\033[0;32m{msg1}\033[0m \033[7;32m{msg2}\033[0m'  # 绿色
            elif record.levelno == 20:
                # msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, self.bule, msg))  # 青蓝色 36    96
                msg_color = f'\033[0;{self.bule}m{msg1}\033[0m \033[7;{self.bule}m{msg2}\033[0m'
            elif record.levelno == 30:
                # msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, self.yellow, msg))
                msg_color = f'\033[0;{self.yellow}m{msg1}\033[0m \033[7;{self.yellow}m{msg2}\033[0m'
            elif record.levelno == 40:
                # msg_color = ('\033[%s;35m%s\033[0m' % (self._display_method, msg))  # 紫红色
                msg_color = f'\033[0;35m{msg1}\033[0m \033[7;35m{msg2}\033[0m'
            elif record.levelno == 50:
                # msg_color = ('\033[%s;31m%s\033[0m' % (self._display_method, msg))  # 血红色
                msg_color = f'\033[0;31m{msg1}\033[0m \033[7;31m{msg2}\033[0m'
            else:
                msg_color = msg
            # print(msg_color,'***************')
            stream.write(msg_color)
            stream.write(self.terminator)
            self.flush()
        except BaseException :
            self.handleError(record)

    @staticmethod
    def __spilt_msg(log_level, msg: str):
        split_text = '- 级别 -'
        if log_level == 10:
            split_text = '- DEBUG -'
        elif log_level == 20:
            split_text = '- INFO -'
        elif log_level == 30:
            split_text = '- WARNING -'
        elif log_level == 40:
            split_text = '- ERROR -'
        elif log_level == 50:
            split_text = '- CRITICAL -'
        msg_split = msg.split(split_text, maxsplit=1)
        return msg_split[0] + split_text, msg_split[-1]

    def __repr__(self):
        level = logging.getLevelName(self.level)
        name = getattr(self.stream, 'name', '')
        if name:
            name += ' '
        return '<%s %s(%s)>' % (self.__class__.__name__, name, level)


logging.StreamHandler = ColorHandler  # REMIND 这一行就是打猴子补丁，可以尝试注释掉这一行对比。
"""
这里就是打猴子补丁,要在脚本最开始打猴子补丁，越早越好。
否则原来脚本中使用from logging import StreamHandler变为不了彩色的handler。
只有import logging，logging.StreamHandler的这种用法才会变彩。所以猴子补丁要趁早打。
"""


def my_func():
    """
    模拟常规使用控制台StreamHandler日志的方式。自动变彩。
    :return:
    """
    from logging import StreamHandler
    logger = logging.getLogger('abc')
    print(logger.handlers)
    print(StreamHandler().formatter)
    logger.addHandler(StreamHandler())
    logger.setLevel(10)
    print(logger.handlers)
    for _ in range(100):
        logger.debug('一个debug级别的日志' * 5)
        logger.info('一个info级别的日志' * 5)
        logger.warning('一个warning级别的日志' * 5)
        logger.error('一个error级别的日志' * 5)
        logger.critical('一个critical级别的日志' * 5)


if __name__ == '__main__':
    my_func()

```

### 代码文件: funboost\utils\monkey_patches.py
```python


import collections.abc

setattr(collections,'MutableMapping',collections.abc.MutableMapping)





'''

Traceback (most recent call last):
  File "D:\codes\funboost\funboost\concurrent_pool\async_pool_executor0223.py", line 267, in <module>
    test_async_pool_executor()
  File "D:\codes\funboost\funboost\concurrent_pool\async_pool_executor0223.py", line 225, in test_async_pool_executor
    from funboost.concurrent_pool import CustomThreadPoolExecutor as ThreadPoolExecutor
  File "D:\codes\funboost\funboost\__init__.py", line 8, in <module>
    from funboost.set_frame_config import patch_frame_config, show_frame_config
  File "D:\codes\funboost\funboost\set_frame_config.py", line 167, in <module>
    use_config_form_funboost_config_module()
  File "D:\codes\funboost\funboost\set_frame_config.py", line 115, in use_config_form_funboost_config_module
    m = importlib.import_module('funboost_config')
  File "D:\ProgramData\Miniconda3\envs\py310\lib\importlib\__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
  File "D:\codes\funboost\funboost_config.py", line 8, in <module>
    from funboost import concurrent_pool
  File "D:\codes\funboost\funboost\concurrent_pool\__init__.py", line 14, in <module>
    from .custom_evenlet_pool_executor import CustomEventletPoolExecutor
  File "D:\codes\funboost\funboost\concurrent_pool\custom_evenlet_pool_executor.py", line 7, in <module>
    from eventlet import greenpool, monkey_patch, patcher, Timeout
  File "D:\ProgramData\Miniconda3\envs\py310\lib\site-packages\eventlet\__init__.py", line 17, in <module>
    from eventlet import convenience
  File "D:\ProgramData\Miniconda3\envs\py310\lib\site-packages\eventlet\convenience.py", line 7, in <module>
    from eventlet.green import socket
  File "D:\ProgramData\Miniconda3\envs\py310\lib\site-packages\eventlet\green\socket.py", line 21, in <module>
    from eventlet.support import greendns
  File "D:\ProgramData\Miniconda3\envs\py310\lib\site-packages\eventlet\support\greendns.py", line 79, in <module>
    setattr(dns, pkg, import_patched('dns.' + pkg))
  File "D:\ProgramData\Miniconda3\envs\py310\lib\site-packages\eventlet\support\greendns.py", line 61, in import_patched
    return patcher.import_patched(module_name, **modules)
  File "D:\ProgramData\Miniconda3\envs\py310\lib\site-packages\eventlet\patcher.py", line 132, in import_patched
    return inject(
  File "D:\ProgramData\Miniconda3\envs\py310\lib\site-packages\eventlet\patcher.py", line 109, in inject
    module = __import__(module_name, {}, {}, module_name.split('.')[:-1])
  File "D:\ProgramData\Miniconda3\envs\py310\lib\site-packages\dns\namedict.py", line 35, in <module>
    class NameDict(collections.MutableMapping):
AttributeError: module 'collections' has no attribute 'MutableMapping'
'''

```

### 代码文件: funboost\utils\mqtt_util.py
```python
import urllib3
import json
import nb_log
import decorator_libs

# https://www.cnblogs.com/YrRoom/p/14054282.html

"""
-p 18083 服务器启动端口
-p 1882 TCP端口
-p 8083 WS端口
-p 8084 WSS端口
-p 8883 SSL端口
"""

"""
非常适合 前端订阅唯一uuid的topic 然后表单中带上这个topic名字请求python接口 -> 接口中发布任务到rabbitmq或redis消息队列 ->
后台消费进程执行任务消费,并将结果发布到mqtt的那个唯一uuid的topic -> mqtt 把结果推送到前端。

使用ajax轮训或者后台导入websocket相关的包来做和前端的长耗时任务的交互都是伪命题，没有mqtt好。
"""


class MqttHttpHelper(nb_log.LoggerMixin, nb_log.LoggerLevelSetterMixin):

    def __init__(self, mqtt_publish_url='http://127.0.0.1:18083/api/v2/mqtt/publish', user='admin', passwd='public', display_full_msg=False):
        """
        :param mqtt_publish_url: mqtt的http接口，这是mqtt中间件自带的，不是重新自己实现的接口。不需要导入paho.mqtt.client,requeests urllib3即可。
        :param display_full_msg: 时候打印发布的任务
        """
        self._mqtt_publish_url = mqtt_publish_url
        self.http = urllib3.PoolManager()
        self._headers = urllib3.util.make_headers(basic_auth=f'{user}:{passwd}')
        self._headers['Content-Type'] = 'application/json'
        self._display_full_msg = display_full_msg

    # @decorator_libs.tomorrow_threads(10)
    def pub_message(self, topic, msg):
        msg = json.dumps(msg) if isinstance(msg, (dict, list)) else msg
        if not isinstance(msg, str):
            raise Exception('推送的不是字符串')
        post_data = {"qos": 1, "retain": False, "topic": topic, "payload": msg}
        try:  # UnicodeEncodeError: 'latin-1' codec can't encode character '\u6211' in position 145: Body ('我') is not valid Latin-1. Use body.encode('utf-8') if you want to send it encoded in UTF-8.
            resp_dict = json.loads(self.http.request('post', self._mqtt_publish_url, body=json.dumps(post_data),
                                                     headers=self._headers).data)
        except UnicodeEncodeError as e:
            self.logger.warning(e)
            post_data['payload'] = post_data['payload'].encode().decode('latin-1')
            resp_dict = json.loads(self.http.request('post', self._mqtt_publish_url, body=json.dumps(post_data),
                                                     headers=self._headers).data)
        if resp_dict['code'] == 0:
            self.logger.debug(f' 推送mqtt成功 ，主题名称是:{topic} ，长度是 {len(msg)}， 消息是 {msg if self._display_full_msg else msg[:200]} ')
        else:
            self.logger.debug(f' 推送mqtt失败,主题名称是:{topic},mqtt返回响应是 {json.dumps(resp_dict)} ， 消息是 {msg if self._display_full_msg else msg[:200]}')


if __name__ == '__main__':
    with decorator_libs.TimerContextManager():
        mp = MqttHttpHelper('http://192.168.6.130:18083/api/v2/mqtt/publish')
        for i in range(2000):
            mp.pub_message('/topic_test_uuid123456', 'msg_test3')

```

### 代码文件: funboost\utils\paramiko_util.py
```python
#coding=utf-8
import os
import re
import sys
import time
from nb_log import LoggerMixin, LoggerLevelSetterMixin
import paramiko


class ParamikoFolderUploader(LoggerMixin, LoggerLevelSetterMixin):
    """
    paramoki 实现的文件夹上传
    """

    def __init__(self, host, port, user, password, local_dir: str, remote_dir: str,
                 path_pattern_exluded_tuple=('/.git/', '/.idea/', '/dist/', '/build/'),
                 file_suffix_tuple_exluded=('.pyc', '.log', '.gz'),
                 only_upload_within_the_last_modify_time=3650 * 24 * 60 * 60,
                 file_volume_limit=1000 * 1000, sftp_log_level=20, pkey_file_path=None):
        """

        :param host:
        :param port:
        :param user:
        :param password:
        :param local_dir:
        :param remote_dir:
        :param path_pattern_exluded_tuple: 命中了这些正则的直接排除
        :param file_suffix_tuple_exluded: 这些结尾的文件排除
        :param only_upload_within_the_last_modify_time: 仅仅上传最近多少天修改的文件
        :param file_volume_limit: 大于这个体积的不上传，单位b。
        :param sftp_log_level:日志级别
        :param pkey_file_path: 私钥文件路径，如果设置了这个，那么使用私钥登录。
        """
        self._host = host
        self._port = port
        self._user = user
        self._password = password

        self._local_dir = str(local_dir).replace('\\', '/')
        if not self._local_dir.endswith('/'):
            self._local_dir += '/'
        self._remote_dir = str(remote_dir).replace('\\', '/')
        if not self._remote_dir.endswith('/'):
            self._remote_dir += '/'
        self._path_pattern_exluded_tuple = path_pattern_exluded_tuple
        self._file_suffix_tuple_exluded = file_suffix_tuple_exluded
        self._only_upload_within_the_last_modify_time = only_upload_within_the_last_modify_time
        self._file_volume_limit = file_volume_limit

        t = paramiko.Transport((host, port))
        if pkey_file_path is not None and os.path.exists(pkey_file_path):
            pkey = paramiko.RSAKey.from_private_key_file(pkey_file_path)
            t.connect(username=user, pkey=pkey)
        else:
            t.connect(username=user, password=password)
        self.sftp = paramiko.SFTPClient.from_transport(t)

        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=user, password=password, compress=True)
        self.ssh = ssh

        self.set_log_level(sftp_log_level)

    def _judge_need_filter_a_file(self, filename: str):
        ext = filename.split('.')[-1]
        if '.' + ext in self._file_suffix_tuple_exluded:
            return True
        for path_pattern_exluded in self._path_pattern_exluded_tuple:
            # print(path_pattern_exluded,filename)
            if re.search(path_pattern_exluded, filename):
                return True
        file_st_mtime = os.stat(filename).st_mtime
        volume = os.path.getsize(filename)
        if time.time() - file_st_mtime > self._only_upload_within_the_last_modify_time:
            return True
        if volume > self._file_volume_limit:
            return True
        return False

    def _make_dir(self, dirc, final_dir):
        """
        sftp.mkdir 不能直接越级创建深层级文件夹。
        :param dirc:
        :param final_dir:
        :return:
        """
        # print(dir,final_dir)
        try:
            self.sftp.mkdir(dirc)
            if dirc != final_dir:
                self._make_dir(final_dir, final_dir)
        except (FileNotFoundError,):
            parrent_dir = os.path.split(dirc)[0]
            self._make_dir(parrent_dir, final_dir)

    def upload(self):
        for parent, dirnames, filenames in os.walk(self._local_dir):
            for filename in filenames:
                file_full_name = os.path.join(parent, filename).replace('\\', '/')
                if not self._judge_need_filter_a_file(file_full_name):
                    remote_full_file_name = re.sub(f'^{self._local_dir}', self._remote_dir, file_full_name)
                    try:
                        self.logger.debug(f'本地：{file_full_name}   远程： {remote_full_file_name}')
                        self.sftp.put(file_full_name, remote_full_file_name)
                    except (FileNotFoundError,) as e:
                        # self.logger.warning(remote_full_file_name)
                        self._make_dir(os.path.split(remote_full_file_name)[0], os.path.split(remote_full_file_name)[0])
                        self.sftp.put(file_full_name, remote_full_file_name)
                else:
                    if '/.git' not in file_full_name and '.pyc' not in file_full_name:
                        self.logger.debug(f'根据过滤规则，不上传这个文件 {file_full_name}')


if __name__ == '__main__':
    uploader = ParamikoFolderUploader('192.168.6.133', 22, 'ydf', '372148', sys.path[1], '/home/ydf/codes/dssf/')
    uploader.upload()

```

### 代码文件: funboost\utils\rabbitmq_factory.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 11:51
import pikav0 as pika
import rabbitpy
from pikav0.adapters.blocking_connection import BlockingChannel

from funboost.funboost_config_deafult import BrokerConnConfig


class RabbitmqClientRabbitPy:
    """
    使用rabbitpy包。
    """

    # noinspection PyUnusedLocal
    def __init__(self, username, password, host, port, virtual_host, heartbeat=0):
        rabbit_url = f'amqp://{username}:{password}@{host}:{port}/{virtual_host}?heartbeat={heartbeat}'
        self.connection = rabbitpy.Connection(rabbit_url)

    def creat_a_channel(self) -> rabbitpy.AMQP:
        return rabbitpy.AMQP(self.connection.channel())  # 使用适配器，使rabbitpy包的公有方法几乎接近pika包的channel的方法。


class RabbitmqClientPika:
    """
    使用pika包,多线程不安全的包。
    """

    def __init__(self, username, password, host, port, virtual_host, heartbeat=0):
        """
        parameters = pika.URLParameters('amqp://guest:guest@localhost:5672/%2F')

        connection = pika.SelectConnection(parameters=parameters,
                                  on_open_callback=on_open)
        :param username:
        :param password:
        :param host:
        :param port:
        :param virtual_host:
        :param heartbeat:
        """
        credentials = pika.PlainCredentials(username, password)
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host, port, virtual_host, credentials, heartbeat=heartbeat))
        # self.connection = pika.SelectConnection(pika.ConnectionParameters(
        #     host, port, virtual_host, credentials, heartbeat=heartbeat))

    def creat_a_channel(self) -> BlockingChannel:
        return self.connection.channel()


class RabbitMqFactory:
    def __init__(self, heartbeat=600 , is_use_rabbitpy=0):
        """
        :param heartbeat:
        :param is_use_rabbitpy: 为0使用pika，多线程不安全。为1使用rabbitpy，多线程安全的包。
        """
        if is_use_rabbitpy:
            self.rabbit_client = RabbitmqClientRabbitPy(BrokerConnConfig.RABBITMQ_USER, BrokerConnConfig.RABBITMQ_PASS,
                                                        BrokerConnConfig.RABBITMQ_HOST, BrokerConnConfig.RABBITMQ_PORT,
                                                        BrokerConnConfig.RABBITMQ_VIRTUAL_HOST, heartbeat)
        else:
            self.rabbit_client = RabbitmqClientPika(BrokerConnConfig.RABBITMQ_USER, BrokerConnConfig.RABBITMQ_PASS,
                                                    BrokerConnConfig.RABBITMQ_HOST, BrokerConnConfig.RABBITMQ_PORT,
                                                    BrokerConnConfig.RABBITMQ_VIRTUAL_HOST, heartbeat)

    def get_rabbit_cleint(self):
        return self.rabbit_client

```

### 代码文件: funboost\utils\README.md
```python
# 这里的utils功能是从已有项目复制出来的，大部分没用到，不要管这里。

# 最主要的是要看base_consumer.py,框架90%逻辑流程在 AbstractConsumer
```

### 代码文件: funboost\utils\redis_manager.py
```python
# coding=utf8

import copy
# import redis2 as redis
# import redis3
import redis5
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.utils import decorators

# from aioredis.client import Redis as AioRedis



def get_redis_conn_kwargs():
    return {'host': BrokerConnConfig.REDIS_HOST, 'port': BrokerConnConfig.REDIS_PORT,
            'username': BrokerConnConfig.REDIS_USERNAME,'ssl' : BrokerConnConfig.REDIS_SSL,
            'password': BrokerConnConfig.REDIS_PASSWORD, 'db': BrokerConnConfig.REDIS_DB}


def _get_redis_conn_kwargs_by_db(db):
    conn_kwargs = copy.copy(get_redis_conn_kwargs())
    conn_kwargs['db'] = db
    return conn_kwargs


class RedisManager(object):
    _redis_db__conn_map = {}

    def __init__(self, host='127.0.0.1', port=6379, db=0, username='', password='',ssl=False):
        self._key = (host, port, db, username, password,ssl)
        if self._key not in self.__class__._redis_db__conn_map:
            self.__class__._redis_db__conn_map[self._key] = redis5.Redis(host=host, port=port, db=db, username=username,
                                                                         password=password, max_connections=1000,
                                                                         ssl=ssl,
                                                                         decode_responses=True)
        self.redis = self.__class__._redis_db__conn_map[self._key]

    def get_redis(self) -> redis5.Redis:
        """
        :rtype :redis5.Redis
        """
        return self.redis


# class AioRedisManager(object):
#     _redis_db__conn_map = {}
#
#     def __init__(self, host='127.0.0.1', port=6379, db=0, username='', password=''):
#         self._key = (host, port, db, username, password,)
#         if self._key not in self.__class__._redis_db__conn_map:
#             self.__class__._redis_db__conn_map[self._key] = AioRedis(host=host, port=port, db=db, username=username,
#                                                                      password=password, max_connections=1000, decode_responses=True)
#         self.redis = self.__class__._redis_db__conn_map[self._key]
#
#     def get_redis(self) -> AioRedis:
#         """
#         :rtype :redis5.Redis
#         """
#         return self.redis


# noinspection PyArgumentEqualDefault
class RedisMixin(object):
    """
    可以被作为万能mixin能被继承，也可以单独实例化使用。
    """

    def redis_db_n(self, db):
        return RedisManager(**_get_redis_conn_kwargs_by_db(db)).get_redis()

    @property
    @decorators.cached_method_result
    def redis_db_frame(self):
        return RedisManager(**get_redis_conn_kwargs()).get_redis()

    @property
    @decorators.cached_method_result
    def redis_db_filter_and_rpc_result(self):
        return RedisManager(**_get_redis_conn_kwargs_by_db(BrokerConnConfig.REDIS_DB_FILTER_AND_RPC_RESULT)).get_redis()

    def timestamp(self):
        """ 如果是多台机器做分布式控频 乃至确认消费，每台机器取自己的时间，如果各机器的时间戳不一致会发生问题，改成统一使用从redis服务端获取时间，单位是时间戳秒。"""
        time_tuple = self.redis_db_frame.time()
        # print(time_tuple)
        return time_tuple[0] + time_tuple[1] / 1000000


class AioRedisMixin(object):
    @property
    @decorators.cached_method_result
    def aioredis_db_filter_and_rpc_result(self):
        # aioredis 包已经不再更新了,推荐使用redis包的asyncio中的类
        # return AioRedisManager(**_get_redis_conn_kwargs_by_db(BrokerConnConfig.REDIS_DB_FILTER_AND_RPC_RESULT)).get_redis()
        return redis5.asyncio.Redis(**_get_redis_conn_kwargs_by_db(BrokerConnConfig.REDIS_DB_FILTER_AND_RPC_RESULT),decode_responses=True)

```

### 代码文件: funboost\utils\redis_manager_old.py
```python
# # coding=utf8
# import redis2 as redis
# import redis3
# # from funboost.funboost_config_deafult import BrokerConnConfig
# from funboost.utils import decorators
#
# from aioredis.client import Redis as AioRedis
#
#
# class RedisManager(object):
#     _pool_dict = {}
#
#     def __init__(self, host='127.0.0.1', port=6379, db=0, username='',password='123456'):
#         if (host, port, db, password) not in self.__class__._pool_dict:
#             # print ('创建一个连接池')
#             self.__class__._pool_dict[(host, port, db, password)] = redis.ConnectionPool(host=host, port=port, db=db,username=username,
#                                                                                          password=password,max_connections=100)
#         self._r = redis.Redis(connection_pool=self._pool_dict[(host, port, db, password)])
#         self._ping()
#
#     def get_redis(self):
#         """
#         :rtype :redis.Redis
#         """
#         return self._r
#
#     def _ping(self):
#         try:
#             self._r.ping()
#         except BaseException as e:
#             raise e
#
#
# # noinspection PyArgumentEqualDefault
# class RedisMixin(object):
#     """
#     可以被作为万能mixin能被继承，也可以单独实例化使用。
#     """
#
#     @property
#     @decorators.cached_method_result
#     def redis_db0(self):
#         return RedisManager(host=funboost_config_deafult.REDIS_HOST, port=funboost_config_deafult.REDIS_PORT,
#                             password=funboost_config_deafult.REDIS_PASSWORD, db=0,username=funboost_config_deafult.REDIS_USERNAME).get_redis()
#
#     @property
#     @decorators.cached_method_result
#     def redis_db8(self):
#         return RedisManager(host=funboost_config_deafult.REDIS_HOST, port=funboost_config_deafult.REDIS_PORT,
#                             password=funboost_config_deafult.REDIS_PASSWORD, db=8,username=funboost_config_deafult.REDIS_USERNAME).get_redis()
#
#     @property
#     @decorators.cached_method_result
#     def redis_db7(self):
#         return RedisManager(host=funboost_config_deafult.REDIS_HOST, port=funboost_config_deafult.REDIS_PORT,
#                             password=funboost_config_deafult.REDIS_PASSWORD, db=7,username=funboost_config_deafult.REDIS_USERNAME).get_redis()
#
#     @property
#     @decorators.cached_method_result
#     def redis_db6(self):
#         return RedisManager(host=funboost_config_deafult.REDIS_HOST, port=funboost_config_deafult.REDIS_PORT,
#                             password=funboost_config_deafult.REDIS_PASSWORD, db=6,username=funboost_config_deafult.REDIS_USERNAME).get_redis()
#
#     @property
#     @decorators.cached_method_result
#     def redis_db_frame(self):
#         return RedisManager(host=funboost_config_deafult.REDIS_HOST, port=funboost_config_deafult.REDIS_PORT,
#                             password=funboost_config_deafult.REDIS_PASSWORD, db=funboost_config_deafult.REDIS_DB,
#                             username=funboost_config_deafult.REDIS_USERNAME).get_redis()
#
#     @property
#     @decorators.cached_method_result
#     def redis_db_frame_version3(self):
#         ''' redis 3和2 入参和返回差别很大，都要使用'''
#         return redis3.Redis(host=funboost_config_deafult.REDIS_HOST, port=funboost_config_deafult.REDIS_PORT,
#                             password=funboost_config_deafult.REDIS_PASSWORD, db=funboost_config_deafult.REDIS_DB,
#                             username=funboost_config_deafult.REDIS_USERNAME,decode_responses=True)
#
#     @property
#     @decorators.cached_method_result
#     def redis_db_filter_and_rpc_result(self):
#         return RedisManager(host=funboost_config_deafult.REDIS_HOST, port=funboost_config_deafult.REDIS_PORT,
#                             password=funboost_config_deafult.REDIS_PASSWORD, db=funboost_config_deafult.REDIS_DB_FILTER_AND_RPC_RESULT,
#                             username=funboost_config_deafult.REDIS_USERNAME).get_redis()
#
#     @property
#     @decorators.cached_method_result
#     def redis_db_filter_and_rpc_result_version3(self):
#         return redis3.Redis(host=funboost_config_deafult.REDIS_HOST, port=funboost_config_deafult.REDIS_PORT,
#                             password=funboost_config_deafult.REDIS_PASSWORD, db=funboost_config_deafult.REDIS_DB_FILTER_AND_RPC_RESULT,
#                             username=funboost_config_deafult.REDIS_USERNAME,
#                             decode_responses=True)
#
#     def timestamp(self):
#         """ 如果是多台机器做分布式控频 乃至确认消费，每台机器取自己的时间，如果各机器的时间戳不一致会发生问题，改成统一使用从redis服务端获取时间，单位是时间戳秒。"""
#         time_tuple = self.redis_db_frame.time()
#         # print(time_tuple)
#         return time_tuple[0] + time_tuple[1] / 1000000
#
#
# class AioRedisMixin(object):
#     @property
#     @decorators.cached_method_result
#     def aioredis_db_filter_and_rpc_result(self):
#         return AioRedis(host=funboost_config_deafult.REDIS_HOST, port=funboost_config_deafult.REDIS_PORT,
#                         password=funboost_config_deafult.REDIS_PASSWORD, db=funboost_config_deafult.REDIS_DB_FILTER_AND_RPC_RESULT,
#                         username=funboost_config_deafult.REDIS_USERNAME,
#                         decode_responses=True)

```

### 代码文件: funboost\utils\resource_monitoring.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/9/18 0018 10:29
import datetime
import json
import socket
import sys
import threading
import time

from funboost.core.lazy_impoter import PsutilImporter
from funboost.utils import LoggerLevelSetterMixin, LoggerMixin, decorators
from funboost.utils.mongo_util import MongoMixin

"""
# psutil.virtual_memory()
svmem = namedtuple(
    'svmem', ['total', 'available', 'percent', 'used', 'free',
              'active', 'inactive', 'buffers', 'cached', 'shared', 'slab'])
# psutil.disk_io_counters()
sdiskio = namedtuple(
    'sdiskio', ['read_count', 'write_count',
                'read_bytes', 'write_bytes',
                'read_time', 'write_time',
                'read_merged_count', 'write_merged_count',
                'busy_time'])
# psutil.Process().open_files()
popenfile = namedtuple(
    'popenfile', ['path', 'fd', 'position', 'mode', 'flags'])
# psutil.Process().memory_info()
pmem = namedtuple('pmem', 'rss vms shared text lib data dirty')
# psutil.Process().memory_full_info()
pfullmem = namedtuple('pfullmem', pmem._fields + ('uss', 'pss', 'swap'))
# psutil.Process().memory_maps(grouped=True)
pmmap_grouped = namedtuple(
    'pmmap_grouped',
    ['path', 'rss', 'size', 'pss', 'shared_clean', 'shared_dirty',
     'private_clean', 'private_dirty', 'referenced', 'anonymous', 'swap'])
# psutil.Process().memory_maps(grouped=False)
pmmap_ext = namedtuple(
    'pmmap_ext', 'addr perms ' + ' '.join(pmmap_grouped._fields))
# psutil.Process.io_counters()
pio = namedtuple('pio', ['read_count', 'write_count',
                         'read_bytes', 'write_bytes',
                         'read_chars', 'write_chars'])


p = psutil.Process()
print(p)
print(p.memory_info()[0])

print(p.cpu_percent(interval=1))
print(p.cpu_percent(interval=1))

print(psutil.cpu_percent(1,percpu=True))
print(psutil.virtual_memory())

"""


class ResourceMonitor(LoggerMixin, LoggerLevelSetterMixin, MongoMixin):
    # ResourceMonitor(is_save_info_to_mongo=True).set_log_level(20).start_build_info_loop_on_daemon_thread(60)
    cpu_count = PsutilImporter().psutil.cpu_count()
    host_name = socket.gethostname()

    def __init__(self, process=PsutilImporter().psutil.Process(), is_save_info_to_mongo=False, mongo_col='default'):
        self.process = process
        self.logger.setLevel(20)
        self.all_info = {}
        self._is_save_info_to_mongo = is_save_info_to_mongo
        self._mongo_col = mongo_col

    @staticmethod
    def divide_1m(value):
        return round(value / (1024 * 1024), 2)

    def get_current_process_memory(self) -> float:
        result = self.process.memory_info()
        self.logger.debug(result)
        return self.divide_1m(result[0])

    def get_current_process_cpu(self):
        result = self.process.cpu_percent(interval=1)
        self.logger.debug(result)
        return result

    def get_os_cpu_percpu(self):
        result = PsutilImporter().psutil.cpu_percent(1, percpu=True)
        self.logger.debug(result)
        return result

    def get_os_cpu_totalcpu(self):
        result = round(PsutilImporter().psutil.cpu_percent(1, percpu=False) * self.cpu_count, 2)
        self.logger.debug(result)
        return result

    def get_os_cpu_avaragecpu(self):
        result = PsutilImporter().psutil.cpu_percent(1, percpu=False)
        self.logger.debug(result)
        return result

    def get_os_virtual_memory(self) -> dict:
        memory_tuple = PsutilImporter().psutil.virtual_memory()
        self.logger.debug(memory_tuple)
        return {
            'total': self.divide_1m(memory_tuple[0]),
            'available': self.divide_1m(memory_tuple[1]),
            'used': self.divide_1m(memory_tuple[3]),
        }

    def get_os_net_info(self):
        result1 = PsutilImporter().psutil.net_io_counters(pernic=False)
        time.sleep(1)
        result2 = PsutilImporter().psutil.net_io_counters(pernic=False)
        speed_dict = dict()
        speed_dict['up_speed'] = self.divide_1m(result2[0] - result1[0])
        speed_dict['down_speed'] = self.divide_1m(result2[1] - result1[1])
        speed_dict['packet_sent_speed'] = result2[2] - result1[2]
        speed_dict['packet_recv_speed'] = result2[3] - result1[3]
        self.logger.debug(result1)
        return speed_dict

    def get_all_info(self):
        self.all_info = {
            'host_name': self.host_name,
            'process_id': self.process.pid,
            'process_name': self.process.name(),
            'process_script': sys.argv[0],
            'memory': self.get_current_process_memory(),
            'cpu': self.get_current_process_cpu(),
            'os_memory': self.get_os_virtual_memory(),
            'os_cpu': {'cpu_count': self.cpu_count, 'total_cpu': self.get_os_cpu_totalcpu(), 'avarage_cpu': self.get_os_cpu_avaragecpu()},
            'net_info': self.get_os_net_info()
        }
        # nb_print(json.dumps(self.all_info,indent=4))
        self.logger.info(json.dumps(self.all_info, indent=4))
        if self._is_save_info_to_mongo:
            self.all_info.update({'update_time': datetime.datetime.now()})
            self.mongo_client.get_database('process_info').get_collection(self._mongo_col).insert_one(self.all_info)
        return self.all_info

    def start_build_info_loop(self, interval=60, ):
        decorators.keep_circulating(interval)(self.get_all_info)()

    def start_build_info_loop_on_daemon_thread(self, interval=60, ):
        threading.Thread(target=self.start_build_info_loop, args=(interval,), daemon=True).start()

```

### 代码文件: funboost\utils\restart_python.py
```python
import datetime
import os
import sys
import threading
import time

import nb_log

# print(sys.path)

logger = nb_log.get_logger('restart_program')

""" 这个只能在 win cmd 或者 linux下测试重启功能，
   不能在pycharm中观察有无打印来判断是否重启了，因为重启后python进程变化了，pycharm控制台不能捕捉到新进程的打印输出，所以不要在pycharm下运行python来验证重启功能。

"""


def restart_program(seconds):
    '''
    间隔n秒重启脚本
    :param seconds:
    :return:
    '''
    """ 
    这个只能在 win cmd 或者 linux下测试重启功能，
    不能在pycharm中观察有无打印来判断是否重启了，因为重启后python进程变化了，pycharm控制台不能捕捉到新进程的打印输出，所以不要在pycharm下运行python来验证重启功能。
    """

    def _restart_program():
        time.sleep(seconds)
        python = sys.executable
        logger.warning(f'重启当前python程序 {python} , {sys.argv}')
        os.execl(python, python, *sys.argv)

    threading.Thread(target=_restart_program).start()


def _run():
    print(datetime.datetime.now(),'开始运行程序')
    for i in range(1000):
        time.sleep(0.5)
        print(datetime.datetime.now(),i)

if __name__ == '__main__':
    restart_program(10)  # 每隔10秒重启。
    _run()

```

### 代码文件: funboost\utils\simple_data_class.py
```python
import json

import copy
import typing

from funboost.utils import json_helper
from funboost.utils.str_utils import PwdEnc, StrHelper


class DataClassBase:
    """
    使用类实现的 简单数据类。
    也可以使用装饰器来实现数据类
    """

    def __new__(cls, **kwargs):
        self = super().__new__(cls)
        self.__dict__ = copy.copy({k: v for k, v in cls.__dict__.items() if not k.startswith('__')})
        return self

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __call__(self, ) -> dict:
        return self.get_dict()

    def get_dict(self):
        return {k: v.get_dict() if isinstance(v, DataClassBase) else v for k, v in self.__dict__.items()}

    def __str__(self):
        return f"{self.__class__}    {self.get_dict()}"

    def __getitem__(self, item):
        return getattr(self, item)

    def get_json(self,indent=4):
        return json_helper.dict_to_un_strict_json(self.get_dict(),indent=indent)

    def get_pwd_enc_json(self,indent=4):
        """防止打印密码明文,泄漏密码"""
        dict_new = {}
        for k, v in self.get_dict().items():
            # only_print_on_main_process(f'{k} :  {v}')
            if isinstance(v, (bool, tuple, dict, float, int)):
                dict_new[k] = v
            else:
                v_enc =PwdEnc.enc_broker_uri(str(v))
                if StrHelper(k).judge_contains_str_list(['pwd', 'pass_word', 'password', 'passwd', 'pass']):
                    v_enc = PwdEnc.enc_pwd(v_enc)
                dict_new[k] = v_enc
        return json.dumps(dict_new, ensure_ascii=False, indent=indent)

    @classmethod
    def update_cls_attribute(cls,**kwargs):
        for k ,v in kwargs.items():
            setattr(cls,k,v)
        return cls

    def update_instance_attribute(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self


if __name__ == '__main__':
    import datetime


    class A(DataClassBase):
        x = 1
        y = 2
        z = datetime.datetime.now()


    print(A())
    print(A(y=3))
    print(A(y=5).get_dict())

    print(A()['y'])
    print(A().y)

```

### 代码文件: funboost\utils\str_utils.py
```python
import re


class PwdEnc:

    @classmethod
    def enc_broker_uri(cls, uri: str):
        protocol_split_list = uri.split('://')
        if len(protocol_split_list) != 2:
            return uri
        user_pass__ip_port_split_list = protocol_split_list[1].split('@')
        if len(user_pass__ip_port_split_list) != 2:
            return uri
        user__pass_split_list = user_pass__ip_port_split_list[0].split(':')
        if len(user__pass_split_list) != 2:
            return uri
        user = user__pass_split_list[0]
        pwd = user__pass_split_list[1]
        pwd_enc = cls.enc_pwd(pwd)
        return f'{protocol_split_list[0]}://{user}:{pwd_enc}@{user_pass__ip_port_split_list[1]}'

    @staticmethod
    def enc_pwd(pwd: str, plain_len=3):
        pwd_enc = pwd
        if len(pwd_enc) > plain_len:
            pwd_enc = f'{pwd_enc[:plain_len]}{"*" * (len(pwd_enc) - plain_len)}'
        return pwd_enc


class StrHelper:
    def __init__(self, strx: str):
        self.strx = strx

    def judge_contains_str_list(self, str_list: list, ignore_case=True):
        for str1 in str_list:
            if str1 in self.strx:
                return True
            if ignore_case:
                if str1.lower() in self.strx.lower():
                    return True
        return False


if __name__ == '__main__':
    str1 = "amqp://admin:abc234@108.55.33.99:5672/"
    str2 = "redis://:myRedisPass1234@127.0.0.1:6379/0"
    print(PwdEnc.enc_broker_uri(str1))
    print(PwdEnc.enc_broker_uri(str2))
    print(PwdEnc.enc_pwd('465460dsdsd'))



```

### 代码文件: funboost\utils\time_util.py
```python
# coding=utf-8
import functools
import typing
import datetime
import time
import re
import pytz
from funboost.core.funboost_time import FunboostTime

from funboost.utils import nb_print

@functools.lru_cache()
def _get_funboost_timezone():
    from funboost.funboost_config_deafult import FunboostCommonConfig
    return FunboostCommonConfig.TIMEZONE

def build_defualt_date():
    """
    获取今天和明天的日期
    :return:
    """
    today = datetime.date.today()
    today_str = today.__str__()
    tomorrow = today + datetime.timedelta(days=1)
    tomorrow_str = str(tomorrow)
    return today, tomorrow, today_str, tomorrow_str


def get_day_by_interval(n):
    """
    :param n: 离当天的日期，可为正负整数
    :return:
    """
    today = datetime.date.today()
    day = today + datetime.timedelta(days=n)
    day_str = str(day)
    return day, day_str


def get_ahead_one_hour(datetime_str):
    """
    获得提前一小时的时间字符串和时间戳
    :return:
    """
    datetime_obj = datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
    datetime_obj_one_hour_ahead = datetime_obj + datetime.timedelta(hours=-1)
    return datetime_obj_one_hour_ahead.strftime('%Y-%m-%d %H:%M:%S'), datetime_obj_one_hour_ahead.timestamp()


def timestamp_to_datetime_str(timestamp):
    time_local = time.localtime(timestamp)
    # 转换成新的时间格式(2016-05-05 20:28:54)
    return time.strftime("%Y-%m-%d %H:%M:%S", time_local)


class DatetimeConverter:
    """
    最爽的时间操作方式。使用真oop需要实例化，调用方式比纯静态方法工具类好太多。
    """
    DATETIME_FORMATTER = "%Y-%m-%d %H:%M:%S"
    DATETIME_FORMATTER2 = "%Y-%m-%d"
    DATETIME_FORMATTER3 = "%H:%M:%S"

    @classmethod
    def bulid_conveter_with_other_formatter(cls, datetime_str, datetime_formatter):
        """
        :param datetime_str: 时间字符串
        :param datetime_formatter: 能够格式化该字符串的模板
        :return:
        """
        datetime_obj = datetime.datetime.strptime(datetime_str, datetime_formatter)
        return cls(datetime_obj)

    def __init__(self, datetimex: typing.Union[int, float, datetime.datetime, str] = None):  # REMIND 不要写成默认 datetime.datetime.now()或time.time()，否则默认参数值运行一次
        """
        :param datetimex: 接受时间戳  datatime类型 和 时间字符串三种类型
        """
        # if isinstance(datetimex, str):
        #     if not re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', datetimex):
        #         raise ValueError('时间字符串的格式不符合此传参的规定')
        #     else:
        #         self.datetime_obj = datetime.datetime.strptime(datetimex, self.DATETIME_FORMATTER)
        # elif isinstance(datetimex, (int, float)):
        #     if datetimex < 1:
        #         datetimex += 86400
        #     self.datetime_obj = datetime.datetime.fromtimestamp(datetimex, tz=pytz.timezone(_get_funboost_timezone()))  # 时间戳0在windows会出错。
        # elif isinstance(datetimex, datetime.datetime):
        #     self.datetime_obj = datetimex
        # elif datetimex is None:
        #     self.datetime_obj = datetime.datetime.now(tz=pytz.timezone(_get_funboost_timezone()))
        # else:
        #     raise ValueError('实例化时候的传参不符合规定')
        self.datetime_obj = FunboostTime(datetimex).datetime_obj

    @property
    def datetime_str(self):
        return self.datetime_obj.strftime(self.DATETIME_FORMATTER)

    @property
    def time_str(self):
        return self.datetime_obj.strftime(self.DATETIME_FORMATTER3)

    @property
    def date_str(self):
        return self.datetime_obj.strftime(self.DATETIME_FORMATTER2)

    @property
    def timestamp(self):
        return self.datetime_obj.timestamp()

    @property
    def one_hour_ago_datetime_converter(self):
        """
        酒店经常需要提前一小时免费取消，直接封装在这里
        :return:
        """
        one_hour_ago_datetime_obj = self.datetime_obj + datetime.timedelta(hours=-1)
        return self.__class__(one_hour_ago_datetime_obj)

    def is_greater_than_now(self):
        return self.timestamp > time.time()

    def __str__(self):
        return self.datetime_str

    def __call__(self):
        return self.datetime_obj


def seconds_to_hour_minute_second(seconds):
    """
    把秒转化成还需要的时间
    :param seconds:
    :return:
    """
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d" % (h, m, s)


if __name__ == '__main__':
    """
    1557113661.0
    '2019-05-06 12:34:21'
    '2019/05/06 12:34:21'
    DatetimeConverter(1557113661.0)()
    """
    # noinspection PyShadowingBuiltins
    print = nb_print
    o3 = DatetimeConverter('2019-05-06 12:34:21')
    print(o3)
    print('- - - - -  - - -')

    o = DatetimeConverter.bulid_conveter_with_other_formatter('2019/05/06 12:34:21', '%Y/%m/%d %H:%M:%S')
    print(o)
    print(o.date_str)
    print(o.timestamp)
    print('***************')
    o2 = o.one_hour_ago_datetime_converter
    print(o2)
    print(o2.date_str)
    print(o2.timestamp)
    print(o2.is_greater_than_now())
    print(o2(), type(o2()))
    print(DatetimeConverter())
    print(datetime.datetime.now())
    time.sleep(5)
    print(DatetimeConverter())
    print(datetime.datetime.now())
    print(DatetimeConverter(3600 * 24))

    print(seconds_to_hour_minute_second(3600 * 2))

```

### 代码文件: funboost\utils\un_strict_json_dumps.py
```python
import json


def dict2json(dictx: dict, indent=4):
    dict_new = {}
    for k, v in dictx.items():
        # only_print_on_main_process(f'{k} :  {v}')
        if isinstance(v, (bool, tuple, dict, float, int)):
            dict_new[k] = v
        else:
            dict_new[k] = str(v)
    return json.dumps(dict_new, ensure_ascii=False, indent=indent)


if __name__ == '__main__':
    pass

```

### 代码文件: funboost\utils\__init__.py
```python
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 9:48


from funboost.utils.dependency_packages_in_pythonpath import add_to_pythonpath

from nb_log import (LogManager, simple_logger, LoggerMixin, LoggerLevelSetterMixin,
                    LoggerMixinDefaultWithFileHandler,nb_print,patch_print,reverse_patch_print,get_logger)

# from funboost.utils.redis_manager import RedisMixin

from funboost.utils.json_helper import monkey_patch_json


#################以下为打猴子补丁#####################
monkey_patch_json()






```

### 代码文件: funboost\utils\func_timeout\dafunc.py
```python

# vim: set ts=4 sw=4 expandtab :

'''
    Copyright (c) 2016, 2017 Tim Savannah All Rights Reserved.

    Licensed under the Lesser GNU Public License Version 3, LGPLv3. You should have recieved a copy of this with the source distribution as
    LICENSE, otherwise it is available at https://github.com/kata198/func_timeout/LICENSE
'''

import copy
import functools
import inspect
import threading
import time
import types
import sys


from .exceptions import FunctionTimedOut
from .StoppableThread import StoppableThread


from .py3_raise import raise_exception


from functools import wraps

__all__ = ('func_timeout', 'func_set_timeout')




def func_timeout(timeout, func, args=(), kwargs=None):
    '''
        func_timeout - Runs the given function for up to #timeout# seconds.

        Raises any exceptions #func# would raise, returns what #func# would return (unless timeout is exceeded), in which case it raises FunctionTimedOut

        @param timeout <float> - Maximum number of seconds to run #func# before terminating

        @param func <function> - The function to call

        @param args    <tuple> - Any ordered arguments to pass to the function

        @param kwargs  <dict/None> - Keyword arguments to pass to the function.


        @raises - FunctionTimedOut if #timeout# is exceeded, otherwise anything #func# could raise will be raised

        If the timeout is exceeded, FunctionTimedOut will be raised within the context of the called function every two seconds until it terminates,
        but will not block the calling thread (a new thread will be created to perform the join). If possible, you should try/except FunctionTimedOut
        to return cleanly, but in most cases it will 'just work'.

        @return - The return value that #func# gives
    '''

    if not kwargs:
        kwargs = {}
    if not args:
        args = ()

    ret = []
    exception = []
    isStopped = False

    from funboost.core.current_task import thread_current_task

    def funcwrap(args2, kwargs2,):
        # fct = thread_current_task
        # fct.set_fct_context(fct_context)  # 把funboost的消费线程上下文需要传递到超时线程上下文里面来.
        try:
            ret.append( func(*args2, **kwargs2) )
        except FunctionTimedOut:
            # Don't print traceback to stderr if we time out
            pass
        except BaseException as e:
            exc_info = sys.exc_info()
            if isStopped is False:
                # Assemble the alternate traceback, excluding this function
                #  from the trace (by going to next frame)
                # Pytohn3 reads native from __traceback__,
                # python2 has a different form for "raise"
                e.__traceback__ = exc_info[2].tb_next
                exception.append( e )


    # fct = funboost_current_task()
    thread = StoppableThread(target=funcwrap, args=(args, kwargs,))
    thread.daemon = True

    thread.start()
    thread.join(timeout)

    stopException = None
    if thread.is_alive():
        isStopped = True

        class FunctionTimedOutTempType(FunctionTimedOut):
            def __init__(self):
                return FunctionTimedOut.__init__(self, '', timeout, func, args, kwargs)

        FunctionTimedOutTemp = type('FunctionTimedOut' + str( hash( "%d_%d_%d_%d" %(id(timeout), id(func), id(args), id(kwargs))) ), FunctionTimedOutTempType.__bases__, dict(FunctionTimedOutTempType.__dict__))

        stopException = FunctionTimedOutTemp
        # raise FunctionTimedOut('', timeout, func, args, kwargs)
        thread._stopThread(stopException)
        thread.join(min(.1, timeout / 50.0))
        raise FunctionTimedOut('', timeout, func, args, kwargs)
    else:
        # We can still cleanup the thread here..
        # Still give a timeout... just... cuz..
        thread.join(.5)

    if exception:
        raise_exception(exception)

    if ret:
        return ret[0]


def func_set_timeout(timeout, allowOverride=False):
    '''
        func_set_timeout - Decorator to run a function with a given/calculated timeout (max execution time).
            Optionally (if #allowOverride is True), adds a paramater, "forceTimeout", to the
            function which, if provided, will override the default timeout for that invocation.

            If #timeout is provided as a lambda/function, it will be called
              prior to each invocation of the decorated function to calculate the timeout to be used
              for that call, based on the arguments passed to the decorated function.

              For example, you may have a "processData" function whose execution time
              depends on the number of "data" elements, so you may want a million elements to have a
              much higher timeout than seven elements.)

            If #allowOverride is True AND a kwarg of "forceTimeout" is passed to the wrapped function, that timeout
             will be used for that single call.

        @param timeout <float OR lambda/function> -

            **If float:**
                Default number of seconds max to allow function to execute
                  before throwing FunctionTimedOut

            **If lambda/function:

                 If a function/lambda is provided, it will be called for every
                  invocation of the decorated function (unless #allowOverride=True and "forceTimeout" was passed)
                  to determine the timeout to use based on the arguments to the decorated function.

                    The arguments as passed into the decorated function will be passed to this function.
                     They either must match exactly to what the decorated function has, OR
                      if you prefer to get the *args (list of ordered args) and **kwargs ( key : value  keyword args form),
                      define your calculate function like:

                        def calculateTimeout(*args, **kwargs):
                            ...

                      or lambda like:

                        calculateTimeout = lambda *args, **kwargs : ...

                    otherwise the args to your calculate function should match exactly the decorated function.


        @param allowOverride <bool> Default False, if True adds a keyword argument to the decorated function,
            "forceTimeout" which, if provided, will override the #timeout. If #timeout was provided as a lambda / function, it
             will not be called.

        @throws FunctionTimedOut If time alloted passes without function returning naturally

        @see func_timeout
    '''
    # Try to be as efficent as possible... don't compare the args more than once

    #  Helps closure issue on some versions of python
    defaultTimeout = copy.copy(timeout)

    isTimeoutAFunction = bool( issubclass(timeout.__class__, (types.FunctionType, types.MethodType, types.LambdaType, types.BuiltinFunctionType, types.BuiltinMethodType) ) )

    if not isTimeoutAFunction:
        if not issubclass(timeout.__class__, (float, int)):
            try:
                timeout = float(timeout)
            except:
                raise ValueError('timeout argument must be a float/int for number of seconds, or a function/lambda which gets passed the function arguments and returns a calculated timeout (as float or int). Passed type: < %s > is not of any of these, and cannot be converted to a float.' %( timeout.__class__.__name__, ))


    if not allowOverride and not isTimeoutAFunction:
        # Only defaultTimeout provided. Simple function wrapper
        def _function_decorator(func):

            return wraps(func)(lambda *args, **kwargs : func_timeout(defaultTimeout, func, args=args, kwargs=kwargs))

#            def _function_wrapper(*args, **kwargs):
#                return func_timeout(defaultTimeout, func, args=args, kwargs=kwargs)
#            return _function_wrapper
        return _function_decorator

    if not isTimeoutAFunction:
        # allowOverride is True and timeout is not a function. Simple conditional on every call
        def _function_decorator(func):
            def _function_wrapper(*args, **kwargs):
                if 'forceTimeout' in kwargs:
                    useTimeout = kwargs.pop('forceTimeout')
                else:
                    useTimeout = defaultTimeout

                return func_timeout(useTimeout, func, args=args, kwargs=kwargs)

            return wraps(func)(_function_wrapper)
        return _function_decorator


    # At this point, timeout IS known to be a function.
    timeoutFunction = timeout

    if allowOverride:
        # Could use a lambda here... but want traceback to highlight the calculate function,
        #  and not the invoked function
        def _function_decorator(func):
            def _function_wrapper(*args, **kwargs):
                if 'forceTimeout' in kwargs:
                    useTimeout = kwargs.pop('forceTimeout')
                else:
                    useTimeout = timeoutFunction(*args, **kwargs)

                return func_timeout(useTimeout, func, args=args, kwargs=kwargs)

            return wraps(func)(_function_wrapper)
        return _function_decorator

    # Cannot override, and calculate timeout function
    def _function_decorator(func):
        def _function_wrapper(*args, **kwargs):
            useTimeout = timeoutFunction(*args, **kwargs)

            return func_timeout(useTimeout, func, args=args, kwargs=kwargs)

        return wraps(func)(_function_wrapper)
    return _function_decorator


# vim: set ts=4 sw=4 expandtab :

```

### 代码文件: funboost\utils\func_timeout\exceptions.py
```python
'''
    Copyright (c) 2016 Tim Savannah All Rights Reserved.

    Licensed under the Lesser GNU Public License Version 3, LGPLv3. You should have recieved a copy of this with the source distribution as
    LICENSE, otherwise it is available at https://github.com/kata198/func_timeout/LICENSE
'''

__all__ = ('FunctionTimedOut', 'RETRY_SAME_TIMEOUT')

RETRY_SAME_TIMEOUT = 'RETRY_SAME_TIMEOUT'

class FunctionTimedOut(BaseException):
    '''
        FunctionTimedOut - Exception raised when a function times out

        @property timedOutAfter - Number of seconds before timeout was triggered

        @property timedOutFunction - Function called which timed out
        @property timedOutArgs - Ordered args to function
        @property timedOutKwargs - Keyword args to function

        @method retry - Retries the function with same arguments, with option to run with original timeout, no timeout, or a different
          explicit timeout. @see FunctionTimedOut.retry
    '''


    def __init__(self, msg='', timedOutAfter=None, timedOutFunction=None, timedOutArgs=None, timedOutKwargs=None):
        '''
            __init__ - Create this exception type.

                You should not need to do this outside of testing, it will be created by the func_timeout API

                    @param msg <str> - A predefined message, otherwise we will attempt to generate one from the other arguments.

                    @param timedOutAfter <None/float> - Number of seconds before timing-out. Filled-in by API, None will produce "Unknown"

                    @param timedOutFunction <None/function> - Reference to the function that timed-out. Filled-in by API." None will produce "Unknown Function"

                    @param timedOutArgs <None/tuple/list> - List of fixed-order arguments ( *args ), or None for no args.

                    @param timedOutKwargs <None/dict> - Dict of keyword arg ( **kwargs ) names to values, or None for no kwargs.

        '''

        self.timedOutAfter = timedOutAfter

        self.timedOutFunction = timedOutFunction
        self.timedOutArgs = timedOutArgs
        self.timedOutKwargs = timedOutKwargs

        if not msg:
            msg = self.getMsg()

        BaseException.__init__(self, msg)

        self.msg = msg


    def getMsg(self):
        '''
            getMsg - Generate a default message based on parameters to FunctionTimedOut exception'

            @return <str> - Message
        '''
        # Try to gather the function name, if available.
        # If it is not, default to an "unknown" string to allow default instantiation
        if self.timedOutFunction is not None:
            timedOutFuncName = self.timedOutFunction.__name__
        else:
            timedOutFuncName = 'Unknown Function'
        if self.timedOutAfter is not None:
            timedOutAfterStr = "%f" %(self.timedOutAfter, )
        else:
            timedOutAfterStr = "Unknown"

        return 'Function %s (args=%s) (kwargs=%s) timed out after %s seconds.\n' %(timedOutFuncName, repr(self.timedOutArgs), repr(self.timedOutKwargs), timedOutAfterStr)

    def retry(self, timeout=RETRY_SAME_TIMEOUT):
        '''
            retry - Retry the timed-out function with same arguments.

            @param timeout <float/RETRY_SAME_TIMEOUT/None> Default RETRY_SAME_TIMEOUT

                If RETRY_SAME_TIMEOUT : Will retry the function same args, same timeout
                If a float/int : Will retry the function same args with provided timeout
                If None : Will retry function same args no timeout

            @return - Returnval from function
        '''
        if timeout is None:
            return self.timedOutFunction(*(self.timedOutArgs), **self.timedOutKwargs)

        from .dafunc import func_timeout

        if timeout == RETRY_SAME_TIMEOUT:
            timeout = self.timedOutAfter

        return func_timeout(timeout, self.timedOutFunction, args=self.timedOutArgs, kwargs=self.timedOutKwargs)

```

### 代码文件: funboost\utils\func_timeout\py2_raise.py
```python


# Python2 allows specifying an alternate traceback.
def raise_exception(exception):
    '''
    raise exception[0] , None , exception[0].__traceback__  # noqa
    '''

```

### 代码文件: funboost\utils\func_timeout\py3_raise.py
```python

# PEP 409 - Raise with the chained exception context disabled
#  This, in effect, prevents the "funcwrap" wrapper ( chained
#   in context to an exception raised here, due to scope )
# Only available in python3.3+
def raise_exception(exception):
    raise exception[0] from None

```

### 代码文件: funboost\utils\func_timeout\readme.md
```python


# 基于三方包func_timeout的改动点


主要是把  StoppableThread 和 JoinThread 改成了继承 FctContextThread 而非 threading.Thread


原因是为了支持把当前线程的 funboost上下文传给 超时的单独的线程中， 方便用设置了超时后还能用 funboost上下文 funboost_current_task
```

### 代码文件: funboost\utils\func_timeout\StoppableThread.py
```python
'''
    Copyright (c) 2016, 2017, 2019 Timothy Savannah All Rights Reserved.

    Licensed under the Lesser GNU Public License Version 3, LGPLv3. You should have recieved a copy of this with the source distribution as
    LICENSE, otherwise it is available at https://github.com/kata198/func_timeout/LICENSE
'''

import os
import ctypes
import threading

from funboost.core.current_task import FctContextThread
__all__ = ('StoppableThread', 'JoinThread')

class StoppableThread(FctContextThread): # 这里重要，继承的是FctContextThread，而不是原生 threading.Thread
    '''
        StoppableThread - A thread that can be stopped by forcing an exception in the execution context.

          This works both to interrupt code that is in C or in python code, at either the next call to a python function,
           or the next line in python code.

        It is recommended that if you call stop ( @see StoppableThread.stop ) that you use an exception that inherits BaseException, to ensure it likely isn't caught.

         Also, beware unmarked exception handlers in your code. Code like this:

            while True:
                try:
                    doSomething()
                except:
                    continue

        will never be able to abort, because the exception you raise is immediately caught.

        The exception is raised over and over, with a specifed delay (default 2.0 seconds)
    '''


    def _stopThread(self, exception, raiseEvery=2.0):
        '''
            _stopThread - @see StoppableThread.stop
        '''
        if self.is_alive() is False:
            return True

        self._stderr = open(os.devnull, 'w')

        # Create "joining" thread which will raise the provided exception
        #  on a repeat, until the thread stops.
        joinThread = JoinThread(self, exception, repeatEvery=raiseEvery)

        # Try to prevent spurrious prints
        joinThread._stderr = self._stderr
        joinThread.start()
        joinThread._stderr = self._stderr


    def stop(self, exception, raiseEvery=2.0):
        '''
            Stops the thread by raising a given exception.

            @param exception <Exception type> - Exception to throw. Likely, you want to use something

              that inherits from BaseException (so except BaseException as e: continue; isn't a problem)

              This should be a class/type, NOT an instance, i.e.  MyExceptionType   not  MyExceptionType()


            @param raiseEvery <float> Default 2.0 - We will keep raising this exception every #raiseEvery seconds,

                until the thread terminates.

                If your code traps a specific exception type, this will allow you #raiseEvery seconds to cleanup before exit.

                If you're calling third-party code you can't control, which catches BaseException, set this to a low number

                  to break out of their exception handler.


             @return <None>
        '''
        return self._stopThread(exception, raiseEvery)


class JoinThread(FctContextThread):
    '''
        JoinThread - The workhouse that stops the StoppableThread.

            Takes an exception, and upon being started immediately raises that exception in the current context
              of the thread's execution (so next line of python gets it, or next call to a python api function in C code ).

            @see StoppableThread for more details
    '''

    def __init__(self, otherThread, exception, repeatEvery=2.0):
        '''
            __init__ - Create a JoinThread (don't forget to call .start() ! )

                @param otherThread <threading.Thread> - A thread

                @param exception <BaseException> - An exception. Should be a BaseException, to prevent "catch Exception as e: continue" type code
                  from never being terminated. If such code is unavoidable, you can try setting #repeatEvery to a very low number, like .00001,
                  and it will hopefully raise within the context of the catch, and be able to break free.

                @param repeatEvery <float> Default 2.0 - After starting, the given exception is immediately raised. Then, every #repeatEvery seconds,
                  it is raised again, until the thread terminates.
        '''
        threading.Thread.__init__(self)
        self.otherThread = otherThread
        self.exception = exception
        self.repeatEvery = repeatEvery
        self.daemon = True

    def run(self):
        '''
            run - The thread main. Will attempt to stop and join the attached thread.
        '''

        # Try to silence default exception printing.
        self.otherThread._Thread__stderr = self._stderr
        if hasattr(self.otherThread, '_Thread__stop'):
            # If py2, call this first to start thread termination cleanly.
            #   Python3 does not need such ( nor does it provide.. )
            self.otherThread._Thread__stop()
        while self.otherThread.is_alive():
            # We loop raising exception incase it's caught hopefully this breaks us far out.
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.otherThread.ident), ctypes.py_object(self.exception))
            self.otherThread.join(self.repeatEvery)

        try:
            self._stderr.close()
        except:
            pass

# vim: set ts=4 sw=4 expandtab :

```

### 代码文件: funboost\utils\func_timeout\__init__.py
```python

```

### 代码文件: funboost\utils\pysnooper_ydf\pycompat.py
```python
# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.
'''Python 2/3 compatibility'''

import abc
import os
import inspect
import sys
import datetime as datetime_module

PY3 = (sys.version_info[0] == 3)
PY2 = not PY3

if hasattr(abc, 'ABC'):
    ABC = abc.ABC
else:
    class ABC(object):
        """Helper class that provides a standard way to create an ABC using
        inheritance.
        """
        __metaclass__ = abc.ABCMeta
        __slots__ = ()


if hasattr(os, 'PathLike'):
    PathLike = os.PathLike
else:
    class PathLike(ABC):
        """Abstract base class for implementing the file system path protocol."""

        @abc.abstractmethod
        def __fspath__(self):
            """Return the file system path representation of the object."""
            raise NotImplementedError

        @classmethod
        def __subclasshook__(cls, subclass):
            return (
                hasattr(subclass, '__fspath__') or
                # Make a concession for older `pathlib` versions:g
                (hasattr(subclass, 'open') and
                 'path' in subclass.__name__.lower())
            )


try:
    iscoroutinefunction = inspect.iscoroutinefunction
except AttributeError:
    iscoroutinefunction = lambda whatever: False # Lolz

try:
    isasyncgenfunction = inspect.isasyncgenfunction
except AttributeError:
    isasyncgenfunction = lambda whatever: False # Lolz


if PY3:
    string_types = (str,)
    text_type = str
else:
    string_types = (basestring,)
    text_type = unicode

try:
    from collections import abc as collections_abc
except ImportError: # Python 2.7
    import collections as collections_abc

if sys.version_info[:2] >= (3, 6):
    time_isoformat = datetime_module.time.isoformat
else:
    def time_isoformat(time, timespec='microseconds'):
        assert isinstance(time, datetime_module.time)
        if timespec != 'microseconds':
            raise NotImplementedError
        result = '{:02d}:{:02d}:{:02d}.{:06d}'.format(
            time.hour, time.minute, time.second, time.microsecond
        )
        assert len(result) == 15
        return result



```

### 代码文件: funboost\utils\pysnooper_ydf\tracer.py
```python
# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import functools
import inspect
import opcode
import os
import sys
import re
import collections
import datetime as datetime_module
import itertools
import threading
import traceback

from .variables import CommonVariable, Exploding, BaseVariable
from . import utils, pycompat
if pycompat.PY2:
    from io import open


ipython_filename_pattern = re.compile('^<ipython-input-([0-9]+)-.*>$')


def get_local_reprs(frame, watch=(), custom_repr=(), max_length=None):
    code = frame.f_code
    vars_order = (code.co_varnames + code.co_cellvars + code.co_freevars +
                  tuple(frame.f_locals.keys()))

    result_items = [(key, utils.get_shortish_repr(value, custom_repr,
                                                  max_length))
                    for key, value in frame.f_locals.items()]
    result_items.sort(key=lambda key_value: vars_order.index(key_value[0]))
    result = collections.OrderedDict(result_items)

    for variable in watch:
        result.update(sorted(variable.items(frame)))
    return result


class UnavailableSource(object):
    def __getitem__(self, i):
        return u'SOURCE IS UNAVAILABLE'


source_and_path_cache = {}


def get_path_and_source_from_frame(frame):
    globs = frame.f_globals or {}
    module_name = globs.get('__name__')
    file_name = frame.f_code.co_filename
    cache_key = (module_name, file_name)
    try:
        return source_and_path_cache[cache_key]
    except KeyError:
        pass
    loader = globs.get('__loader__')

    source = None
    if hasattr(loader, 'get_source'):
        try:
            source = loader.get_source(module_name)
        except ImportError:
            pass
        if source is not None:
            source = source.splitlines()
    if source is None:
        ipython_filename_match = ipython_filename_pattern.match(file_name)
        if ipython_filename_match:
            entry_number = int(ipython_filename_match.group(1))
            try:
                import IPython
                ipython_shell = IPython.get_ipython()
                ((_, _, source_chunk),) = ipython_shell.history_manager. \
                                  get_range(0, entry_number, entry_number + 1)
                source = source_chunk.splitlines()
            except BaseException :
                pass
        else:
            try:
                with open(file_name, 'rb') as fp:
                    source = fp.read().splitlines()
            except utils.file_reading_errors:
                pass
    if not source:
        # We used to check `if source is None` but I found a rare bug where it
        # was empty, but not `None`, so now we check `if not source`.
        source = UnavailableSource()

    # If we just read the source from a file, or if the loader did not
    # apply tokenize.detect_encoding to decode the source into a
    # string, then we should do that ourselves.
    if isinstance(source[0], bytes):
        encoding = 'utf-8'
        for line in source[:2]:
            # File coding may be specified. Match pattern from PEP-263
            # (https://www.python.org/dev/peps/pep-0263/)
            match = re.search(br'coding[:=]\s*([-\w.]+)', line)
            if match:
                encoding = match.group(1).decode('ascii')
                break
        source = [pycompat.text_type(sline, encoding, 'replace') for sline in
                  source]

    result = (file_name, source)
    source_and_path_cache[cache_key] = result
    return result


def get_write_function(output, overwrite):
    is_path = isinstance(output, (pycompat.PathLike, str))
    if overwrite and not is_path:
        raise Exception('`overwrite=True` can only be used when writing '
                        'content to file.')
    if output is None:
        def write(s):
            # stderr = sys.stderr
            stderr = sys.stdout # REMIND 这行改了，out才能自定义颜色。
            try:
                stderr.write(s)
            except UnicodeEncodeError:
                # God damn Python 2
                stderr.write(utils.shitcode(s))
    elif is_path:
        return FileWriter(output, overwrite).write
    elif callable(output):
        write = output
    else:
        assert isinstance(output, utils.WritableStream)

        def write(s):
            output.write(s)
    return write


class FileWriter(object):
    def __init__(self, path, overwrite):
        self.path = pycompat.text_type(path)
        self.overwrite = overwrite

    def write(self, s):
        with open(self.path, 'w' if self.overwrite else 'a',
                  encoding='utf-8') as output_file:
            output_file.write(s)
        self.overwrite = False


thread_global = threading.local()
DISABLED = bool(os.getenv('PYSNOOPER_DISABLED', ''))

class Tracer:
    '''
    Snoop on the function, writing everything it's doing to stderr.

    This is useful for debugging.

    When you decorate a function with `@pysnooper.snoop()`
    or wrap a block of code in `with pysnooper.snoop():`, you'll get a log of
    every line that ran in the function and a play-by-play of every local
    variable that changed.

    If stderr is not easily accessible for you, you can redirect the output to
    a file::

        @pysnooper.snoop('/my/log/file.log')

    See values of some expressions that aren't local variables::

        @pysnooper.snoop(watch=('foo.bar', 'self.x["whatever"]'))

    Expand values to see all their attributes or items of lists/dictionaries:

        @pysnooper.snoop(watch_explode=('foo', 'self'))

    (see Advanced Usage in the README for more control)

    Show snoop lines for functions that your function calls::

        @pysnooper.snoop(depth=2)

    Start all snoop lines with a prefix, to grep for them easily::

        @pysnooper.snoop(prefix='ZZZ ')

    On multi-threaded apps identify which thread are snooped in output::

        @pysnooper.snoop(thread_info=True)

    Customize how values are represented as strings::

        @pysnooper.snoop(custom_repr=((type1, custom_repr_func1),
                         (condition2, custom_repr_func2), ...))

    Variables and exceptions get truncated to 100 characters by default. You
    can customize that:

        @pysnooper.snoop(max_variable_length=200)

    You can also use `max_variable_length=None` to never truncate them.

    '''
    def __init__(self, output=None, watch=(), watch_explode=(), depth=1,
                 prefix='', overwrite=False, thread_info=False, custom_repr=(),
                 max_variable_length=100,dont_effect_on_linux=True):
        self._write = get_write_function(output, overwrite)

        self.watch = [
            v if isinstance(v, BaseVariable) else CommonVariable(v)
            for v in utils.ensure_tuple(watch)
         ] + [
             v if isinstance(v, BaseVariable) else Exploding(v)
             for v in utils.ensure_tuple(watch_explode)
        ]
        self.frame_to_local_reprs = {}
        self.depth = depth

        self.prefix = prefix
        self.thread_info = thread_info
        self.thread_info_padding = 0
        assert self.depth >= 1
        self.target_codes = set()
        self.target_frames = set()
        self.thread_local = threading.local()
        if len(custom_repr) == 2 and not all(isinstance(x,
                      pycompat.collections_abc.Iterable) for x in custom_repr):
            custom_repr = (custom_repr,)
        self.custom_repr = custom_repr
        self.last_source_path = None
        self.max_variable_length = max_variable_length
        if dont_effect_on_linux and os.name == 'posix':
            global DISABLED
            DISABLED = True            # linux上装饰器自动失效，避免发到生产。
        self.total_run_line = 0

    def __call__(self, function_or_class):
        if DISABLED:
            return function_or_class
        if self.prefix == '':
            self.prefix = f'调试 [{function_or_class.__name__}] 函数 -->  '
        if inspect.isclass(function_or_class):
            return self._wrap_class(function_or_class)
        else:
            return self._wrap_function(function_or_class)

    def _wrap_class(self, cls):
        for attr_name, attr in cls.__dict__.items():
            # Coroutines are functions, but snooping them is not supported
            # at the moment
            if pycompat.iscoroutinefunction(attr):
                continue

            if inspect.isfunction(attr):
                setattr(cls, attr_name, self._wrap_function(attr))
        return cls

    def _wrap_function(self, function):
        self.target_codes.add(function.__code__)

        @functools.wraps(function)
        def simple_wrapper(*args, **kwargs):
            with self:
                return function(*args, **kwargs)

        @functools.wraps(function)
        def generator_wrapper(*args, **kwargs):
            gen = function(*args, **kwargs)
            method, incoming = gen.send, None
            while True:
                with self:
                    try:
                        outgoing = method(incoming)
                    except StopIteration:
                        return
                try:
                    method, incoming = gen.send, (yield outgoing)
                except BaseException as e:
                    method, incoming = gen.throw, e

        if pycompat.iscoroutinefunction(function):
            raise NotImplementedError
        if pycompat.isasyncgenfunction(function):
            raise NotImplementedError
        elif inspect.isgeneratorfunction(function):
            return generator_wrapper
        else:
            return simple_wrapper

    def write(self, s):
        s = u'{self.prefix}{s}\n'.format(**locals())
        self._write(s)

    def __enter__(self):
        if DISABLED:
            return
        calling_frame = inspect.currentframe().f_back
        if not self._is_internal_frame(calling_frame):
            calling_frame.f_trace = self.trace
            self.target_frames.add(calling_frame)

        stack = self.thread_local.__dict__.setdefault(
            'original_trace_functions', []
        )
        stack.append(sys.gettrace())
        sys.settrace(self.trace)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if DISABLED:
            return
        stack = self.thread_local.original_trace_functions
        sys.settrace(stack.pop())
        calling_frame = inspect.currentframe().f_back
        self.target_frames.discard(calling_frame)
        self.frame_to_local_reprs.pop(calling_frame, None)
        utils.nb_print(f'解释运行的总代码行数是 {self.total_run_line} 行')

    def _is_internal_frame(self, frame):
        return frame.f_code.co_filename == Tracer.__enter__.__code__.co_filename

    def set_thread_info_padding(self, thread_info):
        current_thread_len = len(thread_info)
        self.thread_info_padding = max(self.thread_info_padding,
                                       current_thread_len)
        return thread_info.ljust(self.thread_info_padding)

    def trace(self, frame, event, arg):

        ### Checking whether we should trace this line: #######################
        #                                                                     #
        # We should trace this line either if it's in the decorated function,
        # or the user asked to go a few levels deeper and we're within that
        # number of levels deeper.

        if not (frame.f_code in self.target_codes or frame in self.target_frames):
            if self.depth == 1:
                # We did the most common and quickest check above, because the
                # trace function runs so incredibly often, therefore it's
                # crucial to hyper-optimize it for the common case.
                return None
            elif self._is_internal_frame(frame):
                return None
            else:
                _frame_candidate = frame
                for i in range(1, self.depth):
                    _frame_candidate = _frame_candidate.f_back
                    if _frame_candidate is None:
                        return None
                    elif _frame_candidate.f_code in self.target_codes or _frame_candidate in self.target_frames:
                        break
                else:
                    return None

        thread_global.__dict__.setdefault('depth', -1)
        if event == 'call':
            thread_global.depth += 1
        indent = ' ' * 4 * thread_global.depth

        #                                                                     #
        ### Finished checking whether we should trace this line. ##############

        now = datetime_module.datetime.now().time()
        now_string = pycompat.time_isoformat(now, timespec='microseconds')
        line_no = frame.f_lineno
        source_path, source = get_path_and_source_from_frame(frame)
        if self.last_source_path != source_path:
            self.write(u'\033[0;35m{indent}跳转到文件。。。 {source_path}\033[0m'.
                       format(**locals()))
            self.last_source_path = source_path
        source_line = source[line_no - 1]
        thread_info = ""
        if self.thread_info:
            current_thread = threading.current_thread()
            thread_info = "{ident}-{name} ".format(
                ident=current_thread.ident, name=current_thread.getName())
        thread_info = self.set_thread_info_padding(thread_info)

        ### Reporting newish and modified variables: ##########################
        #                                                                     #
        old_local_reprs = self.frame_to_local_reprs.get(frame, {})
        self.frame_to_local_reprs[frame] = local_reprs = \
                                       get_local_reprs(frame,
                                                       watch=self.watch, custom_repr=self.custom_repr,
                                                       max_length=self.max_variable_length)

        newish_string = ('开始变量：。。。 ' if event == 'call' else
                                                            '新变量：。。。 ')

        for name, value_repr in local_reprs.items():
            if name not in old_local_reprs:
                self.write('\033[0;34m{indent}{newish_string}{name} = {value_repr}\033[0m'.format(
                                                                       **locals()))
            elif old_local_reprs[name] != value_repr:
                self.write('\033[0;33m{indent}修改变量：。。。 {name} = {value_repr}\033[0m'.format(
                                                                   **locals()))

        #                                                                     #
        ### Finished newish and modified variables. ###########################


        ### Dealing with misplaced function definition: #######################
        #                                                                     #
        if event == 'call' and source_line.lstrip().startswith('@'):
            # If a function decorator is found, skip lines until an actual
            # function definition is found.
            for candidate_line_no in itertools.count(line_no):
                try:
                    candidate_source_line = source[candidate_line_no - 1]
                except IndexError:
                    # End of source file reached without finding a function
                    # definition. Fall back to original source line.
                    break

                if candidate_source_line.lstrip().startswith('def'):
                    # Found the def line!
                    line_no = candidate_line_no
                    source_line = candidate_source_line
                    break
        #                                                                     #
        ### Finished dealing with misplaced function definition. ##############

        # If a call ends due to an exception, we still get a 'return' event
        # with arg = None. This seems to be the only way to tell the difference
        # https://stackoverflow.com/a/12800909/2482744
        code_byte = frame.f_code.co_code[frame.f_lasti]
        if not isinstance(code_byte, int):
            code_byte = ord(code_byte)
        ended_by_exception = (
                event == 'return'
                and arg is None
                and (opcode.opname[code_byte]
                     not in ('RETURN_VALUE', 'YIELD_VALUE'))
        )

        if ended_by_exception:
            self.write('\033[0;31m{indent}调用结束被异常\033[0m'.
                       format(**locals()))
        else:
            """
            \033[0;94m{"".join(args)}\033[0m
            """
            self.total_run_line +=1
            # self.write('{indent}{now_string} {event:9} '
            #            '{frame.f_lineno:4} {source_line}'.format(**locals()))

            # REMIND 这里改了，改成能显示运行轨迹可点击。
            # utils.nb_print(locals())
            # utils.nb_print(source_line)
            file_name_and_line = f'{frame.f_code.co_filename}:{frame.f_lineno}'

            file_name_and_line2 = f'"{file_name_and_line}"'
            event_map = {
                'call':'调用',
                'line':'代码行',
                'return': '返回',
                'exception':'异常',
            }
            event_cn = event_map.get(event,event)

            self.write(u'\033[0;32m{indent}{now_string} {thread_info} {event_cn:9} {file_name_and_line2:100} {source_line}\033[0m'.format(**locals()))

        if event == 'return':
            del self.frame_to_local_reprs[frame]
            thread_global.depth -= 1

            if not ended_by_exception:
                return_value_repr = utils.get_shortish_repr(arg,
                                                            custom_repr=self.custom_repr,
                                                            max_length=self.max_variable_length)
                self.write('\033[0;36m{indent}返回值：。。。 {return_value_repr}\033[0m'.
                           format(**locals()))

        if event == 'exception':
            exception = '\n'.join(traceback.format_exception_only(*arg[:2])).strip()
            if self.max_variable_length:
                exception = utils.truncate(exception, self.max_variable_length)
            self.write('\033[0;31m{indent}{exception}\033[0m'.
                       format(**locals()))

        return self.trace

```

### 代码文件: funboost\utils\pysnooper_ydf\utils.py
```python
# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import abc
import time
import sys
from .pycompat import ABC, string_types, collections_abc

def _check_methods(C, *methods):
    mro = C.__mro__
    for method in methods:
        for B in mro:
            if method in B.__dict__:
                if B.__dict__[method] is None:
                    return NotImplemented
                break
        else:
            return NotImplemented
    return True


class WritableStream(ABC):
    @abc.abstractmethod
    def write(self, s):
        pass

    @classmethod
    def __subclasshook__(cls, C):
        if cls is WritableStream:
            return _check_methods(C, 'write')
        return NotImplemented



file_reading_errors = (
    IOError,
    OSError,
    ValueError # IronPython weirdness.
)



def shitcode(s):
    return ''.join(
        (c if (0 < ord(c) < 256) else '?') for c in s
    )


def get_repr_function(item, custom_repr):
    for condition, action in custom_repr:
        if isinstance(condition, type):
            condition = lambda x, y=condition: isinstance(x, y)
        if condition(item):
            return action
    return repr


def get_shortish_repr(item, custom_repr=(), max_length=None):
    repr_function = get_repr_function(item, custom_repr)
    try:
        r = repr_function(item)
    except BaseException :
        r = 'REPR FAILED'
    r = r.replace('\r', '').replace('\n', '')
    if max_length:
        r = truncate(r, max_length)
    return r


def truncate(string, max_length):
    if (max_length is None) or (len(string) <= max_length):
        return string
    else:
        left = (max_length - 3) // 2
        right = max_length - 3 - left
        return u'{}...{}'.format(string[:left], string[-right:])


def ensure_tuple(x):
    if isinstance(x, collections_abc.Iterable) and \
                                               not isinstance(x, string_types):
        return tuple(x)
    else:
        return (x,)


def nb_print( *args, sep=' ', end='\n', file=None):
    """
    超流弊的print补丁
    :param x:
    :return:
    """
    # 获取被调用函数在被调用时所处代码行数
    line = sys._getframe().f_back.f_lineno
    # 获取被调用函数所在模块文件名
    file_name = sys._getframe(1).f_code.co_filename
    # sys.stdout.write(f'"{__file__}:{sys._getframe().f_lineno}"    {x}\n')
    args = (str(arg) for arg in args)  # REMIND 防止是数字不能被join
    sys.stdout.write(f'"{file_name}:{line}"  {time.strftime("%H:%M:%S")}  \033[0;94m{"".join(args)}\033[0m\n')
    sys.stdout.flush()# 36  93 96 94


```

### 代码文件: funboost\utils\pysnooper_ydf\variables.py
```python
import itertools
import abc
try:
    from collections.abc import Mapping, Sequence
except ImportError:
    from collections import Mapping, Sequence
from copy import deepcopy

from . import utils
from . import pycompat


def needs_parentheses(source):
    def code(s):
        return compile(s, '<variable>', 'eval').co_code

    return code('{}.x'.format(source)) != code('({}).x'.format(source))


class BaseVariable(pycompat.ABC):
    def __init__(self, source, exclude=()):
        self.source = source
        self.exclude = utils.ensure_tuple(exclude)
        self.code = compile(source, '<variable>', 'eval')
        if needs_parentheses(source):
            self.unambiguous_source = '({})'.format(source)
        else:
            self.unambiguous_source = source

    def items(self, frame):
        try:
            main_value = eval(self.code, frame.f_globals or {}, frame.f_locals)
        except BaseException :
            return ()
        return self._items(main_value)

    @abc.abstractmethod
    def _items(self, key):
        raise NotImplementedError

    @property
    def _fingerprint(self):
        return (type(self), self.source, self.exclude)

    def __hash__(self):
        return hash(self._fingerprint)

    def __eq__(self, other):
        return (isinstance(other, BaseVariable) and
                                       self._fingerprint == other._fingerprint)


class CommonVariable(BaseVariable):
    def _items(self, main_value):
        result = [(self.source, utils.get_shortish_repr(main_value))]
        for key in self._safe_keys(main_value):
            try:
                if key in self.exclude:
                    continue
                value = self._get_value(main_value, key)
            except BaseException :
                continue
            result.append((
                '{}{}'.format(self.unambiguous_source, self._format_key(key)),
                utils.get_shortish_repr(value)
            ))
        return result

    def _safe_keys(self, main_value):
        try:
            for key in self._keys(main_value):
                yield key
        except BaseException :
            pass

    def _keys(self, main_value):
        return ()

    def _format_key(self, key):
        raise NotImplementedError

    def _get_value(self, main_value, key):
        raise NotImplementedError


class Attrs(CommonVariable):
    def _keys(self, main_value):
        return itertools.chain(
            getattr(main_value, '__dict__', ()),
            getattr(main_value, '__slots__', ())
        )

    def _format_key(self, key):
        return '.' + key

    def _get_value(self, main_value, key):
        return getattr(main_value, key)


class Keys(CommonVariable):
    def _keys(self, main_value):
        return main_value.keys()

    def _format_key(self, key):
        return '[{}]'.format(utils.get_shortish_repr(key))

    def _get_value(self, main_value, key):
        return main_value[key]


class Indices(Keys):
    _slice = slice(None)

    def _keys(self, main_value):
        return range(len(main_value))[self._slice]

    def __getitem__(self, item):
        assert isinstance(item, slice)
        result = deepcopy(self)
        result._slice = item
        return result


class Exploding(BaseVariable):
    def _items(self, main_value):
        if isinstance(main_value, Mapping):
            cls = Keys
        elif isinstance(main_value, Sequence):
            cls = Indices
        else:
            cls = Attrs

        return cls(self.source, self.exclude)._items(main_value)

```

### 代码文件: funboost\utils\pysnooper_ydf\__init__.py
```python
# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.
'''

基于最新的改版的pysnooper，修改成彩色可点击。
PySnooper - Never use print for debugging again

Usage:

    import pysnooper

    @pysnooper.snoop()
    def your_function(x):
        ...

A log will be written to stderr showing the lines executed and variables
changed in the decorated function.

For more information, see https://github.com/cool-RR/PySnooper
'''

from .tracer import Tracer as snoop
from .variables import Attrs, Exploding, Indices, Keys
import collections

__VersionInfo = collections.namedtuple('VersionInfo',
                                       ('major', 'minor', 'micro'))

__version__ = '0.2.8'
__version_info__ = __VersionInfo(*(map(int, __version__.split('.'))))

del collections, __VersionInfo # Avoid polluting the namespace

```

### 代码文件: funboost\utils\times\version.py
```python
VERSION = '0.7'

```

### 代码文件: funboost\utils\times\__init__.py
```python
import datetime
import sys

import arrow

from .version import VERSION

PY3 = sys.version_info[0] == 3
if PY3:
    string_types = str
else:
    string_types = basestring


__author__ = 'Vincent Driessen <vincent@3rdcloud.com>'
__version__ = VERSION


def to_universal(local_dt, timezone=None):
    """
    Converts the given local datetime or UNIX timestamp to a universal
    datetime.
    """
    if isinstance(local_dt, (int, float)):
        if timezone is not None:
            raise ValueError('Timezone argument illegal when using UNIX timestamps.')
        return from_unix(local_dt)
    elif isinstance(local_dt, string_types):
        local_dt = arrow.get(local_dt).to('UTC').naive

    return from_local(local_dt, timezone)


def from_local(local_dt, timezone=None):
    """Converts the given local datetime to a universal datetime."""
    if not isinstance(local_dt, datetime.datetime):
        raise TypeError('Expected a datetime object')

    if timezone is None:
        a = arrow.get(local_dt)
    else:
        a = arrow.get(local_dt, timezone)
    return a.to('UTC').naive


def from_unix(ut):
    """
    Converts a UNIX timestamp, as returned by `time.time()`, to universal
    time.  Assumes the input is in UTC, as `time.time()` does.
    """
    if not isinstance(ut, (int, float)):
        raise TypeError('Expected an int or float value')

    return arrow.get(ut).naive


def to_local(dt, timezone):
    """Converts universal datetime to a local representation in given timezone."""
    if dt.tzinfo is not None:
        raise ValueError(
            'First argument to to_local() should be a universal time.'
        )
    if not isinstance(timezone, string_types):
        raise TypeError('expected a timezone name (string), but got {} instead'.format(type(timezone)))
    return arrow.get(dt).to(timezone).datetime


def to_unix(dt):
    """Converts a datetime object to unixtime"""
    if not isinstance(dt, datetime.datetime):
        raise TypeError('Expected a datetime object')

    return arrow.get(dt).timestamp


def format(dt, timezone, fmt=None):
    """Formats the given universal time for display in the given time zone."""
    local = to_local(dt, timezone)
    if fmt is None:
        return local.isoformat()
    else:
        return local.strftime(fmt)


now = datetime.datetime.utcnow

```

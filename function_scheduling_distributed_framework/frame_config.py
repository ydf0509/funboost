# -*- coding: utf-8 -*-

from function_scheduling_distributed_framework.constant import BrokerEnum

'''
你项目根目录下自动生成的 distributed_frame_config.py 文件中修改配置，会被自动读取到。
此文件按需修改，例如你使用redis中间件作为消息队列，可以不用管rabbitmq的配置。

框架使用文档是 https://function-scheduling-distributed-framework.readthedocs.io/zh_CN/latest/

'''

# 如果@task_deco装饰器没有亲自指定broker_kind入参，则默认使用DEFAULT_BROKER_KIND这个中间件。
# 强烈推荐安装rabbitmq然后使用 BrokerEnum.RABBITMQ_AMQPSTORM 这个中间件,
# 次之 BrokerEnum.REDIS_ACK_ABLE中间件，kafka则推荐 BrokerEnum.CONFLUENT_KAFKA。
# BrokerEnum.PERSISTQUEUE 的优点是基于单机磁盘的消息持久化，不需要安装消息中间件软件就能使用，但不是跨机器的真分布式。
DEFAULT_BROKER_KIND = BrokerEnum.PERSISTQUEUE

MONGO_CONNECT_URL = f'mongodb://myUserAdmin:8mwTdy1klnSYepNo@{"192.168.199.202"}:27016/admin'

RABBITMQ_USER = 'rabbitmq_user'
RABBITMQ_PASS = 'rabbitmq_pass'
RABBITMQ_HOST = '127.0.0.1'
RABBITMQ_PORT = 5672
RABBITMQ_VIRTUAL_HOST = 'rabbitmq_virtual_host'

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

ROCKETMQ_NAMESRV_ADDR = '192.168.199.202:9876'

MQTT_HOST = '127.0.0.1'
MQTT_TCP_PORT = 1883

HTTPSQS_HOST = '127.0.0.1'
HTTPSQS_PORT = '1218'
HTTPSQS_AUTH = '123456'

KOMBU_URL = 'redis://127.0.0.1:6379/0'
# KOMBU_URL =  'sqla+sqlite:////dssf_kombu_sqlite.sqlite'  # 4个//// 代表磁盘根目录下生成一个文件。推荐绝对路径。3个///是相对路径。


# nb_log包的第几个日志模板，内置了7个模板，可以在你当前项目根目录下的nb_log_config.py文件扩展模板。
NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER = 11  # 7是简短的不可跳转，5是可点击跳转的，11是可显示ip 进程 线程的模板。
FSDF_DEVELOP_LOG_LEVEL = 50  # 开发时候的日志，仅供我自己用，所以日志级别跳到最高，用户不需要管。

TIMEZONE = 'Asia/Shanghai'

# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 9:51


# 你项目根目录下自动生成的 distributed_frame_config.py 文件种修改配置，会被自动读取到。

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

SQLLITE_QUEUES_PATH = '/sqllite_queues'

ROCKETMQ_NAMESRV_ADDR = '192.168.199.202:9876'

KOMBU_URL = 'redis://127.0.0.1:6379/0'
# KOMBU_URL = 'sqla+sqlite:////celery_sqlite3.sqlite'  # 4个//// 代表磁盘根目录下生成一个文件。推荐绝对路径。3个///是相对路径。

# nb_log包的第几个日志模板，内置了7个模板，可以在你当前项目根目录下的nb_log_config.py文件扩展模板。
NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER = 7  # 7是简短的不可跳转，5是可点击跳转的
FSDF_DEVELOP_LOG_LEVEL = 50  # 开发时候的日志，仅供自己用，所以日志级别跳到最高

TIMEZONE = 'Asia/Shanghai'

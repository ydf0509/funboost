# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 9:51


# 你需要使用patch_frame_config函数打猴子补丁的方式修改这里的配置就可以了，很简单。最好不要去改框架源码这里，但也可以改这里。

MONGO_CONNECT_URL = f'mongodb://yourname:yourpassword@127.0.01:27017/admin'

RABBITMQ_USER = 'rabbitmq_user'
RABBITMQ_PASS = 'rabbitmq_pass'
RABBITMQ_HOST = '127.0.0.1'
RABBITMQ_PORT = 5672
RABBITMQ_VIRTUAL_HOST = 'rabbitmq_virtual_host'

REDIS_HOST = '127.0.0.1'
REDIS_PASSWORD = 'redis_password'
REDIS_PORT = 6379
REDIS_DB = 7

NSQD_TCP_ADDRESSES = ['127.0.0.1:4150']
NSQD_HTTP_CLIENT_HOST = '127.0.0.1'
NSQD_HTTP_CLIENT_PORT = 4151

KAFKA_BOOTSTRAP_SERVERS = ['127.0.0.1:9092']

SQLACHEMY_ENGINE_URL ='sqlite:////sqlachemy_queues/queues.db'

# nb_log包的第几个日志模板，内置了7个模板，可以在你当前项目根目录下的nb_log_config.py文件扩展模板。
NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER = 7
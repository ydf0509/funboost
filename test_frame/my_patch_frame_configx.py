# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:50

from function_scheduling_distributed_framework import patch_frame_config, show_frame_config



def do_patch_frame_config():
    patch_frame_config(MONGO_CONNECT_URL='mongodb://myUserAdminxx:xxxx@xx.90.89.xx:27016/admin',

                       RABBITMQ_USER='silxxxx',
                       RABBITMQ_PASS='Fr3Mxxxxx',
                       RABBITMQ_HOST='1xx.90.89.xx',
                       RABBITMQ_PORT=5672,
                       RABBITMQ_VIRTUAL_HOST='test_host',

                       REDIS_HOST='1xx.90.89.xx',
                       REDIS_PASSWORD='yxxxxxxR',
                       REDIS_PORT=6543,
                       REDIS_DB=7,

                       NSQD_TCP_ADDRESSES=['xx.112.34.56:4150'],
                       NSQD_HTTP_CLIENT_HOST='12.34.56.78',
                       NSQD_HTTP_CLIENT_PORT=4151,

                       KAFKA_BOOTSTRAP_SERVERS=['12.34.56.78:9092'],

                       # SQLACHEMY_ENGINE_URL='mysql+pymysql://root:123456@127.0.0.1:3306/sqlachemy_queues?charset=utf8',
                       SQLACHEMY_ENGINE_URL='sqlite:////sqlachemy_queues/queues.db'
                       )

    show_frame_config()



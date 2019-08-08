# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:50

from function_scheduling_distributed_framework import patch_frame_config,show_frame_config


def do_patch_frame_config():
    patch_frame_config(MONGO_CONNECT_URL='mongodb://myUserAdmin:8mwTdy1klnSYepNo@112.90.89.16:27016/admin',

                       RABBITMQ_USER='silktest',
                       RABBITMQ_PASS='Fr3M3j@lXZLF*iMB',
                       RABBITMQ_HOST='112.90.89.16',
                       RABBITMQ_PORT=5672,
                       RABBITMQ_VIRTUAL_HOST='crawlers_host',

                       REDIS_HOST='112.90.89.16',
                       REDIS_PASSWORD='yMxsueZD9yx0AkfR',
                       REDIS_PORT=6543,
                       REDIS_DB=7, )

    show_frame_config()
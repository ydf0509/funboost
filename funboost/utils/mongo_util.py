# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/9/17 0017 15:26
import os
import pymongo
from funboost import funboost_config_deafult
from funboost.utils import decorators


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
        return pymongo.MongoClient(funboost_config_deafult.MONGO_CONNECT_URL, connect=False)  # connect等于False原因见注释

    @property
    @decorators.cached_method_result
    def mongo_db_task_status(self):
        return self.mongo_client.get_database('task_status')


class MongoMixin:
    """
    mixin类被继承，也可以直接实例化。

    这个是修改后的，当使用f.multi_process_connsume() + linux +  保存结果到mongo + pymongo.0.2 时候不再报错了。
    """
    processid__client_map = {}
    processid__db_map = {}

    @property
    def mongo_client(self):
        pid = os.getpid()
        if pid not in MongoMixin.processid__client_map:
            MongoMixin.processid__client_map[pid] = pymongo.MongoClient(funboost_config_deafult.MONGO_CONNECT_URL, connect=False)
        return MongoMixin.processid__client_map[pid]

    @property
    def mongo_db_task_status(self):
        pid = os.getpid()
        if pid not in MongoMixin.processid__db_map:
            MongoMixin.processid__db_map[pid] = self.mongo_client.get_database('task_status')
        return MongoMixin.processid__db_map[pid]


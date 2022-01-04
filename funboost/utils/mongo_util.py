# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/9/17 0017 15:26
import pymongo
from funboost import funboost_config_deafult
from funboost.utils import decorators


class MongoMixin:
    """
    mixin类被继承，也可以直接实例化。
    """
    @property
    @decorators.cached_method_result
    def mongo_client(self):
        return pymongo.MongoClient(funboost_config_deafult.MONGO_CONNECT_URL, connect=False)  # connect等于False原因见注释

    @property
    @decorators.cached_method_result
    def mongo_db_task_status(self):
        return self.mongo_client.get_database('task_status')


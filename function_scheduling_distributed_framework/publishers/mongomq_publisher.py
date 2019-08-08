# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 12:23
import json

import pymongo
from mongomq import MongoQueue

from function_scheduling_distributed_framework import frame_config
from function_scheduling_distributed_framework.publishers.base_publisher import AbstractPublisher
from function_scheduling_distributed_framework.utils import decorators, time_util


class MongoMixin:
    """
    mixin类被继承，也可以直接实例化。
    """

    @property
    @decorators.cached_method_result
    def mongo_client(self):
        mongo_var = pymongo.MongoClient(frame_config.MONGO_CONNECT_URL, connect=False)  # connect等于False原因见注释
        return mongo_var


class MongoMqPublisher(AbstractPublisher, MongoMixin):
    # 使用mongo-queue包实现的基于mongodb的队列。 队列是一个col，自动存放在consume_queues库中。
    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self.queue = MongoQueue(
            self.mongo_client.get_database('consume_queues').get_collection(self._queue_name),
            consumer_id=f"consumer-{time_util.DatetimeConverter().datetime_str}",
            timeout=600,
            max_attempts=3,
            ttl=0)

    def concrete_realization_of_publish(self, msg):
        # noinspection PyTypeChecker
        self.queue.put(json.loads(msg))

    def clear(self):
        self.queue.clear()
        self.logger.warning(f'清除 mongo队列 {self._queue_name} 中的消息成功')

    def get_message_count(self):
        return self.queue.size()

    def close(self):
        pass

# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 12:23
import json
from funboost.utils.dependency_packages.mongomq import MongoQueue
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.utils import time_util
from funboost.utils.mongo_util import MongoMixin


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

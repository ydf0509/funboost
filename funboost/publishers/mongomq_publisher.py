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

# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/8 0008 12:12
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.publishers.redis_queue_flush import FlushRedisQueueMixin
from funboost.utils import RedisMixin


class RedisPublisher(FlushRedisQueueMixin, AbstractPublisher, RedisMixin, ):
    """
    使用redis作为中间件
    """

    def concrete_realization_of_publish(self, msg):
        self.redis_db_frame.rpush(self._queue_name, msg)

    def get_message_count(self):
        # nb_print(self.redis_db7,self._queue_name)
        return self.redis_db_frame.llen(self._queue_name)

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass

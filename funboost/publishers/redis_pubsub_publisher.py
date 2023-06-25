# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.utils import RedisMixin


class RedisPubSubPublisher(AbstractPublisher, RedisMixin, ):
    """
    使用redis作为中间件
    """

    def concrete_realization_of_publish(self, msg):
        self.redis_db_frame.publish(self._queue_name, msg)

    def clear(self):
        self.redis_db_frame.delete(self._queue_name)
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    def get_message_count(self):
        return -1

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass

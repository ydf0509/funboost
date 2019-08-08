# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 12:12
from function_scheduling_distributed_framework.publishers.base_publisher import AbstractPublisher
from function_scheduling_distributed_framework.utils import RedisMixin


class RedisPublisher(AbstractPublisher, RedisMixin):
    """
    使用redis作为中间件
    """

    def concrete_realization_of_publish(self, msg):
        # noinspection PyTypeChecker
        self.redis_db7.rpush(self._queue_name, msg)

    def clear(self):
        self.redis_db7.delete(self._queue_name)
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    def get_message_count(self):
        # nb_print(self.redis_db7,self._queue_name)
        return self.redis_db7.llen(self._queue_name)

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass

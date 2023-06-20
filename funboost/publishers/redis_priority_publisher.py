# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import os
import time
# noinspection PyUnresolvedReferences
from queue import Queue, Empty
from threading import Lock

from funboost import funboost_config_deafult
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.publishers.redis_publisher_simple import RedisPublisher
from funboost.utils import RedisMixin, decorators


class RedisPriorityPublisher(RedisPublisher):
    def custom_init(self):
        queue_list = [self._queue_name]
        x_max_priority = self.broker_exclusive_config['x-max-priority']
        if x_max_priority:
            for i in range(1, x_max_priority + 1):
                queue_list.append(f'{self.queue_name}:{i}')
        queue_list.sort(reverse=True)
        self.queue_list = queue_list

    def build_queue_name_by_msg(self, msg):
        priority = self._get_from_other_extra_params('priroty', msg)
        x_max_priority = self.broker_exclusive_config['x-max-priority']
        queue_name = self.queue_name
        if x_max_priority and priority is not None:
            priority = min(priority, x_max_priority)
            queue_name = f'{self.queue_name}:{priority}'
        return queue_name

    def concrete_realization_of_publish(self, msg):
        queue_name = self.build_queue_name_by_msg(msg)
        self.logger.debug([queue_name,msg])
        self.redis_db_frame.rpush(queue_name, msg)

    def clear(self):
        self.redis_db_frame.delete(*self.queue_list)
        self.redis_db_frame.delete(f'{self._queue_name}__unack')
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    def get_message_count(self):
        count = 0
        for queue_name in self.queue_list:
            count += self.redis_db_frame.llen(queue_name)
        return count

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass

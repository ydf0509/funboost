# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12

from funboost.publishers.base_publisher import AbstractPublisher
from funboost.publishers.redis_queue_flush_mixin import FlushRedisQueueMixin
from funboost.utils.redis_manager import RedisMixin


class RedisPriorityPublisher(FlushRedisQueueMixin,AbstractPublisher, RedisMixin,):
    """
    redis队列，支持任务优先级。
    """

    def custom_init(self):
        queue_list = [self._queue_name]
        x_max_priority = self.publisher_params.broker_exclusive_config['x-max-priority']
        if x_max_priority:
            for i in range(1, x_max_priority + 1):
                queue_list.append(f'{self.queue_name}:{i}')
        queue_list.sort(reverse=True)
        self.queue_list = queue_list

    def build_queue_name_by_msg(self, msg):
        """
        根据消息的other_extra_params的 priority ，自动生成子队列名。例如 queue_name:1   queue_name:2  queue_name:3 queue_name:4
        :param msg:
        :return:
        """
        priority = self._get_from_other_extra_params('priroty', msg)
        x_max_priority = self.publisher_params.broker_exclusive_config['x-max-priority']
        queue_name = self.queue_name
        if x_max_priority and priority:
            priority = min(priority, x_max_priority)  # 防止有傻瓜发布消息的优先级priroty比最大支持的优先级还高。
            queue_name = f'{self.queue_name}:{priority}'
        return queue_name

    def concrete_realization_of_publish(self, msg):
        queue_name = self.build_queue_name_by_msg(msg)
        # self.logger.debug([queue_name, msg])
        self.redis_db_frame.rpush(queue_name, msg)


    def get_message_count(self):
        count = 0
        for queue_name in self.queue_list:
            count += self.redis_db_frame.llen(queue_name)
        return count

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass

    def clear(self):
        self.logger.warning(f'清除 {self.queue_list} 中的消息')
        self.redis_db_frame.delete(*self.queue_list)
        FlushRedisQueueMixin.clear(self)

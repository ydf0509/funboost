# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2020/7/9 0008 12:12
from rocketmq.client import Producer, Message

from function_scheduling_distributed_framework import frame_config
from function_scheduling_distributed_framework.publishers.base_publisher import AbstractPublisher


class KafkaPublisher(AbstractPublisher, ):
    def custom_init(self):
        producer = Producer(f'g-{self._queue_name}')
        producer.set_namesrv_addr(frame_config.ROCKETMQ_NAMESRV_ADDR)
        producer.start()
        self._producer = producer

    def concrete_realization_of_publish(self, msg):
        self._producer.send_sync(msg)

    def clear(self):
        self.logger.error('python版的rocket包太弱了，没有方法设置偏移量或者删除主题。')

    def get_message_count(self):
        self.logger.warning('python版的rocket包太弱了，没找到方法，，java才能做到。')
        return 0

    def close(self):
        self._producer.shutdown()

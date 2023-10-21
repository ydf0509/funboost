'''

import pulsar

client = pulsar.Client('pulsar://localhost:6650')

producer = client.create_producer('my-topic36')

for i in range(10):
    producer.send(('Hello-%d' % i).encode('utf-8'))

client.close()

'''

# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import os

from pulsar.schema import schema

from funboost.publishers.base_publisher import AbstractPublisher
from funboost.funboost_config_deafult import BrokerConnConfig


class PulsarPublisher(AbstractPublisher, ):
    """
    使用pulsar作为中间件
    """

    def custom_init(self):
        import pulsar
        self._client = pulsar.Client(BrokerConnConfig.PULSAR_URL, )
        self._producer = self._client.create_producer(self._queue_name, schema=schema.StringSchema(), producer_name=f'funboost_publisher_{os.getpid()}')

    def concrete_realization_of_publish(self, msg):
        self._producer.send(msg)

    def clear(self):
        """用户换个 subscription_name 就可以重新消费了，不需要清空消息"""
        pass


    def get_message_count(self):
        return -1

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        self._client.close()

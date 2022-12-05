


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
from funboost.publishers.base_publisher import AbstractPublisher
from  funboost import funboost_config_deafult


class PulsarPublisher(AbstractPublisher, ):
    """
    使用pulsar作为中间件
    """
    def custom_init(self):
        import pulsar
        self._client = pulsar.Client(funboost_config_deafult.PULSAR_URL)
        self._producer = self._client.create_producer(self._queue_name)

    def concrete_realization_of_publish(self, msg):
        self._producer.send(msg.encode('utf-8'))

    def clear(self):
        pass

    def get_message_count(self):
        # nb_print(self.redis_db7,self._queue_name)
        return -1

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        self._client.close()

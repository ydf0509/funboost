


'''

import pulsar

client = pulsar.Client('pulsar://localhost:6650')
consumer = client.subscribe('my-topic',
                            subscription_name='my-sub')

while True:
    msg = consumer.receive()
    print("Received message: '%s'" % msg.data())
    consumer.acknowledge(msg)

client.close()
'''

# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json
from funboost.consumers.base_consumer import AbstractConsumer
from  funboost import funboost_config_deafult


class PulsarConsumer(AbstractConsumer, ):
    """
    pulsar作为中间件实现的。
    """
    BROKER_KIND = 20
    BROKER_EXCLUSIVE_CONFIG_KEYS = ['subscription_name']
    SUBSCRIPTION_NAME = 'funboost_subc'

    def custom_init(self):
        try:
            import pulsar  # 需要用户自己 pip install pulsar-client ，目前20221206只支持linux安装此python包。
        except ImportError:
            raise ImportError('需要用户自己 pip install pulsar-client ，目前20221206只支持linux安装此python包,win不支持。')
        self._client = pulsar.Client(funboost_config_deafult.PULSAR_URL)
        self._consumer = self._client.subscribe(self._queue_name,
                                    subscription_name=self.SUBSCRIPTION_NAME)

    def _shedual_task(self):
        while True:
            msg = self._consumer.receive()
            if msg:
                self._print_message_get_from_broker('pulsar',msg.data())
                kw = {'body': json.loads(msg.data()),'msg':msg}
                self._submit_task(kw)

    def _confirm_consume(self, kw):
        self._consumer.acknowledge(kw['msg'])

    def _requeue(self, kw):
        self._consumer.negative_acknowledge(kw['msg'])




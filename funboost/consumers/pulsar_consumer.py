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
import os

import json
from _pulsar import ConsumerType
from pulsar.schema import schema
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.funboost_config_deafult import BrokerConnConfig


class PulsarConsumer(AbstractConsumer, ):
    """
    pulsar作为中间件实现的。
    """



    def custom_init(self):
        pass

    def _dispatch_task(self):
        try:
            import pulsar  # 需要用户自己 pip install pulsar-client ，目前20221206只支持linux安装此python包。
        except ImportError:
            raise ImportError('需要用户自己 pip install pulsar-client ，')
        self._client = pulsar.Client(BrokerConnConfig.PULSAR_URL, )

        consumer_type_map = {
            'Exclusive':ConsumerType.Exclusive,
            'Shared':ConsumerType.Shared,
            'Failover':ConsumerType.Failover,
            'KeyShared':ConsumerType.KeyShared,
        }
        consumer_type_obj = consumer_type_map[self.consumer_params.broker_exclusive_config['consumer_type']]
        self._consumer = self._client.subscribe(self._queue_name, schema=schema.StringSchema(), consumer_name=f'funboost_consumer_{os.getpid()}',
                                                subscription_name=self.consumer_params.broker_exclusive_config['subscription_name'],
                                                consumer_type=consumer_type_obj,
                                                replicate_subscription_state_enabled=self.consumer_params.broker_exclusive_config['replicate_subscription_state_enabled'])
        while True:
            msg = self._consumer.receive()
            if msg:
                kw = {'body': msg.data(), 'msg': msg}
                self._submit_task(kw)

    def _confirm_consume(self, kw):
        self._consumer.acknowledge(kw['msg'])

    def _requeue(self, kw):
        self._consumer.negative_acknowledge(kw['msg'])

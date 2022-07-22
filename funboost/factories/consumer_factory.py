# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:19
import copy
# from collections import Callable
from typing import Callable
from funboost.consumers.http_consumer import HTTPConsumer
from funboost.consumers.kafka_consumer import KafkaConsumer
from funboost.consumers.kafka_consumer_manually_commit import KafkaConsumerManuallyCommit
from funboost.consumers.kombu_consumer import KombuConsumer
from funboost.consumers.local_python_queue_consumer import LocalPythonQueueConsumer
from funboost.consumers.mongomq_consumer import MongoMqConsumer
from funboost.consumers.nats_consumer import NatsConsumer
from funboost.consumers.nsq_consumer import NsqConsumer
from funboost.consumers.peewee_conusmer import PeeweeConsumer
from funboost.consumers.persist_queue_consumer import PersistQueueConsumer
from funboost.consumers.rabbitmq_amqpstorm_consumer import RabbitmqConsumerAmqpStorm
from funboost.consumers.rabbitmq_pika_consumer import RabbitmqConsumer
from funboost.consumers.rabbitmq_rabbitpy_consumer import RabbitmqConsumerRabbitpy
from funboost.consumers.redis_brpoplpush_consumer import RedisBrpopLpushConsumer
from funboost.consumers.redis_consumer import RedisConsumer
from funboost.consumers.redis_consumer_ack_able import RedisConsumerAckAble
from funboost.consumers.rocketmq_consumer import RocketmqConsumer
from funboost.consumers.sqlachemy_consumer import SqlachemyConsumer
from funboost.consumers.redis_stream_consumer import RedisStreamConsumer
from funboost.consumers.tcp_consumer import TCPConsumer
from funboost.consumers.txt_file_consumer import TxtFileConsumer
from funboost.consumers.udp_consumer import UDPConsumer
from funboost.consumers.zeromq_consumer import ZeroMqConsumer
from funboost.consumers.mqtt_consumer import MqttConsumer
from funboost.consumers.httpsqs_consumer import HttpsqsConsumer

broker_kind__consumer_type_map = {
    0: RabbitmqConsumerAmqpStorm,
    1: RabbitmqConsumerRabbitpy,
    2: RedisConsumer,
    3: LocalPythonQueueConsumer,
    4: RabbitmqConsumer,
    5: MongoMqConsumer,
    6: PersistQueueConsumer,
    7: NsqConsumer,
    8: KafkaConsumer,
    9: RedisConsumerAckAble,
    10: SqlachemyConsumer,
    11: RocketmqConsumer,
    12: RedisStreamConsumer,
    13: ZeroMqConsumer,
    14: RedisBrpopLpushConsumer,
    15: KombuConsumer,
    16: KafkaConsumerManuallyCommit,
    17: MqttConsumer,
    18: HttpsqsConsumer,
    21: UDPConsumer,
    22: TCPConsumer,
    23: HTTPConsumer,
    24: NatsConsumer,
    25: TxtFileConsumer,
    26: PeeweeConsumer,
}


def get_consumer(*args, broker_kind: int = None, **kwargs):
    """
    :param args: 入参是AbstractConsumer的入参
    :param broker_kind:
    :param kwargs:
    :return:
    """

    if broker_kind not in broker_kind__consumer_type_map:
        raise ValueError(f'设置的中间件种类数字不正确,你设置的值是 {broker_kind} ')
    return broker_kind__consumer_type_map[broker_kind](*args, **kwargs)

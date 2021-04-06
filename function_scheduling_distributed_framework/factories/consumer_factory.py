# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:19
import copy
from collections import Callable

from function_scheduling_distributed_framework.consumers.base_consumer import FunctionResultStatusPersistanceConfig
from function_scheduling_distributed_framework.consumers.kafka_consumer import KafkaConsumer
from function_scheduling_distributed_framework.consumers.local_python_queue_consumer import LocalPythonQueueConsumer
from function_scheduling_distributed_framework.consumers.mongomq_consumer import MongoMqConsumer
from function_scheduling_distributed_framework.consumers.nsq_consumer import NsqConsumer
from function_scheduling_distributed_framework.consumers.persist_queue_consumer import PersistQueueConsumer
from function_scheduling_distributed_framework.consumers.rabbitmq_amqpstorm_consumer import RabbitmqConsumerAmqpStorm
from function_scheduling_distributed_framework.consumers.rabbitmq_pika_consumer import RabbitmqConsumer
from function_scheduling_distributed_framework.consumers.rabbitmq_rabbitpy_consumer import RabbitmqConsumerRabbitpy
from function_scheduling_distributed_framework.consumers.redis_consumer import RedisConsumer
from function_scheduling_distributed_framework.consumers.redis_consumer_ack_able import RedisConsumerAckAble
from function_scheduling_distributed_framework.consumers.rocketmq_consumer import RocketmqConsumer
from function_scheduling_distributed_framework.consumers.sqlachemy_consumer import SqlachemyConsumer
from function_scheduling_distributed_framework.consumers.redis_stream_consumer import RedisStreamConsumer
from function_scheduling_distributed_framework.consumers.zeromq_consumer import ZeroMqConsumer


def get_consumer(*args, broker_kind=0, **kwargs):
    """
    :param args: 入参是AbstractConsumer的入参
    :param broker_kind:
    :param kwargs:
    :return:
    """
    broker_kind__consumer_type_map = {
        0: RabbitmqConsumer,
        1: RabbitmqConsumerRabbitpy,
        2: RedisConsumer,
        3: LocalPythonQueueConsumer,
        4: RabbitmqConsumerAmqpStorm,
        5: MongoMqConsumer,
        6: PersistQueueConsumer,
        7: NsqConsumer,
        8: KafkaConsumer,
        9: RedisConsumerAckAble,
        10: SqlachemyConsumer,
        11: RocketmqConsumer,
        12: RedisStreamConsumer,
        13:ZeroMqConsumer,
    }
    if broker_kind not in broker_kind__consumer_type_map:
        raise ValueError(f'设置的中间件种类数字不正确,你设置的值是 {broker_kind} ')
    return broker_kind__consumer_type_map[broker_kind](*args, **kwargs)

# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:16
import copy
from typing import Callable

from funboost.publishers.confluent_kafka_publisher import ConfluentKafkaPublisher
from funboost.publishers.http_publisher import HTTPPublisher
from funboost.publishers.kombu_publisher import KombuPublisher
from funboost.publishers.nats_publisher import NatsPublisher
from funboost.publishers.peewee_publisher import PeeweePublisher
from funboost.publishers.redis_publisher_lpush import RedisPublisherLpush
from funboost.publishers.tcp_publisher import TCPPublisher
from funboost.publishers.txt_file_publisher import TxtFilePublisher
from funboost.publishers.udp_publisher import UDPPublisher
from funboost.publishers.zeromq_publisher import ZeroMqPublisher
from funboost.publishers.kafka_publisher import KafkaPublisher
from funboost.publishers.local_python_queue_publisher import LocalPythonQueuePublisher
from funboost.publishers.mongomq_publisher import MongoMqPublisher
from funboost.publishers.nsq_publisher import NsqPublisher
from funboost.publishers.persist_queue_publisher import PersistQueuePublisher
from funboost.publishers.rabbitmq_amqpstorm_publisher import RabbitmqPublisherUsingAmqpStorm
from funboost.publishers.rabbitmq_pika_publisher import RabbitmqPublisher
from funboost.publishers.rabbitmq_rabbitpy_publisher import RabbitmqPublisherUsingRabbitpy
from funboost.publishers.redis_publisher import RedisPublisher
from funboost.publishers.rocketmq_publisher import RocketmqPublisher
from funboost.publishers.sqla_queue_publisher import SqlachemyQueuePublisher
from funboost.publishers.redis_stream_publisher import RedisStreamPublisher
from funboost.publishers.mqtt_publisher import MqttPublisher
from funboost.publishers.httpsqs_publisher import HttpsqsPublisher

broker_kind__publisher_type_map = {
    0: RabbitmqPublisherUsingAmqpStorm,
    1: RabbitmqPublisherUsingRabbitpy,
    2: RedisPublisher,
    3: LocalPythonQueuePublisher,
    4: RabbitmqPublisher,
    5: MongoMqPublisher,
    6: PersistQueuePublisher,
    7: NsqPublisher,
    8: KafkaPublisher,
    9: RedisPublisher,
    10: SqlachemyQueuePublisher,
    11: RocketmqPublisher,
    12: RedisStreamPublisher,
    13: ZeroMqPublisher,
    14: RedisPublisherLpush,
    15: KombuPublisher,
    16: ConfluentKafkaPublisher,
    17: MqttPublisher,
    18: HttpsqsPublisher,
    21: UDPPublisher,
    22: TCPPublisher,
    23: HTTPPublisher,
    24: NatsPublisher,
    25: TxtFilePublisher,
    26: PeeweePublisher,
}


def get_publisher(queue_name, *, log_level_int=10, logger_prefix='', is_add_file_handler=True,
                  clear_queue_within_init=False, is_add_publish_time=True, consuming_function: Callable = None,
                  broker_kind: int = None,
                  broker_exclusive_config:dict=None,
                  ):
    """
    :param queue_name:
    :param log_level_int:
    :param logger_prefix:
    :param is_add_file_handler:
    :param clear_queue_within_init:
    :param is_add_publish_time:是否添加发布时间，以后废弃，都添加。
    :param consuming_function:消费函数，为了做发布时候的函数入参校验用的，如果不传则不做发布任务的校验，
               例如add 函数接收x，y入参，你推送{"x":1,"z":3}就是不正确的，函数不接受z参数。
    :param broker_kind: 中间件或使用包的种类。
    :param broker_exclusive_config 加上一个不同种类中间件非通用的配置,不同中间件自身独有的配置，不是所有中间件都兼容的配置，因为框架支持30种消息队列，消息队列不仅仅是一般的先进先出queue这么简单的概念，
           例如kafka支持消费者组，rabbitmq也支持各种独特概念例如各种ack机制 复杂路由机制，每一种消息队列都有独特的配置参数意义，可以通过这里传递。

    :return:
    """

    all_kwargs = copy.deepcopy(locals())
    all_kwargs.pop('broker_kind')
    if broker_kind not in broker_kind__publisher_type_map:
        raise ValueError(f'设置的中间件种类数字不正确,你设置的值是 {broker_kind} ')
    return broker_kind__publisher_type_map[broker_kind](**all_kwargs)

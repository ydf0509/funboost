# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:16
import copy
from typing import Callable

from function_scheduling_distributed_framework.publishers.kafka_publisher import KafkaPublisher
from function_scheduling_distributed_framework.publishers.local_python_queue_publisher import LocalPythonQueuePublisher
from function_scheduling_distributed_framework.publishers.mongomq_publisher import MongoMqPublisher
from function_scheduling_distributed_framework.publishers.nsq_publisher import NsqPublisher
from function_scheduling_distributed_framework.publishers.persist_queue_publisher import PersistQueuePublisher
from function_scheduling_distributed_framework.publishers.rabbitmq_amqpstorm_publisher import RabbitmqPublisherUsingAmqpStorm
from function_scheduling_distributed_framework.publishers.rabbitmq_pika_publisher import RabbitmqPublisher
from function_scheduling_distributed_framework.publishers.rabbitmq_rabbitpy_publisher import RabbitmqPublisherUsingRabbitpy
from function_scheduling_distributed_framework.publishers.redis_publisher import RedisPublisher
from function_scheduling_distributed_framework.publishers.rocketmq_publisher import RocketmqPublisher
from function_scheduling_distributed_framework.publishers.sqla_queue_publisher import SqlachemyQueuePublisher


def get_publisher(queue_name, *, log_level_int=10, logger_prefix='', is_add_file_handler=True,
                  clear_queue_within_init=False, is_add_publish_time=True, consuming_function: Callable = None,
                  broker_kind=0):
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
    :return:
    """
    all_kwargs = copy.deepcopy(locals())
    all_kwargs.pop('broker_kind')
    broker_kind__publisher_type_map = {
        0: RabbitmqPublisher,
        1: RabbitmqPublisherUsingRabbitpy,
        2: RedisPublisher,
        3: LocalPythonQueuePublisher,
        4: RabbitmqPublisherUsingAmqpStorm,
        5: MongoMqPublisher,
        6: PersistQueuePublisher,
        7: NsqPublisher,
        8: KafkaPublisher,
        9: RedisPublisher,
        10: SqlachemyQueuePublisher,
        11:RocketmqPublisher,
    }
    if broker_kind not in broker_kind__publisher_type_map:
        raise ValueError(f'设置的中间件种类数字不正确,你设置的值是 {broker_kind} ')
    return broker_kind__publisher_type_map[broker_kind](**all_kwargs)

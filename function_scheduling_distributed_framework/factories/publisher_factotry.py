# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:16
import copy

from function_scheduling_distributed_framework.publishers.local_python_queue_publisher import LocalPythonQueuePublisher
from function_scheduling_distributed_framework.publishers.mongomq_publisher import MongoMqPublisher
from function_scheduling_distributed_framework.publishers.persist_queue_publisher import PersistQueuePublisher
from function_scheduling_distributed_framework.publishers.rabbitmq_amqpstorm_publisher import RabbitmqPublisherUsingAmqpStorm
from function_scheduling_distributed_framework.publishers.rabbitmq_pika_publisher import RabbitmqPublisher
from function_scheduling_distributed_framework.publishers.rabbitmq_rabbitpy_publisher import RabbitmqPublisherUsingRabbitpy
from function_scheduling_distributed_framework.publishers.redis_publisher import RedisPublisher


def get_publisher(queue_name, *, log_level_int=10, logger_prefix='', is_add_file_handler=False, clear_queue_within_init=False, is_add_publish_time=False, broker_kind=0):
    """
    :param queue_name:
    :param log_level_int:
    :param logger_prefix:
    :param is_add_file_handler:
    :param clear_queue_within_init:
    :param is_add_publish_time:是否添加发布时间到中间件，如果设置了过期时间不为0，需要设为True
    :param broker_kind: 中间件或使用包的种类。
    :return:
    """
    all_kwargs = copy.deepcopy(locals())
    all_kwargs.pop('broker_kind')
    if broker_kind == 0:
        return RabbitmqPublisher(**all_kwargs)
    elif broker_kind == 1:
        return RabbitmqPublisherUsingRabbitpy(**all_kwargs)
    elif broker_kind == 2:
        return RedisPublisher(**all_kwargs)
    elif broker_kind == 3:
        return LocalPythonQueuePublisher(**all_kwargs)
    elif broker_kind == 4:
        return RabbitmqPublisherUsingAmqpStorm(**all_kwargs)
    elif broker_kind == 5:
        return MongoMqPublisher(**all_kwargs)
    elif broker_kind == 6:
        return PersistQueuePublisher(**all_kwargs)
    else:
        raise ValueError('设置的中间件种类数字不正确')

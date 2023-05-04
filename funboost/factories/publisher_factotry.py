# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:16
import copy

from typing import Callable
from funboost.publishers.base_publisher import AbstractPublisher


# broker_kind__publisher_type_map

def get_publisher(queue_name, *, log_level_int=10, logger_prefix='', is_add_file_handler=True,
                  clear_queue_within_init=False, is_add_publish_time=True, consuming_function: Callable = None,
                  broker_kind: int = None,
                  broker_exclusive_config: dict = None,
                  ) -> AbstractPublisher:
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
    from funboost.factories.broker_kind__publsiher_consumer_type_map import broker_kind__funboost_cls_map
    if broker_kind not in broker_kind__funboost_cls_map:
        raise ValueError(f'设置的中间件种类数字不正确,你设置的值是 {broker_kind} ')
    return broker_kind__funboost_cls_map[broker_kind][0](**all_kwargs)

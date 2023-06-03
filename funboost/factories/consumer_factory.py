# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:19


from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer


def get_consumer(*args, broker_kind: int = None, **kwargs) -> AbstractConsumer:
    """
    :param args: 入参是AbstractConsumer的入参
    :param broker_kind:
    :param kwargs:
    :return:
    """
    from funboost.factories.broker_kind__publsiher_consumer_type_map import broker_kind__publsiher_consumer_type_map, regist_to_funboost
    regist_to_funboost(broker_kind)  # 动态注册中间件到框架是为了延迟导入，用户没安装不需要的第三方包不报错。

    if broker_kind not in broker_kind__publsiher_consumer_type_map:
        raise ValueError(f'设置的中间件种类数字不正确,你设置的值是 {broker_kind} ')
    return broker_kind__publsiher_consumer_type_map[broker_kind][1](*args, **kwargs)

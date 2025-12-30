# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:19

import os
import threading
import typing
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.func_params_model import BoosterParams


def get_consumer(boost_params: BoosterParams) -> AbstractConsumer:
    """
    :param args: 入参是AbstractConsumer的入参
    :param broker_kind:
    :param kwargs:
    :return:
    """
    from funboost.factories.broker_kind__publsiher_consumer_type_map import broker_kind__publsiher_consumer_type_map, regist_to_funboost
    regist_to_funboost(boost_params.broker_kind)  # 动态注册中间件到框架是为了延迟导入，用户没安装不需要的第三方包不报错。

    if boost_params.broker_kind not in broker_kind__publsiher_consumer_type_map:
        raise ValueError(f'设置的中间件种类不正确,你设置的值是 {boost_params.broker_kind} ')
    consumer_cls = broker_kind__publsiher_consumer_type_map[boost_params.broker_kind][1]
    if not boost_params.consumer_override_cls:
        return consumer_cls(boost_params)
    else:
        ConsumerClsOverride = type(f'{consumer_cls.__name__}__{boost_params.consumer_override_cls.__name__}', (boost_params.consumer_override_cls, consumer_cls, AbstractConsumer), {})
        # class ConsumerClsOverride(boost_params.consumer_override_cls, consumer_cls, AbstractConsumer):
        #     pass

        return ConsumerClsOverride(boost_params)


class ConsumerCacheProxy:
    pid_registry_queue_name__consumer_map:typing.Dict[typing.Tuple[int,str,str],AbstractConsumer] = {}
    _lock = threading.Lock()

    def __init__(self,boost_params: BoosterParams):
        self.boost_params = boost_params

    @property
    def consumer(self) ->AbstractConsumer:
        pid = os.getpid()
        # 加入 booster_registry_name 作为命名空间隔离，支持不同 registry 使用相同的 queue_name 而不冲突
        key = (pid, self.boost_params.booster_registry_name, self.boost_params.queue_name)
        if key not in self.pid_registry_queue_name__consumer_map:
            with self._lock:
                if key not in self.pid_registry_queue_name__consumer_map:
                    self.pid_registry_queue_name__consumer_map[key] = get_consumer(self.boost_params)
        return self.pid_registry_queue_name__consumer_map[key]
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/8 0008 12:12
import copy
import json
import time
import typing
import uuid

from nameko.standalone.rpc import ClusterRpcProxy

from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher, PriorityConsumingControlConfig


def get_nameko_config():
    return {'AMQP_URI': f'amqp://{BrokerConnConfig.RABBITMQ_USER}:{BrokerConnConfig.RABBITMQ_PASS}@{BrokerConnConfig.RABBITMQ_HOST}:{BrokerConnConfig.RABBITMQ_PORT}/{BrokerConnConfig.RABBITMQ_VIRTUAL_HOST}'}


class NamekoPublisher(AbstractPublisher, ):
    """
    使用nameko作为中间件
    """

    def custom_init(self):
        self._rpc = ClusterRpcProxy(get_nameko_config())

    def publish(self, msg: typing.Union[str, dict], task_id=None,
                priority_control_config: PriorityConsumingControlConfig = None):
        msg, msg_function_kw, extra_params, task_id = self._convert_msg(msg, task_id, priority_control_config)
        t_start = time.time()
        with self._rpc as rpc:
            res = getattr(rpc, self.queue_name).call(**msg_function_kw)
        self.logger.debug(f'调用nameko的 {self.queue_name} service 的 call方法 耗时{round(time.time() - t_start, 4)}秒，入参  {msg_function_kw}')  # 显示msg太长了。
        return res

    def concrete_realization_of_publish(self, msg):
        pass

    def clear(self):
        self.logger.warning('還沒開始實現')

    def get_message_count(self):
        return -1

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass

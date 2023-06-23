# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/8 0008 12:12
import copy
import json
import time
import typing
import uuid

from nameko.standalone.rpc import ClusterRpcProxy

from funboost import funboost_config_deafult
from funboost.publishers.base_publisher import AbstractPublisher, PriorityConsumingControlConfig

NAMEKO_CONFIG = {'AMQP_URI': f'amqp://{funboost_config_deafult.RABBITMQ_USER}:{funboost_config_deafult.RABBITMQ_PASS}@{funboost_config_deafult.RABBITMQ_HOST}:{funboost_config_deafult.RABBITMQ_PORT}/{funboost_config_deafult.RABBITMQ_VIRTUAL_HOST}'}


class NamekoPublisher(AbstractPublisher, ):
    """
    使用nameko作为中间件
    """

    def custom_init(self):
        self._rpc = ClusterRpcProxy(NAMEKO_CONFIG)

    def publish(self, msg: typing.Union[str, dict], task_id=None,
                priority_control_config: PriorityConsumingControlConfig = None):
        msg, msg_function_kw, extra_params,task_id = self._convert_msg(msg, task_id, priority_control_config)
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

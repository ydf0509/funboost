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
        if isinstance(msg, str):
            msg = json.loads(msg)
        msg_function_kw = copy.copy(msg)
        if self.publish_params_checker:
            self.publish_params_checker.check_params(msg)
        task_id = task_id or f'{self._queue_name}_result:{uuid.uuid4()}'
        msg['extra'] = extra_params = {'task_id': task_id, 'publish_time': round(time.time(), 4),
                                       'publish_time_format': time.strftime('%Y-%m-%d %H:%M:%S')}
        if priority_control_config:
            extra_params.update(priority_control_config.to_dict())
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

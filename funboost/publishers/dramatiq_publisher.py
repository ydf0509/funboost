# -*- coding: utf-8 -*-
# @Author  : ydf

import copy
import json

from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.assist.dramatiq_helper import DramatiqHelper
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.utils.redis_manager import RedisMixin


class DramatiqPublisher(AbstractPublisher, ):
    """
    使用dramatiq框架作为中间件
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        pass

    def concrete_realization_of_publish(self, msg):
        if isinstance(msg, str):
            msg = json.loads(msg)
        msg_function_kw = copy.deepcopy(msg)
        if 'extra' in msg:
            msg_function_kw.pop('extra')
        DramatiqHelper.queue_name__actor_map[self.queue_name].send(**msg_function_kw)

    def clear(self):
        DramatiqHelper.broker.flush(self.queue_name)

    def get_message_count(self):
        # pass
        # return -1
        if BrokerConnConfig.DRAMATIQ_URL.startswith('redis'):
            return RedisMixin().redis_db_frame.llen(self.queue_name)  # redis 无，需要自己实现
        if BrokerConnConfig.DRAMATIQ_URL.startswith('amqp'):
            cnts = DramatiqHelper.broker.get_queue_message_counts(self.queue_name)
            return cnts[0]
        return -1

    def close(self):
        DramatiqHelper.broker.close()

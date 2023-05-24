# -*- coding: utf-8 -*-
# @Author  : ydf

import copy
import json

from huey import RedisHuey

from funboost import funboost_config_deafult
from funboost.assist.huey_helper import HueyHelper
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.utils.redis_manager import RedisMixin


class HueyPublisher(AbstractPublisher, ):
    """
    使用huey框架作为中间件
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._huey_task_fun = HueyHelper.queue_name__huey_task_fun_map[self.queue_name]
        self._huey_obj = HueyHelper.huey_obj # type: RedisHuey

    def concrete_realization_of_publish(self, msg):
        if isinstance(msg, str):
            msg = json.loads(msg)
        msg_function_kw = copy.deepcopy(msg)
        if 'extra' in msg:
            msg_function_kw.pop('extra')
        self._huey_task_fun(**msg_function_kw)

    def clear(self):
        self._huey_obj.flush()

    def get_message_count(self):
        pass
        return -1


    def close(self):
        pass

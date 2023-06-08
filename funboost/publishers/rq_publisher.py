# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import json

from funboost.assist.rq_helper import RqHelper
from funboost.publishers.base_publisher import AbstractPublisher


class RqPublisher(AbstractPublisher):
    """
    使用redis作为中间件,这个是大幅优化了发布速度的方式。简单的发布是 redis_publisher_0000.py 中的代码方式。

    这个是复杂版，批量推送，简单版在 funboost/publishers/redis_publisher_simple.py
    """

    def concrete_realization_of_publish(self, msg):
        func_kwargs = json.loads(msg)
        func_kwargs.pop('extra')
        RqHelper.queue_name__rq_job_map[self.queue_name].delay(**func_kwargs)

    def clear(self):
        pass

    def get_message_count(self):
        pass

    def close(self):
        pass

    def _at_exit(self):
        pass

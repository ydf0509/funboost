# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 12:12

from funboost.publishers.base_publisher import AbstractPublisher
from urllib3 import PoolManager


class HTTPPublisher(AbstractPublisher, ):
    """
    http实现的，不支持持久化。
    """

    BROKER_KIND = 23

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._http = PoolManager(10)

    def concrete_realization_of_publish(self, msg):
        url = self.queue_name + '/queue'
        self._http.request('post', url, fields={'msg': msg})

    def clear(self):
        pass  # udp没有保存消息

    def get_message_count(self):
        return -1  # http模式没有持久化保存消息

    def close(self):
        pass

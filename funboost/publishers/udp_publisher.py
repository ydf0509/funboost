# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import socket
from funboost.publishers.base_publisher import AbstractPublisher


class UDPPublisher(AbstractPublisher, ):
    """
    使用udp作为中间件,不支持持久化，支持分布式
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._bufsize = self.publisher_params.broker_exclusive_config['bufsize']
        self.__udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._ip = self.publisher_params.broker_exclusive_config['host']
        self._port = self.publisher_params.broker_exclusive_config['port']
        self.__ip_port = (self._ip, self._port)
        if self._port is None:
            raise ValueError('please specify port')
        self.__udp_client.connect(self.__ip_port)

    # noinspection PyAttributeOutsideInit
    def _publish_impl(self, msg):
        self.__udp_client.send(msg.encode('utf-8'), )
        self.__udp_client.recv(self._bufsize)

    def clear(self):
        pass  # udp没有保存消息

    def get_message_count(self):
        # nb_print(self.redis_db7,self._queue_name)
        return -1  # udp没有保存消息

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        self.__udp_client.close()

# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 12:12
import socket
from function_scheduling_distributed_framework.publishers.base_publisher import AbstractPublisher


class UDPPublisher(AbstractPublisher, ):
    """
    使用redis作为中间件,这个是大幅优化了发布速度的方式。简单的发布是 redis_publisher_0000.py 中的代码方式。
    """

    BROKER_KIND = 21

    BUFSIZE = 10240

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        """ queue_name 要设置为例如  127.0.0.1:5689"""
        self.__udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ip__port_str = self.queue_name.split(':')
        self.__ip_port = (ip__port_str[0], int(ip__port_str[1]))

    def concrete_realization_of_publish(self, msg):
        self.__udp_client.sendto(msg.encode('utf-8'), self.__ip_port)
        data, server_addr = self.__udp_client.recvfrom(self.BUFSIZE)

    def clear(self):
        pass  # udp没有保存消息

    def get_message_count(self):
        # nb_print(self.redis_db7,self._queue_name)
        return -1  # udp没有保存消息

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        self.__udp_client.close()

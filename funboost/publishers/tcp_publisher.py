# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 12:12
import socket
from funboost.publishers.base_publisher import AbstractPublisher


class TCPPublisher(AbstractPublisher, ):
    """
    使用tco作为中间件,不支持持久化，支持分布式
    """

    BROKER_KIND = 21

    BUFSIZE = 10240

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        """ tcp为消息队列中间件 时候 queue_name 要设置为例如  127.0.0.1:5689"""
        pass

    # noinspection PyAttributeOutsideInit
    def concrete_realization_of_publish(self, msg):
        if not hasattr(self, '_tcp_cli_sock'):
            ip__port_str = self.queue_name.split(':')
            ip_port = (ip__port_str[0], int(ip__port_str[1]))
            tcp_cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_cli_sock.connect(ip_port)
            self._tcp_cli_sock = tcp_cli_sock

        self._tcp_cli_sock.send(msg.encode())
        self._tcp_cli_sock.recv(self.BUFSIZE)

    def clear(self):
        pass  # udp没有保存消息

    def get_message_count(self):
        # nb_print(self.redis_db7,self._queue_name)
        return -1  # udp没有保存消息

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        self._tcp_cli_sock.close()

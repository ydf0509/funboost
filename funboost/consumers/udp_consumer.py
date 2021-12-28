# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:32
import json
import socket

from funboost.consumers.base_consumer import AbstractConsumer


class UDPConsumer(AbstractConsumer, ):
    """
    socket 实现消息队列，不支持持久化，但不需要安装软件。
    """
    BROKER_KIND = 21

    BUFSIZE = 10240

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        """ udp为消息队列中间件 时候 queue_name 要设置为例如  127.0.0.1:5689"""
        self.__udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ip__port_str = self.queue_name.split(':')
        self.__ip_port = (ip__port_str[0], int(ip__port_str[1]))
        self.__udp_client.connect(self.__ip_port)

    # noinspection DuplicatedCode
    def _shedual_task(self):
        ip_port = ('', self.__ip_port[1])
        # ip_port = ('', 9999)
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # udp协议
        server.bind(ip_port)
        while True:
            data, client_addr = server.recvfrom(self.BUFSIZE)
            # print('server收到的数据', data)
            self._print_message_get_from_broker(f'udp {ip_port}', data.decode())
            server.sendto('has_recived'.encode(), client_addr)
            kw = {'body': json.loads(data)}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # 没有确认消费的功能。

    def _requeue(self, kw):
        self.__udp_client.send(json.dumps(kw['body']).encode())
        data = self.__udp_client.recv(self.BUFSIZE)

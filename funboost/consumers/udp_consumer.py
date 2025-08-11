# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json
import socket
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer


class UDPConsumer(AbstractConsumer, ):
    """
    socket 实现消息队列，不支持持久化，但不需要安装软件。
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'host': '127.0.0.1', 'port': None, 'bufsize': 10240}

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        
        self.__udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # ip__port_str = self.queue_name.split(':')
        # self.__ip_port = (ip__port_str[0], int(ip__port_str[1]))
        self.__ip_port = (self.consumer_params.broker_exclusive_config['host'],
                          self.consumer_params.broker_exclusive_config['port'])
        self._bufsize = self.consumer_params.broker_exclusive_config['bufsize']
        self.__udp_client.connect(self.__ip_port)

    # noinspection DuplicatedCode
    def _shedual_task(self):
        ip_port = ('', self.__ip_port[1])
        # ip_port = ('', 9999)
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # udp协议
        server.bind(ip_port)
        while True:
            data, client_addr = server.recvfrom(self._bufsize)
            # print('server收到的数据', data)
            # self._print_message_get_from_broker(f'udp {ip_port}', data.decode())
            server.sendto('has_recived'.encode(), client_addr)
            kw = {'body': data}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # 没有确认消费的功能。

    def _requeue(self, kw):
        self.__udp_client.send(json.dumps(kw['body']).encode())
        data = self.__udp_client.recv(self._bufsize)

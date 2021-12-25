# -*- coding: utf-8 -*-
# @Author  : ydf
import zmq
from funboost import funboost_config_deafult
from funboost.publishers.base_publisher import AbstractPublisher


# noinspection PyProtectedMember
class ZeroMqPublisher(AbstractPublisher):
    """
    zeromq 中间件的发布者，zeromq基于socket代码，不会持久化，且不需要安装软件。
    """
    def custom_init(self):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect(f"tcp://localhost:{int(self._queue_name)}")
        self.socket =socket
        self.logger.warning('框架使用 zeromq 中间件方式，必须先启动消费者(消费者会顺便启动broker) ,只有启动了服务端才能发布任务')

    def concrete_realization_of_publish(self, msg):
        self.socket.send(msg.encode())
        self.socket.recv()

    def clear(self):
        pass

    def get_message_count(self):
        return -1

    def close(self):
        pass


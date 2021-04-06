# -*- coding: utf-8 -*-
# @Author  : ydf
import zmq
from function_scheduling_distributed_framework import frame_config
from function_scheduling_distributed_framework.publishers.base_publisher import AbstractPublisher


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

    def concrete_realization_of_publish(self, msg):
        self.socket.send(msg.encode())
        self.socket.recv()

    def clear(self):
        pass

    def get_message_count(self):
        return 0

    def close(self):
        pass

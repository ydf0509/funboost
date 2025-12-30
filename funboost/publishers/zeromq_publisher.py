# -*- coding: utf-8 -*-
# @Author  : ydf
from funboost.core.lazy_impoter import ZmqImporter
from funboost.publishers.base_publisher import AbstractPublisher


# noinspection PyProtectedMember
class ZeroMqPublisher(AbstractPublisher):
    """
    zeromq 中间件的发布者，zeromq基于socket代码，不会持久化，且不需要安装软件。
    """
    def custom_init(self):
        self._port = self.publisher_params.broker_exclusive_config['port']
        if self._port is None:
            raise ValueError('please specify port')

        context = ZmqImporter().zmq.Context()
        socket = context.socket(ZmqImporter().zmq.REQ)
        socket.connect(f"tcp://localhost:{int(self._port)}")
        self.socket =socket
        self.logger.warning('框架使用 zeromq 中间件方式，必须先启动消费者(消费者会顺便启动broker) ,只有启动了服务端才能发布任务')

    def _publish_impl(self, msg):
        self.socket.send(msg.encode())
        self.socket.recv()

    def clear(self):
        pass

    def get_message_count(self):
        return -1

    def close(self):
        pass


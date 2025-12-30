# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json

from funboost.core.lazy_impoter import GnsqImporter
# from gnsq import Consumer, Message

from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.consumers.base_consumer import AbstractConsumer
# from nb_log import LogManager
from funboost.core.loggers import get_funboost_file_logger

get_funboost_file_logger('gnsq',log_level_int=20)


class NsqConsumer(AbstractConsumer):
    """
    nsq作为中间件实现的。
    """


    def _dispatch_task(self):
        consumer = GnsqImporter().Consumer(self._queue_name, 'frame_channel', BrokerConnConfig.NSQD_TCP_ADDRESSES,
                            max_in_flight=self.consumer_params.concurrent_num, heartbeat_interval=60, timeout=600, )  # heartbeat_interval 不能设置为600

        @consumer.on_message.connect
        def handler(consumerx: GnsqImporter().Consumer, message: GnsqImporter().Message):
            # 第一条消息不能并发，第一条消息之后可以并发。
            # self.logger.debug(f'从nsq的 [{self._queue_name}] 主题中 取出的消息是：  {message.body.decode()}')
            message.enable_async()
            kw = {'consumer': consumerx, 'message': message, 'body': message.body}
            self._submit_task(kw)

        consumer.start()

    def _confirm_consume(self, kw):
        kw['message'].finish()

    def _requeue(self, kw):
        kw['message'].requeue()

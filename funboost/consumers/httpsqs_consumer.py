# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json
import time
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers.httpsqs_publisher import HttpsqsPublisher
from funboost.core.func_params_model import PublisherParams

class HttpsqsConsumer(AbstractConsumer):
    """
    httpsqs作为中间件
    """


    def custom_init(self):
        # noinspection PyAttributeOutsideInit
        self.httpsqs_publisher = HttpsqsPublisher(publisher_params=PublisherParams(queue_name=self.queue_name))

    # noinspection DuplicatedCode
    def _shedual_task(self):
        while True:
            text = self.httpsqs_publisher.opt_httpsqs('get')
            if text == 'HTTPSQS_GET_END':
                time.sleep(0.5)
            else:
                kw = {'body': json.loads(text)}
                self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        try:
            kw['body'].pop('extra')
        except KeyError:
            pass
        self.httpsqs_publisher.publish(kw['body'])

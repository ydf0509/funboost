# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:32
import json
import time
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers.httpsqs_publisher import HttpsqsPublisher


class HttpsqsConsumer(AbstractConsumer):
    """
    httpsqs作为中间件
    """
    BROKER_KIND = 18

    def custom_init(self):
        # noinspection PyAttributeOutsideInit
        self.httpsqs_publisher = HttpsqsPublisher(self._queue_name)

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

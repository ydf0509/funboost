# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:33
import time

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers.mongomq_publisher import MongoMixin, MongoMqPublisher


class MongoMqConsumer(AbstractConsumer, MongoMixin):
    """
    Mongo queue包实现的基于mongo的消息队列，支持消费确认。
    """
    BROKER_KIND = 5

    def _shedual_task(self):
        mp = MongoMqPublisher(self.queue_name)
        while True:
            job = mp.queue.next()
            if job is not None:
                # self.logger.debug(f'从mongo的 [{self._queue_name}] 队列中 取出的消息是：   消息是：  {job.payload}  ')
                self._print_message_get_from_broker('mongo', job.payload)
                kw = {'body': job.payload, 'job': job}
                self._submit_task(kw)
            else:
                time.sleep(0.1)

    def _confirm_consume(self, kw):
        kw['job'].complete()

    def _requeue(self, kw):
        kw['job'].release()

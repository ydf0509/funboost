# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:35
import json
import time

from function_scheduling_distributed_framework.consumers.base_consumer import AbstractConsumer
from function_scheduling_distributed_framework.publishers.persist_queue_publisher import PersistQueuePublisher


class PersistQueueConsumer(AbstractConsumer):
    """
    persist queue包实现的本地持久化消息队列。
    """
    BROKER_KIND = 6

    def _shedual_task(self):
        pub = PersistQueuePublisher(self.queue_name)
        while True:
            t_start = time.time()
            item = pub.queue.get()
            self.logger.debug(f'从本地持久化sqlite的 [{self._queue_name}] 队列中 取出的消息是：    消息是：  {item}  ')
            kw = {'body': json.loads(item), 'q': pub.queue, 'item': item}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        kw['q'].ack(kw['item'])

    def _requeue(self, kw):
        kw['q'].nack(kw['item'])
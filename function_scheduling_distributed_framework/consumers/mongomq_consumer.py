# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:33
import time

from function_scheduling_distributed_framework.consumers.base_consumer import AbstractConsumer
from function_scheduling_distributed_framework.publishers.mongomq_publisher import MongoMixin, MongoMqPublisher


class MongoMqConsumer(AbstractConsumer, MongoMixin):
    """
    Mongo queue包实现的基于mongo的消息队列，支持消费确认。
    """
    BROKER_KIND = 5

    def _shedual_task(self):
        mp = MongoMqPublisher(self.queue_name)
        while True:
            t_start = time.time()
            job = mp.queue.next()
            if job is not None:
                self.logger.debug(f'取出的任务时间是 {round(time.time() - t_start, 4)}    消息是：  {job.payload}  ')
                kw = {'body': job.payload, 'job': job}
                self._submit_task(kw)
            else:
                time.sleep(self._msg_schedule_time_intercal)

    def _confirm_consume(self, kw):
        kw['job'].complete()

    def _requeue(self, kw):
        kw['job'].release()

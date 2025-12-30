# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/8 0008 13:32

import time
from funboost.assist.rq_helper import RqHelper
from funboost.consumers.base_consumer import AbstractConsumer
from rq.decorators import job


class RqConsumer(AbstractConsumer):
    """
    redis作为中间件实现的。
    """

    def custom_init(self):
        self.rq_job = job(queue=self.queue_name, connection=RqHelper.redis_conn)(self.consuming_function)
        RqHelper.queue_name__rq_job_map[self.queue_name] = self.rq_job

    def start_consuming_message(self):
        RqHelper.to_be_start_work_rq_queue_name_set.add(self.queue_name)
        super().start_consuming_message()

    def _dispatch_task(self):
        while 1:
            time.sleep(100)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        pass

# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:33
import json
from funboost.constant import BrokerEnum
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.queues.peewee_queue import PeeweeQueue,TaskStatus


class PeeweeConsumer(AbstractConsumer):
    """
    peewee实现的操作5种数据库模拟消息队列，支持消费确认。
    """


    def _shedual_task(self):
        self.queue = PeeweeQueue(self.queue_name)
        while True:
            task_dict = self.queue.get()
            # print(task_dict)
            # self.logger.debug(f'从数据库 {frame_config.SQLACHEMY_ENGINE_URL[:25]}。。 的 [{self._queue_name}] 队列中 取出的消息是：   消息是：  {sqla_task_dict}')
            kw = {'body':task_dict['body'], 'job_id': task_dict['job_id']}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        self.queue.set_success(kw['job_id'])

    def _requeue(self, kw):
        self.queue.requeue_task(kw['job_id'])




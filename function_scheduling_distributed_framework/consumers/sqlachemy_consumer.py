# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:33
import json

from function_scheduling_distributed_framework import frame_config
from function_scheduling_distributed_framework.consumers.base_consumer import AbstractConsumer
from function_scheduling_distributed_framework.utils import sqla_queue


class SqlachemyConsumer(AbstractConsumer):
    """
    sqlachemy实现的操作5种数据库模拟消息队列，支持消费确认。
    """
    BROKER_KIND = 10

    def _shedual_task(self):
        self.queue = sqla_queue.SqlaQueue(self._queue_name, frame_config.SQLACHEMY_ENGINE_URL)
        while True:
            sqla_task_dict = self.queue.get()
            self.logger.debug(f'从数据库 {frame_config.SQLACHEMY_ENGINE_URL[:20]} 的 [{self._queue_name}] 队列中 取出的消息是：   消息是：  {sqla_task_dict}')
            kw = {'body': json.loads(sqla_task_dict['body']), 'sqla_task_dict': sqla_task_dict}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        self.queue.set_success(kw['sqla_task_dict'])

    def _requeue(self, kw):
        self.queue.set_task_status(kw['sqla_task_dict'], sqla_queue.TaskStatus.REQUEUE)



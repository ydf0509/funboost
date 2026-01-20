# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:36
from queue import Queue
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.queues.memory_queues_map import PythonQueues


class LocalPythonQueueConsumer(AbstractConsumer):
    """
    python 内置queue对象作为消息队列，这个要求发布和消费必须在同一python解释器内部运行，不支持分布式。
    """

    @property
    def local_python_queue(self) -> Queue:
        return PythonQueues.get_queue(self._queue_name)

    def _dispatch_task(self):
        while True:
            task = self.local_python_queue.get()
            kw = {'body': task}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        self.local_python_queue.put(kw['body'])


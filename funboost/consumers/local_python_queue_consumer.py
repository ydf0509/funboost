# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:36
import json
from queue import Queue

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers import local_python_queue_publisher


class LocalPythonQueueConsumer(AbstractConsumer):
    """
    python 内置queue对象作为消息队列，这个要求发布和消费必须在同一python解释器内部运行，不支持分布式。
    """
    BROKER_KIND = 3

    @property
    def local_python_queue(self) -> Queue:
        return local_python_queue_publisher.local_pyhton_queue_name__local_pyhton_queue_obj_map[self._queue_name]

    def _shedual_task(self):
        while True:
            task = self.local_python_queue.get()
            if isinstance(task, str):
                task = json.loads(task)
            self._print_message_get_from_broker('当前python解释器内部', task)
            # self.logger.debug(f'从当前python解释器内部的 [{self._queue_name}] 队列中 取出的消息是：  {json.dumps(task)}  ')
            kw = {'body': task}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        self.local_python_queue.put(kw['body'])

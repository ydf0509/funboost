# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:36
import json
import time
from queue import Queue

from function_scheduling_distributed_framework.consumers.base_consumer import AbstractConsumer
from function_scheduling_distributed_framework.publishers import local_python_queue_publisher


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
            t_start = time.time()
            task = self.local_python_queue.get()
            if isinstance(task, str):
                task = json.loads(task)
            self.logger.debug(f'取出的任务时间是 {round(time.time() - t_start, 4)}    消息是：  {json.dumps(task)}  ')
            task_dict = task
            kw = {'body': task_dict}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        self.local_python_queue.put(kw['body'])

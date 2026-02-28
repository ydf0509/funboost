# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:36
from queue import Queue
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.queues.memory_queues_map import PythonQueues


class LocalPythonQueueConsumer(AbstractConsumer):
    """
    python 内置queue对象作为消息队列，这个要求发布和消费必须在同一python解释器内部运行，不支持分布式。
    但是重要性是sss级别，高性能 不担心有的对象无法pickele序列化，
    """

    @property
    def local_python_queue(self) -> Queue:
        maxsize = self.consumer_params.broker_exclusive_config['maxsize']
        return PythonQueues.get_queue(self._queue_name, maxsize=maxsize)

    def _dispatch_task(self):
        while True:
            task = self.local_python_queue.get()
            kw = {'body': task}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        self.local_python_queue.put(kw['body'])

    def _set_rpc_result(self, task_id, kw, current_function_result_status, current_retry_times, **kwargs):
        """
        重写父类的 _set_rpc_result，优先检查消息体中是否携带了 _memory_call_future（由 publisher.call 方法塞入）。
        如果有，直接通过 Future.set_result 将 FunctionResultStatus 设置回去，不依赖 Redis。
        如果没有，回退到父类的 Redis RPC 逻辑（用于 is_using_rpc_mode=True 的场景）。
        """
        future = kw['body']['extra'].pop('_memory_call_future', None)
        if future is not None:
            future.set_result(current_function_result_status)
            return
        super()._set_rpc_result(task_id, kw, current_function_result_status, current_retry_times, **kwargs)



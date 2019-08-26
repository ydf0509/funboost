# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:32
import json
import time

from function_scheduling_distributed_framework.consumers.base_consumer import AbstractConsumer
from function_scheduling_distributed_framework.utils import RedisMixin


class RedisConsumer(AbstractConsumer, RedisMixin):
    """
    redis作为中间件实现的。
    """
    BROKER_KIND = 2

    def _shedual_task(self):
        while True:
            t_start = time.time()
            result = self.redis_db_frame.blpop(self._queue_name,timeout=60)
            if result:
                self.logger.debug(f'取出的任务时间是 {round(time.time() - t_start, 4)}    消息是：  {result[1].decode()}  ')
                task_dict = json.loads(result[1])
                kw = {'body': task_dict}
                self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # redis没有确认消费的功能。

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name, json.dumps(kw['body']))

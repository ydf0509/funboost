# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:32
import json
import time

from function_scheduling_distributed_framework.consumers.base_consumer import AbstractConsumer
from function_scheduling_distributed_framework.utils import RedisMixin


class RedisConsumer(AbstractConsumer, RedisMixin):
    """
    redis作为中间件实现的，使用redis list 结构实现的。
    """
    BROKER_KIND = 2

    def _shedual_task000(self):
        while True:
            result = self.redis_db_frame.blpop(self._queue_name,timeout=60)
            if result:
                self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {result[1].decode()}  ')
                task_dict = json.loads(result[1])
                kw = {'body': task_dict}
                self._submit_task(kw)

    def _shedual_task(self):
        while True:
            with self.redis_db_frame_version3.pipeline() as p:
                p.lrange(self._queue_name,0,499)
                p.ltrim(self._queue_name,500,-1)
                task_str_list = p.execute()[0]
            if not task_str_list:
                time.sleep(0.1)
            for task_str in task_str_list:
                kw = {'body': json.loads(task_str)}
                self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # redis没有确认消费的功能。

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name, json.dumps(kw['body']))


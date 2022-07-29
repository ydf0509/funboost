# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:32
import json
# import time
import time

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.utils import RedisMixin


class RedisConsumer(AbstractConsumer, RedisMixin):
    """
    redis作为中间件实现的，使用redis list 结构实现的。
    这个如果消费脚本在运行时候随意反复重启或者非正常关闭或者消费宕机，会丢失大批任务。高可靠需要用rabbitmq或者redis_ack_able或者redis_stream的中间件方式。

    这个是复杂版，一次性拉取100个，简单版在 funboost/consumers/redis_consumer_simple.py
    """
    BROKER_KIND = 2
    BROKER_EXCLUSIVE_CONFIG_KEYS = ['redis_bulk_push', ]

    # noinspection DuplicatedCode
    def _shedual_task000(self):
        while True:
            result = self.redis_db_frame.blpop(self._queue_name, timeout=60)
            if result:
                # self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {result[1].decode()}  ')
                self._print_message_get_from_broker('reids', result[1].decode())
                task_dict = json.loads(result[1])
                kw = {'body': task_dict}
                self._submit_task(kw)

    # noinspection DuplicatedCode
    def _shedual_task(self):
        while True:
            with self.redis_db_frame_version3.pipeline() as p:
                get_msg_batch_size = 100
                p.lrange(self._queue_name, 0, get_msg_batch_size - 1)
                p.ltrim(self._queue_name, get_msg_batch_size, -1)
                task_str_list = p.execute()[0]
            if task_str_list:
                # self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {task_str_list}  ')
                self._print_message_get_from_broker('redis', task_str_list)
                for task_str in task_str_list:
                    kw = {'body': json.loads(task_str)}
                    self._submit_task(kw)
            else:
                result = self.redis_db_frame.brpop(self._queue_name, timeout=60)
                if result:
                    # self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {result[1].decode()}  ')
                    self._print_message_get_from_broker('redis', result[1].decode())
                    task_dict = json.loads(result[1])
                    kw = {'body': task_dict}
                    self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # redis没有确认消费的功能。

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name, json.dumps(kw['body']))

# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json
import time
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.utils.redis_manager import RedisMixin

"""
使用消息ack超时策略实现的 redis 消费者.
例如取出消息  msg1,  这个消息长时间未能主动ack, 可能是这个消费者挂了,或某些其他原因导致的以后天荒地老可能都不能主动ack,把这种消息重回消息队列,
所以一定要对消费函数的执行耗时谨慎,如果你的消费函数本身就需要执行几十分钟几个小时,但是你的 ack_timeout 设置的比函数耗时还小,会当做不能正确的主动ack,从而触发框架让消息无限反复放入redis,造成重复消费.

"""

class RedisConsumerAckUsingTimeout(AbstractConsumer, RedisMixin):
    """
    redis作为中间件实现的，使用redis list 结构实现的。
    这个如果消费脚本在运行时候随意反复重启或者非正常关闭或者消费宕机，会丢失大批任务。高可靠需要用rabbitmq或者redis_ack_able或者redis_stream的中间件方式。

    这个是复杂版，一次性拉取100个，简单版在 funboost/consumers/redis_consumer_simple.py
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'ack_timeout':30 * 60}

    # noinspection DuplicatedCode
    def _shedual_task(self):
        while True:
            result = self.redis_db_frame.blpop(self._queue_name,timeout=60)
            msg = result[1]
            if result:
                kw = {'body': msg}
                self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # redis没有确认消费的功能。

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name, json.dumps(kw['body']))



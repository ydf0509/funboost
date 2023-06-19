# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
"""

这个是加强版的可确认消费的redis消费实现，所以比redis_conusmer实现复杂很多。
这个可以确保随意反复多次停止重启脚本，任务永不丢失
"""
import json
import time
from funboost.consumers.redis_consumer_ack_able import RedisConsumerAckAble


class RedisPriorityConsumer(RedisConsumerAckAble):
    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'x-max-priority': None} # x-max-priority 是 rabbitmq的优先级队列配置，必须为整数，强烈建议要小于5。为None就代表队列不支持优先级。

    def _shedual_task(self):

        while True:
            # task_str_list = script(keys=[queues_str, self._unack_zset_name], args=[time.time()])
            task_tuple = self.redis_db_frame_version3.blpop(keys=self.publisher_of_same_queue.queue_list, timeout=60)
            if task_tuple:
                msg =  task_tuple[1]
                self.redis_db_frame_version3.zadd(self._unack_zset_name,{msg:time.time()})
                self.logger.debug(task_tuple)
                self._print_message_get_from_broker('redis',msg)
                # self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {task_str_list}  ')
                task_dict = json.loads(msg)
                kw = {'body': task_dict, 'task_str': msg}
                self._submit_task(kw)

    def _requeue(self, kw):
        self.publisher_of_same_queue.publish(kw['body'])

# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:32
import json
# import time

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.utils import RedisMixin, decorators


class RedisBrpopLpushConsumer(AbstractConsumer, RedisMixin):
    """
    redis作为中间件实现的，使用redis brpoplpush 实现的，并且使用心跳来解决 关闭/掉线 重新分发问题。

    """
    BROKER_KIND = 14

    def start_consuming_message(self):
        self._is_send_consumer_hearbeat_to_redis = True
        super().start_consuming_message()
        self.keep_circulating(60, block=False)(self._requeue_tasks_which_unconfirmed)()

    # noinspection DuplicatedCode
    def _shedual_task(self):
        unack_list_name = f'unack_{self._queue_name}_{self.consumer_identification}'
        while True:
            msg = self.redis_db_frame.brpoplpush(self._queue_name, unack_list_name, timeout=60)
            if msg:
                self._print_message_get_from_broker('redis', msg.decode())
                task_dict = json.loads(msg)
                kw = {'body': task_dict, 'raw_msg': msg}
                self._submit_task(kw)

    def _confirm_consume(self, kw):
        self.redis_db_frame.lrem(f'unack_{self._queue_name}_{self.consumer_identification}', kw['raw_msg'], num=1)

    def _requeue(self, kw):
        self.redis_db_frame.lpush(self._queue_name, json.dumps(kw['body']))

    def _requeue_tasks_which_unconfirmed(self):
        lock_key = f'fsdf_lock__requeue_tasks_which_unconfirmed:{self._queue_name}'
        with decorators.RedisDistributedLockContextManager(self.redis_db_frame, lock_key, ) as lock:
            if lock.has_aquire_lock:
                self._distributed_consumer_statistics.send_heartbeat()
                current_queue_hearbeat_ids = self._distributed_consumer_statistics.get_queue_heartbeat_ids(without_time=True)
                current_queue_unacked_msg_queues = self.redis_db_frame.scan(0, f'unack_{self._queue_name}_*', 100)
                for current_queue_unacked_msg_queue in current_queue_unacked_msg_queues[1]:
                    current_queue_unacked_msg_queue_str = current_queue_unacked_msg_queue.decode()
                    if current_queue_unacked_msg_queue_str.split(f'unack_{self._queue_name}_')[1] not in current_queue_hearbeat_ids:
                        msg_list = self.redis_db_frame.lrange(current_queue_unacked_msg_queue_str, 0, -1)
                        self.logger.warning(f"""{current_queue_unacked_msg_queue_str} 是掉线或关闭消费者的待确认任务, 将 一共 {len(msg_list)} 个消息,
                                            详情是 {msg_list} 推送到正常消费队列 {self._queue_name} 队列中。
                                            """)
                        self.redis_db_frame.lpush(self._queue_name, *msg_list)
                        self.redis_db_frame.delete(current_queue_unacked_msg_queue_str)

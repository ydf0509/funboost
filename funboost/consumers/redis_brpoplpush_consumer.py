# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json
# import time
from funboost.constant import RedisKeys
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.utils import  decorators
from funboost.utils.redis_manager import RedisMixin


class RedisBrpopLpushConsumer(AbstractConsumer, RedisMixin):
    """
    redis作为中间件实现的，使用redis brpoplpush 实现的，并且使用心跳来解决 关闭/掉线 重新分发问题。

    """


    def start_consuming_message(self):
        self.consumer_params.is_send_consumer_heartbeat_to_redis = True
        # 方案C：注册当前消费者的 unack list key，作为“全量索引”
        self._unack_list_name = f'unack_{self._queue_name}_{self.consumer_identification}'
        self._unack_registry_key = RedisKeys.gen_funboost_unack_registry_key_by_queue_name(self._queue_name)
        self.redis_db_frame.sadd(self._unack_registry_key, self._unack_list_name)
        super().start_consuming_message()
        self.keep_circulating(60, block=False)(self._requeue_tasks_which_unconfirmed)()

    # noinspection DuplicatedCode
    def _dispatch_task(self):
        while True:
            msg = self.redis_db_frame.brpoplpush(self._queue_name, self._unack_list_name, timeout=60)
            if msg:
                kw = {'body': msg, 'raw_msg': msg}
                self._submit_task(kw)

    def _confirm_consume(self, kw):
        self.redis_db_frame.lrem(self._unack_list_name, count=1, value=kw['raw_msg'], )

    def _requeue(self, kw):
        self.redis_db_frame.lpush(self._queue_name, json.dumps(kw['body']))

    def _requeue_tasks_which_unconfirmed(self):
        lock_key = f'fsdf_lock__requeue_tasks_which_unconfirmed:{self._queue_name}'
        with decorators.RedisDistributedLockContextManager(self.redis_db_frame, lock_key, ) as lock:
            if lock.has_aquire_lock:
                self._distributed_consumer_statistics.send_heartbeat()
                current_queue_hearbeat_ids = self._distributed_consumer_statistics.get_queue_heartbeat_ids(without_time=True)
                registry_key = self._unack_registry_key
                all_unack_keys = self.redis_db_frame.smembers(registry_key)
                unack_key_prefix = f'unack_{self._queue_name}_'
                for current_queue_unacked_msg_queue_str in all_unack_keys:
                    consumer_id = current_queue_unacked_msg_queue_str[len(unack_key_prefix):]
                    if consumer_id in current_queue_hearbeat_ids:
                        continue
                    msg_list = self.redis_db_frame.lrange(current_queue_unacked_msg_queue_str, 0, -1)
                    if msg_list:
                        self.logger.warning(f"""{current_queue_unacked_msg_queue_str} 是掉线或关闭消费者的待确认任务, 将 一共 {len(msg_list)} 个消息,
                                        详情是 {msg_list} 推送到正常消费队列 {self._queue_name} 队列中。
                                        """)
                        self.redis_db_frame.lpush(self._queue_name, *msg_list)
                    self.redis_db_frame.delete(current_queue_unacked_msg_queue_str)
                    self.redis_db_frame.srem(registry_key, current_queue_unacked_msg_queue_str)

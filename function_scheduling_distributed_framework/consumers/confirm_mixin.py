# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/23 0023 21:10
import time
import json
import uuid
from function_scheduling_distributed_framework.utils import RedisMixin,decorators


# noinspection PyUnresolvedReferences
class ConsumerConfirmMixinWithTheHelpOfRedis(RedisMixin):
    """
    使用redis的zset结构，value为任务，score为时间戳，这样具有良好的按时间范围搜索特性和删除特性。
    把这个抽离出来了。，是因为这个不仅可以给redis做消息确认，也可以给其他不支持消费确认的消息中间件增加消费确认。
    """
    # 超时未确认的时间，例如取出来后600秒都没有确认消费，就重新消费。这在rabbitmq和nsq对应的相同功能参数是heartbeat_interval。
    UNCONFIRMED_TIMEOUT = 600

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._unack_zset_name = f'{self._queue_name}__unack'
        self._is_send_consumer_hearbeat_to_redis = True

    def start_consuming_message(self):
        self.logger.warning('启动了任务redis确认消费助手')
        self.keep_circulating(60, block=False)(self._requeue_tasks_which_unconfirmed)()
        super().start_consuming_message()

    def _add_task_str_to_unack_zset(self, task_str, ):
        self.redis_db_frame.zadd(self._unack_zset_name, task_str, time.time())

    def _confirm_consume(self, kw):
        self.redis_db_frame.zrem(self._unack_zset_name, kw['task_str'])

    def _requeue_tasks_which_unconfirmed(self):
        ## 防止在多个进程或多个机器中同时做扫描和放入未确认消费的任务。使用个分布式锁。
        lock_key = f'fsdf_lock__requeue_tasks_which_unconfirmed_timeout:{self._queue_name}'
        with decorators.RedisDistributedLockContextManager(self.redis_db_frame,lock_key,) as lock:
            if lock.has_aquire_lock:
                time_max = time.time() - self.UNCONFIRMED_TIMEOUT
                for value in self.redis_db_frame.zrangebyscore(self._unack_zset_name, 0, time_max):
                    self.logger.warning(f'向 {self._queue_name} 重新放入未消费确认的任务 {value}')
                    self._requeue({'body': json.loads(value)})
                    self.redis_db_frame.zrem(self._unack_zset_name, value)
                self.redis_db_frame.delete(lock_key)
                self.logger.info(f'{self._unack_zset_name} 中有待确认消费任务的数量是'
                                 f' {self.redis_db_frame.zcard(self._unack_zset_name)}')







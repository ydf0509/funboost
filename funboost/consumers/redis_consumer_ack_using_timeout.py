# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2024/8/8 0008 13:32
import json
import time
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.utils.decorators import RedisDistributedLockContextManager
from funboost.utils.json_helper import JsonUtils
from funboost.utils.redis_manager import RedisMixin


class RedisConsumerAckUsingTimeout(AbstractConsumer, RedisMixin):
    """
    redis作为中间件实现的。
    使用超时未能ack就自动重入消息队列，例如消息取出后，由于突然断电或重启或其他原因，导致消息以后再也不能主动ack了，超过一定时间就重新放入消息队列
    """
    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'ack_timeout':3600}

    def custom_init(self):
        self._unack_zset_name = f'{self._queue_name}__unack_using_timeout'
        self._ack_timeout= self.consumer_params.broker_exclusive_config['ack_timeout']
        self._last_show_unack_ts = time.time()

    def start_consuming_message(self):
        self._is_send_consumer_hearbeat_to_redis = True
        super().start_consuming_message()
        self.keep_circulating(60, block=False)(self._requeue_tasks_which_unconfirmed)()

    # def _add_task_str_to_unack_zset(self, task_str, ):
    #     self.redis_db_frame.zadd(self._unack_zset_name, {task_str: time.time()})

    def _confirm_consume(self, kw):
        self.redis_db_frame.zrem(self._unack_zset_name, kw['task_str'])

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name, JsonUtils.to_json_str(kw['body']))

    def _shedual_task(self):
        lua = '''
                     local v = redis.call("lpop", KEYS[1])
                     if v then
                     redis.call('zadd',KEYS[2],ARGV[1],v)
                      end
                     return v
                '''
        script = self.redis_db_frame.register_script(lua)
        while True:
            return_v = script(keys=[self._queue_name, self._unack_zset_name], args=[time.time()])
            if return_v:
                task_str = return_v
                kw = {'body': task_str, 'task_str': task_str}
                self._submit_task(kw)
            else:
                time.sleep(0.1)

    def _requeue_tasks_which_unconfirmed(self):
        """不使用这种方案，不适合本来来就需要长耗时的函数，很死板"""
        # 防止在多个进程或多个机器中同时做扫描和放入未确认消费的任务。使用个分布式锁。
        lock_key = f'funboost_lock__requeue_tasks_which_unconfirmed_timeout:{self._queue_name}'
        with RedisDistributedLockContextManager(self.redis_db_frame, lock_key, ) as lock:
            if lock.has_aquire_lock:
                time_max = time.time() - self._ack_timeout
                for value in self.redis_db_frame.zrangebyscore(self._unack_zset_name, 0, time_max):
                    self.logger.warning(f'超过了 {self._ack_timeout} 秒未能确认消费, 向 {self._queue_name} 队列重新放入未消费确认的任务 {value} ,')
                    self._requeue({'body': value})
                    self.redis_db_frame.zrem(self._unack_zset_name, value)
                if time.time() - self._last_show_unack_ts > 600: # 不要频繁提示打扰
                    self.logger.info(f'{self._unack_zset_name} 中有待确认消费任务的数量是'
                                     f' {self.redis_db_frame.zcard(self._unack_zset_name)}')
                    self._last_show_unack_ts = time.time()








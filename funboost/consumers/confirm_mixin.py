# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/23 0023 21:10
import json
import time

from funboost.utils import RedisMixin, decorators

"""
此模块是依赖redis的确认消费，所以比较复杂。
"""


# noinspection PyUnresolvedReferences
class ConsumerConfirmMixinWithTheHelpOfRedis(RedisMixin):
    """
    使用redis的zset结构，value为任务，score为时间戳，这样具有良好的按时间范围搜索特性和删除特性。
    把这个抽离出来了。，是因为这个不仅可以给redis做消息确认，也可以给其他不支持消费确认的消息中间件增加消费确认。

    """
    # 超时未确认的时间，例如取出来后600秒都没有确认消费，就重新消费。这在rabbitmq和nsq对应的相同功能参数是heartbeat_interval。
    # 这个弊端很多，例如一个函数本身就需要10分钟以上，重回队列会造成死循环消费。已近废弃了。基于消费者的心跳是确认消费好的方式。
    UNCONFIRMED_TIMEOUT = 600

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._unack_zset_name = f'{self._queue_name}__unack'

    def start_consuming_message(self):
        self._is_send_consumer_hearbeat_to_redis = True
        super().start_consuming_message()
        self.keep_circulating(60, block=False)(self._requeue_tasks_which_unconfirmed)()

    def _add_task_str_to_unack_zset(self, task_str, ):
        self.redis_db_frame.zadd(self._unack_zset_name, task_str, time.time())

    def _confirm_consume(self, kw):
        self.redis_db_frame.zrem(self._unack_zset_name, kw['task_str'])

    def _requeue_tasks_which_unconfirmed(self):
        """不使用这种方案，不适合本来来就需要长耗时的函数，很死板"""
        # 防止在多个进程或多个机器中同时做扫描和放入未确认消费的任务。使用个分布式锁。
        lock_key = f'fsdf_lock__requeue_tasks_which_unconfirmed_timeout:{self._queue_name}'
        with decorators.RedisDistributedLockContextManager(self.redis_db_frame, lock_key, ) as lock:
            if lock.has_aquire_lock:
                time_max = time.time() - self.UNCONFIRMED_TIMEOUT
                for value in self.redis_db_frame.zrangebyscore(self._unack_zset_name, 0, time_max):
                    self.logger.warning(f'向 {self._queue_name} 重新放入未消费确认的任务 {value}')
                    self._requeue({'body': json.loads(value)})
                    self.redis_db_frame.zrem(self._unack_zset_name, value)
                self.logger.info(f'{self._unack_zset_name} 中有待确认消费任务的数量是'
                                 f' {self.redis_db_frame.zcard(self._unack_zset_name)}')


# noinspection PyUnresolvedReferences
class ConsumerConfirmMixinWithTheHelpOfRedisByHearbeat(ConsumerConfirmMixinWithTheHelpOfRedis):
    """
    使用的是根据心跳，判断非活跃消费者，将非活跃消费者对应的unack zset的重新回到消费队列。
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._unack_zset_name = f'{self._queue_name}__unack_id_{self.consumer_identification}'
        self._is_send_consumer_hearbeat_to_redis = True
        self._last_show_unacked_msg_num_log = 0

    def _requeue_tasks_which_unconfirmed(self):
        lock_key = f'fsdf_lock__requeue_tasks_which_unconfirmed:{self._queue_name}'
        with decorators.RedisDistributedLockContextManager(self.redis_db_frame, lock_key, ).set_log_level(30) as lock:
            if lock.has_aquire_lock:
                self._distributed_consumer_statistics.send_heartbeat()
                current_queue_hearbeat_ids = self._distributed_consumer_statistics.get_queue_heartbeat_ids(without_time=True)
                current_queue_unacked_msg_queues = self.redis_db_frame.scan(0, f'{self._queue_name}__unack_id_*', 100)
                # print(current_queue_unacked_msg_queues)
                for current_queue_unacked_msg_queue in current_queue_unacked_msg_queues[1]:
                    current_queue_unacked_msg_queue_str = current_queue_unacked_msg_queue.decode()
                    if time.time() - self._last_show_unacked_msg_num_log > 600:
                        self.logger.info(f'{current_queue_unacked_msg_queue_str} 中有待确认消费任务的数量是'
                                         f' {self.redis_db_frame.zcard(current_queue_unacked_msg_queue_str)}')
                        self._last_show_unacked_msg_num_log = time.time()
                    if current_queue_unacked_msg_queue_str.split(f'{self._queue_name}__unack_id_')[1] not in current_queue_hearbeat_ids:
                        self.logger.warning(f'{current_queue_unacked_msg_queue_str} 是掉线或关闭消费者的')
                        for unacked_task_str in self.redis_db_frame.zrevrange(current_queue_unacked_msg_queue_str, 0, 1000):
                            self.logger.warning(f'从 {current_queue_unacked_msg_queue_str} 向 {self._queue_name} 重新放入掉线消费者未消费确认的任务 {unacked_task_str.decode()}')
                            self.redis_db_frame.lpush(self._queue_name, unacked_task_str)
                            self.redis_db_frame.zrem(current_queue_unacked_msg_queue_str, unacked_task_str)
                    else:
                        pass
                        # print('是活跃消费者')

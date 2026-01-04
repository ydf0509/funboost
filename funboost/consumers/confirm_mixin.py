# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/23 0023 21:10
import time
from funboost.utils.redis_manager import RedisMixin
from funboost.utils import decorators
from funboost.core.serialization import Serialization
from funboost.constant import RedisKeys
"""
此模块是依赖redis的确认消费，所以比较复杂。
"""


# noinspection PyUnresolvedReferences

# noinspection PyUnresolvedReferences
class ConsumerConfirmMixinWithTheHelpOfRedisByHearbeat(RedisMixin):
    """
    使用的是根据心跳，判断非活跃消费者，将非活跃消费者对应的unack zset的重新回到消费队列。
    """
    

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._unack_zset_name = f'{self._queue_name}__unack_id_{self.consumer_identification}'
        self._unack_registry_key = RedisKeys.gen_funboost_unack_registry_key_by_queue_name(self._queue_name)
        self.consumer_params.is_send_consumer_heartbeat_to_redis = True
        self._last_show_unacked_msg_num_log = 0
        self.consumer_params.is_send_consumer_heartbeat_to_redis = True
        # 方案C：注册 unack key，作为“全量索引”，避免依赖心跳 key 是否包含死亡消费者记录
        self.redis_db_frame.sadd(self._unack_registry_key, self._unack_zset_name)

    def start_consuming_message(self):
        super().start_consuming_message()
        self.keep_circulating(60, block=False)(self._requeue_tasks_which_unconfirmed)()

    def _add_task_str_to_unack_zset(self, task_str, ):
        self.redis_db_frame.zadd(self._unack_zset_name, {task_str: time.time()})

    def _confirm_consume(self, kw):
        self.redis_db_frame.zrem(self._unack_zset_name, kw['task_str'])

    def _requeue_tasks_which_unconfirmed(self):
        lock_key = f'fsdf_lock__requeue_tasks_which_unconfirmed:{self._queue_name}'
        with decorators.RedisDistributedLockContextManager(self.redis_db_frame, lock_key, ).set_log_level(30) as lock:
            if lock.has_aquire_lock:
                # 方案C：心跳 key 只用于判断活跃消费者；全量 unack key 从 registry 获取
                heartbeat_redis_key = RedisKeys.gen_redis_hearbeat_set_key_by_queue_name(self._queue_name)
                all_heartbeat_records = self.redis_db_frame.smembers(heartbeat_redis_key)  # {"consumer_id&&timestamp", ...}
                alive_consumer_ids = set()
                for record in all_heartbeat_records:
                    parts = record.rsplit('&&', 1)
                    if parts:
                        alive_consumer_ids.add(parts[0])

                # registry 中存放具体的 unack key 名称
                all_unack_keys = self.redis_db_frame.smembers(self._unack_registry_key)
                unack_key_prefix = f'{self._queue_name}__unack_id_'

                
                # 显示当前自己的 unack 队列数量
                if time.time() - self._last_show_unacked_msg_num_log > 600:
                    self.logger.info(f'{self._unack_zset_name} 中有待确认消费任务的数量是'
                                     f' {self.redis_db_frame.zcard(self._unack_zset_name)}')
                    self._last_show_unacked_msg_num_log = time.time()
                
                # 处理死亡消费者的 unack 队列（只处理 ack-able 的 zset unack key）
                for unack_key in all_unack_keys:
                    dead_consumer_id = unack_key[len(unack_key_prefix):]
                    if dead_consumer_id in alive_consumer_ids:
                        continue
                    current_queue_unacked_msg_queue_name = unack_key
                    self.logger.warning(f'{current_queue_unacked_msg_queue_name} 是掉线或关闭消费者的')
                    while True:
                        # 【优化1】批量获取 unacked 任务
                        unacked_task_list = self.redis_db_frame.zrevrange(current_queue_unacked_msg_queue_name, 0, 1000)
                        if not unacked_task_list:
                            break
                        
                        # 先批量 publish 重回队列
                        for unacked_task_str in unacked_task_list:
                            self.logger.warning(f'从 {current_queue_unacked_msg_queue_name} 向 {self._queue_name} 重新放入掉线消费者未消费确认的任务'
                                                f' {unacked_task_str}')
                            self.publisher_of_same_queue.publish(unacked_task_str)
                        
                        # 【优化1】批量删除 unack 队列中的任务，减少 IO 次数
                        self.redis_db_frame.zrem(current_queue_unacked_msg_queue_name, *unacked_task_list)

                    # 清理 registry 和 unack key，避免 registry 无限增长
                    
                    if self.redis_db_frame.zcard(current_queue_unacked_msg_queue_name) == 0:
                        self.redis_db_frame.delete(current_queue_unacked_msg_queue_name)
                        self.redis_db_frame.srem(self._unack_registry_key, current_queue_unacked_msg_queue_name)
                

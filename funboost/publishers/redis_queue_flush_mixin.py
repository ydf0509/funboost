from funboost.constant import RedisKeys


class FlushRedisQueueMixin:
    # noinspection PyUnresolvedReferences
    def clear(self):
        self.redis_db_frame.delete(self._queue_name)
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

        # 方案C：优先从 unack registry 获取所有 unack key 直接删除（不依赖心跳是否还包含死亡消费者）
        registry_key = RedisKeys.gen_funboost_unack_registry_key_by_queue_name(self._queue_name)
        unack_keys_from_registry = self.redis_db_frame.smembers(registry_key)
        if unack_keys_from_registry:
            self.redis_db_frame.delete(*list(unack_keys_from_registry))
            self.redis_db_frame.delete(registry_key)
            self.logger.warning(f'清除 {list(unack_keys_from_registry)} 队列中的消息成功')
        
        # 兼容兜底：老逻辑仍然保留（用于尚未启用 registry 的历史场景）
        # 【优化】从心跳 set 获取所有消费者 ID，直接构造 unack 队列名称，避免使用 scan 命令
        heartbeat_redis_key = RedisKeys.gen_redis_hearbeat_set_key_by_queue_name(self._queue_name)
        all_heartbeat_records = self.redis_db_frame.smembers(heartbeat_redis_key)
        
        unack_queue_name_list = []
        for record in all_heartbeat_records:
            parts = record.rsplit('&&', 1)
            if len(parts) >= 1:
                consumer_id = parts[0]
                unack_queue_name_list.append(f'{self._queue_name}__unack_id_{consumer_id}')
                unack_queue_name_list.append(f'unack_{self._queue_name}_{consumer_id}') # brpoplpush的
        
              
        if unack_queue_name_list:
            self.redis_db_frame.delete(*unack_queue_name_list)
            self.logger.warning(f'清除 {unack_queue_name_list} 队列中的消息成功')

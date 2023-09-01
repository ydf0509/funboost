class FlushRedisQueueMixin:
    # noinspection PyUnresolvedReferences
    def clear(self):
        self.redis_db_frame.delete(self._queue_name)
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')
        # self.redis_db_frame.delete(f'{self._queue_name}__unack')
        unack_queue_name_list = self.redis_db_frame.scan(match=f'{self._queue_name}__unack_id_*', count=100000)[1] + \
                                self.redis_db_frame.scan(match=f'unack_{self._queue_name}_*', count=100000)[1]  # noqa
        if unack_queue_name_list:
            self.redis_db_frame.delete(*unack_queue_name_list)
            self.logger.warning(f'清除 {unack_queue_name_list} 队列中的消息成功')

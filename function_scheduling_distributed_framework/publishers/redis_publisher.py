# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 12:12
import json
from threading import Lock
from queue import Queue, Empty
import time
from function_scheduling_distributed_framework.publishers.base_publisher import AbstractPublisher
from function_scheduling_distributed_framework.utils import RedisMixin, decorators
from function_scheduling_distributed_framework import frame_config


class RedisPublisher(AbstractPublisher, RedisMixin):
    """
    使用redis作为中间件,
    """
    _push_method = 'rpush'

    def custom_init(self):
        self._temp_msg_queue = Queue()
        self._temp_msg_list = list()
        self._lock_for_bulk_push = Lock()
        self._last_push_time = time.time()
        decorators.keep_circulating(time_sleep=0.5, is_display_detail_exception=True, block=False, daemon=False)(self._initiative_bulk_push_to_broker, )

    def __bulk_push_and_init(self):
        if len(self._temp_msg_list) > 0:
            getattr(self.redis_db_frame, self._push_method)(self._queue_name, *self._temp_msg_list)
            self._temp_msg_list = []

    def _initiative_bulk_push_to_broker(self):  # 主动触发。concrete_realization_of_publish防止发布最后一条后没达到2000但sleep很久，无法触发at_exit，不能自动触发进入消息队列。
        with self._lock_for_bulk_push:
            self.__bulk_push_and_init()

    def concrete_realization_of_publish(self, msg):
        # print(getattr(frame_config,'has_start_a_consumer',0))
        # 这里的 has_start_a_consumer 是一个标志，借用此模块设置的一个标识变量而已，框架运行时候自动设定的，不要把这个变量写到模块里面。
        if getattr(frame_config, 'has_start_a_consumer', 0) == 0:  # 加快速度推送，否则每秒只能推送4000次。如果是独立脚本推送，使用批量推送，如果是消费者中发布任务，为了保持原子性，用原来的单个推送。
            # self._temp_msg_queue.put(msg)
            with self._lock_for_bulk_push:
                self._temp_msg_list.append(msg)
                if len(self._temp_msg_list) >= 1000:
                    # print(len(self._temp_msg_list))
                    self.__bulk_push_and_init()
        else:
            getattr(self.redis_db_frame, self._push_method)(self._queue_name, msg)

    def clear(self):
        self.redis_db_frame.delete(self._queue_name)
        self.redis_db_frame.delete(f'{self._queue_name}__unack')
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    def get_message_count(self):
        # nb_print(self.redis_db7,self._queue_name)
        return self.redis_db_frame.llen(self._queue_name)

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass

    def _at_exit(self):
        time.sleep(2) # 不需要
        # self._real_bulk_push_to_broker()
        with self._lock_for_bulk_push:
            self.__bulk_push_and_init()
        super()._at_exit()

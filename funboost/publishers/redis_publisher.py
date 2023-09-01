# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import os
import time
# noinspection PyUnresolvedReferences
from queue import Queue, Empty
from threading import Lock

from funboost import funboost_config_deafult
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.publishers.redis_queue_flush_mixin import FlushRedisQueueMixin
from funboost.utils import RedisMixin, decorators


class RedisPublisher(FlushRedisQueueMixin, AbstractPublisher, RedisMixin, ):
    """
    使用redis作为中间件,这个是大幅优化了发布速度的方式。简单的发布是 redis_publisher_0000.py 中的代码方式。

    这个是复杂版，批量推送，简单版在 funboost/publishers/redis_publisher_simple.py
    """
    _push_method = 'rpush'

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._temp_msg_queue = Queue()
        self._temp_msg_list = list()
        self._lock_for_bulk_push = Lock()
        self._last_push_time = time.time()
        decorators.keep_circulating(time_sleep=0.1, is_display_detail_exception=True, block=False,
                                    daemon=True)(self._initiative_bulk_push_to_broker, )()

    def __bulk_push_and_init(self):
        if len(self._temp_msg_list) > 0:
            getattr(self.redis_db_frame, self._push_method)(self._queue_name, *self._temp_msg_list)
            self._temp_msg_list = []

    def _initiative_bulk_push_to_broker(self):  # 主动触发。concrete_realization_of_publish防止发布最后一条后没达到2000但sleep很久，无法触发at_exit，不能自动触发进入消息队列。
        with self._lock_for_bulk_push:
            self.__bulk_push_and_init()

    def concrete_realization_of_publish(self, msg):
        # print(getattr(frame_config,'has_start_a_consumer_flag',0))
        # 这里的 has_start_a_consumer_flag 是一个标志，借用此模块设置的一个标识变量而已，框架运行时候自动设定的，不要把这个变量写到模块里面。
        # if getattr(funboost_config_deafult, 'has_start_a_consumer_flag', 0) == 0:  # 加快速度推送，否则每秒只能推送4000次。如果是独立脚本推送，使用批量推送，如果是消费者中发布任务，为了保持原子性，用原来的单个推送。
        if self.broker_exclusive_config.get('redis_bulk_push', 0) == 1:  # RedisConsumer传了,  RedisAckAble  没传
            # self._temp_msg_queue.put(msg)
            with self._lock_for_bulk_push:
                self._temp_msg_list.append(msg)
                if len(self._temp_msg_list) >= 1000:
                    # print(len(self._temp_msg_list))
                    self.__bulk_push_and_init()
        else:
            getattr(self.redis_db_frame, self._push_method)(self._queue_name, msg)
            # print(msg)

    def get_message_count(self):
        # print(self.redis_db7,self._queue_name)
        return self.redis_db_frame.llen(self._queue_name)

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass

    def _at_exit(self):
        # time.sleep(2) # 不需要
        # self._real_bulk_push_to_broker()
        with self._lock_for_bulk_push:
            self.__bulk_push_and_init()
        super()._at_exit()

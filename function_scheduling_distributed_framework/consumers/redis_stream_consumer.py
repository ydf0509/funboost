# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:32
import json
import time
from queue import Queue

import redis3

from function_scheduling_distributed_framework.consumers.base_consumer import AbstractConsumer
from function_scheduling_distributed_framework.utils import RedisMixin, decorators


class RedisStreamConsumer(AbstractConsumer, RedisMixin):
    """
    redis作为中间件实现的。
    """
    BROKER_KIND = 12

    def start_consuming_message(self):
        redis_server_info_dict = self.redis_db_frame_version3.info()
        print(redis_server_info_dict)
        if float(redis_server_info_dict['redis_version'][0]) < 5:
            raise EnvironmentError('必须是5.0版本以上redis服务端才能支持  stream 数据结构，'
                                   '请升级服务端，否则使用 REDIS_ACK_ABLE 方式使用redis')
        if self.redis_db_frame_version3.type(self._queue_name) == 'list':
            raise EnvironmentError(f'检测到已存在 {self._queue_name} 这个键，且类型是list， 必须换个队列名字或者删除这个 list 类型的键。'
                                   f'RedisStreamConsumer 使用的是 stream数据结构')
        try:
            self.redis_db_frame_version3.xgroup_create(self._queue_name, 'distributed_frame_group', id=0)
        except redis3.exceptions.ResponseError as e:
            self.logger.info(e)  # BUSYGROUP Consumer Group name already exists  不能重复创建消费者组。

        self._is_send_consumer_hearbeat_to_redis = True
        self.logger.warning('启动了任务redis确认消费助手')
        super().start_consuming_message()
        self.keep_circulating(60, block=False)(self._requeue_tasks_which_unconfirmed)()

    def _shedual_task(self):
        while True:
            # redis服务端必须是5.0以上，并且确保这个键的类型是stream不能是list数据结构。
            results = self.redis_db_frame_version3.xreadgroup('distributed_frame_group', self.consumer_identification,
                                                              {self.queue_name: ">"}, count=200, block=60 * 1000)
            if results:
                self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {results}  ')
                # print(results[0][1])
                for msg_id, msg in results[0][1]:
                    kw = {'body': json.loads(msg['']), 'msg_id': msg_id}
                    self._submit_task(kw)

    def _confirm_consume(self, kw):
        print(self.redis_db_frame_version3.xack(self._queue_name, 'distributed_frame_group', kw['msg_id']))
        self.redis_db_frame_version3.xdel(self._queue_name, kw['msg_id'])

    def _requeue(self, kw):
        # self.redis_db_frame_version3.xadd(self._queue_name, {'':json.dumps(kw['body'])})
        print(self.redis_db_frame_version3.xclaim(self._queue_name,
                                            'distributed_frame_group', self.consumer_identification,
                                            min_idle_time=0, message_ids=[kw['msg_id']]))

    def _requeue_tasks_which_unconfirmed(self):
        lock_key = f'fsdf_lock__requeue_tasks_which_unconfirmed:{self._queue_name}'
        with decorators.RedisDistributedLockContextManager(self.redis_db_frame, lock_key, ) as lock:
            if lock.has_aquire_lock:
                self._distributed_consumer_statistics.send_heartbeat()
                current_queue_hearbeat_ids = self._distributed_consumer_statistics.get_queue_heartbeat_ids(without_time=True)
                xinfo_consumers = self.redis_db_frame_version3.xinfo_consumers(self._queue_name, 'distributed_frame_group')
                print(current_queue_hearbeat_ids)
                print(xinfo_consumers)
                for xinfo_item in xinfo_consumers:
                    if xinfo_item['name'] not in current_queue_hearbeat_ids and xinfo_item['pending'] >0:
                        pending_msg_list = self.redis_db_frame_version3.xpending_range(
                            self._queue_name, 'distributed_frame_group', '-', '+', 1000, xinfo_item['name'])
                        if pending_msg_list:
                            self.logger.warning(f'从断开的消费者 {xinfo_item["name"]} 向 {self._queue_name} 的消费者 {self.consumer_identification} 中'
                                                f' 转移已断开掉线的任务 {len(pending_msg_list)} 个，详细 {pending_msg_list}')
                            print(self.redis_db_frame_version3.xclaim(self._queue_name, 'distributed_frame_group', self.consumer_identification,
                                                                min_idle_time=0, message_ids=[task_item['message_id'] for task_item in pending_msg_list]))

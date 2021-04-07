# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:32
import json
# import time

from function_scheduling_distributed_framework.consumers.base_consumer import AbstractConsumer
from function_scheduling_distributed_framework.utils import RedisMixin, decorators


class RedisBrpopLpushConsumer(AbstractConsumer, RedisMixin):
    """
    redis作为中间件实现的，使用redis list 结构实现的。
    这个如果消费脚本在运行时候随意反复重启或者非正常关闭或者消费宕机，会丢失大批任务。高可靠需要用rabbitmq或者redis_ack_able或者redis_stream的中间件方式。
    """
    BROKER_KIND = 14

    def start_consuming_message(self):
        self._is_send_consumer_hearbeat_to_redis = True
        super().start_consuming_message()
        self.logger.warning('启动了任务redis确认消费助手')
        self.keep_circulating(60, block=False)(self._requeue_tasks_which_unconfirmed)()


    # noinspection DuplicatedCode
    def _shedual_task(self):
        unack_list_name = f'unack_{self._queue_name}_{self.consumer_identification}'
        while True:
            result = self.redis_db_frame_version3.brpoplpush(self._queue_name, unack_list_name,timeout=60)
            if result:
                self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {result[1].decode()}  ')
                task_dict = json.loads(result[1])
                kw = {'body': task_dict,'raw_msg':result[1].decode()}
                self._submit_task(kw)


    def _confirm_consume(self, kw):
        pass  # redis没有确认消费的功能。
        self.redis_db_frame.lrem(self.queue_name,kw['raw_msg'],num=1)

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name, json.dumps(kw['body']))

    def _requeue_tasks_which_unconfirmed(self):
        lock_key = f'fsdf_lock__requeue_tasks_which_unconfirmed:{self._queue_name}'
        with decorators.RedisDistributedLockContextManager(self.redis_db_frame, lock_key, ) as lock:
            if lock.has_aquire_lock:
                self._distributed_consumer_statistics.send_heartbeat()
                current_queue_hearbeat_ids = self._distributed_consumer_statistics.get_queue_heartbeat_ids(without_time=True)
                current_queue_unacked_msg_queues = self.redis_db_frame.scan(0, f'unack_{self._queue_name}_*', 100)
                for current_queue_unacked_msg_queue in current_queue_unacked_msg_queues[1]:
                    current_queue_unacked_msg_queue_str = current_queue_unacked_msg_queue.decode()
                    if current_queue_unacked_msg_queue_str.split(f'unack_{self._queue_name}_')[1] not in current_queue_hearbeat_ids:
                        msg_list = self.redis_db_frame.lrange(current_queue_unacked_msg_queue_str,0,-1)
                        self.logger.warning(f"""{current_queue_unacked_msg_queue_str} 是掉线或关闭消费者的待确认任务, 将 一共 {len(msg_list)} 个消息,
                                            详情是 {msg_list} 推送到正常消费队列 {self._queue_name} 队列中。
                                            """)
                        self.redis_db_frame.lpush(self._queue_name,*msg_list)









                xinfo_consumers = self.redis_db_frame_version3.xinfo_consumers(self._queue_name, self.GROUP)
                # print(current_queue_hearbeat_ids)
                # print(xinfo_consumers)
                for xinfo_item in xinfo_consumers:
                    # print(xinfo_item)
                    if xinfo_item['idle'] > 7 * 24 * 3600 * 1000 and xinfo_item['pending'] == 0:
                        self.redis_db_frame_version3.xgroup_delconsumer(self._queue_name, self.GROUP, xinfo_item['name'])
                    if xinfo_item['name'] not in current_queue_hearbeat_ids and xinfo_item['pending'] > 0:  # 说明这个消费者掉线断开或者关闭了。
                        pending_msg_list = self.redis_db_frame_version3.xpending_range(
                            self._queue_name, self.GROUP, '-', '+', 1000, xinfo_item['name'])
                        if pending_msg_list:
                            # min_idle_time 不需要，因为加了分布式锁，所以不需要基于idle最小时间的判断，并且启动了基于心跳的确认消费助手，检测消费者掉线或关闭或断开的准确率100%。
                            xclaim_task_list = self.redis_db_frame_version3.xclaim(self._queue_name, self.GROUP, self.consumer_identification, force=True,
                                                                                   min_idle_time=0 * 1000, message_ids=[task_item['message_id'] for task_item in pending_msg_list])
                            if xclaim_task_list:
                                self.logger.warning(f' {self._queue_name}  的分组 {self.GROUP} 的消费者 {self.consumer_identification} 夺取 断开的消费者 {xinfo_item["name"]}'
                                                    f'  {len(xclaim_task_list)} 个任务，详细是 {xclaim_task_list} ')
                                for task in xclaim_task_list:
                                    kw = {'body': json.loads(task[1]['']), 'msg_id': task[0]}
                                    self._submit_task(kw)


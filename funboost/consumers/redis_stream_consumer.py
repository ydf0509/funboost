# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2021/4/3 0008 13:32
import json
import redis5
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.utils import decorators
from funboost.utils.redis_manager import RedisMixin


class RedisStreamConsumer(AbstractConsumer, RedisMixin):
    """
    redis 的 stream 结构 作为中间件实现的。需要redis 5.0以上，redis stream结构 是redis的消息队列，概念类似kafka，功能远超 list结构。
    """
    GROUP = 'funboost_group'
    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'group': 'funboost_group','pull_msg_batch_size': 100}

    def custom_init(self):
        self.group = self.consumer_params.broker_exclusive_config['group'] or self.GROUP

    def start_consuming_message(self):
        redis_server_info_dict = self.redis_db_frame.info()
        # print(redis_server_info_dict)
        if float(redis_server_info_dict['redis_version'][0]) < 5:
            raise EnvironmentError('必须是5.0版本以上redis服务端才能支持  stream 数据结构，'
                                   '请升级服务端，否则使用 REDIS_ACK_ABLE 方式使用redis 的 list 结构')
        if self.redis_db_frame.type(self._queue_name) == 'list':
            raise EnvironmentError(f'检测到已存在 {self._queue_name} 这个键，且类型是list， 必须换个队列名字或者删除这个 list 类型的键。'
                                   f'RedisStreamConsumer 使用的是 stream 数据结构')
        self.consumer_params.is_send_consumer_hearbeat_to_redis = True
        super().start_consuming_message()
        self.keep_circulating(60, block=False)(self._requeue_tasks_which_unconfirmed)()

    def _shedual_task(self):
        pull_msg_batch_size = self.consumer_params.broker_exclusive_config['pull_msg_batch_size']

        try:
            self.redis_db_frame.xgroup_create(self._queue_name,self.group , id=0, mkstream=True)
        except redis5.exceptions.ResponseError as e:
            self.logger.info(e)  # BUSYGROUP Consumer Group name already exists  不能重复创建消费者组。
        while True:
            # redis服务端必须是5.0以上，并且确保这个键的类型是stream不能是list数据结构。
            results = self.redis_db_frame.xreadgroup(self.group, self.consumer_identification,
                                                              {self.queue_name: ">"}, count=pull_msg_batch_size, block=60 * 1000)
            if results:
                # self.logger.debug(f'从redis的 [{self._queue_name}] stream 中 取出的消息是：  {results}  ')
                self._print_message_get_from_broker( results)
                # print(results[0][1])
                for msg_id, msg in results[0][1]:
                    kw = {'body': msg[''], 'msg_id': msg_id}
                    self._submit_task(kw)

    def _confirm_consume(self, kw):
        # self.redis_db_frame.xack(self._queue_name, 'distributed_frame_group', kw['msg_id'])
        # self.redis_db_frame.xdel(self._queue_name, kw['msg_id']) # 便于xlen
        with self.redis_db_frame.pipeline() as pipe:
            pipe.xack(self._queue_name, self.group, kw['msg_id'])
            pipe.xdel(self._queue_name, kw['msg_id'])  # 直接删除不需要保留， 便于xlen
            pipe.execute()

    def _requeue(self, kw):
        self.redis_db_frame.xack(self._queue_name, self.group, kw['msg_id'])
        self.redis_db_frame.xadd(self._queue_name, {'': json.dumps(kw['body'])})
        # print(self.redis_db_frame.xclaim(self._queue_name,
        #                                     'distributed_frame_group', self.consumer_identification,
        #                                     min_idle_time=0, message_ids=[kw['msg_id']]))

    def _requeue_tasks_which_unconfirmed(self):
        lock_key = f'funboost_lock__requeue_tasks_which_unconfirmed:{self._queue_name}'
        with decorators.RedisDistributedLockContextManager(self.redis_db_frame, lock_key, ) as lock:
            if lock.has_aquire_lock:
                self._distributed_consumer_statistics.send_heartbeat()
                current_queue_hearbeat_ids = self._distributed_consumer_statistics.get_queue_heartbeat_ids(without_time=True)
                xinfo_consumers = self.redis_db_frame.xinfo_consumers(self._queue_name, self.group)
                # print(current_queue_hearbeat_ids)
                # print(xinfo_consumers)
                for xinfo_item in xinfo_consumers:
                    # print(xinfo_item)
                    if xinfo_item['idle'] > 7 * 24 * 3600 * 1000 and xinfo_item['pending'] == 0:
                        self.redis_db_frame.xgroup_delconsumer(self._queue_name, self.group, xinfo_item['name'])
                    if xinfo_item['name'] not in current_queue_hearbeat_ids and xinfo_item['pending'] > 0:  # 说明这个消费者掉线断开或者关闭了。
                        pending_msg_list = self.redis_db_frame.xpending_range(
                            self._queue_name, self.group, '-', '+', 1000, xinfo_item['name'])
                        if pending_msg_list:
                            # min_idle_time 不需要，因为加了分布式锁，所以不需要基于idle最小时间的判断，并且启动了基于心跳的确认消费助手，检测消费者掉线或关闭或断开的准确率100%。
                            xclaim_task_list = self.redis_db_frame.xclaim(self._queue_name, self.group,
                                                                                   self.consumer_identification, force=True,
                                                                                   min_idle_time=0 * 1000,
                                                                                   message_ids=[task_item['message_id'] for task_item in pending_msg_list])
                            if xclaim_task_list:
                                self.logger.warning(f' {self._queue_name}  的分组 {self.group} 的消费者 {self.consumer_identification} 夺取 断开的消费者 {xinfo_item["name"]}'
                                                    f'  {len(xclaim_task_list)} 个任务，详细是 {xclaim_task_list} ')
                                for task in xclaim_task_list:
                                    kw = {'body': task[1][''], 'msg_id': task[0]}
                                    self._submit_task(kw)

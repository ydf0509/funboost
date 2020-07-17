# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2020/7/8 0008 13:27
import json
from rocketmq.client import PushConsumer, RecvMessage
from function_scheduling_distributed_framework.consumers.base_consumer import AbstractConsumer
from function_scheduling_distributed_framework import frame_config
from function_scheduling_distributed_framework.publishers.rocketmq_publisher import RocketPublisher


class RocketmqConsumer(AbstractConsumer):
    """
    安装
    """
    BROKER_KIND = 11

    def _shedual_task(self):
        consumer = PushConsumer(f'g-{self._queue_name}')
        consumer.set_namesrv_addr(frame_config.ROCKETMQ_NAMESRV_ADDR)
        consumer.set_thread_count(1)

        self._publisher = RocketPublisher(self._queue_name)

        def callback(rocketmq_msg: RecvMessage):
            self.logger.debug(f'从rocketmq的 [{self._queue_name}] 主题的队列 {rocketmq_msg.queue_id} 中 取出的消息是：{rocketmq_msg.body}')
            kw = {'body': json.loads(rocketmq_msg.body), 'rocketmq_msg': rocketmq_msg}
            self._submit_task(kw)

        consumer.subscribe(self._queue_name, callback)
        consumer.start()

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        self._publisher.publish(kw['body'])


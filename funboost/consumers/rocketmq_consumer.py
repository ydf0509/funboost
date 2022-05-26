# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2020/7/8 0008 13:27
import json
import time

from funboost.consumers.base_consumer import AbstractConsumer
from funboost import funboost_config_deafult
from funboost.publishers.rocketmq_publisher import RocketmqPublisher


class RocketmqConsumer(AbstractConsumer):
    """
    安装
    """
    BROKER_KIND = 11
    GROUP_ID = 'g_funboost'

    def _shedual_task(self):
        try:
            from rocketmq.client import PushConsumer
        except Exception as e:
            # print(traceback.format_exc())
            raise ImportError(f'rocketmq包 只支持linux和mac {e}')
        consumer = PushConsumer(self.GROUP_ID)
        consumer.set_namesrv_addr(funboost_config_deafult.ROCKETMQ_NAMESRV_ADDR)
        consumer.set_thread_count(1)
        consumer.set_message_batch_max_size(self._concurrent_num)

        self._publisher = RocketmqPublisher(self._queue_name)

        def callback(rocketmq_msg):
            # self.logger.debug(f'从rocketmq的 [{self._queue_name}] 主题的queue_id {rocketmq_msg.queue_id} 中 取出的消息是：{rocketmq_msg.body}')
            self._print_message_get_from_broker('rocketmq', rocketmq_msg.body)
            kw = {'body': json.loads(rocketmq_msg.body), 'rocketmq_msg': rocketmq_msg}
            self._submit_task(kw)

        consumer.subscribe(self._queue_name, callback)
        consumer.start()

        while True:
            time.sleep(3600)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        self._publisher.publish(kw['body'])

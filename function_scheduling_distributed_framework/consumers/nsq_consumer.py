# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:32
import json
import time
from gnsq import Consumer, Message

from function_scheduling_distributed_framework import frame_config
from function_scheduling_distributed_framework.consumers.base_consumer import AbstractConsumer
from function_scheduling_distributed_framework.utils import LogManager, nb_print

LogManager('gnsq').get_logger_and_add_handlers(20)


class NsqConsumer(AbstractConsumer):
    """
    nsq作为中间件实现的。
    """
    BROKER_KIND = 7


    def _shedual_task(self):
        consumer = Consumer(self._queue_name, 'frame_channel', frame_config.NSQD_TCP_ADDRESSES, max_in_flight=self._threads_num, heartbeat_interval=600, timeout=600, )

        @consumer.on_message.connect
        def handler(consumerx: Consumer, message: Message):
            # 第一条消息不能并发，第一条消息之后可以并发。
            self.logger.debug(f'从nsq的 [{self._queue_name}] 主题中 取出的消息是：  {message.body.decode()}')
            message.enable_async()
            kw = {'consumer': consumerx, 'message': message, 'body': json.loads(message.body)}
            self._submit_task(kw)

        consumer.start()

    def _confirm_consume(self, kw):
        kw['message'].finish()

    def _requeue(self, kw):
        kw['message'].requeue()


if __name__ == '__main__':
    LogManager(None).get_logger_and_add_handlers()


    def task(a, b):
        nb_print(f'{a}  + {b} = {a + b}')
        time.sleep(5)


    NsqConsumer('topic666', consuming_function=task, threads_num=2, ).start_consuming_message()
    NsqConsumer('topic666', consuming_function=task, threads_num=3, ).start_consuming_message()

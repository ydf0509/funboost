# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:31
import json
import rabbitpy

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.utils.rabbitmq_factory import RabbitMqFactory


class RabbitmqConsumerRabbitpy(AbstractConsumer):
    """
    使用rabbitpy实现的
    """
    BROKER_KIND = 1

    def _shedual_task(self):
        # noinspection PyTypeChecker
        channel = RabbitMqFactory(is_use_rabbitpy=1).get_rabbit_cleint().creat_a_channel()  # type:  rabbitpy.AMQP         #
        channel.queue_declare(queue=self._queue_name, durable=True)
        channel.basic_qos(prefetch_count=self._concurrent_num)
        for message in channel.basic_consume(self._queue_name, no_ack=False):
            body = message.body.decode()
            # self.logger.debug(f'从rabbitmq {self._queue_name} 队列中 取出的消息是：  {body}')
            self._print_message_get_from_broker('rabbitmq', body)
            kw = {'message': message, 'body': json.loads(message.body.decode())}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        kw['message'].ack()

    def _requeue(self, kw):
        kw['message'].nack(requeue=True)

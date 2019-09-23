# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:27
import json

from pika.exceptions import AMQPError

from function_scheduling_distributed_framework.consumers.base_consumer import AbstractConsumer
from function_scheduling_distributed_framework.utils import LogManager
from function_scheduling_distributed_framework.utils.rabbitmq_factory import RabbitMqFactory

LogManager('pika').get_logger_and_add_handlers(20)


class RabbitmqConsumer(AbstractConsumer):
    """
    使用pika包实现的。
    """
    BROKER_KIND = 0

    def _shedual_task(self):
        channel = RabbitMqFactory(is_use_rabbitpy=0).get_rabbit_cleint().creat_a_channel()
        channel.queue_declare(queue=self._queue_name, durable=True)
        channel.basic_qos(prefetch_count=self._threads_num)

        def callback(ch, method, properties, body):
            body = body.decode()
            self.logger.debug(f'从rabbitmq的 [{self._queue_name}] 队列中 取出的消息是：  {body}')
            body = json.loads(body)
            kw = {'ch': ch, 'method': method, 'properties': properties, 'body': body}
            self._submit_task(kw)

        channel.basic_consume(callback,
                              queue=self._queue_name,
                              # no_ack=True
                              )
        channel.start_consuming()

    def _confirm_consume(self, kw):
        with self._lock_for_pika:
            try:
                kw['ch'].basic_ack(delivery_tag=kw['method'].delivery_tag)  # 确认消费
            except AMQPError as e:
                self.logger.error(f'pika确认消费失败  {e}')

    def _requeue(self, kw):
        with self._lock_for_pika:
            # ch.connection.add_callback_threadsafe(functools.partial(self.__ack_message_pika, ch, method.delivery_tag))
            return kw['ch'].basic_nack(delivery_tag=kw['method'].delivery_tag)  # 立即重新入队。

    @staticmethod
    def __ack_message_pika(channelx, delivery_tagx):
        """Note that `channel` must be the same pika channel instance via which
        the message being ACKed was retrieved (AMQP protocol constraint).
        """
        if channelx.is_open:
            channelx.basic_ack(delivery_tagx)
        else:
            # Channel is already closed, so we can't ACK this message;
            # log and/or do something that makes sense for your app in this case.
            pass

# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:27
import functools
import json
from threading import Lock

from funboost.publishers.base_publisher import deco_mq_conn_error
import pikav0.exceptions
from pikav0.exceptions import AMQPError

from funboost.consumers.base_consumer import AbstractConsumer
from nb_log import LogManager, get_logger
from funboost.utils.rabbitmq_factory import RabbitMqFactory

get_logger('pikav0', log_level_int=20)


class RabbitmqConsumer(AbstractConsumer):
    """
    使用pika包实现的。
    """
    BROKER_KIND = 0

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._lock_for_pika = Lock()

    def _shedual_task(self):
        # channel = RabbitMqFactory(is_use_rabbitpy=0).get_rabbit_cleint().creat_a_channel()
        # channel.queue_declare(queue=self._queue_name, durable=True)
        # channel.basic_qos(prefetch_count=self._concurrent_num)
        def callback(ch, method, properties, body):
            body = body.decode()
            self.logger.debug(f'从rabbitmq的 [{self._queue_name}] 队列中 取出的消息是：  {body}')
            body = json.loads(body)
            kw = {'ch': ch, 'method': method, 'properties': properties, 'body': body}
            self._submit_task(kw)

        while True:
            # 文档例子  https://github.com/pika/pika
            try:
                self.logger.warning(f'使用pika 链接mq')
                self.rabbit_client = RabbitMqFactory(is_use_rabbitpy=0).get_rabbit_cleint()
                self.channel = self.rabbit_client.creat_a_channel()
                self.rabbitmq_queue = self.channel.queue_declare(queue=self._queue_name, durable=True)
                self.channel.basic_consume(callback,
                                           queue=self._queue_name,
                                           # no_ack=True
                                           )
                self.channel.start_consuming()
            # Don't recover if connection was closed by broker
            # except pikav0.exceptions.ConnectionClosedByBroker:
            #     break
            # Don't recover on channel errors
            except pikav0.exceptions.AMQPChannelError as e:
                # break
                self.logger.error(e)
                continue
                # Recover on all other connection errors
            except pikav0.exceptions.AMQPConnectionError as e:
                self.logger.error(e)
                continue

    def _confirm_consume000(self, kw):
        with self._lock_for_pika:
            try:
                kw['ch'].basic_ack(delivery_tag=kw['method'].delivery_tag)  # 确认消费
            except AMQPError as e:
                self.logger.error(f'pika确认消费失败  {e}')

    def _confirm_consume(self, kw):
        with self._lock_for_pika:
            self.__ack_message_pika(kw['ch'], kw['method'].delivery_tag)
        # kw['ch'].connection.add_callback_threadsafe(functools.partial(self.__ack_message_pika, kw['ch'], kw['method'].delivery_tag))

    def _requeue(self, kw):
        # kw['ch'].connection.add_callback_threadsafe(functools.partial(self.__nack_message_pika, kw['ch'], kw['method'].delivery_tag))
        # with self._lock_for_pika:
        # return kw['ch'].basic_nack(delivery_tag=kw['method'].delivery_tag)  # 立即重新入队。
        with self._lock_for_pika:
            self.__nack_message_pika(kw['ch'], kw['method'].delivery_tag)

    def __nack_message_pika(self, channelx, delivery_tagx):
        """Note that `channel` must be the same pika channel instance via which
        the message being ACKed was retrieved (AMQP protocol constraint).
        """
        if channelx.is_open:
            channelx.basic_nack(delivery_tagx)
        else:
            # Channel is already closed, so we can't ACK this message;
            # log and/or do something that makes sense for your app in this case.
            self.logger.error(channelx.is_open)
            pass

    def __ack_message_pika(self, channelx, delivery_tagx):
        """Note that `channel` must be the same pika channel instance via which
        the message being ACKed was retrieved (AMQP protocol constraint).
        """
        if channelx.is_open:
            channelx.basic_ack(delivery_tagx)
        else:
            # Channel is already closed, so we can't ACK this message;
            # log and/or do something that makes sense for your app in this case.
            self.logger.error(channelx.is_open)
            pass

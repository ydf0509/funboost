# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 12:03
from threading import Lock

from pika import BasicProperties

from function_scheduling_distributed_framework.publishers.base_publisher import AbstractPublisher, deco_mq_conn_error
from function_scheduling_distributed_framework.utils.rabbitmq_factory import RabbitMqFactory


class RabbitmqPublisher(AbstractPublisher):
    """
    使用pika实现的。
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._lock_for_pika = Lock()

    # noinspection PyAttributeOutsideInit
    def init_broker(self):
        self.logger.warning(f'使用pika 链接mq')
        self.rabbit_client = RabbitMqFactory(is_use_rabbitpy=0).get_rabbit_cleint()
        self.channel = self.rabbit_client.creat_a_channel()
        self.queue = self.channel.queue_declare(queue=self._queue_name, durable=True)

    # noinspection PyAttributeOutsideInit
    @deco_mq_conn_error
    def concrete_realization_of_publish(self, msg):
        with self._lock_for_pika:  # 亲测pika多线程publish会出错
            self.channel.basic_publish(exchange='',
                                       routing_key=self._queue_name,
                                       body=msg,
                                       properties=BasicProperties(
                                           delivery_mode=2,  # make message persistent   2(1是非持久化)
                                       )
                                       )

    @deco_mq_conn_error
    def clear(self):
        self.channel.queue_purge(self._queue_name)
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    @deco_mq_conn_error
    def get_message_count(self):
        with self._lock_for_pika:
            queue = self.channel.queue_declare(queue=self._queue_name, durable=True)
            return queue.method.message_count

    # @deco_mq_conn_error
    def close(self):
        self.channel.close()
        self.rabbit_client.connection.close()
        self.logger.warning('关闭pika包 链接')


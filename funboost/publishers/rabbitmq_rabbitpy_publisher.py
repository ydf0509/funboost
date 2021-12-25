# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 12:04
import os
import rabbitpy

from funboost.publishers.base_publisher import AbstractPublisher, deco_mq_conn_error
from funboost.utils.rabbitmq_factory import RabbitMqFactory


class RabbitmqPublisherUsingRabbitpy(AbstractPublisher):
    """
    使用rabbitpy包实现的。
    """

    # noinspection PyAttributeOutsideInit
    def init_broker(self):
        self.logger.warning(f'使用rabbitpy包 链接mq')
        self.rabbit_client = RabbitMqFactory(is_use_rabbitpy=1).get_rabbit_cleint()
        self.channel = self.rabbit_client.creat_a_channel()
        self.queue = self.channel.queue_declare(queue=self._queue_name, durable=True)
        self.logger.critical('rabbitpy 快速发布 有问题会丢失大量任务，如果使用 rabbitmq 建议设置中间件为 BrokerEnum.RABBITMQ_AMQPSTORM')
        os._exit(444) # noqa

    # @decorators.tomorrow_threads(10)
    @deco_mq_conn_error
    def concrete_realization_of_publish(self, msg):
        # noinspection PyTypeChecker
        import time
        # time.sleep(0.1)
        print(self.channel.basic_publish(
            exchange='',
            routing_key=self._queue_name,
            body=msg,
            properties={'delivery_mode': 2},
        ))


    @deco_mq_conn_error
    def clear(self):
        self.channel.queue_purge(self._queue_name)
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    @deco_mq_conn_error
    def get_message_count(self):
        # noinspection PyUnresolvedReferences
        ch_raw_rabbity = self.channel.channel
        return len(rabbitpy.amqp_queue.Queue(ch_raw_rabbity, self._queue_name, durable=True))

    # @deco_mq_conn_error
    def close(self):
        self.channel.close()
        self.rabbit_client.connection.close()
        self.logger.warning('关闭rabbitpy包 链接mq')

# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2026/1/14
"""
使用 amqp 包实现的高性能 RabbitMQ Publisher。
amqp 是 Celery/Kombu 底层使用的 AMQP 客户端，性能比 pika 更好。

安装：pip install amqp (通常已随 celery/kombu 安装)
"""

import amqp
from amqp import Message
from funboost.publishers.base_publisher import AbstractPublisher, deco_mq_conn_error
from funboost.funboost_config_deafult import BrokerConnConfig


class RabbitmqAmqpPublisher(AbstractPublisher):
    """
    使用 amqp 包实现，高性能 AMQP 客户端。
    amqp 是 Celery/Kombu 底层依赖，性能比 pika 更好。
    """
    
    # 类型提示，方便 IDE 补全
    connection: amqp.Connection
    channel: amqp.Channel

    def custom_init(self):
        self._queue_durable = self.publisher_params.broker_exclusive_config['queue_durable']
        arguments = {}
        if self.publisher_params.broker_exclusive_config['x-max-priority']:
            arguments['x-max-priority'] = self.publisher_params.broker_exclusive_config['x-max-priority']
        self._arguments = arguments if arguments else None

    def init_broker(self):
        self.logger.warning('使用 amqp 包链接 RabbitMQ')
        # amqp 包中空字符串表示名为空的vhost，需要转换为 '/'
        virtual_host = BrokerConnConfig.RABBITMQ_VIRTUAL_HOST or '/'
        self.connection = amqp.Connection(
            host=f'{BrokerConnConfig.RABBITMQ_HOST}:{BrokerConnConfig.RABBITMQ_PORT}',
            userid=BrokerConnConfig.RABBITMQ_USER,
            password=BrokerConnConfig.RABBITMQ_PASS,
            virtual_host=virtual_host,
            heartbeat=60 * 10,
        )
        self.connection.connect()
        self.channel = self.connection.channel()
        self.channel.queue_declare(
            queue=self._queue_name,
            durable=self._queue_durable,
            auto_delete=False,  # 队列永久存在，不会在没有消费者时被删除
            arguments=self._arguments,
        )

    @deco_mq_conn_error
    def _publish_impl(self, msg: str):
        message = Message(
            body=msg,
            delivery_mode=2,  # persistent message
        )
        self.channel.basic_publish(
            msg=message,
            exchange='',
            routing_key=self._queue_name,
        )

    @deco_mq_conn_error
    def clear(self):
        self.channel.queue_purge(self._queue_name)
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    @deco_mq_conn_error
    def get_message_count(self):
        # amqp 的 queue_declare 返回 (queue_name, message_count, consumer_count)
        # 不使用 passive=True，这样队列不存在时会自动创建而不是报错
        try:
            result = self.channel.queue_declare(
                queue=self._queue_name,
                durable=self._queue_durable,
                auto_delete=False,
                arguments=self._arguments,
            )
            if hasattr(result, 'message_count'):
                return result.message_count
            return -1
        except Exception as e:
            self.logger.warning(f'get_message_count 失败: {e}')
            return -1

    def close(self):
        self.channel.close()
        self.connection.close()
        self.logger.warning('关闭 amqp 链接')

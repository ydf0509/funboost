# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:06
import amqpstorm
from amqpstorm.basic import Basic as AmqpStormBasic
from amqpstorm.queue import Queue as AmqpStormQueue
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher, deco_mq_conn_error
from funboost.utils import decorators


class RabbitmqComplexRoutingPublisher(AbstractPublisher):
    # 使用amqpstorm包实现的mq操作。
    # 实例属性没在__init__里面写，造成代码补全很麻烦，写在这里做类属性，方便pycharm补全
    connection : amqpstorm.UriConnection
    channel : amqpstorm.Channel
    channel_wrapper_by_ampqstormbaic : AmqpStormBasic
    queue : AmqpStormQueue


    def custom_init(self):
        arguments = {}     #  {'x-queue-type':'classic'} classic stream lazy quorum
        if self.publisher_params.broker_exclusive_config.get('x-max-priority'):
            arguments['x-max-priority'] = self.publisher_params.broker_exclusive_config['x-max-priority']
        self._queue_durable = self.publisher_params.broker_exclusive_config['queue_durable']
        self.queue_declare_params = dict(queue=self._queue_name, durable=self._queue_durable,
                                         arguments=arguments,auto_delete=False)
        
        self._exchange_name = self.publisher_params.broker_exclusive_config['exchange_name']
        self._exchange_type = self.publisher_params.broker_exclusive_config['exchange_type']
        # 如果用户没有在 broker_exclusive_config 中指定 routing_key_for_publish，则默认使用队列名作为 routing_key
        self._routing_key_for_publish = self.publisher_params.broker_exclusive_config.get('routing_key_for_publish') or self._queue_name  # 这里你已经用了很好的实践

        self._exchange_declare_durable = self.publisher_params.broker_exclusive_config['exchange_declare_durable']

        self.init_broker()


    # noinspection PyAttributeOutsideInit
    # @decorators.synchronized
    def init_broker(self):
        # username=app_config.RABBITMQ_USER, password=app_config.RABBITMQ_PASS, host=app_config.RABBITMQ_HOST, port=app_config.RABBITMQ_PORT, virtual_host=app_config.RABBITMQ_VIRTUAL_HOST, heartbeat=60 * 10
        self.logger.warning(f'使用AmqpStorm包 链接mq')
        self.connection = amqpstorm.UriConnection(
            f'amqp://{BrokerConnConfig.RABBITMQ_USER}:{BrokerConnConfig.RABBITMQ_PASS}@{BrokerConnConfig.RABBITMQ_HOST}:{BrokerConnConfig.RABBITMQ_PORT}/{BrokerConnConfig.RABBITMQ_VIRTUAL_HOST}?heartbeat={60 * 10}&timeout=20000'
        )
        self.channel = self.connection.channel()  # type:amqpstorm.Channel
        self.channel_wrapper_by_ampqstormbaic = AmqpStormBasic(self.channel)
        # 发布者不声明队列，队列的声明和绑定完全由消费者负责。
        if self._exchange_name:
            self.channel.exchange.declare(exchange=self._exchange_name, exchange_type=self._exchange_type,
                                          durable=self._exchange_declare_durable)

    # @decorators.tomorrow_threads(10)
    @deco_mq_conn_error
    def _publish_impl(self, msg: str):
        routing_key_publish_dynamic = self._get_from_other_extra_params('routing_key_for_publish', msg)
        routing_key_publish = routing_key_publish_dynamic if routing_key_publish_dynamic is not None else self._routing_key_for_publish
        # 核心修正2：为 headers 交换机添加 headers 支持
        headers = self._get_from_other_extra_params('headers_for_publish', msg)

        self.channel_wrapper_by_ampqstormbaic.publish(exchange=self._exchange_name,
                                                      routing_key=routing_key_publish,
                                                      body=msg,
                                                      properties={'delivery_mode': 2,
                                                                  'priority': self._get_from_other_extra_params('priority', msg),
                                                                  'headers': headers}, )
        # nb_print(msg)

    @deco_mq_conn_error
    def clear(self):
        AmqpStormQueue(self.channel).purge(self._queue_name)
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    @deco_mq_conn_error
    def get_message_count(self):
        # noinspection PyUnresolvedReferences
        return AmqpStormQueue(self.channel).declare(**self.queue_declare_params)['message_count']

    # @deco_mq_conn_error
    def close(self):
        self.channel.close()
        self.connection.close()
        self.logger.warning('关闭amqpstorm包 链接mq')

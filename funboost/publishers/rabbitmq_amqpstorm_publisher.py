# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:06
import amqpstorm
from amqpstorm.basic import Basic as AmqpStormBasic
from amqpstorm.queue import Queue as AmqpStormQueue
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher, deco_mq_conn_error
from funboost.utils import decorators


class RabbitmqPublisherUsingAmqpStorm(AbstractPublisher):
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
        self._queue_durable =  self.publisher_params.broker_exclusive_config['queue_durable']
        self.queue_declare_params = dict(queue=self._queue_name, durable=self._queue_durable, arguments=arguments,auto_delete=False)

    # noinspection PyAttrib_durableuteOutsideInit
    # @decorators.synchronized
    def init_broker(self):
        # username=app_config.RABBITMQ_USER, password=app_config.RABBITMQ_PASS, host=app_config.RABBITMQ_HOST, port=app_config.RABBITMQ_PORT, virtual_host=app_config.RABBITMQ_VIRTUAL_HOST, heartbeat=60 * 10
        self.logger.warning(f'使用AmqpStorm包 链接mq')
        self.connection = amqpstorm.UriConnection(
            f'amqp://{BrokerConnConfig.RABBITMQ_USER}:{BrokerConnConfig.RABBITMQ_PASS}@{BrokerConnConfig.RABBITMQ_HOST}:{BrokerConnConfig.RABBITMQ_PORT}/{BrokerConnConfig.RABBITMQ_VIRTUAL_HOST}?heartbeat={60 * 10}&timeout=20000'
        )
        self.channel = self.connection.channel()  # type:amqpstorm.Channel
        self.channel_wrapper_by_ampqstormbaic = AmqpStormBasic(self.channel)
        self.queue = AmqpStormQueue(self.channel)
        self.queue.declare(**self.queue_declare_params)

    # @decorators.tomorrow_threads(10)
    @deco_mq_conn_error
    def _publish_impl(self, msg: str):
        self.channel_wrapper_by_ampqstormbaic.publish(exchange='',
                                                      routing_key=self._queue_name,
                                                      body=msg,
                                                      properties={'delivery_mode': 2, 'priority': self._get_from_other_extra_params('priroty', msg)}, )
        # nb_print(msg)

    @deco_mq_conn_error
    def clear(self):
        self.queue.purge(self._queue_name)
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    @deco_mq_conn_error
    def get_message_count(self):
        # noinspection PyUnresolvedReferences
        return self.queue.declare(**self.queue_declare_params)['message_count']

    # @deco_mq_conn_error
    def close(self):
        self.channel.close()
        self.connection.close()
        self.logger.warning('关闭amqpstorm包 链接mq')

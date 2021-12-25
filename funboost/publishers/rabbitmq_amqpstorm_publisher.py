# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 12:06
import amqpstorm
from amqpstorm.basic import Basic as AmqpStormBasic
from amqpstorm.queue import Queue as AmqpStormQueue
from funboost import funboost_config_deafult
from funboost.publishers.base_publisher import AbstractPublisher, deco_mq_conn_error


class RabbitmqPublisherUsingAmqpStorm(AbstractPublisher):
    # 使用amqpstorm包实现的mq操作。
    # 实例属性没在init里面写，造成补全很麻烦，写在这里做类属性，方便pycharm补全
    connection = amqpstorm.UriConnection
    channel = amqpstorm.Channel
    channel_wrapper_by_ampqstormbaic = AmqpStormBasic
    queue = AmqpStormQueue

    # noinspection PyAttributeOutsideInit
    # @decorators.synchronized
    def init_broker(self):
        # username=app_config.RABBITMQ_USER, password=app_config.RABBITMQ_PASS, host=app_config.RABBITMQ_HOST, port=app_config.RABBITMQ_PORT, virtual_host=app_config.RABBITMQ_VIRTUAL_HOST, heartbeat=60 * 10
        self.logger.warning(f'使用AmqpStorm包 链接mq')
        self.connection = amqpstorm.UriConnection(
            f'amqp://{funboost_config_deafult.RABBITMQ_USER}:{funboost_config_deafult.RABBITMQ_PASS}@{funboost_config_deafult.RABBITMQ_HOST}:{funboost_config_deafult.RABBITMQ_PORT}/{funboost_config_deafult.RABBITMQ_VIRTUAL_HOST}?heartbeat={60 * 10}'
        )
        self.channel = self.connection.channel()  # type:amqpstorm.Channel
        self.channel_wrapper_by_ampqstormbaic = AmqpStormBasic(self.channel)
        self.queue = AmqpStormQueue(self.channel)
        self.queue.declare(queue=self._queue_name, durable=True)

    # @decorators.tomorrow_threads(10)
    @deco_mq_conn_error
    def concrete_realization_of_publish(self, msg):
        self.channel_wrapper_by_ampqstormbaic.publish(exchange='',
                                                      routing_key=self._queue_name,
                                                      body=msg,
                                                      properties={'delivery_mode': 2}, )
        # nb_print(msg)

    @deco_mq_conn_error
    def clear(self):
        self.queue.purge(self._queue_name)
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    @deco_mq_conn_error
    def get_message_count(self):
        # noinspection PyUnresolvedReferences
        return self.queue.declare(queue=self._queue_name, durable=True)['message_count']

    # @deco_mq_conn_error
    def close(self):
        self.channel.close()
        self.connection.close()
        self.logger.warning('关闭amqpstorm包 链接mq')

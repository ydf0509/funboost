# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:30

import amqpstorm
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers.rabbitmq_amqpstorm_publisher import RabbitmqPublisherUsingAmqpStorm
from funboost.core.func_params_model import PublisherParams


class RabbitmqConsumerAmqpStorm(AbstractConsumer):
    """
    使用AmqpStorm实现的，多线程安全的，不用加锁。
    funboost 强烈推荐使用这个做消息队列中间件。
    """
    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'x-max-priority': None,'no_ack':False}  # x-max-priority 是 rabbitmq的优先级队列配置，必须为整数，强烈建议要小于5。为None就代表队列不支持优先级。

    def _shedual_task(self):
        # noinspection PyTypeChecker
        def callback(amqpstorm_message: amqpstorm.Message):
            body = amqpstorm_message.body
            # self.logger.debug(f'从rabbitmq的 [{self._queue_name}] 队列中 取出的消息是：  {body}')
            kw = {'amqpstorm_message': amqpstorm_message, 'body': body}
            self._submit_task(kw)

        rp = RabbitmqPublisherUsingAmqpStorm(publisher_params=PublisherParams(queue_name=self.queue_name,
                                                                              broker_exclusive_config=self.consumer_params.broker_exclusive_config))
        rp.init_broker()
        rp.channel_wrapper_by_ampqstormbaic.qos(self.consumer_params.concurrent_num)
        rp.channel_wrapper_by_ampqstormbaic.consume(callback=callback, queue=self.queue_name, no_ack=self.consumer_params.broker_exclusive_config['no_ack'],
                                                    )
        self._rp=rp
        rp.channel.start_consuming(auto_decode=True)

    def _confirm_consume(self, kw):
        # noinspection PyBroadException
        if self.consumer_params.broker_exclusive_config['no_ack'] is False:
            try:
                kw['amqpstorm_message'].ack()  # 确认消费
            except BaseException as e:
                self.logger.error(f'AmqpStorm确认消费失败  {type(e)} {e}')

    def _requeue(self, kw):
        # amqpstorm.Message.delivery_tag
        # print(kw['amqpstorm_message'].delivery_tag)
        kw['amqpstorm_message'].nack(requeue=True)
        # kw['amqpstorm_message'].reject(requeue=True)
        # kw['amqpstorm_message'].ack()
        # self.publisher_of_same_queue.publish(kw['body'])


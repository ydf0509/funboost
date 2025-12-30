# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:30
import amqpstorm
from funboost.consumers.rabbitmq_amqpstorm_consumer import RabbitmqConsumerAmqpStorm
from amqpstorm.queue import Queue as AmqpStormQueue


class RabbitmqComplexRoutingConsumer(RabbitmqConsumerAmqpStorm):
    """
    
    """
    def custom_init(self):
        super().custom_init()
        rp = self.bulid_a_new_publisher_of_same_queue()
        rp.init_broker()  # 发布者那边只声明了交换机

        # 消费者负责声明队列和唯一的绑定逻辑
        AmqpStormQueue(rp.channel).declare(**rp.queue_declare_params)
        
        # 消费者负责唯一的绑定逻辑
        if rp._exchange_name:
            self.logger.info(f'消费者开始绑定: 队列 [{self._queue_name}] <--> 交换机 [{rp._exchange_name}] (类型: {rp._exchange_type})')
            
            routing_key_bind = self.consumer_params.broker_exclusive_config.get('routing_key_for_bind')
            arguments_for_bind = None

            if rp._exchange_type == 'fanout':
                routing_key_bind = ''  # fanout 必须使用空 routing_key
            elif rp._exchange_type == 'headers':
                routing_key_bind = ''  # headers 必须使用空 routing_key
                arguments_for_bind = self.consumer_params.broker_exclusive_config.get('headers_for_bind', {})
                arguments_for_bind['x-match'] = self.consumer_params.broker_exclusive_config.get('x_match_for_bind', 'all')
            elif routing_key_bind is None:  # 用户未指定绑定键时，根据交换机类型设置默认值
                if rp._exchange_type == 'topic':
                    routing_key_bind = '#'  # topic 默认订阅所有
                else:  # direct
                    routing_key_bind = self._queue_name

            AmqpStormQueue(rp.channel).bind(queue=self._queue_name, exchange=rp._exchange_name,
                                           routing_key=routing_key_bind, arguments=arguments_for_bind)
        self._rp = rp

    def _dispatch_task(self):
        # 重写父类的方法，以支持更复杂的绑定逻辑
        def callback(amqpstorm_message: amqpstorm.Message):
            body = amqpstorm_message.body
            kw = {'amqpstorm_message': amqpstorm_message, 'body': body}
            self._submit_task(kw)

        rp = self._rp
        rp.channel_wrapper_by_ampqstormbaic.qos(self.consumer_params.concurrent_num)
        rp.channel_wrapper_by_ampqstormbaic.consume(callback=callback, queue=self.queue_name, no_ack=self.consumer_params.broker_exclusive_config['no_ack'])
        rp.channel.start_consuming(auto_decode=True)

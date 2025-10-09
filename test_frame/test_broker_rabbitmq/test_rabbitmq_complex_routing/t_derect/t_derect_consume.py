
# -*- coding: utf-8 -*-
# @Author  : ydf

import time
from funboost import BoosterParams, BrokerEnum, PriorityConsumingControlConfig, ctrl_c_recv, BoostersManager, PublisherParams

# 假设 RABBITMQ_COMPLEX_ROUTING 是您自定义的支持复杂路由的 amqpstorm broker
# 如果不是，请替换为 funboost 内置的 BrokerEnum.RABBITMQ_AMQPSTORM
BROKER_KIND_FOR_TEST = BrokerEnum.RABBITMQ_COMPLEX_ROUTING

# 定义交换机名称
EXCHANGE_NAME = 'direct_log_exchange'


@BoosterParams(
    queue_name='q_info5',  # 队列1的名字
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'direct',
        'routing_key_for_bind': 'info',  # 关键：此队列只通过 info 这个 key 绑定到交换机
    })
def info_fun(msg: str):
    """这个消费者只处理info级别的日志"""
    print(f'【INFO消费者】 收到消息: {msg}')
    time.sleep(1)


@BoosterParams(
    queue_name='q_error5',  # 队列2的名字
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'direct',
        'routing_key_for_bind': 'error',  # 关键：此队列只通过 error 这个 key 绑定到交换机
    })
def error_fun(msg: str):
    """这个消费者只处理error级别的日志"""
    print(f'!!!!!!!!!!【ERROR消费者】 收到消息: {msg} !!!!!!!!!!')
    time.sleep(1)


if __name__ == '__main__':
    # 清理之前的消息
    # info_fun.clear()
    # error_fun.clear()

  
    # time.sleep(5)
    # print(info_fun.get_message_count())
    # print(error_fun.get_message_count())

    # # 启动消费
    # info_fun.consume()
    # error_fun.consume()

    # 阻塞主线程，使消费者可以持续运行
    ctrl_c_recv()
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 14:57

from auto_run_on_remote import run_current_script_on_remote
# run_current_script_on_remote()

import random

import time

from funboost import boost, BrokerEnum,ExceptionForRequeue


@boost('test_rpc_queue', is_using_rpc_mode=True, broker_kind=BrokerEnum.REDIS_ACK_ABLE, qps=100,max_retry_times=5)
def add(a, b):
    time.sleep(2)
    if random.random() >0.5:
        raise ValueError('模拟消费函数出错，触发重试')
        # raise ExceptionForRequeue('模拟消费函数可能出错,抛出ExceptionForRequeue类型的错误可以使消息立即重回消息队列')
    return a + b


if __name__ == '__main__':
    add.consume()


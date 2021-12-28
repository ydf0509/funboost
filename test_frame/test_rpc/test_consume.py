# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
import time

from funboost import boost, BrokerEnum


@boost('test_rpc_queue', is_using_rpc_mode=True, broker_kind=BrokerEnum.REDIS_ACK_ABLE, qps=100)
def add(a, b):
    time.sleep(2)
    return a / b


if __name__ == '__main__':
    add.consume()


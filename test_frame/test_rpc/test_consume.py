# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
import time

from function_scheduling_distributed_framework import task_deco, BrokerEnum


@task_deco('test_rpc_queue', is_using_rpc_mode=True, broker_kind=BrokerEnum.REDIS_ACK_ABLE,qps=100)
def add(a, b):
    time.sleep(2)
    return a / b


if __name__ == '__main__':
    add.consume()


# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
import time

from function_scheduling_distributed_framework import get_publisher, PriorityConsumingControlConfig



pb = get_publisher('queue_test33',broker_kind=2)


# [consumer.publisher_of_same_queue.publish({'a': i, 'b': 2 * i}) for i in range(100)]

for i in range(10000000):
    a = i
    b = i * 2
    async_result = pb.publish({'a': a, 'b': b})
    print(f'{a}  {b} 之和是 {async_result.result}')
    







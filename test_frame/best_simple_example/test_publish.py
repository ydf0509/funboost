# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
import time

from test_frame.best_simple_example.test_consume import consumer

consumer.publisher_of_same_queue.clear()
# 这里的publisher_of_same_queue 也可以使用get_publisher函数得到发布者，但需要手动确保消费者的队列名字与发布者的队列名字一致，并且中间件种类一致。用法如下。
# pb = get_publisher('queue_test2',broker_kind=6)
# pb.publish({'a': i, 'b': 2 * i})



# [consumer.publisher_of_same_queue.publish({'a': i, 'b': 2 * i}) for i in range(100)]

for i in range(10000):
    time.sleep(0.05)
    consumer.publisher_of_same_queue.publish({'a': i, 'b': 2 * i})
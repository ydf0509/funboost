# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
import time

from test_frame.test_frame_using_thread.test_consume import consumer_add,consumer_sub

pb = consumer_add.publisher_of_same_queue
pb.clear()

for i in range(10000):
    time.sleep(0.1)
    pb.publish({'a': i, 'b': 2 * i})
    consumer_sub.publisher_of_same_queue.publish({'x':i,'y':i * 6})
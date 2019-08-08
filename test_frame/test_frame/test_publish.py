# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
from test_frame.test_frame.test_consume import consumer

consumer.publisher_of_same_queue.clear()
[consumer.publisher_of_same_queue.publish({'a': i, 'b': 2 * i}) for i in range(10000)]

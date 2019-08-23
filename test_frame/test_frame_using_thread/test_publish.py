# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
from test_frame.test_frame_using_thread.test_consume import consumer

pb = consumer.publisher_of_same_queue
pb.clear()
[pb.publish({'a': i, 'b': 2 * i}) for i in range(500)]

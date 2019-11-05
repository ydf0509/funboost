# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
import time

from test_frame.test_frame_using_thread.test_consume import consumer_add

pb_add = consumer_add.bulid_a_new_publisher_of_same_queue().set_is_using_rpc_mode()
pb_add.clear()

for i in range(10000):
    # time.sleep(0.2)
    async_result = pb_add.publish(dict(a=i, b=2 * i))
    # print(async_result.status_and_result)
    # print('结果', async_result.result)
    # consumer_sub.publisher_of_same_queue.publish({'x':i,'y':i * 6})

"""
mtfy
export PYTHONPATH=./
python test_frame/test_frame_using_thread/test_publish.py
"""





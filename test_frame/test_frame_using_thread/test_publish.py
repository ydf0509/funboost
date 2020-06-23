# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57

from test_frame.test_frame_using_thread.test_consume import consumer_add, consumer_sub
from function_scheduling_distributed_framework.publishers.base_publisher import PriorityConsumingControlConfig

pb_add = consumer_add.bulid_a_new_publisher_of_same_queue()
pb_add.clear()

pb_sub = consumer_sub.bulid_a_new_publisher_of_same_queue()
pb_sub.clear()

for i in range(1000000):
    # time.sleep(0.2)
    async_result = pb_add.publish(dict(a=i, b=2 * i))
    # print(async_result.status_and_result)
    # print('结果', async_result.result)
    # async_result = consumer_sub.publisher_of_same_queue.publish({'x': i, 'y': i * 6},
    #                                                             priority_control_config=PriorityConsumingControlConfig(is_using_rpc_mode=False))
    # print('同步结果', async_result.result)

"""
mtfy
export PYTHONPATH=./
python test_frame/test_frame_using_thread/test_publish.py
"""


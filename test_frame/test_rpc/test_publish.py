# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
from function_scheduling_distributed_framework import PriorityConsumingControlConfig
from test_frame.test_rpc.test_consume import add

for i in range(100):
    async_result = add.push(i, i * 2)
    print(async_result.result)


    async_result = add.publish(dict(a=i*10, b=i * 20),priority_control_config = PriorityConsumingControlConfig(is_using_rpc_mode=True))
    print(async_result.status_and_result)

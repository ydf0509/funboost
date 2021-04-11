# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57

from test_frame.test_rpc.test_consume import add

for i in range(100):
    async_result = add.push(i, i * 2)
    print(async_result.result)

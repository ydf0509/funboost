# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
import time

from test_frame.best_simple_example.test_consume import f2

f2.clear()

for i in range(10000):
    time.sleep(0.1)
    f2.pub({'a': i, 'b': 2 * i})  # pub这是发布字典，另外还能设置函数控制参数
    f2.push(i, i * 2)  # push这是发布函数参数形式，不是发布一个指点的形式

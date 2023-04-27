# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 14:57
import time

from funboost import get_publisher

pb = get_publisher('task1_queue', broker_kind=2)

for i in range(100):
    pb.publish({'x':i,'y':i * 2})
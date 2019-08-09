# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
import time

from function_scheduling_distributed_framework import get_publisher
from test_frame.my_patch_frame_config import do_patch_frame_config

do_patch_frame_config()
pb = get_publisher('task1_queue', broker_kind=2)

for i in range(100):
    pb.publish({'x':i,'y':i * 2})
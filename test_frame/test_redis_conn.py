# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:53
from function_scheduling_distributed_framework.utils import RedisMixin

from test_frame.my_patch_frame_config import do_patch_frame_config

do_patch_frame_config()

print(RedisMixin().redis_db_frame.keys())
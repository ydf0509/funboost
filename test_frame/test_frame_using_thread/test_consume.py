# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
import time
import random

from function_scheduling_distributed_framework import get_consumer
from function_scheduling_distributed_framework.utils import LogManager

from test_frame.my_patch_frame_config import do_patch_frame_config

do_patch_frame_config()

logger = LogManager('f2').get_logger_and_add_handlers()


def add(a, b):
    logger.info(f'消费此消息 {a} + {b} 中。。。。。')
    time.sleep(random.randint(30,50))  # 模拟做某事需要阻塞10秒种，必须用并发绕过此阻塞。
    logger.info(f'计算 {a} + {b} 得到的结果是  {a + b}')

def sub(x, y):
    logger.info(f'消费此消息 {x} - {y} 中。。。。。')
    time.sleep(4)  # 模拟做某事需要阻塞10秒种，必须用并发绕过此阻塞。
    logger.info(f'计算 {x} - {y} 得到的结果是  {x - y}')

# 把消费的函数名传给consuming_function，就这么简单。
consumer_add = get_consumer('queue_test54', consuming_function=add, threads_num=80, msg_schedule_time_intercal=0.01, log_level=10, logger_prefix='zz平台消费',
                        function_timeout=80, is_print_detail_exception=True,
                        msg_expire_senconds=3600, broker_kind=6, concurrent_mode=1)  # 通过设置broker_kind，一键切换中间件为rabbitmq或redis等9种中间件或包。

consumer_sub =  get_consumer('queue_test55', consuming_function=sub, threads_num=50, msg_schedule_time_intercal=0.2, log_level=10, logger_prefix='xxxxx平台消费',
                        function_timeout=80, is_print_detail_exception=True,
                        broker_kind=9, concurrent_mode=1)  # 通过设置

if __name__ == '__main__':
    # consumer_add.start_consuming_message()
    consumer_sub.start_consuming_message()
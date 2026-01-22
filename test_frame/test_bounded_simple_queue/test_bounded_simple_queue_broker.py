# -*- coding: utf-8 -*-
"""
有界 SimpleQueue Broker 测试

演示按照 funboost 文档 4.21 章节，动态扩展 broker 的使用方法：
1. 导入 bounded_simple_queue_broker 模块（自动注册 broker）
2. 使用 broker_kind='BOUNDED_SIMPLE_QUEUE' 
"""

import time
import datetime
from funboost import boost, BoosterParams, ConcurrentModeEnum

# 导入自定义 broker（导入即自动注册）
from test_frame.test_bounded_simple_queue.bounded_simple_queue_broker import BOUNDED_SIMPLE_QUEUE


total_cnt = 200000

class GlobalVars:
    t_start_publish = None
    t_end_publish = None
    t_start_consume = None
    t_end_consume = None


@boost(BoosterParams(
    queue_name='test_bounded_simple_queue',
    broker_kind=BOUNDED_SIMPLE_QUEUE,
    concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
    log_level=20,
    broker_exclusive_config={
        'maxsize': 500000,  # 队列最大容量
    }
))
def f(x):
    if x == 0:
        GlobalVars.t_start_consume = time.time()
    if x == total_cnt:
        GlobalVars.t_end_consume = time.time()
    if x % 10000 == 0:
        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], x)


if __name__ == '__main__':
    time.sleep(5)
    for i in range(0, total_cnt + 1):
        if i == 0:
            GlobalVars.t_start_publish = time.time()
        if i == total_cnt:
            GlobalVars.t_end_publish = time.time()
        if i % 10000 == 0:
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], i)
        f.push(i)
    
    f.consume()
    
    while GlobalVars.t_end_consume is None:
        time.sleep(0.1)
    
    print(f"publish time: {GlobalVars.t_end_publish - GlobalVars.t_start_publish}")
    print(f"consume time: {GlobalVars.t_end_consume - GlobalVars.t_start_consume}")

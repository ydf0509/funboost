# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 14:57
import gevent.monkey;gevent.monkey.patch_all()  # 需要打猴子补丁。
# import eventlet;eventlet.monkey_patch(all=True)
import time
from funboost import ConcurrentModeEnum, BoosterParams


@BoosterParams(queue_name='queue_test62', concurrent_num=200, log_level=10, logger_prefix='zz平台消费',
               function_timeout=20, is_print_detail_exception=True,
               msg_expire_senconds=500, concurrent_mode=ConcurrentModeEnum.GEVENT)
def f2(a, b):
    print(f'消费此消息 {a} + {b} 中。。。。。')
    time.sleep(10)  # 模拟做某事需要阻塞10秒种，必须用并发绕过此阻塞。
    print(f'计算 {a} + {b} 得到的结果是  {a + b}')


@BoosterParams(queue_name='queue_test63', concurrent_num=200, log_level=10, logger_prefix='zz平台消费',
               function_timeout=20, is_print_detail_exception=True,
               msg_expire_senconds=500, concurrent_mode=ConcurrentModeEnum.GEVENT)
def f3(a, b):
    print(f'消费此消息 {a} + {b} 中。。。。。')
    time.sleep(10)  # 模拟做某事需要阻塞10秒种，必须用并发绕过此阻塞。
    print(f'计算 {a} + {b} 得到的结果是  {a + b}')

if __name__ == '__main__':
    for i in range(100):
        f2.push(1 * i, 2 * i)
        f3.push(1 * i, 2 * i)
    f2.consume()
    f3.consume()

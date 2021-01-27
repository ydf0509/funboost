# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
import time
import random

from function_scheduling_distributed_framework import task_deco, LogManager, BrokerEnum


@task_deco('queue_test2', qps=6, broker_kind=BrokerEnum.PERSISTQUEUE, )  # 通过设置broker_kind，一键切换中间件为mq或redis等15种中间件或包。
def f2(a, b):
    # sleep_time = random.randrange(1,300) /10
    sleep_time = 0.07
    # sleep_time = 20
    print(f'消费此消息 {a} + {b} 中。。。。。,此次需要消耗 {sleep_time} 秒')
    time.sleep(sleep_time)  # 模拟做某事需要阻塞n秒种，必须用并发绕过此阻塞。
    print(f'计算 {a} + {b} 得到的结果是  {a + b}')


if __name__ == '__main__':
    f2.clear()
    for i in range(200):
        f2.push(i, i * 2)
    f2.consume()

# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 14:57
import threading

import time
from funboost import boost, BrokerEnum


# 通过设置broker_kind，一键切换中间件为mq或redis等20种中间件或包。
# 通过设置concurrent_mode，来设置并发方式，改这一个参数能自动支持threading eventlet gevent asyncio并发
# 通过设置qps，能够精确的指定每秒运行多少次函数，无视函数需要耗时多久。
# 通过设置concurrent_num，设置并发大小。此例，设置300的线程池大小，但qps为6，函数需要耗时5秒钟，
#    框架的智能线程池会自动只开30个线程，不会造成启动线程太多切换影响效率性能，所以可以自信大胆的设置线程数量。
#    智能线程池能自动扩大也能自动缩小线程数量，例如某段时间函数耗时大，会增大线程数量来达到qps，如果函数耗时变小了，会自动缩小线程数量，框架不需要提前知道函数的确定耗时，会自动调节并发数量的。
# 还有其他30种函数运行控制参数，看代码里面的函数入参说明，说的非常详细了。

# @boost('queue_test2', )  # @task_deco必须参数只有一个。
@boost('queue_test2', qps=6, broker_kind=BrokerEnum.REDIS)
def f2(a, b):
    sleep_time = 7
    result = a + b
    print(f'消费此消息 {a} + {b} 中。。。。。,此次需要消耗 {sleep_time} 秒')
    time.sleep(sleep_time)  # 模拟做某事需要阻塞n秒种，必须用并发绕过此阻塞。
    print(f'{a} + {b} 的结果是 {result}')
    return result


if __name__ == '__main__':
    pass
    # print(f2.__name__)
    # f2.clear()
    # for i in range(200):
    #     f2.push(i, i * 2)
    f2.consume()



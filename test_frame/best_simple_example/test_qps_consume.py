# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 14:57
import time
import threading
from funboost import boost, BrokerEnum,ConcurrentModeEnum

t_start = time.time()

@boost('queue_test2_qps', qps=2, broker_kind=BrokerEnum.PERSISTQUEUE, concurrent_mode=ConcurrentModeEnum.THREADING, concurrent_num=600)
def f2(a, b):
    """
    concurrent_num = 600 不用怕，因为这是智能线程池，如果函数耗时短，不会真开那么多线程。
    这个例子是测试函数耗时是动态变化的，这样就不可能通过提前设置参数预估函数固定耗时和搞鬼了。看看能不能实现qps稳定和线程池自动扩大自动缩小
    要说明的是打印的线程数量也包含了框架启动时候几个其他的线程，所以数量不是刚好和所需的线程计算一样的。

    ## 可以在运行控制台搜索 新启动线程  这个关键字，看看是不是何时适合扩大线程数量。
    ## 可以在运行控制台搜索 停止线程  这个关键字，看看是不是何时适合缩小线程数量。
    """
    result = a + b
    sleep_time = 0.01
    if time.time() - t_start > 60:  # 先测试函数耗时慢慢变大了，框架能不能按需自动增大线程数量
        sleep_time = 7
    if time.time() - t_start > 120:
        sleep_time = 31
    if time.time() - t_start > 200:
        sleep_time = 79
    if time.time() - t_start > 400: # 最后把函数耗时又减小，看看框架能不能自动缩小线程数量。
        sleep_time = 0.8
    if time.time() - t_start > 500:
        sleep_time = None
    print(f'{time.strftime("%H:%M:%S")}  ，当前线程数量是 {threading.active_count()},   {a} + {b} 的结果是 {result}， sleep {sleep_time} 秒')
    if sleep_time is not None:
        time.sleep(sleep_time)  # 模拟做某事需要阻塞n秒种，必须用并发绕过此阻塞。
    return result

if __name__ == '__main__':
    f2.clear()
    for i in range(1400):
        f2.push(i, i * 2)
    f2.consume()
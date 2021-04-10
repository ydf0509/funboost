import time

"""
这种是多进程方式，一次编写能够兼容win和linux的运行。一次性启动16个进程 叠加 多线程 并发。
"""
from function_scheduling_distributed_framework import task_deco, BrokerEnum, ConcurrentModeEnum, run_consumer_with_multi_process
import os
import requests
import threading


@task_deco('test_multi_process_queue', broker_kind=BrokerEnum.REDIS_ACK_ABLE, concurrent_mode=ConcurrentModeEnum.THREADING, qps=10)
def fff(x):
    # resp = requests.get('http://www.baidu.com/content-search.xml')
    resp = requests.get('http://127.0.0.1')
    print(x, os.getpid(), threading.get_ident(), resp.text[:5])


if __name__ == '__main__':
    # for i in range(10000):
    #     fff.push(i)
    # fff.consume() # 这个是单进程多线程/协程 消费。
    # 一次性启动16个进程 叠加 多线程 并发。此demo可以作为超高速爬虫例子，能充分利用io和cpu，在16核机器上请求效率远远暴击 scrapy 数十倍，大家可以亲自对比测试。
    run_consumer_with_multi_process(fff, 4)
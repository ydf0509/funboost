import time
"""
这种是多进程方式，一次编写能够兼容win和linux的运行。一次性启动6个进程 叠加 多线程 并发。
"""
from function_scheduling_distributed_framework import task_deco, BrokerEnum, ConcurrentModeEnum, run_consumer_with_multi_process
import os

@task_deco('test_multi_process_queue',broker_kind=BrokerEnum.REDIS,concurrent_mode=ConcurrentModeEnum.THREADING,log_level=20)
def fff(x):
    pass
    # print(x * 10,os.getpid())

if __name__ == '__main__':
    # fff.consume()
    run_consumer_with_multi_process(fff,16) # 一次性启动6个进程 叠加 多线程 并发。

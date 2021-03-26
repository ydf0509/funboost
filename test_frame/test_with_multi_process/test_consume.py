import time

"""
这种是多进程方式，一次编写能够兼容win和linux的运行。一次性启动6个进程 叠加 多线程 并发。
"""
import os
from function_scheduling_distributed_framework import task_deco, BrokerEnum, ConcurrentModeEnum, run_consumer_with_multi_process


@task_deco('test_multi_process_queue', broker_kind=BrokerEnum.REDIS, concurrent_mode=ConcurrentModeEnum.THREADING, log_level=20, qps=2)
def fff(x):
    time.sleep(0.1)
    print(x * 10, os.getpid())


if __name__ == '__main__':
    # fff.consume()

    run_consumer_with_multi_process(fff, 1)  # 一次性启动6个进程 叠加 多线程 并发。

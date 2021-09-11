
from auto_run_on_remote import run_current_script_on_remote
run_current_script_on_remote()
import os

import time
import random
from function_scheduling_distributed_framework import task_deco, BrokerEnum,ConcurrentModeEnum


# @task_deco('test_queue66', broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM, qps=5, log_level=10, is_print_detail_exception=False, is_show_message_get_from_broker=False,
#            is_using_distributed_frequency_control=True)
@task_deco('test_queue667', broker_kind=BrokerEnum.REDIS,log_level=20,concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,qps=3)
def f(x, y):
    # time.sleep(10)
    if x %10 == 0:
        print(x)
    # print(f''' pid:{os.getpid()}, {int(time.time())} 计算  {x} + {y} = {x + y}''')
    # time.sleep(0.7)
    # return x + y


if __name__ == '__main__':
    f.clear()
    for i in range(10000):
        f.push(i, i * 2)
    f.consume()
    # f.multi_process_consume(2)

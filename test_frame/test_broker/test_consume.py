# coding=utf-8
from auto_run_on_remote import run_current_script_on_remote
# run_current_script_on_remote()
import json
import os

import time
import random
# from distributed_frame_config import REDIS_HOST
import nb_log
from concurrent.futures import ProcessPoolExecutor
from funboost import boost, BrokerEnum, ConcurrentModeEnum, FunctionResultStatusPersistanceConfig
from funboost.utils import RedisMixin
from funboost.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAble

pool = ThreadPoolExecutorShrinkAble(10)


# @boost('test_queue66', broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM, qps=5, log_level=10, is_print_detail_exception=False, is_show_message_get_from_broker=False,
#            is_using_distributed_frequency_control=True)
@boost('test_queue70ac', do_task_filtering=True, qps=0, log_level=20, concurrent_num=20)
def f(x, y):
    # time.sleep(100)
    return x + y

pool2 = ProcessPoolExecutor(4)
@boost('test_queue73ac', log_level=10, broker_kind=BrokerEnum.SQLITE_QUEUE, qps=0,
       # specify_concurrent_pool= pool2,
       concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD, concurrent_num=3)
def f2(a, b):
    # time.sleep(100)
    print(a, b)
    if a % 10000 == 0:
        print(a)
    sum = 0
    for i in range(10000*10000):
        sum +=i
    return a - b


if __name__ == '__main__':
    # pass
    # f.clear()
    # f2.clear()
    for i in range(1000):
        # f.push(i, i * 2)
        f2.push(i, i * 2)

    # f2.consume()

    f2.multi_process_consume(5)

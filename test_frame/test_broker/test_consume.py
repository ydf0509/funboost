from auto_run_on_remote import run_current_script_on_remote
# run_current_script_on_remote()
import json
import os
import time
import random
# from distributed_frame_config import REDIS_HOST
from funboost import boost, BrokerEnum, ConcurrentModeEnum, FunctionResultStatusPersistanceConfig
from funboost.utils import RedisMixin
from funboost.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAble


pool = ThreadPoolExecutorShrinkAble(10)
# @boost('test_queue66', broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM, qps=5, log_level=10, is_print_detail_exception=False, is_show_message_get_from_broker=False,
#            is_using_distributed_frequency_control=True)
@boost('test_queue70ac',)
def f(x, y):
    # time.sleep(100)
    return x + y


@boost('test_queue72ac',)
def f2(a, b):
    # time.sleep(100)
    return a - b


if __name__ == '__main__':
    # pass
    # f.clear()
    for i in range(1000):
        f.push(i, i * 2)
        f2.push(i, i * 2)

    f.consume()
    f2.consume()


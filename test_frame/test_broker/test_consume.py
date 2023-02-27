# coding=utf-8
import sys
print(sys.path)
import os



print(os.getenv('path'))
from auto_run_on_remote import run_current_script_on_remote
# run_current_script_on_remote()
import json
import os

import time
import random
# from distributed_frame_config import REDIS_HOST
import nb_log
from concurrent.futures import ProcessPoolExecutor
from funboost import boost, BrokerEnum, ConcurrentModeEnum, FunctionResultStatusPersistanceConfig,boost_queue__fun_map
from funboost.utils import RedisMixin
from funboost.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAble

pool = ThreadPoolExecutorShrinkAble(10)


# @boost('test_queue66', broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM, qps=5, log_level=10, is_print_detail_exception=False, is_show_message_get_from_broker=False,
#            is_using_distributed_frequency_control=True)
@boost('test_queue70ac', do_task_filtering=True, qps=0, log_level=20, concurrent_num=20,broker_exclusive_config={'a':1})
def f(x, y):
    # time.sleep(100)
    return x + y

pool2 = ProcessPoolExecutor(4)

@boost('test_queue77h', log_level=10, broker_kind=BrokerEnum.REDIS_STREAM,
       create_logger_file=False,is_show_message_get_from_broker=True,concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
       concurrent_num=50,
       # specify_concurrent_pool= pool2,
       # concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD, concurrent_num=3,is_send_consumer_hearbeat_to_redis=True,function_timeout=10,
       # function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(True,True,is_use_bulk_insert=True)
       )
def f2(a, b):
    # time.sleep(100)
    # time.sleep(10)
    if random.random() > 0.99999:
        while 1:
            time.sleep(10)
    print(a, b)
    return a - b


if __name__ == '__main__':
    # pass
    # f.clear()
    # f2.clear()
    from nb_log import handlers
    # nb_log.LogManager(f2.consumer.logger.name).remove_handler_by_handler_class(nb_log.handlers.ColorHandler)
    for i in range(92):
        f2.push(i, i * 5)
    f2.consume()

    for queue_name,consumex in boost_queue__fun_map.items():
        consumex.consume()
    # f2.consume()
    # f2.consume()
    # print(f2.get_message_count())
    #
    # f2.clear()
    # for i in range(20):
    #     f2.push(i, i * 2)
    # print(f2.get_message_count())
    #
    # f2.consume()


    # f2.continue_consume()
    # time.sleep(20)
    # while 1:
    #     f2.consumer.pause_consume()
    #     time.sleep(300)
    #     f2.continue_consume()
    #     time.sleep(300)




    # f2.multi_process_consume(5)

    while 1:
        time.sleep(60)


    """
    win命令行运行
    conda activate py311c    conda activate  py37c
    set PYTHONPATH=/codes/funboost &&  python /codes/funboost/test_frame/test_broker/test_consume.py
    d:  ;cd  /codes/funboost  ;$ENV:PYTHONPATH="./" ;  python /codes/funboost/test_frame/test_broker/test_consume.py
    """


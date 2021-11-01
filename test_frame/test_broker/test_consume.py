
# from auto_run_on_remote import run_current_script_on_remote
# run_current_script_on_remote()
import json
import os
import time
import random
from function_scheduling_distributed_framework import task_deco, BrokerEnum,ConcurrentModeEnum
from function_scheduling_distributed_framework.utils import RedisMixin

# @task_deco('test_queue66', broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM, qps=5, log_level=10, is_print_detail_exception=False, is_show_message_get_from_broker=False,
#            is_using_distributed_frequency_control=True)
@task_deco('test_queue668', broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM,log_level=10,concurrent_mode=ConcurrentModeEnum.THREADING,qps=0)
def f(x, y):
    # time.sleep(10)
    # if x %10 == 0:
    #     print(x)

    print(f''' pid:{os.getpid()}, {int(time.time())} 计算  {x} + {y} = {x + y}''')
    # time.sleep(0.7)
    time.sleep(60)
    print(x,y)
    return x + y


if __name__ == '__main__':
    # f.clear()
    # for i in range(10):
    #     f.push(i, i * 2)
        # r.lpush(json.dumps({'x':i,'y':i*2}))
    f.consume()
    # f.fabric_deploy('192.168.114.137',22,'ydf','372148',sftp_log_level=10)
    # f.multi_process_consume(2)

import time
import multiprocessing
from function_scheduling_distributed_framework import task_deco,BrokerEnum,run_consumer_with_multi_process
from nb_log import stdout_write,print_raw
import os

print(multiprocessing.process.current_process().name)  # MainProcess

@task_deco('test_rabbit_queue7',broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM,qps=100,log_level=10)
def test_fun(x):
    pass
    # print(x)
    print(multiprocessing.process.current_process(),x)
    # time.sleep(20)

if __name__ == '__main__':
    run_consumer_with_multi_process(test_fun,1)
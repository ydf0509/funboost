import time

from function_scheduling_distributed_framework import task_deco,BrokerEnum,run_consumer_with_multi_process
from nb_log import stdout_write,print_raw
@task_deco('test_rabbit_queue',broker_kind=BrokerEnum.RABBITMQ_PIKA,qps=300,is_using_distributed_frequency_control=True,log_level=30)
def test_fun(x):
    # print(x)
    print_raw(x)
    time.sleep(1)

if __name__ == '__main__':
    run_consumer_with_multi_process(test_fun,4)
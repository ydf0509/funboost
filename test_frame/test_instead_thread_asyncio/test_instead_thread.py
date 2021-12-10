import time
from function_scheduling_distributed_framework import task_deco, BrokerEnum


@task_deco("test_insteda_thread_queue", broker_kind=BrokerEnum.MEMORY_QUEUE, concurrent_num=10)
def f(x):
    time.sleep(3)
    print(x)


for i in range(100):
    f.push(i)

f.consume()


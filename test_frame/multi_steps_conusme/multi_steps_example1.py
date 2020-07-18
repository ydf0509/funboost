import time

from function_scheduling_distributed_framework import  task_deco,BrokerEnum


@task_deco('queue_test_step1',qps=0.5,broker_kind=BrokerEnum.REDIS_ACK_ABLE)
def step1(x):
    print(f'x 的值是 {x}')
    if x == 0:
        for i in range(1, 30):
            step1.pub(dict(x=x + i))
    for j in range(10):
        step2.push(x * 100 + j)
    time.sleep(10)


@task_deco('queue_test_step2',qps=3,broker_kind=BrokerEnum.REDIS_ACK_ABLE)
def step2(y):
    time.sleep(10)
    print(f'y 的值是 {y}')


# step1.clear()
step1.pub({'x': 0})

step1.consume()
step2.consume()

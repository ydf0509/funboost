import time
from function_scheduling_distributed_framework import task_deco,BrokerEnum

@task_deco('30778',broker_kind=BrokerEnum.REDIS_ACK_ABLE,qps=5,)
def f(x):
    time.sleep(3)
    print(x)


if __name__ == '__main__':
    f.consume()
import time
from function_scheduling_distributed_framework import task_deco,BrokerEnum

@task_deco('test_kafka5',broker_kind=BrokerEnum.KAFKA,qps=0.5)
def f(x):
    time.sleep(1)
    print(x)


if __name__ == '__main__':
    # for i in range(100):
    #     f.push(i)
    f.consume()
import time
from function_scheduling_distributed_framework import task_deco,BrokerEnum

@task_deco('test_kombu2',broker_kind=BrokerEnum.KAFKA,qps=0,log_level=10)
def f(x):
    # time.sleep(60)
    print(x)


if __name__ == '__main__':
    f.consume()
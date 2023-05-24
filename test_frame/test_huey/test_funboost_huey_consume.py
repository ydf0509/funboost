import time

from funboost.assist.huey_helper import HueyHelper
from funboost import boost, BrokerEnum


@boost('test_huey_queue1', broker_kind=BrokerEnum.HUEY, broker_exclusive_config={'huey_task_kwargs': {}})
def f1(x, y):
    time.sleep(10)
    print(x, y)
    return 666


@boost('test_huey_queue2', broker_kind=BrokerEnum.HUEY)
def f2(a):
    time.sleep(7)
    print(a)


if __name__ == '__main__':
    for i in range(10):
        f1.push(i, i + 1)
        f2.push(i)
    HueyHelper.realy_start_huey_consume()

from function_scheduling_distributed_framework import task_deco, BrokerEnum
import logging


@task_deco('speed_test_queue', broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE, log_level=20, )
def f_test_speed(x):
    pass
    # f_test_speed2.push(x * 10)
    print(x)


@task_deco('speed_test_queue2', broker_kind=BrokerEnum.REDIS, log_level=20, qps=2)
def f_test_speed2(y):
    pass
    print(y)


if __name__ == '__main__':
    # f_test_speed.clear()

    for i in range(1000000):
        f_test_speed.push(i)

    f_test_speed.consume()
    # # f_test_speed2.consume()

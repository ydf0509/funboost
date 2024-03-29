import os
import time
from functools import wraps

from funboost import boost, BrokerEnum


def deco(f):
    @wraps(f)
    def _f(*args, **kwargs):
        print('叠加装饰器测试')
        return f(*args, **kwargs)

    return _f


@boost(queue_name='s1qc', qps=0.2, broker_kind=BrokerEnum.REDIS, consumin_function_decorator=deco)
def step1(x):
    print(f'x 的值是 {x}')
    if x == 0:
        for i in range(1, 10):
            step1.publish(dict(x=x + i))
    for j in range(10):
        step2.publish(dict(y=x * 100 + j))


@boost(queue_name='s2qc', qps=2, broker_kind=BrokerEnum.REDIS)
def step2(y):
    print(f'y 的值是 {y}')


if __name__ == '__main__':
    pass
    # from funboost.core.get_booster import get_booster, pid_queue_name__booster_map
    #
    # print(os.getpid(), pid_queue_name__booster_map)
    # print(step1)
    # step1.push(0)
    # step2.multi_process_pub_params_list([{'y':i*2} for i in range(100000)],20)

    for i in range(100000):
        step2.publish({'y': i * 2})
    # step1.consume()
    # step2.multi_process_consume(2)
    #
    # step2.fabric_deploy(host='106.55.244.110',port=22,user='root',password='****',process_num=3,only_upload_within_the_last_modify_time=86400*10)
    # #
    # # print(step1.consumer.consuming_function.__name__)
    #
    # step2(8899)
    #
    # while 1:
    #     print(os.getpid(),pid_queue_name__booster_map)
    #     time.sleep(60)


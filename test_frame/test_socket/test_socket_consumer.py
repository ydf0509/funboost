import time
import random
from function_scheduling_distributed_framework import task_deco, BrokerEnum, ConcurrentModeEnum


@task_deco('10.0.126.147:5691', broker_kind=BrokerEnum.REDIS, qps=0.5, concurrent_mode=ConcurrentModeEnum.ASYNC, is_print_detail_exception=True,max_retry_times=3)
async def f(x):
    # time.sleep(7)
    if x % 10 == 0 and random.random() < 0.5:
        raise ValueError('测试函数出错')
    print(x)
    return x * 10


if __name__ == '__main__':
    f.consume()
    for i in range(10):
        f.push(i)

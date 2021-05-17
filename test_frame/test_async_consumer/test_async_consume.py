import time
import asyncio
from function_scheduling_distributed_framework import task_deco, BrokerEnum, ConcurrentModeEnum


@task_deco('test_async_queue', concurrent_mode=ConcurrentModeEnum.ASYNC, qps=3, broker_kind=BrokerEnum.PERSISTQUEUE, concurrent_num=60)
async def async_f(x):   # 调度异步消费函数
    print(x)
    # time.sleep(2)   # 不能搞同步time.sleep 2秒的代码，否则不管设置多大并发实际qps最大只能达到0.5
    await asyncio.sleep(2)
    return x * 3


@task_deco('test_f_queue', concurrent_mode=ConcurrentModeEnum.THREADING, qps=5, broker_kind=BrokerEnum.PERSISTQUEUE)
def f(y):  # 调度同步消费函数
    print(y)
    time.sleep(7)


if __name__ == '__main__':
    async_f.clear()
    f.clear()

    for i in range(200):
        async_f.push(i)
        f.push(i * 10)

    async_f.consume()
    f.consume()

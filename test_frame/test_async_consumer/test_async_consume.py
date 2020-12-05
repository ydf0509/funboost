from function_scheduling_distributed_framework import task_deco, BrokerEnum
import asyncio
import time


@task_deco('test_async_queue', concurrent_mode=4, qps=0, broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE, concurrent_num=60)
async def async_f(x):
    print(x)
    # time.sleep(2)   # 不能搞同步time.sleep 2秒的代码，否则实际qps最大只能达到0.5
    # await asyncio.sleep(0.02)


@task_deco('test_f_queue', concurrent_mode=1, qps=0, broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE)
def f(y):
    print(y)
    # time.sleep(1)


if __name__ == '__main__':
    async_f.clear()
    f.clear()
    for i in range(20000):
        async_f.push(i)
        f.push(i * 10)

    # async_f.consume()
    f.consume()

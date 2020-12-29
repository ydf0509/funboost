from function_scheduling_distributed_framework import task_deco, BrokerEnum,ConcurrentModeEnum
import asyncio


@task_deco('test_async_queue2', concurrent_mode=ConcurrentModeEnum.ASYNC,
            broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE, log_level=10,concurrent_num=5,)
async def async_f(x):
    await asyncio.sleep(1,)
    if x % 10 ==0:
        raise ValueError(x)
    print(x)

if __name__ == '__main__':
    async_f.clear()
    for i in range(30):
        async_f.push(i, )
    async_f.consume()
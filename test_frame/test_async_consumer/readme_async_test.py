from function_scheduling_distributed_framework import task_deco, BrokerEnum, ConcurrentModeEnum, ExceptionForRequeue
import asyncio


@task_deco('test_async_queue2', concurrent_mode=ConcurrentModeEnum.ASYNC,
           broker_kind=BrokerEnum.REDIS_ACK_ABLE, log_level=10, concurrent_num=5, is_using_rpc_mode=True,do_task_filtering=1)
async def async_f(x):
    await asyncio.sleep(1, )
    if x % 10 == 0:
        raise ValueError(x)
        # raise ExceptionForRequeue(x)
    print(x)
    return x % 10


if __name__ == '__main__':
    async_f.clear()
    for i in range(40):
        async_f.push(i, )
    async_f.consume()

import time

from funboost import boost, BrokerEnum, ConcurrentModeEnum, ExceptionForRequeue
import asyncio
import random

@boost('test_async_queue2', concurrent_mode=ConcurrentModeEnum.ASYNC, qps=3,
       broker_kind=BrokerEnum.REDIS_ACK_ABLE, log_level=10, concurrent_num=500, is_using_rpc_mode=True, do_task_filtering=0)
async def async_f(x):
    print(id(asyncio.get_event_loop()))   # 可以看到每个并发用的是同一个loop
    await asyncio.sleep(1, )
    if x % 10 == 0 and random.randint(1,10) < 5:
        raise ValueError(x)
        # raise ExceptionForRequeue(x)
    print(x)
    return x % 10


if __name__ == '__main__':
    async_f.clear()
    for i in range(40):
        async_f.push(i, )
    async_f.consume()
    while 1:
        time.sleep(10)

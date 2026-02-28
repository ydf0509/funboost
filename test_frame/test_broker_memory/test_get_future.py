

import time

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum
import asyncio
import threading
import concurrent.futures 

@boost(BoosterParams(
    queue_name='test_memory_queue_call_q1',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=0,
    concurrent_num=10,
    max_retry_times=4,
))
def add(x, y):
    time.sleep(2)  # 模拟耗时
    return x + y,threading.Lock()  # 证明可以返回任何不可pickle序列化的对象，连线程锁都可以作为返回值。


# 内存作为队列时候，可以把@boost当做一个超级装饰器，并发 控频 重试。
@boost(BoosterParams(
    queue_name='test_memory_queue_call_q2',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=0,
    concurrent_mode = ConcurrentModeEnum.ASYNC,
    concurrent_num=10,
    max_retry_times=5,
))
async def divide(a, b):
    await asyncio.sleep(3)  # 模拟耗时
    return a / b

def t_get_future():
    future : concurrent.futures.Future = add.publisher.get_future(10, y=20)
    result_status = future.result(timeout=10) # 阻塞等待结果
    print(result_status.result)
    print(result_status.success)

async def t_get_aio_future():
    aio_future: asyncio.Future = divide.publisher.get_aio_future(40, b=20)
    result_status = await aio_future # 异步阻塞等待结果
    print(result_status.result)
    print(result_status.success)


if __name__ == '__main__':
    add.consume()
    divide.consume()
   
    t_get_future()
    asyncio.run(t_get_aio_future())
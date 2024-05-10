import asyncio
import time
from funboost import boost,BrokerEnum,ConcurrentModeEnum,BoosterParams

# funboost 直接方便性支持 async def 函数逇消费,远超 celery对async 函数的支持
@boost(BoosterParams(queue_name='aio_long_time_fun_queue',is_using_rpc_mode=True))
async def aio_long_time_fun(x):
    await asyncio.sleep(10)
    print(f'aio_long_time_fun {x}')
    return f'aio_long_time_fun {x}'

@boost(BoosterParams(queue_name='long_time_fun_queue',is_using_rpc_mode=True))
def long_time_fun(x):
    time.sleep(5)
    print(f'long_time_fun {x}')
    return f'long_time_fun {x}'


if __name__ == '__main__':
    async def aio_push_msg():
        for i in range(10):
            await aio_long_time_fun.aio_push(i)
    asyncio.run(aio_push_msg()) # asyncio 发布消息到中间件演示

    for j in range(10):     # 同步发布消息到中间件演示
        long_time_fun.push(j)


    aio_long_time_fun.consume() # 启动消费,funboost 能直接性支持async def 的函数作为消费函数,这点上的方便性完爆celery对asycn def的支持.
    long_time_fun.consume()  # 启动消费
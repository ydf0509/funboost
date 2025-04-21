

import asyncio
import time

from funboost import boost, BrokerEnum, ConcurrentModeEnum, BoosterParams

# 创建事件循环
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


async def init():
    # 一些异步操作
    await asyncio.sleep(1)
    print('id loop:',id(asyncio.get_running_loop()))



@boost(BoosterParams(queue_name='task_list', concurrent_mode=ConcurrentModeEnum.ASYNC,
                     broker_kind=BrokerEnum.REDIS_ACK_ABLE,
                     qps=10, max_retry_times=1, specify_async_loop=loop, is_auto_start_consuming_message=True))
async def task_list():
    print('id loop:',id(asyncio.get_running_loop()))
    await asyncio.sleep(1)
    await init()


if __name__ == '__main__':
    loop.run_until_complete(init())
    for i in range(3):
        task_list.push()
    task_list.consume()



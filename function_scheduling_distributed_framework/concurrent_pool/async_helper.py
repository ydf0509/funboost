from functools import partial
import asyncio

from function_scheduling_distributed_framework.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAble

async_executor = ThreadPoolExecutorShrinkAble(20)


async def simple_run_in_executor(f, *args, async_loop=None, **kwargs):
    loopx = async_loop or asyncio.get_event_loop()
    # print(id(loopx))
    result = await loopx.run_in_executor(async_executor, partial(f, *args, **kwargs))
    return result


if __name__ == '__main__':
    import time
    import requests


    def block_fun(x):
        time.sleep(5)
        print(x)
        return x * 10


    async def enter_fun(xx):  # 入口函数，盈利为一旦异步，必须处处异步。不能直接调用block_fun，否则阻塞其他任务。
        await asyncio.sleep(1)
        r = await  simple_run_in_executor(block_fun, xx)
        print(r)


    loopy = asyncio.get_event_loop()
    print(id(loopy))
    tasks = []
    tasks.append(simple_run_in_executor(requests.get, url='http://www.baidu.com'))

    tasks.append(simple_run_in_executor(block_fun, 1))
    tasks.append(simple_run_in_executor(block_fun, 2))
    tasks.append(simple_run_in_executor(block_fun, 3))

    tasks.append(enter_fun(4))
    tasks.append(enter_fun(5))

    print('开始')
    loopy.run_until_complete(asyncio.wait(tasks))
    print('结束')

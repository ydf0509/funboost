from functools import partial
import asyncio
from concurrent.futures import Executor
from funboost.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAble

# 没有使用内置的concurrent.futures.ThreadpoolExecutor线程池，而是使用智能伸缩线程池。
async_executor_default = ThreadPoolExecutorShrinkAble()


async def simple_run_in_executor(f, *args, async_executor: Executor = None, async_loop=None, **kwargs):
    """
    一个很强的函数，使任意同步同步函数f，转化成asyncio异步api语法，
    例如 r = await  simple_run_in_executor(block_fun, 20)，可以不阻塞事件循环。

    asyncio.run_coroutine_threadsafe 和 run_in_executor 是一对反义词。

    asyncio.run_coroutine_threadsafe 是在非异步的上下文环境(也就是正常的同步语法的函数里面)下调用异步函数对象（协程），
    因为当前函数定义没有被async修饰，就不能在函数里面使用await，必须使用这。这个是将asyncio包的future对象转化返回一个concurrent.futures包的future对象。

    run_in_executor 是在异步环境（被async修饰的异步函数）里面，调用同步函数，将函数放到线程池运行防止阻塞整个事件循环的其他任务。
    这个是将 一个concurrent.futures包的future对象 转化为 asyncio包的future对象，
    asyncio包的future对象是一个asyncio包的awaitable对象，所以可以被await，concurrent.futures.Future对象不能被await。


    :param f:  f是一个同步的阻塞函数，f前面不能是由async定义的。
    :param args: f函数的位置方式入参
    :async_executor: 线程池
    :param async_loop: async的loop对象
    :param kwargs:f函数的关键字方式入参
    :return:
    """
    loopx = async_loop or asyncio.get_event_loop()
    async_executorx = async_executor or async_executor_default
    # print(id(loopx))
    result = await loopx.run_in_executor(async_executorx, partial(f, *args, **kwargs))
    return result


if __name__ == '__main__':
    import time
    import requests


    def block_fun(x):
        print(x)
        time.sleep(5)
        return x * 10


    async def enter_fun(xx):  # 入口函数，模拟一旦异步，必须处处异步。不能直接调用block_fun，否则阻塞其他任务。
        await asyncio.sleep(1)
        # r = block_fun(xx)  # 如果这么用就完蛋了，阻塞事件循环， 运行完所有任务需要更久。
        r = await  simple_run_in_executor(block_fun, xx)
        print(r)


    loopy = asyncio.get_event_loop()
    print(id(loopy))
    tasks = []
    tasks.append(simple_run_in_executor(requests.get, url='http://www.baidu.com', timeout=10))  # 同步变异步用法。

    tasks.append(simple_run_in_executor(block_fun, 1))
    tasks.append(simple_run_in_executor(block_fun, 2))
    tasks.append(simple_run_in_executor(block_fun, 3))
    tasks.append(simple_run_in_executor(time.sleep, 8))

    tasks.append(enter_fun(4))
    tasks.append(enter_fun(5))
    tasks.append(enter_fun(6))

    print('开始')
    loopy.run_until_complete(asyncio.wait(tasks))
    print('结束')

    time.sleep(200)

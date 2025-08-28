"""
此脚本主要是演示，在funboost自动的单独的子线程的loop中,如何使用asyncio的异步socket池，来发送异步请求。
核心是要把主线程的loop传递到子线程中,让子线程和主线程使用同一个loop来运行异步函数,
在funboost 中 通过 specify_async_loop=主线程loop 来传递.


跨线程的不同loop,使用在主线程的loop生成的异步连接池 来发请求是不行的.
不管是任何三方包的socket池,例如 aiomysql aioredis aiohttp httpx 创建的http或者数据库连接池,
都不能在子线程的loop的异步函数中直接去使用这个连接池中的连接发请求.
有些异步三方包的连接池能直接在子线程的loop去使用连接发请求或查询数据库而不报错,是因为惰性生成的.
"""

"""
用户一定要搞清楚 线程和loop的绑定关系
一定要知道为什么不同的loop,不能操作同一个异步连接池发请求或者查询数据库.

用户一定要多写子线程的loop调用连接池发请求测试demo,这个和funboost本身无关,
用户的asyncio知识体系太差,用户只会在主线程使用loop,导致对loop和线程绑定关系不懂,对不同loop操作一个连接池不懂.
在子线程运行异步函数的loop,比在主线程的loop运行难得多,坑也更多.用户需要多写demo例子测试练习,多问ai大模型.
"""

# 例如子线程的loop去使用主线程loop绑定的http连接池发请求,会报错如下.  数据库连接池同理也会报错.
"""
Traceback (most recent call last):
  File "D:\codes\funboost\funboost\consumers\base_consumer.py", line 929, in _async_run_consuming_function_with_confirm_and_retry
    rs = await corotinue_obj
  File "D:\codes\funboost\test_frame\test_async_consumer\test_child_thread_loop_use_asyncio_sokcet_pool.py", line 64, in async_f2
    async with ss.request('get', url=url) as resp:  # 如果是这样请求，boost装饰器必须指定specify_async_loop，
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiohttp\client.py", line 1425, in __aenter__
    self._resp: _RetType = await self._coro
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiohttp\client.py", line 607, in _request
    with timer:
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiohttp\helpers.py", line 636, in __enter__
    raise RuntimeError("Timeout context manager should be used inside a task")
RuntimeError: Timeout context manager should be used inside a task

"""

from funboost import boost, BrokerEnum, ConcurrentModeEnum, ctrl_c_recv, BoosterParams
import asyncio
import aiohttp
import time

url = 'http://mini.eastday.com/assets/v1/js/search_word.js'

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop) # 这是重点
ss = aiohttp.ClientSession(loop=loop) # 这是重点,ss和主线程的loop绑定了.


@boost(BoosterParams(queue_name='test_async_queue1', concurrent_mode=ConcurrentModeEnum.ASYNC, broker_kind=BrokerEnum.REDIS,
        log_level=10,concurrent_num=3,
       specify_async_loop=loop, # specify_async_loop传参是核心灵魂代码,不传这个还要使用主loop绑定的连接池就会报错.
       is_auto_start_specify_async_loop_in_child_thread=False,
       ))
async def async_f1(x):
    """
    这个函数是自动被funboost在一个单独的子线程中的loop运行的,loop会并发运行很多协程来执行async_f1的逻辑
    用户最最需要明白的是,在用funboost的 ConcurrentModeEnum.ASYNC时候,你不是在主线程中操作的异步函数,而是子线程的loop中调用的.
    假设如果是在主线程中去运行的,你怎么可能连续丝滑启动多个函数消费 f1.consume()  f2.consume()  f3.consume() ? 用脑子想想就知道不是主线程去调用异步函数的.
    """

    # 如果是async with ss.request('get', url=url)使用主线程loop的连接池发请求，boost装饰器必须指定 specify_async_loop，
    # 如果你不使用ss连接池,而是 async with aiohttp.request('GET', 'https://httpbin.org/get') as resp: 那就不需要指定 specify_async_loop
    async with ss.request('get', url=url) as resp:
        text = await resp.text()
        print('async_f1', x, resp.url, text[:10])
    await asyncio.sleep(5)
    return x


@boost(BoosterParams(queue_name='test_async_queue2', concurrent_mode=ConcurrentModeEnum.ASYNC, broker_kind=BrokerEnum.REDIS,
        log_level=10,concurrent_num=3,
       # specify_async_loop=loop, # specify_async_loop传参是核心灵魂代码,连接池不传这个还要使用主loop绑定的连接池就会报错.
       is_auto_start_specify_async_loop_in_child_thread=False,
       ))
async def async_f2(x):
    # 如果是async with ss.request('get', url=url)使用主线程loop的连接池发请求，boost装饰器必须指定 specify_async_loop，
    # 如果你不使用ss连接池,而是 async with aiohttp.request('GET', 'https://httpbin.org/get') as resp: 那就不需要指定 specify_async_loop
    async with aiohttp.request('get', url=url) as resp:
        text = await resp.text()
        print('async_f2', x, resp.url, text[:10])
    await asyncio.sleep(5)
    return x



async def do_req(i):
    async with ss.request('get', url=url) as resp:  # 如果是这样请求，boost装饰器必须指定specify_async_loop，
        text = await resp.text()
        print(f'主线程的loop运行的{i}:',text[:10])
    await asyncio.sleep(3)

if __name__ == '__main__':

    async_f1.clear()
    async_f2.clear()
 
    for i in range(10):
        async_f1.push(i)
        async_f2.push(i*10)
      
    async_f1.consume()
    async_f2.consume()
  
    # time.sleep(5) 加这个是测试主线程的loop和子线程loop谁先启动,造成的影响,如果子线程的specify_async_loop先启动,主线程下面的 loop.run_forever() 会报错已启动 RuntimeError: This event loop is already running
    main_tasks = [loop.create_task(do_req(i)) for i in range(20)]
    loop.run_forever()  # 如果你除了要在funboost运行异步函数,也要在自己脚本调用,那么装饰器配置  is_auto_start_specify_async_loop_in_child_thread=False,,自己手动 启动loop.run_forever()

    ctrl_c_recv()

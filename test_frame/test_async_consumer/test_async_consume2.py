"""

这个脚本可以得出协程asyncio + aiohttp 比 threading + requests 多线程快70%
"""


from funboost import boost, BrokerEnum,ConcurrentModeEnum,ctrl_c_recv
import asyncio
import time
import aiohttp
import requests

url = 'http://mini.eastday.com/assets/v1/js/search_word.js'
# url = 'https://www.baidu.com/content-search.xml'
# rl = 'https://www.google-analytics.com/analytics.js'

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
ss = aiohttp.ClientSession(loop=loop)


@boost('test_async_queue1', concurrent_mode=ConcurrentModeEnum.ASYNC, broker_kind=BrokerEnum.REDIS,
        log_level=10,concurrent_num=3,
       specify_async_loop=loop
       )
async def async_f1(x):
    # 如果使使用了同一个session，async with ss.request，必须指定specify_async_loop的值和ClientSession的loop相同。
    # 否则 如果使使用 async with aiohttp.request ，则无需指定specify_async_loop参数。
    # async with aiohttp.request('get', url=url) as resp:  # 如果是这样请求，boost装饰器无需指定specify_async_loop
    #     text = await resp.text()
    # print(x,55555555555)
    # await asyncio.sleep(1,)
    # print(x,66666666666)
    # ss = aiohttp.ClientSession( )
    async with ss.request('get', url=url) as resp:  # 如果是这样请求，boost装饰器必须指定specify_async_loop，
        text = await resp.text()
        print('async_f1', x, resp.url, text[:10])
    await asyncio.sleep(5)
    return x


@boost('test_async_queue2', concurrent_mode=ConcurrentModeEnum.ASYNC, broker_kind=BrokerEnum.REDIS,
        log_level=10,concurrent_num=3,
       specify_async_loop=loop
       )
async def async_f2(x):
    async with ss.request('get', url=url) as resp:  # 如果是这样请求，boost装饰器必须指定specify_async_loop，
        text = await resp.text()
        print('async_f2', x, resp.url, text[:10])
    await asyncio.sleep(5)
    return x

rss = requests.session()
@boost('test_f_queue2', concurrent_mode=ConcurrentModeEnum.THREADING, broker_kind=BrokerEnum.REDIS, concurrent_num=500, log_level=10)
def f(y):
    # resp = requests.request('get', url)
    resp = rss.request('get', url)
    print(y, resp.text[:10])

async def do_req(i):
    async with ss.request('get', url=url) as resp:  # 如果是这样请求，boost装饰器必须指定specify_async_loop，
        text = await resp.text()
        print(f'主线程的loop运行的{i}:',text[:10])
    await asyncio.sleep(3)

if __name__ == '__main__':

    async_f1.clear()
    async_f2.clear()
    f.clear()

    for i in range(10):
        async_f1.push(i)
        async_f2.push(i*10)
        f.push(i * 10)

    async_f1.consume()
    async_f2.consume()
    # f.consume()
    # loop.run_until_complete(main_run())
    [loop.create_task(do_req(i)) for i in range(20)]
    loop.run_forever()


    ctrl_c_recv()

"""

这个脚本可以得出协程asyncio + aiohttp 比 threading + requests 多线程快70%
"""


from funboost import boost, BrokerEnum,ConcurrentModeEnum
import asyncio
import time
import aiohttp
import requests

url = 'http://mini.eastday.com/assets/v1/js/search_word.js'
# url = 'https://www.baidu.com/content-search.xml'
# rl = 'https://www.google-analytics.com/analytics.js'

loop = asyncio.new_event_loop()
ss = aiohttp.ClientSession(loop=loop, )


@boost('test_async_queue2', concurrent_mode=ConcurrentModeEnum.ASYNC, broker_kind=BrokerEnum.REDIS, log_level=10,
       concurrent_num=500, specify_async_loop=loop)
async def async_f(x):
    # 如果使使用了同一个session，async with ss.request，必须指定specify_async_loop的值和ClientSession的loop相同。
    # 否则 如果使使用 async with aiohttp.request ，则无需指定specify_async_loop参数。
    # async with aiohttp.request('get', url=url) as resp:  # 如果是这样请求，boost装饰器无需指定specify_async_loop
    #     text = await resp.text()
    # print(x,55555555555)
    # await asyncio.sleep(1,)
    # print(x,66666666666)
    async with ss.request('get', url=url) as resp:  # 如果是这样请求，boost装饰器必须指定specify_async_loop，
        text = await resp.text()
        # print(x, resp.url, text[:10])
    print(x)
    return x


rss = requests.session()


@boost('test_f_queue2', concurrent_mode=ConcurrentModeEnum.THREADING, broker_kind=BrokerEnum.REDIS, concurrent_num=500, log_level=10)
def f(y):
    # resp = requests.request('get', url)
    resp = rss.request('get', url)
    print(y, resp.text[:10])


if __name__ == '__main__':

    async_f.clear()
    f.clear()

    for i in range(10000):
        async_f.push(i)
        f.push(i * 10)

    # async_f.consume()
    f.consume()

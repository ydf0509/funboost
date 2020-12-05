"""

这个脚本可以得出协程asyncio + aiohttp 比 threading + requests 多线程快70%
"""
from function_scheduling_distributed_framework import task_deco, BrokerEnum
import asyncio
import time
import aiohttp
import requests

url = 'http://mini.eastday.com/assets/v1/js/search_word.js'
# url = 'https://www.baidu.com/content-search.xml'
# rl = 'https://www.google-analytics.com/analytics.js'

loop = asyncio.new_event_loop()
ss = aiohttp.ClientSession(loop=loop,)

@task_deco('test_async_queue2', concurrent_mode=4, broker_kind=BrokerEnum.REDIS,log_level=10,specify_async_loop=loop,concurrent_num=500)
async def async_f(x):
    # async with aiohttp.request('get', url=url) as resp:
    async with ss.request('get', url=url) as resp:
        text = await resp.text()
        print(x,resp.url, text[:10])

rss = requests.session()
@task_deco('test_f_queue2', concurrent_mode=1, broker_kind=BrokerEnum.REDIS,concurrent_num=500,log_level=10)
def f(y):
    # resp = requests.request('get', url)
    resp = rss.request('get',url)
    print(y,resp.text[:10])


if __name__ == '__main__':
    async_f.clear()
    f.clear()
    for i in range(10000):
        async_f.push(i)
        f.push(i * 10)

    async_f.consume()
    f.consume()

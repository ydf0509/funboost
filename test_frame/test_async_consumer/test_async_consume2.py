from function_scheduling_distributed_framework import task_deco, BrokerEnum
from function_scheduling_distributed_framework.concurrent_pool.async_pool_executor import AsyncPoolExecutor
import asyncio
import time
import aiohttp
import requests

url = 'http://henan.china.com.cn/edu/2020-10/16/content_41326458.htm'
url = 'https://www.baidu.com/content-search.xml'
# rl = 'https://www.google-analytics.com/analytics.js'

loop = asyncio.new_event_loop()
conn=aiohttp.TCPConnector(verify_ssl=False,limit=0,loop=loop)
ss = aiohttp.ClientSession(loop=loop,connector=conn)

@task_deco('test_async_queue2', concurrent_mode=4, broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE,log_level=20,specify_async_loop=loop,concurrent_num=500)
async def async_f(x):
    # loop = asyncio.get_running_loop()
    # if getattr(loop,'ss',None):
    #     ss = loop.ss
    # else:
    #     ss = aiohttp.ClientSession(loop=loop)
    #     loop.ss = ss
    # await asyncio.sleep(1)
    print(x)

    # url = 'http://www.mamicode.com/info-detail-2398355.html'
    # async with ss.request('get', url=url) as resp:
    #     text = await resp.text()
    #     print(resp.url, text[:10])

rss = requests.session()

@task_deco('test_f_queue2', concurrent_mode=1, broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE,concurrent_num=500,log_level=20)
def f(y):
    # resp = rss.request('get',url)
    # resp = requests.request('get', url)
    # print(resp.text[:10])
    # time.sleep(1)
    print(y)

if __name__ == '__main__':
    async_f.clear()
    f.clear()
    for i in range(10000):
        async_f.push(i)
        f.push(i * 10)

    async_f.consume()
    # f.consume()

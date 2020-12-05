import time
import asyncio
from function_scheduling_distributed_framework.concurrent_pool import *
from function_scheduling_distributed_framework.utils.decorators import TimerContextManager
import aiohttp
import requests
import sys
import threading

url = 'http://mini.eastday.com/assets/v1/js/search_word.js'
url = 'https://www.baidu.com/content-search.xml'

total_succ_async =0
total_succ_sync =0
sync_count_lock = threading.Lock()

async def async_request(i):
    try:
        async with aiohttp.request('get',url,timeout=aiohttp.ClientTimeout(20)) as resp:
            text = await resp.text()
            # print(text[:10])
        print(f'异步{i}')
        await asyncio.sleep(0.1)
        global total_succ_async
        total_succ_async += 1
    except Exception as e:
        pass
        print(e)



def sync_request(i):
    try:
        resp = requests.get(url,timeout=10)
        text = resp.text
        print(f'同步{i}')
        time.sleep(0.1)

        # print(text[:10])
        global total_succ_sync
        with sync_count_lock:
            total_succ_sync += 1
    except Exception as e:
        pass
        print(e)

pool_works = 600
test_times = 10000
pool1 = AsyncPoolExecutor(pool_works)
pool2 = CustomThreadPoolExecutor(pool_works)

t1 = time.time()
for j in range(test_times):
    # t_submit =time.time()
    pool1.submit(async_request,j)
    # print(time.time()-t_submit)

pool1.shutdown()
spend_time_async = time.time() -t1

t2 = time.time()
with TimerContextManager():
    for j in range(test_times):
        # t_submit = time.time()
        pool2.submit(sync_request, j)
        # print(time.time() - t_submit)
    pool2.shutdown()
spend_time_sync = time.time() -t2

print(total_succ_async)
print(total_succ_sync)
print(spend_time_async)
print(spend_time_sync)


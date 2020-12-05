import time
import asyncio
from function_scheduling_distributed_framework.concurrent_pool import *
from function_scheduling_distributed_framework.utils.decorators import TimerContextManager
import aiohttp
import requests
import sys
import threading

url = 'http://mini.eastday.com/assets/v1/js/search_word.js'
# url = 'https://www.baidu.com/content-search.xml'

total_succ_async = 0
total_succ_sync = 0
total_async_run = 0
total_sync_run = 0
spend_time_95_async = None
spend_time_95_sync = None
sync_count_lock = threading.Lock()

loopx = asyncio.new_event_loop()
ss = aiohttp.ClientSession(loop=loopx)


async def async_request(i):
    global total_async_run, spend_time_95_async
    total_async_run += 1
    if total_async_run / test_times > 0.95 and spend_time_95_async is None:
        spend_time_95_async = time.time() - t1
    try:
        t0 = time.time()
        async with ss.request('get', url, timeout=aiohttp.ClientTimeout(30), ) as resp:
            text = await resp.text()
            # print(text[:10])
        print(f'异步{i} {time.time() - t0}')
        # await asyncio.sleep(0.1)
        global total_succ_async
        total_succ_async += 1
    except Exception as e:
        pass
        # print(e)


ss2 = requests.Session()


def sync_request(i):
    global total_sync_run, spend_time_95_sync
    with sync_count_lock:
        total_sync_run += 1
        if total_sync_run / test_times > 0.9 and spend_time_95_sync is None:
            spend_time_95_sync = time.time() - t2
    try:
        t0 = time.time()
        resp = ss2.get(url, timeout=30)
        text = resp.text
        print(f'同步{i} {time.time() - t0}')
        # time.sleep(0.1)
        # print(text[:10])
        global total_succ_sync
        with sync_count_lock:
            total_succ_sync += 1
    except:
        pass


pool_works = 500
test_times = 10
pool1 = AsyncPoolExecutor(500, loop=loopx)
pool2 = CustomThreadPoolExecutor(500)

t1 = time.time()
for j in range(test_times):
    print(j)
    # t_submit =time.time()
    pool1.submit(async_request, j)
    # print(time.time()-t_submit)
pool1.shutdown()
spend_time_async = time.time() - t1

t2 = time.time()
for j in range(test_times):
    # t_submit = time.time()
    pool2.submit(sync_request, j)
    # print(time.time() - t_submit)
pool2.shutdown()
spend_time_sync = time.time() - t2

print(total_succ_async)
print(total_succ_sync)
print(spend_time_async)
print(spend_time_sync)

print(spend_time_95_async)
print(spend_time_95_sync)

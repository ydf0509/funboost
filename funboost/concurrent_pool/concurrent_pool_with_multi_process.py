import time
import multiprocessing
import threading
import asyncio
import nb_log
import atexit
import os
import typing
from funboost.concurrent_pool.custom_threadpool_executor import CustomThreadpoolExecutor
from funboost.concurrent_pool.custom_gevent_pool_executor import GeventPoolExecutor
from funboost.concurrent_pool.custom_evenlet_pool_executor import CustomEventletPoolExecutor
from funboost.concurrent_pool.async_pool_executor import AsyncPoolExecutor


class ConcurrentPoolWithProcess(nb_log.LoggerMixin):
    def _start_a_pool(self, pool_class, max_works):
        pool = pool_class(max_works)
        while True:
            func, args, kwargs = self._multi_process_queue.get()  # 结束可以放None，然后这里判断，终止。或者joinable queue
            print(func, args, kwargs)
            pool.submit(func, *args, **kwargs)

    def __init__(self, pool_class: typing.Type = CustomThreadpoolExecutor, max_works=500, process_num=1):
        self._multi_process_queue = multiprocessing.Queue(100)
        for _ in range(process_num):
            multiprocessing.Process(target=self._start_a_pool, args=(pool_class, max_works), daemon=False).start()

    # noinspection PyUnusedLocal
    def _queue_call_back(self, result):
        self._multi_process_queue.task_done()

    def submit(self, func, *args, **kwargs):
        self._multi_process_queue.put((func, args, kwargs))

    def shutdown(self, wait=True):
        pass


def test_f(x):
    time.sleep(1)
    print(x * 10, os.getpid())


async def async_f(x):
    await asyncio.sleep(1)
    print(x * 10)


if __name__ == '__main__':
    pool = ConcurrentPoolWithProcess(AsyncPoolExecutor, 20, 2)
    # pool = GeventPoolExecutor(200,)

    # time.sleep(15)
    for i in range(1000):
        time.sleep(0.1)
        pool.submit(async_f, i)

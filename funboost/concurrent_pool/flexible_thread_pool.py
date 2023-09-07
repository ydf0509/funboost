"""
比 ThreadPoolExecutorShrinkAble 更简单的的弹性线程池。完全彻底从头手工开发

这个线程池 submit没有返回值，不返回future对象，不支持map方法。

此线程池性能比concurrent.futures.ThreadPoolExecutor高200%

顺便兼容asyns def的函数并发运行
"""

import asyncio
import inspect
import queue
import threading
from functools import wraps

import nb_log
from nb_log import LoggerMixin, LoggerLevelSetterMixin


class FlexibleThreadPool(LoggerMixin, LoggerLevelSetterMixin):
    KEEP_ALIVE_TIME = 10
    MIN_WORKERS = 1

    def __init__(self, max_workers: int = None):
        self.work_queue = queue.Queue(10)
        self.max_workers = max_workers
        self._threads_num = 0
        self.threads_free_count = 0
        self._lock_compute_start_thread = threading.Lock()
        self._lock_compute_threads_free_count = threading.Lock()
        self._lock_for_adjust_thread = threading.Lock()
        self._lock_for_judge_threads_free_count = threading.Lock()
        self.pool_ident = id(self)
        # self.asyncio_loop = asyncio.new_event_loop()

    def _change_threads_free_count(self, change_num):
        with self._lock_compute_threads_free_count:
            self.threads_free_count += change_num

    def _change_threads_start_count(self, change_num):
        with self._lock_compute_start_thread:
            self._threads_num += change_num

    def submit(self, func, *args, **kwargs):
        self.work_queue.put([func, args, kwargs])
        with self._lock_for_adjust_thread:
            if self.threads_free_count <= self.MIN_WORKERS and self._threads_num < self.max_workers:
                _KeepAliveTimeThread(self).start()

class FlexibleThreadPoolMinWorkers0(FlexibleThreadPool):
    MIN_WORKERS = 0


def run_sync_or_async_fun(func, *args, **kwargs):
    fun_is_asyncio = inspect.iscoroutinefunction(func)
    if fun_is_asyncio:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            loop.close()
    else:
        return func(*args, **kwargs)


def sync_or_async_fun_deco(func):
    @wraps(func)
    def _inner(*args, **kwargs):
        return run_sync_or_async_fun(func, *args, **kwargs)

    return _inner


# noinspection PyProtectedMember
class _KeepAliveTimeThread(threading.Thread):
    logger = nb_log.get_logger('_KeepAliveTimeThread', log_level_int=10)

    def __init__(self, thread_pool: FlexibleThreadPool):
        super().__init__()
        self.pool = thread_pool

    def run(self) -> None:
        self.logger.debug(f'新启动线程 {self.ident} ')
        self.pool._change_threads_free_count(1)
        self.pool._change_threads_start_count(1)
        while 1:
            try:
                func, args, kwargs = self.pool.work_queue.get(block=True, timeout=self.pool.KEEP_ALIVE_TIME)
            except queue.Empty:
                with self.pool._lock_for_judge_threads_free_count:
                    # print(self.pool.threads_free_count)
                    if self.pool.threads_free_count > self.pool.MIN_WORKERS:
                        self.logger.debug(f'停止线程 {self._ident}, 触发条件是 {self.pool.pool_ident} 线程池中的 {self.ident} 线程 超过 {self.pool.KEEP_ALIVE_TIME} 秒没有任务，线程池中不在工作状态中的线程数量是 {self.pool.threads_free_count}，超过了指定的最小核心数量 {self.pool.MIN_WORKERS}')  # noqa
                        self.pool._change_threads_free_count(-1)
                        self.pool._change_threads_start_count(-1)
                        break  # 退出while 1，即是结束。
                    else:
                        continue
            self.pool._change_threads_free_count(-1)
            try:
                fun = sync_or_async_fun_deco(func)
                fun(*args, **kwargs)
            except BaseException as exc:
                self.logger.exception(f'函数 {func.__name__} 中发生错误，错误原因是 {type(exc)} {exc} ')
            self.pool._change_threads_free_count(1)


if __name__ == '__main__':
    import time
    from concurrent.futures import ThreadPoolExecutor
    from custom_threadpool_executor import ThreadPoolExecutorShrinkAble


    def testf(x):
        # time.sleep(10)
        if x % 10000 == 0:
            print(x)


    async def aiotestf(x):
        # await asyncio.sleep(1)
        if x % 10 == 0:
            print(x)
        return x * 2


    pool = FlexibleThreadPool(100)
    # pool = ThreadPoolExecutor(100)
    # pool = ThreadPoolExecutorShrinkAble(100)

    # for i in range(20000):
    #     # time.sleep(2)
    #     pool.submit(aiotestf, i)

    for i in range(100000):
        pool.submit(testf, i)

    # while 1:
    #     time.sleep(1000)
    # loop.run_forever()

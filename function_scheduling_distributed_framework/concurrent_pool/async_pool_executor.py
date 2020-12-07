import atexit
import os
import asyncio
import sys
import time
import traceback
from threading import Thread
import nb_log

from function_scheduling_distributed_framework.utils.develop_log import develop_logger

if os.name == 'posix':
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class AsyncPoolExecutor2:
    def __init__(self, size, loop=None):
        self._size = size
        self.loop = loop or asyncio.new_event_loop()
        self._sem = asyncio.Semaphore(self._size, loop=self.loop)
        # atexit.register(self.shutdown)
        Thread(target=self._start_loop_in_new_thread).start()

    def submit(self, func, *args, **kwargs):
        while True:  # 阻止过快放入。
            if self._sem.locked():
                time.sleep(0.01)
            else:
                break
        asyncio.run_coroutine_threadsafe(self._run_func(func, *args, **kwargs), self.loop)

    async def _run_func(self, func, *args, **kwargs):
        async with self._sem:
            result = await func(*args, **kwargs)
            return result

    def _start_loop_in_new_thread(self, ):
        self.loop.run_forever()

    def shutdown(self):
        self.loop.stop()
        self.loop.close()


class AsyncPoolExecutor:
    """
    使api和线程池一样，最好的性能做法是submit也弄成async def，生产和消费在同一个线程同一个loop一起运行，但会对调用链路的兼容性产生破坏，从而调用方式不兼容线程池。
    """

    def __init__(self, size, loop=None):
        """

        :param size: 同时并发运行的协程任务数量。
        :param loop:
        """
        self._size = size
        self.loop = loop or asyncio.new_event_loop()
        self._sem = asyncio.Semaphore(self._size, loop=self.loop)
        self._queue = asyncio.Queue(maxsize=size, loop=self.loop)
        t = Thread(target=self._start_loop_in_new_thread)
        t.setDaemon(True)  # 设置守护线程是为了有机会触发atexit，使程序自动结束，不用手动调用shutdown
        t.start()
        self._can_be_closed_flag = False
        atexit.register(self.shutdown)

    def submit2(self, func, *args, **kwargs):
        # future = asyncio.run_coroutine_threadsafe(self._produce(func, *args, **kwargs), self.loop) # 这个方法也有缺点，消耗的性能巨大。
        # future.result()  # 阻止过快放入，放入超过队列大小后，使submit阻塞。

        # asyncio.ensure_future(self._produce(func, *args, **kwargs),loop=self.loop) # 这样快，但不能阻塞导致快速放入。
        # 这个submit提交方法性能比submit2的 run_coroutine_threadsafe 性能好
        while self._queue.full():
            time.sleep(0.00001)
        asyncio.ensure_future(self._produce(func, *args, **kwargs), loop=self.loop)

    def submit(self, func, *args, **kwargs):
        future = asyncio.run_coroutine_threadsafe(self._produce(func, *args, **kwargs), self.loop)  # 这个方法也有缺点，消耗的性能巨大。
        future.result()  # 阻止过快放入，放入超过队列大小后，使submit阻塞。

    async def _produce(self, func, *args, **kwargs):
        await self._queue.put((func, args, kwargs))

    async def _consume(self):
        while True:
            func, args, kwargs = await self._queue.get()
            if func == 'stop':
                break
            try:
                await func(*args, **kwargs)
            except Exception as e:
                traceback.print_exc()

    async def __run(self):
        for _ in range(self._size):
            asyncio.ensure_future(self._consume())

    def _start_loop_in_new_thread(self, ):
        # self._loop.run_until_complete(self.__run())  # 这种也可以。
        # self._loop.run_forever()

        # asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(asyncio.wait([self._consume() for _ in range(self._size)], loop=self.loop))
        self._can_be_closed_flag = True

    def shutdown(self):
        for _ in range(self._size):
            self.submit('stop', )
        while not self._can_be_closed_flag:
            time.sleep(0.1)
        self.loop.close()
        print('关闭循环')


if __name__ == '__main__':
    from function_scheduling_distributed_framework.concurrent_pool.bounded_threadpoolexcutor import ThreadPoolExecutor


    async def f(x):
        # await asyncio.sleep(1)
        # raise Exception('aaa')
        print('打印', x)


    print(1111)
    pool = AsyncPoolExecutor(500)
    # pool = ThreadPoolExecutor(500)  # 协程不能用线程池运行，否则压根不会执行print打印，对于一部函数 f(x)得到的是一个协程，必须进一步把协程编排成任务放在loop循环里面运行。
    for i in range(1, 41001):
        print('放入', i)
        pool.submit(f, i)
    time.sleep(5)
    pool.submit(f, 'hi')
    pool.submit(f, 'hi2')
    pool.submit(f, 'hi3')
    print(2222)
    # pool.shutdown()

import asyncio
import time
from threading import Thread
import nb_log
import queue
from function_scheduling_distributed_framework.utils.develop_log import develop_logger

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


class AsyncPoolExecutor(nb_log.LoggerMixin):
    def __init__(self, size, loop=None):
        self._size = size
        self.loop = loop or asyncio.new_event_loop()
        self._sem = asyncio.Semaphore(self._size, loop=self.loop)
        # atexit.register(self.shutdown)
        self._queue = asyncio.Queue(maxsize=size, loop=self.loop)
        Thread(target=self._start_loop_in_new_thread).start()
        self._can_be_closed_flag = False

    def submit(self, func, *args, **kwargs):
        future = asyncio.run_coroutine_threadsafe(self._produce(func, *args, **kwargs), self.loop)
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
                self.logger.exception(e)

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



if __name__ == '__main__':
    async def f(x):
        await asyncio.sleep(1)
        print(x)


    print(1111)
    pool = AsyncPoolExecutor(5)
    for i in range(1, 11):
        print('放入', i)
        pool.submit(f, i)
    time.sleep(5)
    pool.submit(f, 'hi')
    pool.submit(f, 'hi2')
    pool.submit(f, 'hi3')
    print(2222)
    pool.shutdown()

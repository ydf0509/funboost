import asyncio
import time
from threading import Thread


class AsyncPoolExecutor:
    def __init__(self, size):
        self._size = size
        self._loop = asyncio.new_event_loop()
        self._sem = asyncio.Semaphore(self._size, loop=self._loop)
        # atexit.register(self.shutdown)
        Thread(target=self._start_loop_in_new_thread).start()

    def submit(self, func, *args, **kwargs):
        # asyncio.create_task()

        # self._loop.create_task(self._run_func(func,*args,**kwargs))
        while True:
            if self._sem.locked():
                time.sleep(0.0001)
            else:
                break
        asyncio.run_coroutine_threadsafe(self._run_func(func, *args, **kwargs), self._loop)
        # print(r, type(r), r.__dict__)
        # asyncio.run_coroutine_threadsafe(func( *args, **kwargs), self._loop)

    async def _run_func(self, func, *args, **kwargs):
        async with self._sem:
            result = await func(*args, **kwargs)
            return result

    def _start_loop_in_new_thread(self, ):
        self._loop.run_forever()

    def shutdown(self):
        pass


if __name__ == '__main__':
    async def f(x):
        await asyncio.sleep(1)
        print(x)


    print(1111)
    pool = AsyncPoolExecutor(2)
    for i in range(1000):
        pool.submit(f, i)
    time.sleep(5)
    pool.submit(f, 'hi')
    pool.submit(f, 'hi2')
    pool.submit(f, 'hi3')
    print(2222)

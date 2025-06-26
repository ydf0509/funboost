import sys

import atexit
import asyncio
import threading
import time
import traceback
from threading import Thread

from funboost.concurrent_pool.base_pool_type import FunboostBaseConcurrentPool
from funboost.core.loggers import FunboostFileLoggerMixin

# if os.name == 'posix':
#     import uvloop
#
#     asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())  # 打猴子补丁最好放在代码顶层，否则很大机会出问题。

"""
# 也可以采用 janus 的 线程安全的queue方式来实现异步池，此queue性能和本模块实现的生产 消费相比，性能并没有提高，所以就不重新用这这个包来实现一次了。
import janus
import asyncio
import time
import threading
import nb_log
queue = janus.Queue(maxsize=6000)

async def consume():
    while 1:
        # time.sleep(1)
        val = await queue.async_q.get() # 这是async，不要看错了
        print(val)

def push():
    for i in range(50000):
        # time.sleep(0.2)
        # print(i)
        queue.sync_q.put(i)  # 这是sync。不要看错了。


if __name__ == '__main__':
    threading.Thread(target=push).start()
    loop = asyncio.get_event_loop()
    loop.create_task(consume())
    loop.run_forever()
"""

if sys.platform == "darwin":  # mac 上会出错
      import selectors
      selectors.DefaultSelector = selectors.PollSelector

class AsyncPoolExecutorLtPy310(FunboostFileLoggerMixin,FunboostBaseConcurrentPool):
    """
    使api和线程池一样，最好的性能做法是submit也弄成 async def，生产和消费在同一个线程同一个loop一起运行，但会对调用链路的兼容性产生破坏，从而调用方式不兼容线程池。
    """

    def __init__(self, size, loop=None):
        """

        :param size: 同时并发运行的协程任务数量。
        :param loop:
        """
        self._size = size
        self.loop = loop or asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._diff_init()
        # self._lock = threading.Lock()
        t = Thread(target=self._start_loop_in_new_thread, daemon=False)
        # t.setDaemon(True)  # 设置守护线程是为了有机会触发atexit，使程序自动结束，不用手动调用shutdown
        t.start()
     

    # def submit000(self, func, *args, **kwargs):
    #     # 这个性能比下面的采用 run_coroutine_threadsafe + result返回快了3倍多。
    #     with self._lock:
    #         while 1:
    #             if not self._queue.full():
    #                 self.loop.call_soon_threadsafe(self._queue.put_nowait, (func, args, kwargs))
    #                 break
    #             else:
    #                 time.sleep(0.01)

    def _diff_init(self):
        self._sem = asyncio.Semaphore(self._size, loop=self.loop)
        self._queue = asyncio.Queue(maxsize=self._size, loop=self.loop)


    def submit(self, func, *args, **kwargs):
        future = asyncio.run_coroutine_threadsafe(self._produce(func, *args, **kwargs), self.loop)  # 这个 run_coroutine_threadsafe 方法也有缺点，消耗的性能巨大。
        future.result()  # 阻止过快放入，放入超过队列大小后，使submit阻塞。

    async def _produce(self, func, *args, **kwargs):
        await self._queue.put((func, args, kwargs))

    async def _consume(self):
        while True:
            func, args, kwargs = await self._queue.get()
            if isinstance(func, str) and func.startswith('stop'):
                # self.logger.debug(func)
                break
            # noinspection PyBroadException,PyUnusedLocal
            try:
                await func(*args, **kwargs)
            except BaseException as e:
                traceback.print_exc()
            # self._queue.task_done()

    async def __run(self):
        for _ in range(self._size):
            asyncio.ensure_future(self._consume())

    def _start_loop_in_new_thread(self, ):
        # self._loop.run_until_complete(self.__run())  # 这种也可以。
        # self._loop.run_forever()

        # asyncio.set_event_loop(self.loop)
        # self.loop.run_until_complete(asyncio.wait([self._consume() for _ in range(self._size)], loop=self.loop))
        # self._can_be_closed_flag = True
        [self.loop.create_task(self._consume()) for _ in range(self._size)]
        try:
            self.loop.run_forever()
        except Exception as e:
            self.logger.warning(f'{e}')   # 如果多个线程使用一个loop，不能重复启动loop，否则会报错。



    # def shutdown(self):
    #     if self.loop.is_running():  # 这个可能是atregster触发，也可能是用户手动调用，需要判断一下，不能关闭两次。
    #         for i in range(self._size):
    #             self.submit(f'stop{i}', )
    #         while not self._can_be_closed_flag:
    #             time.sleep(0.1)
    #         self.loop.stop()
    #         self.loop.close()
    #         print('关闭循环')



class AsyncPoolExecutorGtPy310(AsyncPoolExecutorLtPy310):

    def _diff_init(self):
        self._sem = asyncio.Semaphore(self._size, ) # python3.10后，很多类和方法都删除了loop传参
        self._queue = asyncio.Queue(maxsize=self._size, )





AsyncPoolExecutor = AsyncPoolExecutorLtPy310 if sys.version_info.minor < 10 else AsyncPoolExecutorGtPy310



if __name__ == '__main__':
    def test_async_pool_executor():
        from funboost.concurrent_pool import CustomThreadPoolExecutor as ThreadPoolExecutor
        # from concurrent.futures.thread import ThreadPoolExecutor
        # noinspection PyUnusedLocal
        async def f(x):
            await asyncio.sleep(1)
            pass
            print('打印', x)
            # await asyncio.sleep(1)
            # raise Exception('aaa')

        def f2(x):
            pass
            # time.sleep(0.001)
            print('打印', x)

        print(1111)

        t1 = time.time()
        pool = AsyncPoolExecutor(20)
        # pool = ThreadPoolExecutor(200)  # 协程不能用线程池运行，否则压根不会执行print打印，对于一部函数 f(x)得到的是一个协程，必须进一步把协程编排成任务放在loop循环里面运行。
        for i in range(1, 501):
            print('放入', i)
            pool.submit(f, i)
        # time.sleep(5)
        # pool.submit(f, 'hi')
        # pool.submit(f, 'hi2')
        # pool.submit(f, 'hi3')
        # print(2222)
        pool.shutdown()
        print(time.time() - t1)


    test_async_pool_executor()
    # test_async_producer_consumer()

    print(sys.version_info)

import atexit
import asyncio
import threading
import time
import traceback
from threading import Thread
import nb_log  # noqa

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


class AsyncPoolExecutor2:
    def __init__(self, size, loop=None):
        self._size = size
        self.loop = loop or asyncio.new_event_loop()
        self._sem = asyncio.Semaphore(self._size, loop=self.loop)
        # atexit.register(self.shutdown)
        Thread(target=self._start_loop_in_new_thread).start()

    def submit(self, func, *args, **kwargs):
        while self._sem.locked():
            time.sleep(0.001)
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
        self._sem = asyncio.Semaphore(self._size, loop=self.loop)
        self._queue = asyncio.Queue(maxsize=size, loop=self.loop)
        self._lock = threading.Lock()
        t = Thread(target=self._start_loop_in_new_thread)
        t.setDaemon(True)  # 设置守护线程是为了有机会触发atexit，使程序自动结束，不用手动调用shutdown
        t.start()
        self._can_be_closed_flag = False
        atexit.register(self.shutdown)

        self._event = threading.Event()
        # print(self._event.is_set())
        self._event.set()

    def submit000(self, func, *args, **kwargs):
        # 这个性能比下面的采用 run_coroutine_threadsafe + result返回快了3倍多。
        with self._lock:
            while 1:
                if not self._queue.full():
                    self.loop.call_soon_threadsafe(self._queue.put_nowait, (func, args, kwargs))
                    break
                else:
                    time.sleep(0.01)

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
            except Exception as e:
                traceback.print_exc()
            # self._queue.task_done()

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
        if self.loop.is_running():  # 这个可能是atregster触发，也可能是用户手动调用，需要判断一下，不能关闭两次。
            for i in range(self._size):
                self.submit(f'stop{i}', )
            while not self._can_be_closed_flag:
                time.sleep(0.1)
            self.loop.stop()
            self.loop.close()
            print('关闭循环')


class AsyncProducerConsumer:
    """
    参考 https://asyncio.readthedocs.io/en/latest/producer_consumer.html 官方文档。
    A simple producer/consumer example, using an asyncio.Queue:
    """

    """
    边生产边消费。此框架没用到这个类，这个要求生产和消费在同一个线程里面，对原有同步方式的框架代码改造不方便。
    """

    def __init__(self, items, concurrent_num=200, consume_fun_specify=None):
        """

        :param items: 要消费的参数列表
        :param concurrent_num: 并发数量
        :param consume_fun_specify: 指定的异步消费函数对象，如果不指定就要继承并重写consume_fun函数。
        """
        self.queue = asyncio.Queue()
        self.items = items
        self._concurrent_num = concurrent_num
        self.consume_fun_specify = consume_fun_specify

    async def produce(self):
        for item in self.items:
            await self.queue.put(item)

    async def consume(self):
        while True:
            # wait for an item from the producer
            item = await self.queue.get()
            # process the item
            # print('consuming {}...'.format(item))
            # simulate i/o operation using sleep
            try:
                if self.consume_fun_specify:
                    await self.consume_fun_specify(item)
                else:
                    await self.consume_fun(item)
            except Exception as e:
                print(e)

            # Notify the queue that the item has been processed
            self.queue.task_done()

    @staticmethod
    async def consume_fun(item):
        """
        要么继承此类重写此方法，要么在类的初始化时候指定consume_fun_specify为一个异步函数。
        :param item:
        :return:
        """
        print(item, '请重写 consume_fun 方法')
        await asyncio.sleep(1)

    async def __run(self):
        # schedule the consumer
        tasks = []
        for _ in range(self._concurrent_num):
            task = asyncio.ensure_future(self.consume())
            tasks.append(task)
        # run the producer and wait for completion
        await self.produce()
        # wait until the consumer has processed all items
        await self.queue.join()
        # the consumer is still awaiting for an item, cancel it
        for task in tasks:
            task.cancel()

    def start_run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__run())
        # loop.close()


if __name__ == '__main__':
    def test_async_pool_executor():
        from funboost.concurrent_pool import CustomThreadPoolExecutor as ThreadPoolExecutor
        # from concurrent.futures.thread import ThreadPoolExecutor
        # noinspection PyUnusedLocal
        async def f(x):
            # await asyncio.sleep(0.1)
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
        # pool = AsyncPoolExecutor(200)
        pool = ThreadPoolExecutor(200)  # 协程不能用线程池运行，否则压根不会执行print打印，对于一部函数 f(x)得到的是一个协程，必须进一步把协程编排成任务放在loop循环里面运行。
        for i in range(1, 50001):
            print('放入', i)
            pool.submit(f2, i)
        # time.sleep(5)
        # pool.submit(f, 'hi')
        # pool.submit(f, 'hi2')
        # pool.submit(f, 'hi3')
        # print(2222)
        pool.shutdown()
        print(time.time() - t1)


    async def _my_fun(item):
        print('嘻嘻', item)
        # await asyncio.sleep(1)


    def test_async_producer_consumer():
        AsyncProducerConsumer([i for i in range(100000)], concurrent_num=200, consume_fun_specify=_my_fun).start_run()
        print('over')


    test_async_pool_executor()
    # test_async_producer_consumer()

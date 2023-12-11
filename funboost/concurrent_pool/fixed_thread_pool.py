"""
flxed_thread_pool.py 固定大小的线程池, 最简单的实现线程池方式,任何人都可以写得出来.弊端是代码不会自动结束,因为线程池的每个线程 while 1是非守护线程,不能自动判断代码是否需要结束.
如果有的人的代码是长期运行不需要结束的,可以用这种线程池
"""

import threading
import traceback
from queue import Queue
# import nb_log
from funboost.concurrent_pool import FunboostBaseConcurrentPool
from funboost.core.loggers import FunboostFileLoggerMixin


class FixedThreadPool(FunboostFileLoggerMixin,FunboostBaseConcurrentPool):
    def __init__(self, max_workers: int = None):
        self._max_workers = max_workers
        self._work_queue = Queue(maxsize=10)
        self._start_thrads()

    def submit(self, func, *args, **kwargs):
        self._work_queue.put([func, args, kwargs])

    def _forever_fun(self):
        while True:
            func, args, kwargs = self._work_queue.get()
            try:
                func(*args, **kwargs)
            except BaseException as e:
                self.logger.error(f'func:{func}, args:{args}, kwargs:{kwargs} exc_type:{type(e)}  traceback_exc:{traceback.format_exc()}')

    def _start_thrads(self):
        for i in range(self._max_workers):
            threading.Thread(target=self._forever_fun).start()


if __name__ == '__main__':
    def f3(x):
        # time.sleep(1)
        # 1 / 0
        if x % 10000 == 0:
            print(x)


    pool = FixedThreadPool(100)
    for j in range(10):
        pool.submit(f3, j)

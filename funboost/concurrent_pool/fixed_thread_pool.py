import threading
import time
import traceback
from queue import Queue


class FixedThreadPool:
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
                print(f'{func, args, kwargs} {type(e)} {traceback.format_exc()}')

    def _start_thrads(self):
        for i in range(self._max_workers):
            threading.Thread(target=self._forever_fun).start()


if __name__ == '__main__':
    import nb_log
    def f3(x):
        # time.sleep(1)
        if x % 10000 == 0:
            print(x)


    pool = FixedThreadPool(100)
    for i in range(100000):
        pool.submit(f3, i)

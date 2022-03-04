import os
import multiprocessing
import  threading
import time
from multiprocessing import Queue
from multiprocessing import Process
import nb_log


class SimpleProcessPool():
    def __init__(self, max_works=os.cpu_count()):
        self._max_works = max_works
        # self._queue = Queue(max_works)
        self._queue = multiprocessing.Manager().Queue(max_works)
        for i in range(self._max_works):
            Process(target=self._execute,).start()

    def submit(self, fun, *args, **kwargs):
        self._queue.put(({"fun": fun, 'args': args, 'kwargs': kwargs}))

    def _execute(self,):
        while 1:
            # item = q.get(block=True)
            item = self._queue.get(block=True)
            fun = item['fun']
            try:
                fun(*item['args'], **item['kwargs'])
            except Exception as e:
                print(e)
                # self.logger.exception(e)

class A():
    def __init__(self):
        self.lock = threading.Lock()

    def test_fun(x):
        print(x)
        time.sleep(5)


    def start(self):
        pool = SimpleProcessPool(4)
        pool.submit(self.test_fun,666)


if __name__ == '__main__':
    from auto_run_on_remote import run_current_script_on_remote

    run_current_script_on_remote()
    A().start()



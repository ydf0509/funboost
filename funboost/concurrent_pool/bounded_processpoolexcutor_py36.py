import multiprocessing
import concurrent.futures
import threading
from concurrent.futures.process import _ExceptionWithTraceback, _ResultItem  # noqa
from functools import wraps
import os

import nb_log

name = 'bounded_pool_executor'

logger = nb_log.get_logger('BoundedProcessPoolExecutor')


def _process_worker(call_queue, result_queue):
    """Evaluates calls from call_queue and places the results in result_queue.

    This worker is run in a separate process.

    Args:
        call_queue: A multiprocessing.Queue of _CallItems that will be read and
            evaluated by the worker.
        result_queue: A multiprocessing.Queue of _ResultItems that will written
            to by the worker.
        shutdown: A multiprocessing.Event that will be set as a signal to the
            worker that it should exit when call_queue is empty.
    """
    while True:
        call_item = call_queue.get(block=True)
        if call_item is None:
            # Wake up queue management thread
            result_queue.put(os.getpid())
            return
        try:
            r = call_item.fn(*call_item.args, **call_item.kwargs)
        except BaseException as e:
            exc = _ExceptionWithTraceback(e, e.__traceback__)
            result_queue.put(_ResultItem(call_item.work_id, exception=exc))
            logger.exception(e)  # 主要是直接显示错误。
        else:
            result_queue.put(_ResultItem(call_item.work_id,
                                         result=r))


def _deco(f):
    @wraps(f)
    def __deco(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.exception(e)

    return __deco


class _BoundedPoolExecutor:
    semaphore = None

    def acquire(self):
        self.semaphore.acquire()

    def release(self, fn):
        self.semaphore.release()

    def submit(self, fn, *args, **kwargs):
        self.acquire()
        future = super().submit(fn, *args, **kwargs)  # noqa
        future.add_done_callback(self.release)

        return future


class BoundedProcessPoolExecutor(_BoundedPoolExecutor, concurrent.futures.ProcessPoolExecutor):

    def __init__(self, max_workers=None):
        super().__init__(max_workers)
        self.semaphore = multiprocessing.BoundedSemaphore(max_workers)
        concurrent.futures.process._process_worker = _process_worker


class BoundedThreadPoolExecutor(_BoundedPoolExecutor, concurrent.futures.ThreadPoolExecutor):

    def __init__(self, max_workers=None):
        super().__init__(max_workers)
        self.semaphore = threading.BoundedSemaphore(max_workers)


def test_f(x):
    import time
    time.sleep(5)
    print(x * 10)
    1 / 0


if __name__ == '__main__':
    import nb_log

    # pool = BoundedProcessPoolExecutor(4)
    pool = BoundedThreadPoolExecutor(4)
    for i in range(10):
        print(i)
        pool.submit(test_f, i)
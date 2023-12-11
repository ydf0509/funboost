import multiprocessing
import concurrent.futures
import sys
import threading
import time
import traceback
from concurrent.futures import _base
from concurrent.futures.process import _ExceptionWithTraceback, _ResultItem  # noqa
from functools import wraps
import os



# from funboost.core.loggers import get_funboost_file_logger
# logger = get_funboost_file_logger('BoundedProcessPoolExecutor')

from nb_log import  get_logger
logger = get_logger('BoundedProcessPoolExecutor')

def _deco(f):
    @wraps(f)
    def __deco(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except BaseException as e:
            logger.exception(e)

    return __deco

def __init__(self, exc, tb):
    tb = traceback.format_exception(type(exc), exc, tb)
    tb = ''.join(tb)
    self.exc = exc
    self.tb = '\n"""\n%s"""' % tb
    logger.exception(exc)


_ExceptionWithTraceback.__init__ = __init__


class _BoundedPoolExecutor:
    semaphore = None

    def acquire(self):
        self.semaphore.acquire()

    def release(self, fn):
        self.semaphore.release()

    def submit(self, fn, *args, **kwargs):
        self.acquire()
        # fn = _deco(fn)  # 装饰器发生了变化,只支持linux下
        future = super().submit(fn, *args, **kwargs)  # noqa
        future.add_done_callback(self.release)

        return future


class BoundedProcessPoolExecutor(_BoundedPoolExecutor, concurrent.futures.ProcessPoolExecutor):

    def __init__(self, max_workers=None):
        super().__init__(max_workers)
        self.semaphore = multiprocessing.BoundedSemaphore(max_workers)


class BoundedThreadPoolExecutor(_BoundedPoolExecutor, concurrent.futures.ThreadPoolExecutor):

    def __init__(self, max_workers=None):
        super().__init__(max_workers)
        self.semaphore = threading.BoundedSemaphore(max_workers)


def test_f():
    time.sleep(1)
    print('hi')
    1/0

if __name__ == '__main__':
    pool = BoundedProcessPoolExecutor(2)
    for i in range(10):
        pool.submit(_deco(test_f))
    time.sleep(1100)
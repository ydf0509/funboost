# coding=utf-8
"""
一个有界任务队列的thradpoolexcutor
直接捕获错误日志
"""
from functools import wraps
import queue
from concurrent.futures import ThreadPoolExecutor, Future
# noinspection PyProtectedMember
from concurrent.futures.thread import _WorkItem  # noqa

from nb_log import LogManager

logger = LogManager('BoundedThreadPoolExecutor').get_logger_and_add_handlers()


def _deco(f):
    @wraps(f)
    def __deco(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.exception(e)

    return __deco


class BoundedThreadPoolExecutor(ThreadPoolExecutor, ):
    def __init__(self, max_workers=None, thread_name_prefix=''):
        ThreadPoolExecutor.__init__(self, max_workers, thread_name_prefix)
        self._work_queue = queue.Queue(max_workers * 2)

    def submit(self, fn, *args, **kwargs):
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('cannot schedule new futures after shutdown')
            f = Future()
            fn_deco = _deco(fn)
            w = _WorkItem(f, fn_deco, args, kwargs)
            self._work_queue.put(w)
            self._adjust_thread_count()
            return f


if __name__ == '__main__':
    def fun():
        print(1 / 0)

    # 如果是官方线程池，这样不报错你还以为代码没毛病呢。
    pool = BoundedThreadPoolExecutor(10)
    pool.submit(fun)

import functools
import threading
import typing
import os

from funboost.concurrent_pool.flexible_thread_pool import FlexibleThreadPool
from funboost.concurrent_pool.base_pool_type import FunboostBaseConcurrentPool


class ConcurrentPoolBuilder:
    _pid__pool_map = {}
    _lock = threading.Lock()

    @classmethod
    def get_pool(cls, pool_type: typing.Type[FunboostBaseConcurrentPool], max_workers: int = None):
        key = (os.getpid(), pool_type)
        with cls._lock:
            if key not in cls._pid__pool_map:
                pool = pool_type(max_workers)  # noqa
                cls._pid__pool_map[key] = pool
            return cls._pid__pool_map[key]


if __name__ == '__main__':
    for i in range(10):
        pool = functools.partial(ConcurrentPoolBuilder.get_pool, FlexibleThreadPool, 200)()
        print(id(pool))

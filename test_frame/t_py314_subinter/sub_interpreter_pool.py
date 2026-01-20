# InterpreterPoolExecutor.py
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from concurrent import interpreters
import traceback
import types
import os

from nb_libs.system_monitoring import thread_show_system_cpu_usage,thread_show_process_cpu_usage,thread_show_cpu_per_core

import requests
import nb_log
from m1 import heavy_task2


class InterpreterPoolExecutor:
    """
    A pool executor that uses multiple sub‑interpreters (via concurrent.interpreters)
    in separate OS threads for concurrency.
    API similar to ThreadPoolExecutor: submit, map, shutdown.
    """
    def __init__(self, max_workers: int = None):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()
        self._closed = False

    def submit(self, func, *args, **kwargs) -> Future:
        if not isinstance(func, types.FunctionType):
            raise TypeError("func must be a Python function")

        def _task_wrapper():
            interp = interpreters.create()
            try:
                # Use interp.call to call the function in the sub‑interpreter
                result = interp.call(func, *args, **kwargs)
                return result
            except Exception as e:
                # trace the original exception
                raise
            finally:
                interp.close()

        with self._lock:
            if self._closed:
                raise RuntimeError("Cannot submit to closed InterpreterPoolExecutor")
            future = self._executor.submit(_task_wrapper)
            return future

    def map(self, func, *iterables, timeout=None, chunksize=1):
        # Similar to ThreadPoolExecutor.map
        futures = [self.submit(func, *args) for args in zip(*iterables)]
        results = []
        for f in futures:
            results.append(f.result(timeout=timeout))
        return results

    def shutdown(self, wait: bool = True):
        with self._lock:
            self._closed = True
        self._executor.shutdown(wait=wait)


# example_usage.py
# from InterpreterPoolExecutor import InterpreterPoolExecutor
import time

g_x =8888



def heavy_task(x, y):
    print(f"[{threading.get_ident()}] heavy_task: {x} + {y}")
    print('pid:',os.getpid(),g_x)

    print(requests.get('https://www.baidu.com/').content)
    time.sleep(1)
    nb_log.warning('wwwwwwww')
    print('fffffffffff')
    # simulate work
    # while True:
    #     pass
    time.sleep(10)
    return x + y

if __name__ == "__main__":
    thread_show_system_cpu_usage()
    thread_show_process_cpu_usage()
    thread_show_cpu_per_core()
    pool = InterpreterPoolExecutor(max_workers=1)
    futures = []
    for i in range(16):
        futures.append(pool.submit(heavy_task2, i, i*2))

    for idx, f in enumerate(futures):
        result = f.result()
        print(f"Task {idx} result = {result}")

    # Using map
    results = pool.map(heavy_task, range(3), range(3,6))
    print("Map results:", results)

    pool.shutdown()

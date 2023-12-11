from typing import Callable

from funboost.concurrent_pool import FunboostBaseConcurrentPool


class SoloExecutor(FunboostBaseConcurrentPool):
    # noinspection PyUnusedLocal
    def __init__(self, max_workers: int = 1):
        pass

    # noinspection PyMethodMayBeStatic
    def submit(self, fn: Callable, *args, **kwargs):
        return fn(*args, **kwargs)

    # noinspection PyMethodMayBeStatic
    def shutdown(self, wait=True):
        pass

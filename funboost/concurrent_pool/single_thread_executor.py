from typing import Callable


class SoloExecutor:
    # noinspection PyUnusedLocal
    def __init__(self, max_workers: int = 1):
        pass

    # noinspection PyMethodMayBeStatic
    def submit(self, fn: Callable, *args, **kwargs):
        return fn(*args, **kwargs)

    # noinspection PyMethodMayBeStatic
    def shutdown(self, wait=True):
        pass

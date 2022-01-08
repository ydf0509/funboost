import inspect

from funboost import boost
from funboost.utils import RedisMixin
from functools import wraps
from base_decorator import BaseDecorator


def incr_deco(redis_key):
    def _inner(f):
        print(dir(f))
        print(f.__dict__)
        for k in dir(f):
            print(k,getattr(f,k))
        @wraps(f)
        def __inner(x, y):
            result = f(x, y)
            RedisMixin().redis_db_frame.incr(redis_key)
            return result

        return __inner

    return _inner


@boost('test_queue_235')
@incr_deco('test_queue_235_run_count')
def fun(xxx, yyy):
    print(xxx + yyy)


if __name__ == '__main__':
    print(inspect.getfullargspec(fun))

    for i in range(10):
        fun.push(i, 2 * i)
    fun.consume()

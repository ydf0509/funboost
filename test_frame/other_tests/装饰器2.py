import copy
import multiprocessing
import types
from functools import wraps

glf = None
import nb_log
from typing import TypeVar,Generic

P = TypeVar('P')


class Profiled(Generic[P]):
    def __new__(cls, f: P) -> P:
        self = object.__new__(cls)
        self.ff = copy.deepcopy(f)
        self.__call__ = f
        return self

    def __init__(self, func: P):
        # global glf
        # glf = copy.deepcopy(func)
        print('self', self)
        # self.ff = copy.deepcopy(func)
        # wraps(self.ff)(self)
        self.ncalls = 0

    def __call__(self, *args2, **kwargs):
        self.ncalls += 1
        # print(self.__wrapped__)
        print('call')
        return self.ff(*args2, **kwargs)
        # return self

    def __get__(self, instance, cls):
        if instance is None:
            return self
        else:
            return types.MethodType(self, instance)


@Profiled
def add(x, y):
    print(666,x + y)
    return x + y


# print(add(1,2))

if __name__ == '__main__':
    print(add(1, 2))
    print(add, type(add))
    # print(
    #       type(add),type(add.ff),,isinstance(add,Profiled))
    #
    # # print(glf)
    # multiprocessing.Process(target=add.ff, args=(4, 5)).start()

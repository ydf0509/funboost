import copy
import multiprocessing
import types
from functools import wraps

glf = None

class Profiled:
    def __new__(cls, f):
        self = object.__new__(cls)
        global glf
        glf = copy.deepcopy(f)
        
    def __init__(self, func):
        # global glf
        # glf = copy.deepcopy(func)
        # wraps(func)(self)
        self.ncalls = 0

    def __call__(self, *args, **kwargs):
        self.ncalls += 1
        print(self.__wrapped__)
        return self.__wrapped__(*args, **kwargs)

    def __get__(self, instance, cls):
        if instance is None:
            return self
        else:
            return types.MethodType(self, instance)


@Profiled
def add(x, y):
    return x + y


# print(add(1,2))

if __name__ == '__main__':
    print(add(1, 2))
    print(add)
    print(glf)
    multiprocessing.Process(target=glf,args=(4,5)).start()
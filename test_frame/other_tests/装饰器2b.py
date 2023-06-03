import copy
import multiprocessing
import types
import typing
from functools import wraps

glf = None
import nb_log
from typing import TypeVar,Generic




class Profiled():
    # def __new__(cls, f: P) -> P:
    #     self = object.__new__(cls)
    #     self.ff = copy.deepcopy(f)
    #     self.__call__ = f
    #     return self

    def __init__(self, aaaa):
        # global glf
        # glf = copy.deepcopy(func)
        print('self', self)
        # self.ff = copy.deepcopy(func)
        # wraps(self.ff)(self)
        self.aaaa=aaaa
        self.ncalls = 0

    def __call__(self, f,*args,**kwargs):   # -> typing.Union[F,P]
        print(f,args,kwargs)
        # if len(args) == 1 and isinstance(args[0],typing.Callable):
        if isinstance(f,typing.Callable):
            self.ncalls += 1
            # print(self.__wrapped__)
            print('call')
            self.ff = f
            return self
        else:
            return self.ff(f,*args,**kwargs)

        # if not  isinstance(f, typing.Callable):
        #     return self.ff(f, *args, **kwargs)
        # else:
        #     self.ncalls += 1
        #     # print(self.__wrapped__)
        #     print('call')
        #     self.ff = f
        #     return self

    # def __get__(self, instance, cls):
    #     if instance is None:
    #         return self
    #     else:
    #         return types.MethodType(self, instance)


@Profiled(222)
def add(x, y):
    print(666,x + y)
    return x + y


# print(add(1,2))

if __name__ == '__main__':
    print(add.aaaa)
    print(add(1, 2))
    print(add, type(add))
    # print(
    #       type(add),type(add.ff),,isinstance(add,Profiled))
    #
    # # print(glf)
    # multiprocessing.Process(target=add.ff, args=(4, 5)).start()

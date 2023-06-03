import multiprocessing
from functools import wraps
# from typing import Callable, TypeVar, ParamSpec
#
# R = TypeVar('R')
# P = ParamSpec('P')
#
import nb_log

def other_fun(*args,**kwargs):
    print(args,kwargs)
    return 888

def deco1(b):
    def _deco(f):
        @wraps(f)
        def __deco(*args,**kwargs):
            print('hi ')
            return other_fun(*args,**kwargs)

        return __deco
    return _deco


class A():
    # def __new__(cls, f):
    #     self = object.__new__(cls)
    #     wraps(f)(self)
    #     return self

    def __init__(self,f):
        self.f =f
        wraps(f)(self)


    def __call__(self, *args, **kwargs):
        print('__call__')
        return self.f(*args,**kwargs)


def deco2(b) :
    def _inner(f):
        print(f)
        o = A(f)
        return o

    return _inner


# @deco2(b=3)
@A
def fun(x,y):
    return x+y

if __name__ == '__main__':
    print(fun,fun.f,)
    print(fun(1, 5))
    print(fun, fun.f)
    print(fun.__wrapped__)
    multiprocessing.Process(target=fun.f,args=(4,5)).start()




# def f2():
#     pass
#
#
# print(type(f2))
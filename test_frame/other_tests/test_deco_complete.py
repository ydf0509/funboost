from typing import Callable
from functools import wraps
from decohints import decohints
#
#
# def deco(a:int,b:int):
#     @decohints
#     def _inner(f):
#         @wraps(f)
#         def __inner(*args,**kwargs):
#             print(f'xixi  {a}  {b}')
#             return f(*args,**kwargs)
#
#         __inner.__doc__ = f.__doc__
#         return __inner
#
#     return _inner
#
#
#
# # @deco(1,2)
# def fun(x:str,y,z):
#     """
#
#     :param x:
#     :param y:
#     :param z:
#     :return:
#     """
#
#
#     print(x,y,z)
#
#
# def fun2(g,*args,**kwargs):
#     fun2.__doc__ = fun.__doc__
#     fun2.__annotations__ = fun.__annotations__
#     fun2.__qualname__ = fun.__qualname__
#
#     return fun(*args,**kwargs)
#
# fun2.__doc__ =fun.__doc__
# fun2.__annotations__ = fun.__annotations__
# fun2.__qualname__ = fun.__qualname__
# fun2.
#
# print(fun2.__annotations__)
# print(fun2.__qualname__)
# print(fun2.__doc__)
#
# fun2()
#


'''
https://youtrack.jetbrains.com/issue/PY-51558
'''
from typing import TypeVar, ParamSpec, Any
from collections.abc import Callable, Coroutine


RT = TypeVar("RT")
P = ParamSpec("P")


def decoratorx(func: Callable[P, RT]) -> Callable[P,RT]:
    def wrapper(*args:P.args, **kwargs:P.kwargs) ->RT :
        return func(*args,**kwargs)
    return wrapper

def decoratorx2(func) :
    def wrapper(*args, **kwargs):
        return func(*args,**kwargs)
    return wrapper


@decoratorx
def f4(aaa:str,bbb:int,ccc:float=None,ddd=20):
    print(aaa,bbb,ccc)


f4(1,2,ccc=5.6,ddd=30)

# f4('1',2,ccc=(7,8,))

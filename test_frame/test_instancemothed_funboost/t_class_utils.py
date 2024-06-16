import inspect
from types import MethodType

from funboost.utils.class_utils import ClsHelper


class Myclass():
    def __init__(self, x):
        self.x = x

    def add(self, y):
        return self.x + y

    @classmethod
    def sub(cls, m):
        return m

    @staticmethod
    def div(n):
        return n

    @classmethod
    async def aio_sub(n):
        return n

    def aio_add(self, y):
        return self.x + y


def common_f():
    pass


print(isinstance(Myclass.add, staticmethod))
print(isinstance(Myclass.sub, classmethod))
print(Myclass.add.__annotations__)
print(inspect.getsourcelines(Myclass.add))
print(inspect.getsourcelines(Myclass.sub))

#
print(ClsHelper.get_instncae_method_cls(Myclass.add))
#
print(ClsHelper.get_classs_method_cls(Myclass.sub))

print(inspect.ismethod(Myclass.add))
print(inspect.ismethod(Myclass.sub))
print(inspect.ismethod(Myclass.div))
print(isinstance(Myclass.add, MethodType))
print(type(Myclass.add))
print(type(common_f))

print(ClsHelper.is_instance_method(Myclass.add))
print(ClsHelper.is_instance_method(Myclass.sub))

print(ClsHelper.is_classs_method(Myclass.add))
print(ClsHelper.is_classs_method(Myclass.sub))

print(ClsHelper.is_instance_method(Myclass.aio_add))
print(ClsHelper.is_instance_method(Myclass.aio_sub))

print(ClsHelper.is_classs_method(Myclass.aio_add))
print(ClsHelper.is_classs_method(Myclass.aio_sub))

print(ClsHelper.is_static_method(Myclass.div))

print(inspect.getfullargspec(Myclass.add))

print(ClsHelper.get_method_kind(Myclass.add))
print(ClsHelper.get_method_kind(Myclass.sub))
print(ClsHelper.get_method_kind(Myclass.div))
print(ClsHelper.get_method_kind(common_f))

print(ClsHelper.is_common_function(common_f))

print(dir(common_f))
# for k in dir(Myclass.add):
#     print(k, getattr(Myclass.add, k))
print(common_f.__qualname__)

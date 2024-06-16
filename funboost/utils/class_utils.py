import gc
import inspect
import re
import sys
import typing

import nb_log
from types import MethodType, FunctionType


class FunctionKind:
    class_method = 'class_method'
    instance_method = 'instance_method'
    static_method = 'static_method'
    common_function = 'common_function'


class ClsHelper:
    @staticmethod
    def get_instncae_method_cls(instncae_method):
        print(instncae_method)
        print(instncae_method.__qualname__)
        print(instncae_method.__module__)
        return getattr(sys.modules[instncae_method.__module__],instncae_method.__qualname__.split('.')[0])
        # return instncae_method.__self__.__class__

    @staticmethod
    def get_classs_method_cls(class_method):
        print(class_method)
        print(class_method.__qualname__)
        print(class_method.__module__)
        return getattr(sys.modules[class_method.__module__],class_method.__qualname__.split('.')[0])

    @staticmethod
    def is_class_method(method):
        # if inspect.ismethod(method):
        #     if hasattr(method, '__self__') and inspect.isclass(method.__self__):
        #         return True
        # return False

        sourcelines = inspect.getsourcelines(method)
        print(sourcelines)
        line0: str = sourcelines[0][0]
        if line0.replace(' ', '').startswith('@classmethod'):
            return True

    @staticmethod
    def is_static_method(method):
        sourcelines = inspect.getsourcelines(method)
        line0: str = sourcelines[0][0]
        if line0.replace(' ', '').startswith('@staticmethod'):
            return True

    @classmethod
    def is_instance_method(cls, method):
        if cls.is_class_method(method):
            return False
        if cls.is_static_method(method):
            return False
        if isinstance(method, FunctionType):
            sourcelines = inspect.getsourcelines(method)
            for line in sourcelines[0][:50]:
                if not line.replace( ' ','').startswith('#'):
                    if not line.startswith('def') and re.search('\(\s*?self\s*?,',line):
                        return True
        # method_class = getattr(method, '__qualname__', '').rsplit('.', 1)[0]
        # if method_class:  # 如果能找到类名，说明是类的成员
        #     print( f"{method.__name__} 属于类 {method_class} 的成员")
        #
        #     return True

    @classmethod
    def is_common_function(cls, method):
        if cls.is_static_method(method):
            return False
        if cls.is_class_method(method):
            return False
        if cls.is_instance_method(method):
            return False
        if isinstance(method, FunctionType):
            sourcelines = inspect.getsourcelines(method)
            for line in sourcelines[0][:50]:
                if not line.replace(' ', '').startswith('#'):
                    if not re.search('\(\s*?self\s*?,', line):
                        return True

    @classmethod
    def get_method_kind(cls, method: typing.Callable) -> str:
        if cls.is_class_method(method):
            return FunctionKind.class_method
        elif cls.is_static_method(method):
            return FunctionKind.static_method
        elif cls.is_instance_method(method):
            return FunctionKind.instance_method
        elif cls.is_common_function(method):
            return FunctionKind.common_function


if __name__ == '__main__':
    pass
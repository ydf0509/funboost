import copy
import gc
import inspect
import re
import sys
import traceback
import typing

import nb_log
from types import MethodType, FunctionType




class ClsHelper:
    @staticmethod
    def is_static_method(func):
        # 获取类名
        class_name = func.__qualname__.split('.')[0]
        # 使用 inspect 获取函数的原始定义
        return isinstance(func, staticmethod) or (inspect.isfunction(func) and func.__qualname__.startswith(f'{class_name}.'))

    # 判断函数是否是实例方法
    @staticmethod
    def is_instance_method(method):
        # 检查方法是否是绑定到类实例上的方法
        return inspect.ismethod(method) or (inspect.isfunction(method) and getattr(method, '__self__', None) is not None)

    @staticmethod
    def is_class_method(method):
        # 检查方法是否是类方法
        return isinstance(method, classmethod) or (inspect.isfunction(method) and method.__self__ is None)



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
        func =method
        try:
            if cls.is_instance_method(func):
                return "实例方法"
            if cls.is_static_method(func):
                return "静态方法"
            if cls.is_class_method(func):
                return "类方法"
            if inspect.isfunction(func):
                return "模块级函数"
        except Exception as e:
            print(traceback.format_exc())

    @staticmethod
    def get_obj_init_params_for_funboost(obj_init_params: dict):
        obj_init_params.pop('self')
        return copy.deepcopy(obj_init_params)




if __name__ == '__main__':
    def module_function():
        return "I am a module-level function"


    class MyClass:
        @staticmethod
        def static_method():
            return "I am a static method"

        @classmethod
        def class_method(cls):
            return "I am a class method"

        def instance_method(self):
            return "I am a instance method"

    print(ClsHelper.get_method_kind(module_function))  # 输出: 模块级函数
    print(ClsHelper.get_method_kind(MyClass.static_method))  # 输出: 静态方法
    print(ClsHelper.get_method_kind(MyClass.class_method))  # 输出: 类方法
    print(ClsHelper.get_method_kind(MyClass.instance_method))  # 输出: 实例方法

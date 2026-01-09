
"""
这个pydantic 基类能兼容pydantic v1 和 v2 和v3
使v2中不再警告用户使用过气的方法，使未来的v3中不报错v1的老方法不存在。
"""
import datetime
import functools
import json
import typing
from collections import OrderedDict
from pydantic import BaseModel
import pydantic


def _patch_for_pydantic_field_deepcopy():
    from concurrent.futures import ThreadPoolExecutor
    from asyncio import AbstractEventLoop

    # noinspection PyUnusedLocal,PyDefaultArgument
    def __deepcopy__(self, memodict={}):
        """
        pydantic 的默认值，需要deepcopy
        """
        return self

    # pydantic 的类型需要用到
    ThreadPoolExecutor.__deepcopy__ = __deepcopy__
    AbstractEventLoop.__deepcopy__ = __deepcopy__
    # BaseEventLoop.__deepcopy__ = __deepcopy__

_patch_for_pydantic_field_deepcopy

def get_pydantic_major_version() -> int:
    version = pydantic.VERSION
    try:
        return int(version.split(".", 1)[0])
    except Exception:
        return -1

if get_pydantic_major_version() == 1:

    class CompatibleModel(BaseModel):
        class Config:
            arbitrary_types_allowed = True
            # allow_mutation = False
            extra = "forbid"
            json_encoders = {
                datetime.datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")
            }

        def to_json(self, **kwargs):
            return self.json(**kwargs)

        def to_dict(self):
            return self.dict()

elif get_pydantic_major_version() >= 2:
    from pydantic import ConfigDict

    class CompatibleModel(BaseModel):
        model_config = ConfigDict(
            arbitrary_types_allowed=True,
            extra="forbid",
        )

        # pydantic v2 默认就能正确序列化 datetime，无需额外配置

        def to_json(self, **kwargs):
            return self.model_dump_json(**kwargs)

        def to_dict(self):
            return self.model_dump()


# 统一兼容 root_validator / model_validator 的装饰器
def compatible_root_validator(*, skip_on_failure=True, mode="after"):
    """
    统一 pydantic v1 和 v2 的校验器写法，让用户可以统一用 self.xxx 的方式访问和修改字段。

    v1: root_validator(skip_on_failure=skip_on_failure) - 原本签名是 (cls, values: dict)
    v2: model_validator(mode=mode) - 签名是 (self)

    用法:
        @compatible_root_validator(skip_on_failure=True)
        def check_values(self):
            if self.qps and self.concurrent_num == 50:
                self.concurrent_num = 500
            return self
    """

    def decorator(func):
        if get_pydantic_major_version() == 1:
            from pydantic import root_validator

            # 注意：不能使用 @functools.wraps(func)，否则 pydantic v1 会检查到原函数签名 (self) 而报错
            def v1_wrapper(cls, values: dict):
                # 创建一个命名空间对象，让用户可以用 self.xxx 的方式访问字段
                # 同时代理访问原始模型类的元信息（如 __fields__, model_fields）
                class _ValuesNamespace:
                    # 类属性：存储原始模型类的引用
                    _model_cls = cls
                    _field_keys = set(values.keys())

                    def __init__(self, d: dict):
                        # 将字段值存入实例
                        for k, v in d.items():
                            object.__setattr__(self, k, v)

                    def __setattr__(self, name, value):
                        object.__setattr__(self, name, value)

                    def keys(self):
                        return self._field_keys

                    @property
                    def model_fields(self):
                        # 代理访问类的字段定义（兼容 v2 风格）
                        # 在 v1 中返回 __fields__
                        return self._model_cls.__fields__

                    def __getattr__(self, name):
                        # 处理 __fields__ 等特殊属性的访问
                        if name == "__fields__":
                            return self._model_cls.__fields__
                        raise AttributeError(
                            f"'{self._model_cls.__name__}' object has no attribute '{name}'"
                        )

                    @property
                    def __class__(self):
                        # 让 self.__class__.__name__ 返回正确的类名
                        return self._model_cls

                ns = _ValuesNamespace(values)
                result = func(ns)
                # 把修改后的值同步回 values 字典
                for k in values:
                    if hasattr(result, k):
                        values[k] = getattr(result, k)
                return values

            v1_wrapper.__name__ = func.__name__  # 手动设置函数名，用于调试
            v1_wrapper.__doc__ = func.__doc__
            return root_validator(skip_on_failure=skip_on_failure, allow_reuse=True)(
                v1_wrapper
            )
        else:
            from pydantic import model_validator

            # v2 的 model_validator(mode='after') 直接接收 self
            @functools.wraps(func)
            def v2_wrapper(self):
                return func(self)

            return model_validator(mode=mode)(v2_wrapper)

    return decorator


class BaseJsonAbleModel(CompatibleModel):
    """
    因为model字段包括了 函数和自定义类型的对象,无法直接json序列化,需要自定义json序列化
    """

    def get_str_dict(self):
        model_dict: dict = self.to_dict()  # noqa
        model_dict_copy = OrderedDict()
        for k, v in model_dict.items():
            if isinstance(v, typing.Callable):
                model_dict_copy[k] = str(v)
            # elif k in ['specify_concurrent_pool', 'specify_async_loop'] and v is not None:
            elif (
                type(v).__module__ != "builtins"
            ):  # 自定义类型的对象,json不可序列化,需要转化下.
                model_dict_copy[k] = str(v)
            else:
                model_dict_copy[k] = v
        return model_dict_copy

    def json_str_value(self):
        try:
            return json.dumps(
                dict(self.get_str_dict()),
                ensure_ascii=False,
            )
        except TypeError as e:
            return str(self.get_str_dict())

    def json_pre(self):
        try:
            return json.dumps(self.get_str_dict(), ensure_ascii=False, indent=4)
        except TypeError as e:
            return str(self.get_str_dict())

    def update_from_dict(self, dictx: dict):
        for k, v in dictx.items():
            setattr(self, k, v)
        return self

    def update_from_kwargs(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self

    def update_from_model(self, modelx: BaseModel):
        for k, v in modelx.to_dict().items():
            setattr(self, k, v)
        return self

    @staticmethod
    def init_by_another_model(model_type: typing.Type[BaseModel], modelx: BaseModel):
        init_dict = {}
        for k, v in modelx.to_dict().items():
            if k in model_type.__fields__.keys():
                init_dict[k] = v
        return model_type(**init_dict)


# 缓存每个模型类型的不可序列化字段
_model_non_serializable_fields_cache: typing.Dict[typing.Type, typing.Set[str]] = {}

def get_cant_json_serializable_fields(model_type: typing.Type[BaseModel]) -> typing.Set[str]:
    """
    获取 Pydantic 模型中所有不可JSON序列化的字段名列表
    使用缓存，每个模型类型只在第一次调用时计算
    
    Args:
        model_type: Pydantic 模型类型
        
    Returns:
        不可JSON序列化的字段名集合
        
    Example:
        >>> from funboost.core.func_params_model import BoosterParams
        >>> fields = get_cant_json_serializable_fields(BoosterParams)
        >>> 'specify_concurrent_pool' in fields
        True
        >>> 'queue_name' in fields
        False
    """
    # 如果已有缓存，直接返回
    if model_type in _model_non_serializable_fields_cache:
        return _model_non_serializable_fields_cache[model_type]
    
    import inspect
    from collections.abc import Callable as AbcCallable
    
    non_serializable_fields = set()
    
    # 获取模型的所有字段类型注解
    # 兼容 pydantic v1 和 v2
    if hasattr(model_type, 'model_fields'):
        # pydantic v2
        fields_info = model_type.model_fields
    else:
        # pydantic v1
        fields_info = model_type.__fields__
    
    for field_name, field_info in fields_info.items():
        # 获取字段的类型注解
        if hasattr(field_info, 'annotation'):
            # pydantic v2
            field_type = field_info.annotation
        else:
            # pydantic v1
            field_type = field_info.outer_type_ if hasattr(field_info, 'outer_type_') else field_info.type_
        
        # 判断类型是否不可JSON序列化
        # 使用 typing.get_origin 和 get_args 来准确判断类型
        origin = typing.get_origin(field_type)
        
        # 处理 Optional[X] / Union[X, None] 类型，获取实际类型
        if origin is typing.Union:
            args = typing.get_args(field_type)
            # 过滤掉 NoneType，获取实际类型
            non_none_types = [arg for arg in args if arg is not type(None)]
            if non_none_types:
                field_type = non_none_types[0]
                origin = typing.get_origin(field_type)
        
        # 判断是否是不可序列化的类型
        # 1. typing.Callable - 函数类型
        # 2. typing.Type - 类类型
        # 3. 自定义类 - 实际的类对象（非基本类型）
        is_callable = origin is AbcCallable or (hasattr(typing, 'Callable') and origin is getattr(typing, 'Callable', None))
        is_type = origin is type or str(field_type).startswith('typing.Type')
        
        # 检查是否是自定义类：
        # - 必须是一个实际的类（继承自 type，即 inspect.isclass 为 True）
        # - 不是基本类型（str, int, float, bool, list, dict）
        # - 不是 typing 模块的泛型（Literal, Union, Optional 等已被 origin 处理）
        is_custom_class = False
        if not is_callable and not is_type and origin is None:
            # origin 为 None 说明不是泛型类型，可能是普通类
            # 检查是否是实际的自定义类
            if inspect.isclass(field_type):
                # 是一个类，检查是否是基本类型
                if field_type not in (str, int, float, bool, list, dict):
                    is_custom_class = True
        
        if is_callable or is_type or is_custom_class:
            non_serializable_fields.add(field_name)
    
    # 缓存结果
    _model_non_serializable_fields_cache[model_type] = non_serializable_fields
    return non_serializable_fields

if __name__ == '__main__':
    from funboost.core.func_params_model import BoosterParams
    print(get_cant_json_serializable_fields(BoosterParams))
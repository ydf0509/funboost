# funboost/faas/__init__.py

"""
惰性导入机制：只在用户实际访问时才导入对应的 router
这样用户只使用 fastapi 时不会因为 flask/django 未安装而报错
"""

import typing

from funboost.core.active_cousumer_info_getter import (
    ActiveCousumerProcessInfoGetter,
    QueuesConusmerParamsGetter,
    SingleQueueConusmerParamsGetter,
    CareProjectNameEnv,
)


# 动态导入配置：映射表定义了所有支持的router
_ROUTER_CONFIG = {
    "fastapi_router": {
        "module": "fastapi_adapter",
        "attr": "fastapi_router",
        "package": "fastapi",
    },
    "flask_blueprint": {
        "module": "flask_adapter",
        "attr": "flask_blueprint",
        "package": "flask",
    },
    "django_router": {
        "module": "django_adapter",
        "attr": "django_router",
        "package": "django-ninja",
    },
}

# 动态导入的缓存
_cache = {}


def __getattr__(name: str):
    """
    惰性导入机制：只在用户实际访问时才导入对应的 router
    这样用户只使用 fastapi 时不会因为 flask/django 未安装而报错
    """
    # 检查是否是支持的router
    if name not in _ROUTER_CONFIG:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    # 如果已缓存，直接返回
    if name in _cache:
        return _cache[name]

    # 获取配置信息
    config = _ROUTER_CONFIG[name]

    # 动态导入
    try:
        module = __import__(
            f"{__package__}.{config['module']}", fromlist=[config["attr"]]
        )
        router_obj = getattr(module, config["attr"])
        _cache[name] = router_obj
        return router_obj
    except ImportError as e:
        raise ImportError(
            f"无法导入 {name}，请先安装 {config['package']}: pip install {config['package']}\n"
            f"原始错误: {e}"
        )


# 定义 __all__ 以支持 from funboost.faas import *
__all__ = [
    "ActiveCousumerProcessInfoGetter",
    "QueuesConusmerParamsGetter",
    "SingleQueueConusmerParamsGetter",
    "CareProjectNameEnv",
    "fastapi_router",
    "flask_blueprint",
    "django_router",
]


# 4. 类型检查支持 (让 PyCharm/VSCode 能补全)
if typing.TYPE_CHECKING:
    # 这里只是给 IDE 看的，运行时不会执行，所以不会报错
    from .fastapi_adapter import fastapi_router
    from .flask_adapter import flask_blueprint
    from .django_adapter import django_router

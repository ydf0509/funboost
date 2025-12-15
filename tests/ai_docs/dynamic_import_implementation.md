# Funboost FAAS 动态导入机制实现说明

## 📝 需求背景

用户不想在只使用 FastAPI 时因为 Flask 或 Django 未安装而报错。需要实现按需导入机制。

## 🎯 解决方案

使用 Python 的 `__getattr__` 魔术方法实现模块级别的惰性导入。

## 🏗️ 实现架构

### 1. 配置化设计

使用 `_ROUTER_CONFIG` 字典来配置所有支持的 router：

```python
_ROUTER_CONFIG = {
    'fastapi_router': {
        'module': 'fastapi_adapter',      # 模块名
        'attr': 'fastapi_router',         # 导出的属性名
        'package': 'fastapi',             # 依赖包名
        'cache_var': '_fastapi_router',   # 缓存变量名（备用）
    },
    'flask_blueprint': {...},
    'django_router': {...},
}
```

**优势：**
- ✅ 配置集中管理，易于维护
- ✅ 添加新 router 只需在配置中增加一项
- ✅ 消除硬编码的 if-elif 判断
- ✅ 提高代码可扩展性

### 2. 惰性导入机制

```python
def __getattr__(name: str):
    # 1. 检查是否在配置中
    if name not in _ROUTER_CONFIG:
        raise AttributeError(...)
    
    # 2. 检查缓存
    if name in _cache:
        return _cache[name]
    
    # 3. 动态导入并缓存
    config = _ROUTER_CONFIG[name]
    module = __import__(f"{__package__}.{config['module']}", ...)
    router_obj = getattr(module, config['attr'])
    _cache[name] = router_obj
    return router_obj
```

**工作流程：**
1. 用户访问 `from funboost.faas import fastapi_router`
2. Python 触发 `__getattr__('fastapi_router')`
3. 检查配置是否存在
4. 检查缓存，如已缓存直接返回
5. 否则动态导入并缓存结果
6. 返回 router 对象

### 3. IDE 类型支持

```python
if typing.TYPE_CHECKING:
    from .fastapi_adapter import fastapi_router 
    from .flask_adapter import flask_blueprint
    from .django_adapter import django_router
```

**作用：**
- 只在类型检查时生效（不会实际执行）
- 为 IDE 提供代码补全和类型提示
- 不影响运行时的按需导入

## ✨ 核心特性

### 1. 按需导入
```python
# 只使用 FastAPI，不需要安装 Flask/Django
from funboost.faas import fastapi_router  # ✅ 成功
```

### 2. 友好的错误提示
```python
# 未安装 fastapi 时
ImportError: 无法导入 fastapi_router，请先安装 fastapi: pip install fastapi
原始错误: No module named 'fastapi'
```

### 3. 自动缓存
```python
from funboost.faas import fastapi_router as r1
from funboost.faas import fastapi_router as r2
assert r1 is r2  # ✅ True，同一个对象
```

### 4. 向后兼容
```python
# 所有现有代码都能正常工作
from funboost.faas import fastapi_router, flask_blueprint, django_router
```

## 📊 对比：重构前后

### 重构前（硬编码）：
```python
def __getattr__(name: str):
    if name == 'fastapi_router':
        # ...大量重复代码
    elif name == 'flask_blueprint':
        # ...大量重复代码
    elif name == 'django_router':
        # ...大量重复代码
```

**问题：**
- ❌ 硬编码判断
- ❌ 代码重复
- ❌ 难以扩展
- ❌ 添加新 router 需要修改多处

### 重构后（配置化）：
```python
_ROUTER_CONFIG = {...}  # 配置表

def __getattr__(name: str):
    config = _ROUTER_CONFIG[name]
    # 统一的导入逻辑
```

**优势：**
- ✅ 配置驱动
- ✅ 无代码重复
- ✅ 易于扩展
- ✅ 添加新 router 只需修改配置

## 🔧 如何添加新 Router

假设要添加一个 `tornado_router`：

```python
# 1. 在配置中添加一项
_ROUTER_CONFIG = {
    # ... 现有配置 ...
    'tornado_router': {
        'module': 'tornado_adapter',
        'attr': 'tornado_router',
        'package': 'tornado',
        'cache_var': '_tornado_router',
    },
}

# 2. 在 __all__ 中添加
__all__ = [
    # ... 现有导出 ...
    'tornado_router',
]

# 3. 在 TYPE_CHECKING 中添加类型支持
if typing.TYPE_CHECKING:
    # ... 现有导入 ...
    from .tornado_adapter import tornado_router
```

**就这样！** 无需修改 `__getattr__` 函数。

## 🎉 总结

这次重构实现了：
1. ✅ **消除硬编码**：用配置表替代多个 if 判断
2. ✅ **提高可维护性**：代码更简洁，逻辑更清晰
3. ✅ **增强可扩展性**：添加新 router 变得非常容易
4. ✅ **保持所有优势**：按需导入、友好提示、自动缓存、IDE 支持

## 📚 技术要点

- `__getattr__`: Python 模块级别的属性访问拦截
- `__import__`: 动态导入模块
- `typing.TYPE_CHECKING`: 区分类型检查和运行时
- 配置驱动设计：用数据驱动代码逻辑
- 缓存优化：避免重复导入

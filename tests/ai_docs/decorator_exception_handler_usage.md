# Funboost Router 异常处理装饰器使用文档

## 概述

为了避免在每个 FastAPI 接口都写 try-except，同时又**不影响用户自己的 FastAPI app**，我们创建了一个装饰器 `@handle_funboost_exceptions`，**只在 funboost router 的接口中使用**。

## 为什么用装饰器而不是全局异常处理器？

### 全局异常处理器的问题
- ❌ 会影响用户整个 FastAPI app 的所有接口
- ❌ 可能与用户自己的异常处理逻辑冲突
- ❌ 用户可能不希望 funboost 控制他们的全局错误处理

### 装饰器的优势
- ✅ **只作用于 funboost router 的接口**，不影响用户的 app
- ✅ 用户可以自由定义自己的异常处理逻辑
- ✅ 清晰明了，哪个接口使用了异常处理一目了然
- ✅ 灵活性更高，某些接口可以选择不使用

## 使用方法

### 基本用法

```python
from funboost.faas.fastapi_adapter import fastapi_router, handle_funboost_exceptions, BaseResponse

@fastapi_router.get("/some_endpoint")
@handle_funboost_exceptions  # 添加这个装饰器
async def some_endpoint(queue_name: str):
    """
    直接写业务逻辑，不需要 try-except
    异常会被装饰器自动捕获并返回统一格式
    """
    # 业务逻辑
    result = do_something(queue_name)
    return BaseResponse(succ=True, msg="成功", data=result)
```

### 完整示例

```python
@fastapi_router.get("/get_msg_count")
@handle_funboost_exceptions  # 使用装饰器
def get_msg_count(queue_name: str):
    """根据 queue_name 获取消息数量"""
    # 直接写业务逻辑，不需要 try-except
    publisher = SingleQueueConusmerParamsGetter(queue_name).generate_publisher_by_funboost_redis_info()
    count = publisher.get_message_count()
    
    return BaseResponse(
        succ=True,
        msg="获取成功",
        data={"queue_name": queue_name, "count": count}
    )
```

### 异步函数也支持

```python
@fastapi_router.post("/publish")
@handle_funboost_exceptions  # 异步函数同样支持
async def publish_msg(msg_item: MsgItem):
    """发布消息"""
    # 直接写业务逻辑
    publisher = SingleQueueConusmerParamsGetter(msg_item.queue_name).generate_publisher_by_funboost_redis_info()
    async_result = await publisher.aio_publish(msg_item.msg_body)
    
    return BaseResponse(
        succ=True,
        msg="发布成功",
        data={"task_id": async_result.task_id}
    )
```

## 异常处理规则

装饰器会按以下规则处理异常：

### 1. FunboostException 异常

```python
# 当代码抛出 FunboostException 时
raise QueueNameNotExists(
    message="队列不存在",
    data={"queue_name": "test_queue"}
)

# 装饰器自动返回
{
    "succ": false,
    "msg": "队列不存在",
    "code": 4001,                    # 异常的 code
    "data": {"queue_name": "test_queue"},  # 异常的 data
    "error": "QueueNameNotExists",   # 异常类名
    "traceback": null,               # 业务异常不返回堆栈
    "trace_id": "uuid-xxx"           # 如果异常有 trace_id
}
```

### 2. 普通异常

```python
# 当代码抛出普通异常时
x = "not a number"
result = int(x)  # 抛出 ValueError

# 装饰器自动返回
{
    "succ": false,
    "msg": "系统错误: ValueError: invalid literal for int()",
    "code": 5555,                    # 固定 5555
    "data": null,
    "error": "ValueError",           # 异常类名
    "traceback": "Traceback...",     # 完整堆栈
    "trace_id": null
}
```

## 用户集成示例

### 用户的 FastAPI app

```python
from fastapi import FastAPI
from funboost.faas.fastapi_adapter import fastapi_router

# 创建用户自己的 app
app = FastAPI()

# 用户自己的接口（使用自己的异常处理）
@app.get("/user/endpoint")
def user_endpoint():
    try:
        # 用户自己的逻辑和异常处理
        return {"result": "ok"}
    except Exception as e:
        # 用户自己的异常处理方式
        return {"error": str(e)}

# 引入 funboost router
app.include_router(fastapi_router)
# 注意：不需要注册全局异常处理器！
# funboost router 的异常处理通过装饰器实现，不影响用户 app
```

### 隔离性示例

```python
# 用户的接口 - 不受影响
@app.get("/user/divide")
def divide(a: int, b: int):
    # 如果 b=0，用户可以自己处理异常
    try:
        return {"result": a / b}
    except ZeroDivisionError:
        return {"error": "除数不能为0"}  # 用户自定义的错误格式

# funboost 的接口 - 使用装饰器
@fastapi_router.get("/get_queue_info")
@handle_funboost_exceptions
def get_queue_info(queue_name: str):
    # 如果出错，返回 funboost 统一格式
    info = get_info(queue_name)
    return BaseResponse(succ=True, data=info)
```

## 对比

### 之前（使用 try-except）

```python
@fastapi_router.get("/get_msg_count")
def get_msg_count(queue_name: str):
    try:
        publisher = SingleQueueConusmerParamsGetter(queue_name).generate_publisher_by_funboost_redis_info()
        count = publisher.get_message_count()
        return BaseResponse(succ=True, msg="获取成功", data={"count": count})
    except Exception as e:
        logger.exception(f'获取消息数量失败: {str(e)}')
        return BaseResponse(
            succ=False,
            msg=f"获取消息数量失败: {str(e)}",
            data=None
        )
```

### 现在（使用装饰器）

```python
@fastapi_router.get("/get_msg_count")
@handle_funboost_exceptions  # 只需添加一行
def get_msg_count(queue_name: str):
    # 直接写业务逻辑，更简洁！
    publisher = SingleQueueConusmerParamsGetter(queue_name).generate_publisher_by_funboost_redis_info()
    count = publisher.get_message_count()
    return BaseResponse(succ=True, msg="获取成功", data={"count": count})
```

## 装饰器顺序

**重要：** 装饰器顺序很重要！`@handle_funboost_exceptions` 必须放在路由装饰器之后：

```python
# ✅ 正确
@fastapi_router.get("/endpoint")
@handle_funboost_exceptions
def endpoint():
    pass

# ❌ 错误
@handle_funboost_exceptions
@fastapi_router.get("/endpoint")
def endpoint():
    pass
```

## 可选使用

不是所有接口都必须使用装饰器。如果某个接口需要特殊的异常处理逻辑，可以不使用装饰器：

```python
@fastapi_router.get("/special_endpoint")
def special_endpoint():
    """这个接口有特殊的异常处理需求"""
    try:
        result = do_something_special()
        return BaseResponse(succ=True, data=result)
    except SpecialException as e:
        # 特殊处理逻辑
        return custom_error_response(e)
    except Exception as e:
        # 其他异常的特殊处理
        return another_custom_response(e)
```

## 实现原理

装饰器内部会判断函数是同步还是异步，然后使用对应的包装器：

```python
def handle_funboost_exceptions(func):
    import functools
    
    # 异步函数的包装器
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except FunboostException as e:
            # 处理 FunboostException
            return BaseResponse(...)
        except Exception as e:
            # 处理其他异常
            return BaseResponse(...)
    
    # 同步函数的包装器
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FunboostException as e:
            return BaseResponse(...)
        except Exception as e:
            return BaseResponse(...)
    
    # 根据函数类型返回对应的包装器
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
```

## 优势总结

1. **不影响用户 app** ✅  
   - 只作用于 funboost router 的接口
   - 用户可以自由定义自己的异常处理

2. **代码更简洁** ✅  
   - 不需要在每个接口写 try-except
   - 业务逻辑更清晰

3. **格式统一** ✅  
   - 所有使用装饰器的接口返回统一的错误格式
   - 便于前端统一处理

4. **灵活性高** ✅  
   - 可以选择性地使用
   - 特殊接口可以自定义异常处理

5. **易于维护** ✅  
   - 异常处理逻辑集中在装饰器中
   - 修改一处，所有使用装饰器的接口都生效

## 注意事项

1. **不要忘记添加装饰器**  
   新增的接口如果想要统一的异常处理，记得添加 `@handle_funboost_exceptions`

2. **装饰器顺序很重要**  
   `@handle_funboost_exceptions` 必须在路由装饰器（如 `@fastapi_router.get(...)`）之后

3. **同步和异步都支持**  
   装饰器会自动判断函数类型，无需区分

4. **不影响用户 app**  
   这是最重要的设计原则，funboost 不应该干涉用户的全局配置

## 总结

通过使用装饰器而不是全局异常处理器，我们实现了：

- ✅ 简洁的代码（不需要 try-except）
- ✅ 统一的错误格式
- ✅ **不影响用户的 app**（这是关键！）
- ✅ 灵活性和可维护性

这是一个更优雅、更合理的设计方案！

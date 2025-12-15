# Funboost FastAPI 全局异常处理器使用指南

## 概述

为了避免在每个 FastAPI 接口都写 try-except，我们实现了全局异常处理器。它会自动捕获并处理所有异常，返回统一的错误格式。

## 特性

### 1. FunboostException 异常处理
- 自动提取异常的 `code`、`message`、`data` 等信息
- 返回结构化的错误响应
- 包含 `trace_id` 用于追踪

### 2. 通用异常处理  
- 捕获所有其他类型的异常
- 返回固定 code `5555`
- 包含完整的异常堆栈信息，方便调试

## 使用方法

### 方式一：使用辅助函数（推荐）

```python
from fastapi import FastAPI
from funboost.faas.fastapi_adapter import fastapi_router, register_funboost_exception_handlers

app = FastAPI()

# 1. 引入 funboost router
app.include_router(fastapi_router)

# 2. 注册全局异常处理器
register_funboost_exception_handlers(app)
```

### 方式二：手动注册

```python
from fastapi import FastAPI
from funboost.faas.fastapi_adapter import (
    fastapi_router, 
    funboost_exception_handler, 
    general_exception_handler
)
from funboost.core.exceptions import FunboostException

app = FastAPI()
app.include_router(fastapi_router)

# 手动添加异常处理器
app.add_exception_handler(FunboostException, funboost_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
```

## 错误响应格式

### FunboostException 错误响应

```json
{
    "succ": false,
    "msg": "queue name not exists",
    "code": 4001,
    "data": {
        "queue_name": "non_existent_queue"
    },
    "error": "QueueNameNotExists",
    "trace_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 普通异常错误响应

```json
{
    "succ": false,
    "msg": "系统错误: ValueError: invalid literal for int()",
    "code": 5555,
    "data": null,
    "error": "ValueError",
    "traceback": "Traceback (most recent call last):\n  File ...\n"
}
```

## 自定义异常示例

### 定义自定义异常

```python
from funboost.core.exceptions import FunboostException

class QueueNameNotExists(FunboostException):
    default_message = "queue name not exists"
    default_code = 4001

class FuncParamsError(FunboostException):
    default_message = "consuming function input params error"
    default_code = 5001
```

### 在代码中抛出异常

```python
# 抛出 QueueNameNotExists 异常
if queue_name not in all_queue_names:
    raise QueueNameNotExists(
        message=f"队列 {queue_name} 不存在",
        data={'queue_name': queue_name, 'available_queues': all_queue_names}
    )

# 抛出 FuncParamsError 异常  
if not params_valid:
    error_data = {
        'your_now_publish_params_keys_list': list(publish_params_keys_set),
        'right_func_input_params_list_info': consuming_func_input_params_list_info,
    }
    raise FuncParamsError('Invalid parameters for consuming function', data=error_data)
```

## 接口中不再需要 try-except

### 之前（需要在每个接口写 try-except）

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

### 现在（直接写业务逻辑，异常会被全局处理器捕获）

```python
@fastapi_router.get("/get_msg_count")
def get_msg_count(queue_name: str):
    publisher = SingleQueueConusmerParamsGetter(queue_name).generate_publisher_by_funboost_redis_info()
    count = publisher.get_message_count()
    return BaseResponse(succ=True, msg="获取成功", data={"count": count})
```

## 优势

1. **代码更简洁**：不需要在每个接口都写 try-except
2. **错误格式统一**：所有错误都返回统一的格式
3. **信息更丰富**：
   - FunboostException：包含业务错误码、错误数据
   - 普通异常：包含完整堆栈，方便调试
4. **易于维护**：异常处理逻辑集中管理
5. **追踪能力强**：支持 trace_id，方便分布式追踪

## 注意事项

1. 全局异常处理器必须在创建 FastAPI app 后立即注册
2. 如果某个接口需要特殊的异常处理逻辑，仍然可以在该接口内部使用 try-except
3. HTTP 状态码始终返回 200，业务错误通过响应体中的 `code` 字段区分
4. 建议在开发环境保留堆栈信息，生产环境可以考虑隐藏堆栈详情

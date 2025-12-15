# Funboost FastAPI 全局异常处理器实现总结

## 实现内容

### 1. 核心功能文件修改

#### `funboost/faas/fastapi_adapter.py`

**新增导入:**
```python
from funboost.core.exceptions import FunboostException
from fastapi import Request
from fastapi.responses import JSONResponse
```

**新增功能:**

1. **`funboost_exception_handler`**: 处理 FunboostException 类型的异常
   - 自动提取 `code`, `message`, `data`, `trace_id`
   - 返回统一的JSON格式

2. **`general_exception_handler`**: 处理所有其他异常
   - 固定返回 code 5555
   - 包含完整的异常堆栈信息
   - 自动记录日志

3. **`register_funboost_exception_handlers(app)`**: 辅助注册函数
   - 一行代码注册所有异常处理器
   - 简化用户使用

### 2. 异常类增强

#### `funboost/core/exceptions.py`

**QueueNameNotExists**:
```python
class QueueNameNotExists(FunboostException):
    default_message = "queue name not exists"
    default_code = 4001
```

**FuncParamsError**:
```python
class FuncParamsError(FunboostException):
    default_message = "consuming function input params error"  
    default_code = 5001
```

**FunboostException.to_dict()** 增强:
- 添加 `utc_time` 和 `local_time` 字段
- 使用时区感知的时间格式

### 3. 使用异常的代码

#### `active_cousumer_info_getter.py`
```python
# 导入异常类
from funboost.core.exceptions import QueueNameNotExists

# 使用异常
raise QueueNameNotExists(
    err_msg, 
    data={'queue_name': self.queue_name}
)
```

#### `consuming_func_iniput_params_check.py`
```python
# 导入异常类
from funboost.core.exceptions import FuncParamsError

# 使用异常
error_data = {
    'your_now_publish_params_keys_list': list(publish_params_keys_set),
    'right_func_input_params_list_info': self.consuming_func_input_params_list_info,
}
raise FuncParamsError(
    'Invalid parameters for consuming function',
    data=error_data
)
```

## 使用方式

### 基本用法

```python
from fastapi import FastAPI
from funboost.faas.fastapi_adapter import (
    fastapi_router, 
    register_funboost_exception_handlers
)

app = FastAPI()
app.include_router(fastapi_router)

# 关键：注册全局异常处理器
register_funboost_exception_handlers(app)
```

### 接口代码简化

**之前** (每个接口都需要 try-except):
```python
@fastapi_router.get("/get_msg_count")
def get_msg_count(queue_name: str):
    try:
        publisher = SingleQueueConusmerParamsGetter(queue_name).generate_publisher_by_funboost_redis_info()
        count = publisher.get_message_count()
        return BaseResponse(succ=True, msg="获取成功", data=CountData(queue_name=queue_name, count=count))
    except Exception as e:
        logger.exception(f'获取消息数量失败: {str(e)}')
        return BaseResponse(
            succ=False,
            msg=f"获取消息数量失败: {str(e)}",
            data=CountData(queue_name=queue_name, count=-1)
        )
```

**现在** (直接写业务逻辑):
```python
@fastapi_router.get("/get_msg_count")
def get_msg_count(queue_name: str):
    publisher = SingleQueueConusmerParamsGetter(queue_name).generate_publisher_by_funboost_redis_info()
    count = publisher.get_message_count()
    return BaseResponse(
        succ=True,
        msg="获取成功",
        data=CountData(queue_name=queue_name, count=count)
    )
```

## 错误响应格式

### FunboostException 响应示例

```json
{
    "succ": false,
    "msg": "queue name not exists",
    "code": 4001,
    "data": {
        "queue_name": "non_existent_queue",
        "available_queues": ["queue1", "queue2"]
    },
    "error": "QueueNameNotExists",
    "trace_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 普通异常响应示例

```json
{
    "succ": false,
    "msg": "系统错误: ValueError: invalid literal for int() with base 10: 'abc'",
    "code": 5555,
    "data": null,
    "error": "ValueError",
    "traceback": "Traceback (most recent call last):\n  File \"...\", line 123, in ...\n    ...\nValueError: invalid literal for int() with base 10: 'abc'"
}
```

## 优势

### 1. 代码简洁性
- 不需要在每个接口都写 try-except
- 减少了大量重复代码
- 业务逻辑更清晰

### 2. 错误格式统一
- 所有错误都返回统一的JSON格式
- 前端只需要一套错误处理逻辑

### 3. 错误信息丰富
- **FunboostException**: 包含业务错误码、错误数据、trace_id
- **普通异常**: 包含完整堆栈，方便调试

### 4. 易于维护
- 异常处理逻辑集中管理
- 修改错误格式只需改一处

### 5. 类型安全
- FunboostException 支持自定义 code 和 data
- 易于扩展新的异常类型

## 文件清单

### 修改的文件
1. `funboost/faas/fastapi_adapter.py` - 添加全局异常处理器
2. `funboost/core/exceptions.py` - 优化异常类，添加时间字段
3. `funboost/core/active_cousumer_info_getter.py` - 导入并使用 QueueNameNotExists
4. `funboost/core/consuming_func_iniput_params_check.py` - 导入并使用 FuncParamsError

### 新增的文件
1. `tests/ai_docs/global_exception_handler_usage.md` - 使用文档
2. `tests/ai_codes/test_global_exception_handler.py` - 测试代码
3. `tests/ai_docs/global_exception_handler_summary.md` - 本总结文档

## 测试方法

运行测试代码:
```bash
python tests/ai_codes/test_global_exception_handler.py
```

然后访问:
- http://127.0.0.1:8888/docs - 查看API文档
- http://127.0.0.1:8888/test/funboost_exception - 测试 FunboostException
- http://127.0.0.1:8888/test/normal_exception - 测试普通异常
- http://127.0.0.1:8888/test/success - 测试成功响应

## 注意事项

1. **必须注册**: 全局异常处理器必须调用 `register_funboost_exception_handlers(app)` 才会生效

2. **注册时机**: 必须在创建 FastAPI app 之后立即注册

3. **HTTP状态码**: 所有响应的 HTTP 状态码都是 200，业务错误通过 `code` 字段区分

4. **局部 try-except**: 如果某个接口需要特殊处理，仍然可以在接口内部使用 try-except

5. **生产环境**: 考虑在生产环境隐藏 `traceback` 字段，避免泄露敏感信息

## 扩展建议

### 1. 添加更多自定义异常类
```python
class PermissionDenied(FunboostException):
    default_message = "permission denied"
    default_code = 4003

class ResourceNotFound(FunboostException):
    default_message = "resource not found"
    default_code = 4004
```

### 2. 根据环境控制堆栈信息
```python
import os

def get_traceback():
    if os.getenv('ENV') == 'production':
        return None  # 生产环境不返回堆栈
    return traceback.format_exc()
```

### 3. 添加错误日志记录
```python
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f'未预期的异常: {str(exc)}')
    # 可以上报到监控系统，如 Sentry
    # sentry_sdk.capture_exception(exc)
    ...
```

## 总结

通过实现全局异常处理器，我们成功地:
- ✅ 消除了每个接口的 try-except 重复代码
- ✅ 实现了统一的错误响应格式
- ✅ 提供了丰富的错误信息（code、data、traceback）
- ✅ 简化了用户的使用方式（一行代码注册）
- ✅ 保持了代码的整洁性和可维护性

这是一个优雅的解决方案，符合 FastAPI 的最佳实践！

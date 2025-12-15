# BaseResponse 字段更新说明

## 更新内容

为了保持全局异常处理器返回格式与 `BaseResponse` 模型的一致性，我们在 `BaseResponse` 中新增了三个可选字段。

### 新增字段

```python
class BaseResponse(BaseModel, typing.Generic[T]):
    """统一的泛型响应模型"""
    succ: bool                              # 请求是否成功
    msg: str                                # 消息描述
    data: typing.Optional[T] = None         # 返回的数据
    code: typing.Optional[int] = 200        # 业务状态码
    
    # ========== 新增字段 ==========
    error: typing.Optional[str] = None      # 错误类型名称
    traceback: typing.Optional[str] = None  # 异常堆栈信息
    trace_id: typing.Optional[str] = None   # 追踪ID
```

## 字段说明

### 1. `error` - 错误类型名称
- **类型**: `Optional[str]`
- **何时有值**: 发生异常时
- **示例值**: 
  - `"QueueNameNotExists"` - Funboost自定义异常
  - `"ValueError"` - Python内置异常
  - `"KeyError"` - 字典键错误
- **用途**: 前端可以根据错误类型做不同的UI展示或处理

### 2. `traceback` - 异常堆栈信息
- **类型**: `Optional[str]`
- **何时有值**: 发生普通异常时（code=5555）
- **何时为None**: 
  - 成功响应时
  - FunboostException异常时（业务异常不返回堆栈）
- **示例值**: 
  ```
  Traceback (most recent call last):
    File "/path/to/file.py", line 123, in function_name
      result = int("abc")
  ValueError: invalid literal for int() with base 10: 'abc'
  ```
- **用途**: 开发调试、错误日志分析

### 3. `trace_id` - 追踪ID
- **类型**: `Optional[str]`
- **何时有值**: 
  - FunboostException 启用了 `enable_trace_id=True` 时
  - 手动设置时
- **示例值**: `"550e8400-e29b-41d4-a716-446655440000"`
- **用途**: 分布式系统中追踪请求链路

## 响应示例

### 成功响应

```json
{
    "succ": true,
    "msg": "获取成功",
    "code": 200,
    "data": {
        "count": 100,
        "queue_name": "test_queue"
    },
    "error": null,
    "traceback": null,
    "trace_id": null
}
```

### FunboostException 错误响应

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
    "traceback": null,
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
    "traceback": "Traceback (most recent call last):\n  File ...\n  ValueError: ...",
    "trace_id": null
}
```

## 字段使用场景对照表

| 场景 | succ | code | error | traceback | trace_id |
|-----|------|------|-------|-----------|----------|
| 成功 | true | 200 | null | null | null/有值* |
| FunboostException | false | 4001/5001... | 异常类名 | null | null/有值* |
| 普通异常 | false | 5555 | 异常类名 | 完整堆栈 | null |

*trace_id 在成功时也可以设置，用于请求追踪

## 代码示例

### 接口正常返回

```python
@fastapi_router.get("/get_msg_count")
def get_msg_count(queue_name: str):
    publisher = SingleQueueConusmerParamsGetter(queue_name).generate_publisher_by_funboost_redis_info()
    count = publisher.get_message_count()
    
    # 只需要设置必要字段，可选字段会自动为None
    return BaseResponse(
        succ=True,
        msg="获取成功",
        code=200,
        data=CountData(queue_name=queue_name, count=count)
    )
    # error, traceback, trace_id 会自动为 None
```

### 手动返回错误（不推荐，应该抛出异常让全局处理器处理）

```python
@fastapi_router.get("/some_endpoint")
def some_endpoint():
    # 不推荐这样做，应该直接抛出异常
    return BaseResponse(
        succ=False,
        msg="操作失败",
        code=4001,
        data=None,
        error="CustomError",
        traceback=None,
        trace_id=None
    )
```

### 推荐做法：抛出异常

```python
@fastapi_router.get("/some_endpoint")
def some_endpoint():
    # 推荐：直接抛出异常，让全局处理器自动处理
    if something_wrong:
        raise QueueNameNotExists(
            message="队列不存在",
            data={"queue_name": "xxx"}
        )
    
    # 正常的业务逻辑
    return BaseResponse(succ=True, msg="成功", data={"result": "ok"})
```

## 前端处理建议

### TypeScript 类型定义

```typescript
interface BaseResponse<T = any> {
  succ: boolean;
  msg: string;
  code: number;
  data: T | null;
  error: string | null;
  traceback: string | null;
  trace_id: string | null;
}
```

### 统一错误处理

```typescript
async function handleApiResponse<T>(response: Response): Promise<T> {
  const data: BaseResponse<T> = await response.json();
  
  if (!data.succ) {
    // 记录错误信息
    console.error('API Error:', {
      code: data.code,
      error: data.error,
      msg: data.msg,
      trace_id: data.trace_id
    });
    
    // 开发环境打印堆栈
    if (data.traceback && process.env.NODE_ENV === 'development') {
      console.error('Traceback:', data.traceback);
    }
    
    // 根据错误类型做不同处理
    if (data.error === 'QueueNameNotExists') {
      // 队列不存在的特殊处理
      showNotification('队列不存在', 'warning');
    } else if (data.code === 5555) {
      // 系统错误
      showNotification('系统错误，请联系管理员', 'error');
      // 可以上报错误到监控系统
      reportError(data.trace_id, data.error, data.msg);
    }
    
    throw new Error(data.msg);
  }
  
  return data.data!;
}
```

## 兼容性说明

### 向后兼容
- 新增的三个字段都是可选的，默认值为 `None`
- 现有代码无需修改即可正常工作
- 旧的API响应格式仍然有效

### 迁移建议
1. **不需要立即修改现有代码**
2. 如果前端有类型定义，建议更新类型以包含新字段
3. 可以逐步利用新字段优化错误处理逻辑
4. 建议在日志系统中记录 `trace_id` 用于问题追踪

## 优势

1. **格式统一**: 所有响应（成功/失败）都使用相同的数据结构
2. **类型安全**: Pydantic 自动验证字段类型
3. **便于调试**: `traceback` 字段包含完整堆栈信息
4. **链路追踪**: `trace_id` 支持分布式追踪
5. **错误分类**: `error` 字段帮助快速识别错误类型
6. **向后兼容**: 新字段为可选，不影响现有代码

## 总结

通过在 `BaseResponse` 中添加 `error`、`traceback` 和 `trace_id` 三个可选字段，我们实现了：

✅ 全局异常处理器返回格式与模型定义完全一致  
✅ 更丰富的错误信息便于调试和追踪  
✅ 保持向后兼容性  
✅ 提升了系统的可观测性  

这是一个更加完善和专业的API响应设计！

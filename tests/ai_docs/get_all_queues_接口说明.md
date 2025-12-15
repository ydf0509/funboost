# 新增 get_all_queues 接口说明

## 概述

已成功为 `funboost_router_for_webs` 添加新接口 `/funboost/get_all_queues`，用于获取所有已注册的队列名称。

## 修改的文件

### 1. Flask 版本 - `flask_funboost_router.py`

**新增内容：**
- 添加了 `get_all_queues()` 路由函数
- 接口路径：`/funboost/get_all_queues`
- HTTP 方法：GET
- 更新了启动信息，包含新接口的说明

**接口实现：**
```python
@funboost_blueprint_for_flask.route("/get_all_queues", methods=['GET'])
def get_all_queues():
    """
    获取所有已注册的队列名称
    
    返回所有通过 @boost 装饰器注册的队列名称列表
    """
    try:
        # 获取所有队列名称
        all_queues = list(BoostersManager.get_all_queues())
        
        return jsonify({
            "succ": True,
            "msg": "获取成功",
            "queues": all_queues,
            "count": len(all_queues)
        })
        
    except Exception as e:
        return jsonify({
            "succ": False,
            "msg": f"获取所有队列失败: {str(e)}",
            "queues": [],
            "count": 0
        }), 500
```

### 2. FastAPI 版本 - `fastapi_funboost_router.py`

**新增内容：**
- 添加了 `AllQueuesResponse` 响应模型
- 添加了 `get_all_queues()` 路由函数
- 接口路径：`/funboost/get_all_queues`
- HTTP 方法：GET
- 更新了启动信息，包含新接口的说明

**响应模型：**
```python
class AllQueuesResponse(BaseModel):
    succ: bool
    msg: str
    queues: typing.List[str] = []
    count: int = 0
```

**接口实现：**
```python
@fastapi_router.get("/get_all_queues", response_model=AllQueuesResponse)
def get_all_queues():
    """
    获取所有已注册的队列名称
    
    返回所有通过 @boost 装饰器注册的队列名称列表
    """
    try:
        # 获取所有队列名称
        all_queues = list(BoostersManager.get_all_queues())
        
        return AllQueuesResponse(
            succ=True,
            msg="获取成功",
            queues=all_queues,
            count=len(all_queues)
        )
    except Exception as e:
        return AllQueuesResponse(
            succ=False,
            msg=f"获取所有队列失败: {str(e)}",
            queues=[],
            count=0
        )
```

### 3. Django Ninja 版本 - `django_ninja_funboost_router.py`

**新增内容：**
- 添加了 `AllQueuesResponse` 响应模型
- 添加了 `get_all_queues()` 路由函数
- 接口路径：`/funboost/get_all_queues`
- HTTP 方法：GET

**响应模型：**
```python
class AllQueuesResponse(BaseResponse):
    queues: typing.List[str] = []
    count: int = 0
```

**接口实现：**
```python
@funboost_router_for_django_ninja.get("/get_all_queues", response=AllQueuesResponse, summary="获取所有队列名称")
def get_all_queues(request):
    """
    获取所有已注册的队列名称
    
    返回所有通过 @boost 装饰器注册的队列名称列表
    """
    try:
        # 获取所有队列名称
        all_queues = list(BoostersManager.get_all_queues())
        
        return {
            "succ": True,
            "msg": "获取成功",
            "queues": all_queues,
            "count": len(all_queues)
        }
    except Exception as e:
        return {
            "succ": False,
            "msg": f"获取所有队列失败: {str(e)}",
            "queues": [],
            "count": 0
        }
```

## API 接口说明

### 请求

- **URL**: `/funboost/get_all_queues`
- **方法**: GET
- **参数**: 无

### 响应

**成功响应示例：**
```json
{
    "succ": true,
    "msg": "获取成功",
    "queues": ["queue1", "queue2", "queue3"],
    "count": 3
}
```

**失败响应示例：**
```json
{
    "succ": false,
    "msg": "获取所有队列失败: 错误信息",
    "queues": [],
    "count": 0
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| succ | bool | 请求是否成功 |
| msg | str | 响应消息 |
| queues | List[str] | 所有已注册的队列名称列表 |
| count | int | 队列总数 |

## 使用示例

### Flask 示例

```python
import requests

# 获取所有队列
response = requests.get("http://127.0.0.1:5000/funboost/get_all_queues")
result = response.json()

if result['succ']:
    print(f"共有 {result['count']} 个队列")
    for queue_name in result['queues']:
        print(f"  - {queue_name}")
else:
    print(f"获取失败: {result['msg']}")
```

### FastAPI 示例

```python
import requests

# 获取所有队列
response = requests.get("http://127.0.0.1:16666/funboost/get_all_queues")
result = response.json()

if result['succ']:
    print(f"共有 {result['count']} 个队列")
    for queue_name in result['queues']:
        print(f"  - {queue_name}")
else:
    print(f"获取失败: {result['msg']}")
```

### Django Ninja 示例

```python
import requests

# 获取所有队列
response = requests.get("http://127.0.0.1:8000/api/funboost/get_all_queues")
result = response.json()

if result['succ']:
    print(f"共有 {result['count']} 个队列")
    for queue_name in result['queues']:
        print(f"  - {queue_name}")
else:
    print(f"获取失败: {result['msg']}")
```

### cURL 示例

```bash
# Flask
curl http://127.0.0.1:5000/funboost/get_all_queues

# FastAPI
curl http://127.0.0.1:16666/funboost/get_all_queues

# Django Ninja
curl http://127.0.0.1:8000/api/funboost/get_all_queues
```

## 技术实现

接口使用了 `BoostersManager.get_all_queues()` 方法来获取所有已注册的队列名称。该方法返回 `queue_name__boost_params_map` 字典的所有键（即队列名称）。

**核心逻辑：**
```python
all_queues = list(BoostersManager.get_all_queues())
```

这个方法会返回所有通过 `@boost` 装饰器注册的函数对应的队列名称。

## 完整接口列表

更新后的 `funboost_router_for_webs` 提供以下接口：

1. **POST `/funboost/publish`** - 发布消息到指定队列
2. **GET `/funboost/get_result`** - 根据 task_id 获取任务执行结果
3. **GET `/funboost/get_msg_count`** - 根据 queue_name 获取消息数量
4. **GET `/funboost/get_all_queues`** ⭐ **新增** - 获取所有已注册的队列名称

## 测试文件

已创建测试文件 `tests/ai_codes/test_get_all_queues_api.py`，可以用来测试新接口的功能。该文件包含了 Flask、FastAPI 和 Django Ninja 三个版本的测试函数。

## 注意事项

1. 接口返回的队列列表包含所有通过 `@boost` 装饰器注册的队列
2. 如果没有任何队列注册，将返回空列表
3. 需要确保在启动 Web 服务前已经加载了消费函数的定义（通过 import 或 BoosterDiscovery）
4. 该接口不需要任何参数，直接 GET 请求即可

## 总结

✅ 已成功为 Flask、FastAPI 和 Django Ninja 三个版本都添加了 `/funboost/get_all_queues` 接口  
✅ 接口实现完整，包含错误处理  
✅ 更新了启动信息和文档  
✅ 创建了测试示例文件，支持三个框架的测试  
✅ README.md 中已包含接口说明

# funboost.faas 为什么比 Web 框架写接口更爽

## 传统 Django/Flask 的尴尬："脱了裤子放屁"

Django 的视图函数一般不直接写复杂逻辑，因为**视图函数不能作为普通函数被复用调用**。所以你被迫要：

```python
# 视图函数 - 只是个"搬运工"，不能直接复用
@api_view(['POST'])
def calculate_score_view(request):
    user_id = request.data['user_id']
    weights = request.data['weights']
    result = calculate_score(user_id, weights)  # 被迫多一层调用
    return Response({'result': result})

# 真正的业务逻辑 - 另外封装
def calculate_score(user_id, weights):
    # 复杂逻辑...
    return score
```

**问题**：
- 视图只是个"接收参数 → 调用函数 → 返回结果"的搬运工
- 每个功能都要写两遍：一份业务函数 + 一份视图适配器
- 还要配路由、写序列化器、写参数校验...

---

## funboost.faas 的设计哲学：函数即接口

```python
# 这就是业务函数，同时也是 HTTP 接口，也能被其他代码直接调用
@boost(BoosterParams(queue_name="calculate_score"))
def calculate_score(user_id: int, weights: dict):
    # 复杂逻辑...
    return score

# 直接当普通函数调用
result = calculate_score(123, {"a": 0.5})

# 通过队列异步调用
calculate_score.push(123, {"a": 0.5})

# 通过 HTTP 接口调用
# POST /funboost/publish {"queue_name": "calculate_score", "msg_body": {...}}
```

**一个函数，三种调用方式**，没有"脱了裤子放屁"的中间层！

---

## 代码量对比

| 功能点 | Django 需要写 | funboost 需要写 |
|-------|-------------|----------------|
| 业务函数 | ✅ 1份 | ✅ 1份 |
| 视图/路由 | ❌ 额外1份 | 0（自动） |
| 序列化器 | ❌ 额外1份 | 0（自动） |
| 参数校验 | ❌ 额外写 | 0（根据函数签名自动） |
| 接口文档 | ❌ 额外写 | 0（自动生成） |

---

## 上新功能流程对比

| 对比维度 | 传统 Django/Flask | funboost.faas |
|---------|------------------|---------------|
| **上新功能流程** | 写视图函数 → 配路由 → 写序列化 → 写参数校验 → 重启服务 | 写 `@boost` 函数 → 部署上线 → **自动可调用** |
| **接口文档** | 需要手写或用 Swagger 注解 | 自动从函数签名生成 |
| **参数校验** | 手动写校验逻辑或用 Pydantic | 自动根据 `final_func_input_params_info` 校验 |
| **Web服务重启** | **每次都要重启** | **永不重启**（热加载） |
| **跨项目复用** | 需要打包成库或微服务 | 只要共享 Redis，任意项目都能调用 |

---

## 最爽的几个点

### 1. 真正的"写完即上线"
```python
# 只写这个，部署上线后，HTTP接口马上就能调用
@boost(BoosterParams(queue_name="new_feature"))
def calculate_score(user_id: int, weights: dict):
    return score
```

### 2. Web 网关 = 万能入口
**一个 `app.include_router(fastapi_router)` 搞定所有接口**，不用再纠结：
- 这个接口用 GET 还是 POST？
- URL 路径怎么设计？
- 参数放 query 还是 body？

### 3. 天然支持异步和 RPC
传统视图函数要实现"提交任务 → 轮询结果"需要额外设计，funboost 直接内置：
```python
# need_result=True 一行搞定 RPC
{"queue_name": "xxx", "msg_body": {...}, "need_result": true}
```

### 4. 跨团队协作超方便
其他团队只需要知道 `queue_name` 和入参格式，就能直接调用你的功能，不用关心：
- 你用什么语言实现的
- 你的服务部署在哪里
- 你的服务有没有挂掉（消息队列会等你恢复）

---

## 什么场景传统方式更合适？

| 场景 | 推荐方式 |
|-----|---------|
| 需要精细控制 HTTP 状态码/headers | 传统视图函数 |
| 需要实时流式响应（SSE/WebSocket） | 传统视图函数 |
| 需要复杂的中间件链条 | 传统视图函数 |
| CPU 密集型异步任务 | funboost.faas ✅ |
| 跨服务编排调用 | funboost.faas ✅ |
| 快速迭代上新功能 | funboost.faas ✅ |

---

## 本质区别

> **Django/Flask 以"请求-响应"为中心，funboost 以"函数"为中心。**
> 
> 函数天然可复用，所以不需要适配层！

这就是"函数即服务"(FaaS) 的魅力——**专注业务逻辑本身，基础设施全自动化**。

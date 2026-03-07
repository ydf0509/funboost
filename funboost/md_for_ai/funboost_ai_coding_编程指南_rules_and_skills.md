---
noteId: "b8794550160c11f1876707e213463054"
tags: []

---


# 🤖 Funboost AI 编程指南 (Rules & Skills)

## 📜 一、Rules (AI 行为准则与约束)

这是要求 AI 在编写 `funboost` 代码时 **绝对不可违反的铁律**，用于消除 AI 幻觉（如臆造参数、使用废弃 API、混淆 Celery 概念）。

### 0. 最高知识准则：以官方上下文文档为唯一事实标准 (Single Source of Truth)
- **必须深度阅读**：在编写任何 `funboost` 相关的代码或解答问题前，你必须全面检索并深度学习用户提供的 `funboost_all_docs_and_codes.md` 文档（该文档包含了十万行的全量教程与底层源码架构）。
- **绝对禁止臆想**：你的预训练知识中可能没有最新的 `funboost` 细节，或者极易将其与 `Celery` 混淆。你生成的所有类名、方法名、入参定义（特别是 `BoosterParams` 的属性和中间件配置），**必须 100% 基于该文档中的源码事实或教程示例**，绝不允许产生任何大模型幻觉！

### 1. 核心语法：绝对使用 `BoosterParams`
- **禁止**使用老式的传参方式 `@boost("queue_name", qps=2)`。
- **必须**将所有配置参数放入 `BoosterParams` 对象中：`@boost(BoosterParams(queue_name="xxx", ...))`。
- **禁止臆造参数**：`BoosterParams` 是一个 Pydantic 模型，绝对不允许传递不存在的字段（如 `timeout`，正确的是 `function_timeout`；如 `max_retries`，正确的是 `max_retry_times`）。

### 2. 发布消息 (`push` vs `publish`)
- 只传递函数业务参数时，使用 `func.push(*args, **kwargs)`。
- 需要传递框架控制参数（如 `task_id`, `countdown`, `eta`, `msg_expire_seconds`）时，**必须**使用 `func.publish(msg_dict, task_options=TaskOptions(...))`。
- **异步环境** (async def) 中发布消息，必须使用 `await func.aio_push()` 或 `await func.aio_publish()`。

### 3. 消费启动方式
- 基础启动：`func.consume()`。
- 多进程+多线程叠加并发（性能炸裂）：`func.multi_process_consume(n)` 或简写 `func.mp_consume(n)`。
- 分组启动：`BoostersManager.consume_group("group_name")` （BoosterParams 里需要先设置 booster_group 的值）。
- 启动代码的末尾，如果主线程没有其他阻塞任务，**建议**使用 `from funboost import ctrl_c_recv; ctrl_c_recv()` 阻止主线程退出。
- 连续启动多个函数.consume()消费：`func1.consume(); func2.consume()`， 不要一厢情愿的使用子线程来启动消费，`func1.consume()`不会阻塞主线程。 
  不要使用 `threading.Thread(target=func1.consume).start()` 和  `threading.Thread(target=func2.consume).start()` 来连续启动消费，这样做是多此一举，funboost框架很人性化，早就从框架层面让用户可以避免这样写代码了。
  

### 4. 上下文获取 (禁止 Celery 思维)
- **禁止**像 Celery 一样在函数参数中加 `self` 或 `bind=True` 来获取上下文。
- **必须**使用全局上下文对象：`from funboost import fct`。
- 获取 Task ID：`fct.task_id`。
- 获取重试次数：`fct.function_result_status.run_times`。 （function_result_status 中还有非常丰富的各种其他属性，其类型是 `FunctionResultStatus`）
- 获取完整消息：`fct.full_msg`。

### 5. 定时任务 (ApsJobAdder)
- **禁止**直接使用原生的 `apscheduler.add_job` 去执行消费函数本体。
- **必须**使用 `ApsJobAdder` 类：`ApsJobAdder(func, job_store_kind='redis').add_push_job(trigger='...', ...)`。

### 6. 异步并发 (Asyncio)
- 若消费函数为 `async def`，**必须**在 `BoosterParams` 中设置 `concurrent_mode=ConcurrentModeEnum.ASYNC`（并发模式设置为多线程也可以兼容 async def 的异步函数，但不是最佳选择）。
- asyncio 生态获取 RPC 结果时，**必须**使用 `AioAsyncResult` 并 `await`，绝对禁止在异步函数中使用同步的 `AsyncResult.result`。

### 7. FaaS 微服务
- 集成 FastAPI/Flask/Django 时，**不需要**手动写发布和获取结果的 API。
- **优先使用内置 router**直接引入框架内置的 Router：`from funboost.faas import fastapi_router; app.include_router(fastapi_router)`。

### 8. 异构系统兼容与任意 JSON 消费规范 (非常重要)
- 默认情况下，Funboost 会严格校验发布的消息字段与函数签名的入参是否完全一致。
- **如果要消费非 Funboost 发布的消息（如 Java/Go 写入的消息，或带有未知 key 的 JSON）**：
  - **必须**在 BoosterParams 中设置 `should_check_publish_func_params=False`。
  - **必须**将消费函数入参定义为接收不定长参数，例如 `def task_fun(**kwargs):`，绝对禁止写成 `def task_fun(msg):` 去企图用一个 msg 入参接收整个字典。

### 9. 实例方法与类方法的 `push` 调用规范
- AI 极易用错实例方法的发布方式！Funboost 支持装饰实例方法和类方法，但 `push` 语法与普通函数不同。
- **实例方法**：**禁止**写成 `obj.method.push(x)`。**必须**写成 `ClassName.method.push(obj, x)`，第一个参数必须传入对象实例，且该对象必须定义 `obj_init_params` 属性以便反序列化。
- **类方法**：**禁止**写成 `ClassName.method.push(x)`。**必须**写成 `ClassName.method.push(ClassName, x)`，第一个参数必须传入类本身。

### 10. 自定义扩展规范 (`user_options` 与 `override_cls`)
- **禁止**为了实现自定义逻辑去修改 Funboost 源码或胡编 `BoosterParams` 的属性。
- 如果用户需要传递自定义配置，**必须**放在 `BoosterParams(user_options={'my_key': 'value'})` 字典中。
- 如果用户需要重写拦截逻辑（如格式化消息、限流），**必须**使用 OOP 继承 `AbstractConsumer` 并通过 `consumer_override_cls` 传入。

### 11. AI Agent 应该使用 `python -c "import subprocess; subprocess.run(['python','your_script.py'], timeout=30)"` 启动funboost消费脚本。
- **核心问题**：Funboost 消费函数启动后是无限循环拉取消息，程序不会自动结束，AI Agent 运行测试时会被阻塞。
- **必须主动关闭**：AI Agent 在运行 Funboost 启动消费程序后，**必须**在适当时间后主动强制kill关闭程序，避免长时间阻塞。ai最多50秒钟后就应该强制关闭funboost消费程序。
- **ai应该使用subprocess启动funboost消费** :
  ai agent 启动测试funboost程序，请记住永远使用 `python -c "import subprocess; subprocess.run(['python','your_script.py'], timeout=30)"`  , 这样就会自动杀死funboost程序了。 your_script.py 替换成ai需要启动的消费脚本.
  ai agent 禁止直接使用 `python your_script.py` 启动 funboost程序，以免ai流程被一直阻塞。
- `subprocess.run(['python','your_script.py'], timeout=30)` 中的 your_script.py 替换成实际需要运行的脚本，timeout可以按需修改，但最大不超过50秒，python替换成真正的python解释器绝对路径。


---

## 🛠️ 二、Skills (AI 技能模板)

这是提供给 AI 的**标准代码切片（Snippets）**，让 AI 遇到特定场景（如写爬虫、写定时任务、写微服务）时，直接照抄最佳实践，无需自行发挥。

### Skill 0: 最简 Hello World 任务 (零配置/本地单进程)
**场景**：用户想写一个最简单的后台任务，不需要额外安装 Redis/RabbitMQ，只要求能跑起来。
**模板**：
```python
import time
from funboost import boost, BoosterParams, BrokerEnum, ctrl_c_recv

@boost(BoosterParams(
    queue_name="hello_queue",
    broker_kind=BrokerEnum.MEMORY_QUEUE,  # 极简模式：使用内存队列，无需安装任何外部中间件
    qps=2,                                # 简单的控频：每秒执行2次
))
def hello_task(word: str):
    print(f"Hello, {word}!")
    time.sleep(1)
    return True

if __name__ == '__main__':
    # 1. 发布任务
    for i in range(10):
        hello_task.push(word=f"funboost_{i}")
    
    # 2. 基础启动消费 (当前进程内使用多线程运行，占用内存极小)
    hello_task.consume() 
    
    # 3. 阻塞主线程
    ctrl_c_recv()
```

### Skill 1: 创建标准的基础后台任务 (含高阶控制)
**场景**：用户需要一个后台队列任务，要求高并发、控频、出错重试。
**模板**：
```python
import time
from funboost import boost, BoosterParams, BrokerEnum, ctrl_c_recv

@boost(BoosterParams(
    queue_name="my_standard_task",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE, # 确保不丢数据
    concurrent_num=50,                     # 线程池并发数
    qps=10,                                # 精准控频：每秒执行10次
    max_retry_times=3,                     # 失败最大重试3次
))
def my_task(user_id: int, action: str):
    print(f"Processing user: {user_id}, action: {action}")
    time.sleep(1)
    return True

if __name__ == '__main__':
    # 发布任务
    for i in range(100):
        my_task.push(user_id=i, action="login")
    
    # 启动消费 (多进程叠加多线程)
    my_task.mp_consume(2)  # mp_consume(n) 是 multi_process_consume(n) 的简写
    ctrl_c_recv()
```

### Skill 2: 实现 RPC 模式（发布后等待结果）
**场景**：用户需要在发布任务后，同步或异步等待消费者执行完并返回结果。
**模板**：
```python
from funboost import boost, BoosterParams, BrokerEnum, AsyncResult

@boost(BoosterParams(
    queue_name="rpc_task",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    is_using_rpc_mode=True, # 必须开启 RPC 模式
))
def calc_sum(a: int, b: int):
    return a + b

if __name__ == '__main__':
    calc_sum.consume()
    
    # 发布并获取 AsyncResult 对象
    async_result: AsyncResult = calc_sum.push(10, 20)
    
    print(f"Task ID: {async_result.task_id}, Result: {async_result.result}")
```

### Skill 3: 创建定时调度任务 (Cron / Interval)
**场景**：用户需要每天定时、或每隔几秒钟执行一次任务。
**模板**：
```python
from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder, ctrl_c_recv

@boost(BoosterParams(queue_name="daily_report", broker_kind=BrokerEnum.REDIS))
def generate_report(report_type: str):
    print(f"Generating {report_type} report...")

if __name__ == '__main__':
    generate_report.consume()
    
    # 使用 ApsJobAdder 添加定时任务
    ApsJobAdder(generate_report, job_store_kind='redis').add_push_job(
        trigger='cron',
        hour=2,         # 每天凌晨2点执行
        minute=0,
        kwargs={"report_type": "sales"},
        id='daily_sales_report',
        replace_existing=True
    )
    ctrl_c_recv()
```

### Skill 4: Asyncio 异步任务与协程发布
**场景**：用户使用 FastAPI 或其他 asyncio 生态，需要纯异步的调度。
**模板**：
```python
import asyncio
from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum, AioAsyncResult

@boost(BoosterParams(
    queue_name="async_crawler",
    broker_kind=BrokerEnum.REDIS,
    concurrent_mode=ConcurrentModeEnum.ASYNC, # 指定为 asyncio 并发模式
    is_using_rpc_mode=True
))
async def async_fetch(url: str):
    await asyncio.sleep(1) # 模拟 aiohttp/httpx 异步请求
    return f"Data from {url}"

async def main():
    # 异步生态下，必须使用 aio_push
    aio_result = await async_fetch.aio_push("http://example.com")
    
    # 异步等待结果
    result_status = await AioAsyncResult(aio_result.task_id).status_and_result
    print(result_status.result)

if __name__ == '__main__':
    async_fetch.consume()
    asyncio.run(main())
```

### Skill 5: 声明式工作流编排 (Workflow)
**场景**：用户需要执行串行(Chain)、并行(Group)或并行+汇总(Chord)的复杂任务流。
**模板**：
```python
from funboost import boost
from funboost.workflow import chain, group, chord, WorkflowBoosterParams

@boost(WorkflowBoosterParams(queue_name="wf_download"))
def download(url): return f"/tmp/{url}"

@boost(WorkflowBoosterParams(queue_name="wf_process"))
def process(path, resolution): return f"{path}_{resolution}"

@boost(WorkflowBoosterParams(queue_name="wf_notify"))
def notify(results, user_id): print(f"User {user_id} done: {results}")

if __name__ == '__main__':
    # 启动消费者
    download.consume()
    process.consume()
    notify.consume()
    
    # 构建 Chord 工作流 (先下载 -> 并行处理3种分辨率 -> 汇总通知)
    workflow = chain(
        download.s("video.mp4"),
        chord(
            group(process.s(resolution=r) for r in ['360p', '720p', '1080p']),
            notify.s(user_id=1001)
        )
    )
    result = workflow.apply() # 阻塞等待整个工作流完成
```

### Skill 6: 快速集成 FaaS 微服务接口
**场景**：用户需要将 Funboost 任务直接暴露为 HTTP 接口供外部系统调用。
**模板**：
```python
import uvicorn
from fastapi import FastAPI
from funboost.faas import fastapi_router, CareProjectNameEnv

# 选填：只关注当前项目的队列，防止被其他队列干扰
CareProjectNameEnv.set('my_faas_project')

app = FastAPI()

# 核心：一键挂载 funboost 所有标准路由 (publish, get_result, get_msg_count 等)
app.include_router(fastapi_router)

if __name__ == '__main__':
    # 启动后访问 http://127.0.0.1:8000/docs 即可看到 /funboost/publish 等接口
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**核心 API 接口说明**：

启动服务后，所有接口都在 `/funboost` 前缀下，自动生成交互式文档访问 `http://127.0.0.1:8000/docs`

#### 6.1 发布消息（支持 RPC 模式）

**接口**：`POST /funboost/publish`

**请求体**：
```json
{
    "queue_name": "my_task_queue",
    "msg_body": {"user_id": 1001, "action": "login"},
    "need_result": true,
    "timeout": 60,
    "task_id": "optional_custom_task_id"
}
```

**字段说明**：
- `queue_name` (必填): 队列名称
- `msg_body` (必填): 消息体字典，即消费函数的入参
- `need_result` (可选): 是否等待 RPC 结果，默认 `false`
- `timeout` (可选): 等待结果的最大超时时间（秒），默认 `60`
- `task_id` (可选): 自定义任务 ID，不传则自动生成

---

#### 6.2 其他部分重要接口速查

**说明：**接口定义，ai不方便查看网页接口docs，可以查看 funboost\faas\fastapi_adapter.py 文件中的fastapi的路由和pydantic model定义。

**获取 RPC 结果**：`GET /funboost/get_result?task_id={任务 ID}&timeout=5`

**添加定时任务**：`POST /funboost/add_timing_job`
```json
{
    "queue_name": "my_queue",
    "trigger": "cron",
    "hour": "2",
    "minute": "0",
    "kwargs": {"report_type": "daily"}
}
```
触发器类型：`date`（一次性）/ `interval`（间隔）/ `cron`（周期）

**获取队列消息数**：`GET /funboost/get_msg_count?queue_name={队列名}`

**暂停/恢复消费**：`POST /funboost/pause_consume` 或 `/resume_consume`
```json
{"queue_name": "my_queue"}
```

**获取定时任务列表**：`GET /funboost/get_timing_jobs?queue_name={队列名}`

**获取单个定时任务**：`GET /funboost/get_timing_job?job_id={任务 ID}&queue_name={队列名}`

**删除定时任务**：`DELETE /funboost/delete_timing_job?job_id={任务 ID}&queue_name={队列名}`

**清空队列**：`POST /funboost/clear_queue`
```json
{"queue_name": "my_queue"}
```

**获取所有队列**：`GET /funboost/get_all_queues`

**获取所有队列运行详情**：`GET /funboost/get_all_queue_run_info`

---

**提示**：完整 API 文档访问 `http://127.0.0.1:8000/docs`，所有接口统一返回格式：`{"succ": bool, "msg": str, "data": any, "code": int}`





### Skill 7: 高效爬虫 (配合 boost_spider)
**场景**：用户需要写一个分布式爬虫，要求自动换代理、XPath 解析、一键入库。
**模板**：
```python
from funboost import boost, BoosterParams, BrokerEnum
from boost_spider import  RequestClient, SpiderResponse, DatasetSink

db_sink = DatasetSink("sqlite:///spider_data.db")

@boost(BoosterParams(
    queue_name="spider_task", 
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    qps=3, # 控频防封
    max_retry_times=5
))
def crawl_page(url: str):
    # RequestClient 内置了重试、UA 切换机制
    client = RequestClient(request_retry_times=3, is_change_ua_every_request=True)
    resp: SpiderResponse = client.get(url)
    
    # SpiderResponse 支持直接使用 xpath/css
    title = resp.xpath('//title/text()').extract_first()
    
    data = {"url": url, "title": title}
    # 一键入库
    db_sink.save("article_table", data)
    return data
```

### Skill 8：继承 BoosterParams（减少重复配置）
**场景**：当项目中有多个消费函数时，通常会有大量重复的配置参数。通过继承 `BoosterParams` 创建自定义子类，可以避免在每个 `@boost` 装饰器中重复书写相同的配置。
**模板**：
```python
from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum, ctrl_c_recv

# 定义项目统一的配置子类
class MyBoosterParams(BoosterParams):
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    max_retry_times: int = 3
    concurrent_mode: str = ConcurrentModeEnum.THREADING
    project_name: str = 'my_project'


# 使用自定义配置类，无需每次都写重复参数
@boost(MyBoosterParams(queue_name='task_queue_1'))
def task1(x: int):
    print(f"Task1: {x}")
    return x * 2

@boost(MyBoosterParams(queue_name='task_queue_3', qps=0.5))  # 特殊函数可单独覆盖配置
def task3(report_type: str):
    print(f"Generating {report_type} report")
    return True


if __name__ == '__main__':
    task1.consume()
    task3.consume()
    ctrl_c_recv()
```

### Skill 9: 消费异构系统/第三方的任意 JSON 消息
**场景**：消息不是由 Funboost 发布的（可能是 Java 部门直接写入 Redis 的），JSON 字段不固定或很多，只需要消费其中的某几个字段或全部原样接收。
**模板**：
```python
from funboost import boost, BoosterParams, BrokerEnum, fct

@boost(BoosterParams(
    queue_name="java_topic_queue",
    broker_kind=BrokerEnum.REDIS,
    should_check_publish_func_params=False  # 核心：关闭严格的参数校验
))
def process_any_msg(**kwargs): # 一定要定义成 **kwargs 接收所有未知字段，不要企图用一个msg入参去接受消息队列中的json消息的多个字段。
    # 使用 **kwargs 接收所有未知字段
    print(f"接收到外部系统的完整字典: {kwargs}")
    
    # 也可以通过 fct.full_msg 获取包含框架 extra 信息的完整原始消息
    print(f"原始完整消息: {fct.full_msg}")

if __name__ == '__main__':
    process_any_msg.consume()
```

### Skill 10: 自定义消费者拦截器 (Override Class)
**场景**：用户希望在函数运行前后执行自定义逻辑（如特殊的数据清洗、自定义的全局限流器、自定义的结果入库机制）。
**模板**：
```python
from funboost import boost, BoosterParams, AbstractConsumer, FunctionResultStatus

# 1. 继承 AbstractConsumer 编写自定义逻辑
class MyCustomConsumer(AbstractConsumer):
    def _user_convert_msg_before_run(self, msg) -> dict:
        # 在函数运行前，对消息进行清洗或反序列化
        if isinstance(msg, str) and "=" in msg:
            # 假设消息是 "a=1,b=2" 这种奇葩非 JSON 格式
            return {k: int(v) for k, v in [pair.split('=') for pair in msg.split(',')]}
        return super()._user_convert_msg_before_run(msg)
        
    def user_custom_record_process_info_func(self, function_result_status: FunctionResultStatus):
        # 在函数运行后，自定义记录结果到特定数据库
        if function_result_status.success:
            print(f"自定义入库：任务 {function_result_status.task_id} 成功，耗时 {function_result_status.time_cost}")

# 2. 通过 consumer_override_cls 挂载自定义类
@boost(BoosterParams(
    queue_name="custom_override_queue",
    consumer_override_cls=MyCustomConsumer
))
def my_task(a: int, b: int):
    return a + b
```

### Skill 11: 配置特定中间件专属参数 (`broker_exclusive_config`)

**场景**：你需要为所选的消息队列中间件（如 RabbitMQ、Kafka、Redis）设置其特有的高级功能，例如：RabbitMQ 的消息优先级、Kafka 的消费者组或分区数、Redis Stream 的消费者组名等。这些配置无法通过通用的 `BoosterParams` 字段表达，必须通过 `broker_exclusive_config` 字典传递。

**模板**：
```python
from funboost import boost, BoosterParams, BrokerEnum

# 示例 1: RabbitMQ 启用消息优先级 (x-max-priority)
@boost(BoosterParams(
    queue_name="priority_queue",
    broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM,
    broker_exclusive_config={
        'x-max-priority': 5,      # 必须为整数，建议 ≤5
        'no_ack': False,           # 是否自动确认
    }
))
def priority_task(user_id: int):
    print(f"Processing VIP user: {user_id}")
    return True

# 示例 2: Kafka 配置消费者组和分区数
@boost(BoosterParams(
    queue_name="kafka_topic",
    broker_kind=BrokerEnum.KAFKA_CONFLUENT,
    broker_exclusive_config={
        'group_id': 'my_consumer_group',   # Kafka 消费者组
        'auto_offset_reset': 'earliest',   # 从最早的消息开始消费
        'num_partitions': 10,               # Topic 分区数（自动创建时有效）
        'replication_factor': 1,             # 副本因子
    }
))
def process_kafka_msg(data: dict):
    print(f"Received from Kafka: {data}")

```

**注意事项**：
- `broker_exclusive_config` 是一个字典，**只能包含所选 `broker_kind` 所支持的键**。支持的键定义在 `funboost/core/broker_kind__exclusive_config_default_define.py` 中（例如 `'x-max-priority'` 仅对 RabbitMQ 有效，对 Redis 无效）。
- 如果传递了不支持的键，框架会发出警告，但不会阻止运行。为确保配置生效，请务必查阅对应中间件的文档或框架源码。


### Skill 12: 启动 Funboost Web 管理器 (funboost_web_manager)
**场景**：需要通过 Web 界面实时监控队列状态、消费速度、任务成功率等指标。

**模板**：

#### 方式1：命令行启动（推荐）
```bash
# 设置项目根目录到 PYTHONPATH
# Linux/macOS
export PYTHONPATH=/path/to/your/project
# Windows (cmd)
set PYTHONPATH=C:\path\to\your\project
# Windows (PowerShell)
$env:PYTHONPATH = "C:\path\to\your\project"

# 启动 Web 管理器
python -m funboost.funboost_web_manager.app
```

#### 方式2：代码中启动
```python
from funboost.funboost_web_manager.app import start_funboost_web_manager

# 基础启动（默认端口 27018）
start_funboost_web_manager()

# 自定义端口和项目过滤
start_funboost_web_manager(
    port=8080,
    care_project_name="my_project"  # 只显示该项目的队列
)
```




### 🚨 Skill 100 : BoosterParams 配置参数字典 (AI 必读属性库)
**重要提示**：这是 `BoosterParams` 的全量合法字段定义。**AI 在为用户生成 `@boost` 配置时，只能使用以下属性名，绝对禁止自行创造字典外不存在的参数名！**

```python
class BoosterParams(BaseJsonAbleModel):
    """
    掌握funboost 的精华就是知道 BoosterParams 的入参有哪些，如果知道有哪些入参字段，就掌握了funboost的 90% 用法。

    pydatinc pycharm编程代码补全,请安装 pydantic插件, 在pycharm的  file -> settings -> Plugins -> 输入 pydantic 搜索,点击安装 pydantic 插件.

    @boost的传参必须是此类或者继承此类,如果你不想每个装饰器入参都很多,你可以写一个子类继承BoosterParams, 传参这个子类,例如下面的 BoosterParamsComplete
    """

    queue_name: str  # 队列名字,必传项,每个函数要使用不同的队列名字.
    broker_kind: str = BrokerEnum.SQLITE_QUEUE  # 中间件选型见3.1章节 https://funboost.readthedocs.io/zh-cn/latest/articles/c3.html

    """ project_name是项目名，属于管理层面的标签, 默认为None, 给booster设置所属项目名, 用于对于在redis保存的funboost信息中，根据项目名字查看相关队列。
    # 如果不设置很难从redis保存的funboost信息中，区分哪些队列名属于哪个项目。 主要是给web接口查看用。
    # 一个项目的队列名字有哪些，是保存在redis的set中，key为 f'funboost.project_name:{project_name}'
    # 通常配合 CareProjectNameEnv.set($project_name) 使用 ，它可以让你在监控和管理时“只看自己的一亩三分地“，避免被其他人的队列刷屏干扰。"""
    project_name: typing.Optional[str] = None

    """如果设置了qps，并且cocurrent_num是默认的50，会自动开了500并发，由于是采用的智能线程池任务少时候不会真开那么多线程而且会自动缩小线程数量。
    具体看ThreadPoolExecutorShrinkAble的说明
    由于有很好用的qps控制运行频率和智能扩大缩小的线程池，此框架建议不需要理会和设置并发数量只需要关心qps就行了，框架的并发是自适应并发数量，这一点很强很好用。"""
    concurrent_mode: str = ConcurrentModeEnum.THREADING  # 并发模式,支持THREADING,GEVENT,EVENTLET,ASYNC,SINGLE_THREAD并发,multi_process_consume 支持协程/线程 叠加多进程并发,性能炸裂.
    concurrent_num: int = 50  # 并发数量，并发种类由concurrent_mode决定
    specify_concurrent_pool: typing.Optional[FunboostBaseConcurrentPool] = None  # 使用指定的线程池/携程池，可以多个消费者共使用一个线程池,节约线程.不为None时候。threads_num失效
    
    specify_async_loop: typing.Optional[asyncio.AbstractEventLoop] = None  # 指定的async的loop循环，设置并发模式为async才能起作用。 有些包例如aiohttp,发送请求和httpclient的实例化不能处在两个不同的loop中,可以传过来.
    is_auto_start_specify_async_loop_in_child_thread: bool = True  # 是否自动在funboost asyncio并发池的子线程中自动启动指定的async的loop循环，设置并发模式为async才能起作用。如果是False,用户自己在自己的代码中去手动启动自己的loop.run_forever() 
    
    """qps:
    强悍的控制功能,指定1秒内的函数执行次数，例如可以是小数0.01代表每100秒执行一次，也可以是50代表1秒执行50次.为None则不控频。 
    设置qps时候,不需要指定并发数量,funboost的能够自适应智能动态调节并发池大小."""
    qps: typing.Union[float, int, None] = None
    """is_using_distributed_frequency_control:
    是否使用分布式空频（依赖redis统计消费者数量，然后频率平分），默认只对当前实例化的消费者空频有效。
    假如实例化了2个qps为10的使用同一队列名的消费者，并且都启动，则每秒运行次数会达到20。
    如果使用分布式空频则所有消费者加起来的总运行次数是10。"""
    is_using_distributed_frequency_control: bool = False

    is_send_consumer_heartbeat_to_redis: bool = False  # 是否将发布者的心跳发送到redis，有些功能的实现需要统计活跃消费者。因为有的中间件不是真mq。这个功能,需要安装redis.
    
    # --------------- 重试配置 开始
    """max_retry_times:
    最大自动重试次数，当函数发生错误，立即自动重试运行n次，对一些特殊不稳定情况会有效果。
    可以在函数中主动抛出重试的异常ExceptionForRetry，框架也会立即自动重试。
    主动抛出ExceptionForRequeue异常，则当前 消息会重返中间件，
    主动抛出 ExceptionForPushToDlxqueue  异常，可以使消息发送到单独的死信队列中，死信队列的名字是 队列名字 + _dlx。"""
    max_retry_times: int = 3
    
    """
    is_using_advanced_retry:
    是否使用高级重试，高级重试支持指数退避重试。is_using_advanced_retry=True 时候，is_using_advanced_retry参数才能生效。


    重试间隔有2种模式，requeue 模式 和 sleep 模式。
    requeue模式: 将消息发回队列带延迟重试，立即释放线程,适合重试间隔大，防止长时间sleep占用线程导致降低了系统吞吐量。
    sleep模式: 在当前线程/协程 sleep 重试，适合重试间隔小，并且消息数量少执行不频繁。此模式的sleep时候会占用工作线程/协程
    
    如果retry_base_interval= 1.0,retry_multiplier=2.0,retry_max_interval=60.0,则重试间隔为：
    1s,2s,4s,8s,16s,32s,60s,60s,60s...
    """
    is_using_advanced_retry: bool = False  
    advanced_retry_config :dict =  { 
        'retry_mode': 'sleep', # 可以是 'sleep' 或 'requeue'，如果重试间隔大并且指数退避倍数大，那么应该使用requeue模式。因为sleep原地占用线程/协程降低服务吞吐量
        'retry_base_interval': 1.0, # 基础重试间隔（秒）  1s,2s,4s,8s,16s,30s,30s,30s...
        'retry_multiplier': 2.0, # 指数退避倍数 ，如果你想固定重试间隔，则设置为1.0
        'retry_max_interval': 60.0, # 最大重试间隔上限（秒）
        'retry_jitter': False, # 是否添加随机抖动
    }
    
    is_push_to_dlx_queue_when_retry_max_times: bool = False  # 函数达到最大重试次数仍然没成功，是否发送到死信队列,死信队列的名字是 队列名字 + _dlx。
    # --------------- 重试配置 结束

    consuming_function_decorator: typing.Optional[typing.Callable[..., typing.Any]] = None  # 函数的装饰器。因为此框架做参数自动转指点，需要获取精准的入参名称，不支持在消费函数上叠加 @ *args  **kwargs的装饰器，如果想用装饰器可以这里指定。
    
    
    """
    function_timeout: 
    超时秒数，函数运行超过这个时间，则自动杀死函数。为0是不限制。 
    用户应该尽量使用各种三方包例如 aiohttp pymysql 自己的 socket timeout 设置来控制超时，而不是无脑使用funboost的function_timeout参数。
    谨慎使用,非必要别去设置超时时间,设置后性能会降低(因为需要把用户函数包装到另一个线单独的程中去运行),而且突然强制超时杀死运行中函数,可能会造成死锁.
    (例如用户函数在获得线程锁后突然杀死函数,别的线程再也无法获得锁了)
    """
    function_timeout: typing.Union[int, float,None] = None 
    """
    is_support_remote_kill_task:
    是否支持远程任务杀死功能，如果任务数量少，单个任务耗时长，确实需要远程发送命令来杀死正在运行的函数，才设置为true，否则不建议开启此功能。
    (是把函数放在单独的线程中实现的,随时准备线程被远程命令杀死,所以性能会降低)
    """
    is_support_remote_kill_task: bool = False  
    
    """
    log_level:
        logger_name 对应的 日志级别
        消费者和发布者的日志级别,建议设置DEBUG级别,不然无法知道正在运行什么消息.
        这个是funboost每个队列的单独命名空间的日志级别,丝毫不会影响改变用户其他日志以及root命名空间的日志级别,所以DEBUG级别就好,
        用户不要压根不懂什么是python logger 的name,还去手痒调高级别. 
        不懂python日志命名空间的小白去看nb_log文档,或者直接问 ai大模型 python logger name的作用是什么.
    """
    log_level: int = logging.DEBUG # 不需要改这个级别,请看上面原因
    logger_prefix: str = ''  # 日志名字前缀,可以设置前缀
    create_logger_file: bool = True  # 发布者和消费者是否创建文件文件日志,为False则只打印控制台不写文件.
    logger_name: typing.Union[str, None] = ''  # 队列消费者发布者的日志命名空间.
    log_filename: typing.Union[str, None] = None  # 消费者发布者的文件日志名字.如果为None,则自动使用 funboost.队列 名字作为文件日志名字.  日志文件夹是在nb_log_config.py的 LOG_PATH中决定的.
    is_show_message_get_from_broker: bool = False  # 运行时候,是否记录从消息队列获取出来的消息内容
    is_print_detail_exception: bool = True  # 消费函数出错时候,是否打印详细的报错堆栈,为False则只打印简略的报错信息不包含堆栈.
    publish_msg_log_use_full_msg: bool = False # 发布到消息队列的消息内容的日志，是否显示消息的完整体，还是只显示函数入参。

    msg_expire_seconds: typing.Union[float, int,None] = None  # 消息过期时间,可以设置消息是多久之前发布的就丢弃这条消息,不运行. 为None则永不丢弃

    do_task_filtering: bool = False  # 是否对函数入参进行过滤去重.
    task_filtering_expire_seconds: int = 0  # 任务过滤的失效期，为0则永久性过滤任务。例如设置过滤过期时间是1800秒 ， 30分钟前发布过1 + 2 的任务，现在仍然执行，如果是30分钟以内执行过这个任务，则不执行1 + 2

    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = FunctionResultStatusPersistanceConfig(
        is_save_result=False, is_save_status=False, expire_seconds=7 * 24 * 3600, is_use_bulk_insert=False)  # 是否保存函数的入参，运行结果和运行状态到mongodb。这一步用于后续的参数追溯，任务统计和web展示，需要安装mongo。

    user_custom_record_process_info_func: typing.Optional[typing.Callable[..., typing.Any]] = None  # 提供一个用户自定义的保存消息处理记录到某个地方例如mysql数据库的函数，函数仅仅接受一个入参，入参类型是 FunctionResultStatus，用户可以打印参数

    is_using_rpc_mode: bool = False  # 是否使用rpc模式，可以在发布端获取消费端的结果回调，但消耗一定性能，使用async_result.result时候会等待阻塞住当前线程。
    rpc_result_expire_seconds: int = 1800  # redis保存rpc结果的过期时间.
    rpc_timeout:int = 1800 # rpc模式下，等待rpc结果返回的超时时间

    delay_task_apscheduler_jobstores_kind :Literal[ 'redis', 'memory'] = 'redis'  # 延时任务的aspcheduler对象使用哪种jobstores ，可以为 redis memory 两种作为jobstore

    
    """
    allow_run_time_cron:
    只允许在规定的crontab表达式时间内运行。

    例如 '* 23,0-2 * * *' 表示只在23点到2点运行。
    allow_run_time_cron='* 9-17 * * 1-5', 表示只在周一到周五的9点到17:59:59运行。
    为None则不限制运行时间。
    语法是知名 croniter 包的语法，不是funboost创造的特殊语法，用户自己去google或者ai学习语法。
    """
    allow_run_time_cron: typing.Optional[str] = None

    schedule_tasks_on_main_thread: bool = False  # 直接在主线程调度任务，意味着不能直接在当前主线程同时开启两个消费者。

    is_auto_start_consuming_message: bool = False  # 是否在定义后就自动启动消费，无需用户手动写 .consume() 来启动消息消费。
    
    # booster_group :消费分组名字， BoostersManager.consume_group 时候根据 booster_group 启动多个消费函数,减少需要写 f1.consume() f2.consume() ...这种。
    # 不像BoostersManager.consume_all() 会启动所有不相关消费函数,也不像  f1.consume() f2.consume() 这样需要逐个启动消费函数。
    # 可以根据业务逻辑创建不同的分组，实现灵活的消费启动策略。
    # 用法见文档 4.2d.3 章节.   使用 BoostersManager ,通过 consume_group 启动一组消费函数
    booster_group:typing.Union[str, None] = None

    consuming_function: typing.Optional[typing.Callable[..., typing.Any]] = None  # 消费函数,在@boost时候不用指定,因为装饰器知道下面的函数.
    consuming_function_raw: typing.Optional[typing.Callable[..., typing.Any]] = None  # 不需要传递，自动生成
    consuming_function_name: str = '' # 不需要传递，自动生成

    
    """
    # 加上一个不同种类中间件非通用的配置,不同中间件自身独有的配置，不是所有中间件都兼容的配置，因为框架支持30种消息队列，消息队列不仅仅是一般的先进先出queue这么简单的概念，
    # 例如kafka支持消费者组，rabbitmq也支持各种独特概念例如各种ack机制 复杂路由机制，有的中间件原生能支持消息优先级有的中间件不支持,
    # 每一种消息队列都有独特的配置参数意义，可以通过这里传递。
    # 每种中间件能传递的键值对可以看 funboost/core/broker_kind__exclusive_config_default.py 的 BROKER_EXCLUSIVE_CONFIG_DEFAULT 属性。
    """
    broker_exclusive_config: dict = {} 
    


    should_check_publish_func_params: bool = True  # 消息发布时候是否校验消息发布内容,比如有的人发布消息,函数只接受a,b两个入参,他去传2个入参,或者传参不存在的参数名字; 如果消费函数加了装饰器 ，你非要写*args,**kwargs,那就需要关掉发布消息时候的函数入参检查
    manual_func_input_params :dict= {'is_manual_func_input_params': False,'must_arg_name_list':[],'optional_arg_name_list':[]} # 也可以手动指定函数入参字段，默认是根据消费函数def定义的入参来生成这个。


    consumer_override_cls: typing.Optional[typing.Type] = None  # 使用 consumer_override_cls 和 publisher_override_cls 来自定义重写或新增消费者 发布者,见文档4.21b介绍，
    publisher_override_cls: typing.Optional[typing.Type] = None

    # func_params_is_pydantic_model: bool = False  # funboost 兼容支持 函数娼还是 pydantic model类型，funboost在发布之前和取出来时候自己转化。

    consuming_function_kind: typing.Optional[str] = None  # 自动生成的信息,不需要用户主动传参,如果自动判断失误就传递。是判断消费函数是函数还是实例方法还是类方法。如果传递了，就不自动获取函数类型。
    """ consuming_function_kind 可以为以下类型，
    class FunctionKind:
        CLASS_METHOD = 'CLASS_METHOD'
        INSTANCE_METHOD = 'INSTANCE_METHOD'
        STATIC_METHOD = 'STATIC_METHOD'
        COMMON_FUNCTION = 'COMMON_FUNCTION'
    """

    """
    user_options:
    用户额外自定义的配置,高级用户或者奇葩需求可以用得到,用户可以自由发挥,存放任何设置.
    user_options 提供了一个统一的、用户自定义的命名空间，让用户可以为自己的“奇葩需求”或“高级定制”传递配置，而无需等待框架开发者添加官方支持。
    funboost 是自由框架不是奴役框架,不仅消费函数逻辑自由,目录层级结构自由,自定义奇葩扩展也要追求自由,用户不用改funboost BoosterParams 源码来加装饰器参数
    
    使用场景见文档 4b.6 章节.
    """
    user_options: dict = {} # 用户自定义的配置,高级用户或者奇葩需求可以用得到,用户可以自由发挥,存放任何设置,例如配合 consumer_override_cls中读取 或 register_custom_broker 使用
    
    
    auto_generate_info: dict = {}  # 自动生成的信息,不需要用户主动传参.例如包含 final_func_input_params_info 和 where_to_instantiate 等。
    
    """# is_fake_booster：是否是伪造的booster,
    # 用于faas模式下，因为跨项目的faas管理只拿到了redis的一些基本元数据，没有booster的函数逻辑，
    # 例如ApsJobAdder管理定时任务，需要booster，但没有真实的函数逻辑，
    # 你可以看 SingleQueueConusmerParamsGetter.gen_booster_for_faas 的用法，目前主要是控制不要执行 BoostersManager.regist_booster
    # 普通用户完全不用改这个参数。
    """
    is_fake_booster: bool = False

    # 普通用户不用管不用改，用于隔离boosters注册。例如faas的是虚假的跨服务跨项目的booster，没有具体函数逻辑，不可污染真正的注册。
    # 如果你是想分组启动部分booster，那你应该用的是 booster_group 参数。
    booster_registry_name: str = StrConst.BOOSTER_REGISTRY_NAME_DEFAULT  

    
```

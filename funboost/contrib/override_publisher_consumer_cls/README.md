# override_publisher_consumer_cls 目录介绍

## 1.1 `funboost/contrib/override_publisher_consumer_cls` 目录下是放各种 贡献者贡献的 `consumer_override_cls` 和 `publisher_override_cls` 的实现。

用户可以非常方便的直接使用这里面的mixin父类。

用法见funboost教程4.21章节。    
@boost(BoosterParams(
    consumer_override_cls=XXXXConsumerMixin, 
    publisher_override_cls=XXXXPublisherMixin
)


# 2.1 funboost_otel_mixin.py，opentelemetry 全链路任务追踪可观测，是funboost的一个生产级别的重要战略级功能

使用方式，就是可以直接使用OtelBoosterParams  
或者你在你的BoosterParams中指定consumer_override_cls和publisher_override_cls为OtelConsumerMixin和OtelPublisherMixin。

```python
@boost(OtelBoosterParams(
    queue_name='otel_tree_task_entry',
))
```


Funboost 的 OTel 实现写得**非常出色，且极其重要**。它是 Funboost 作为一个现代分布式框架的“皇冠上的明珠”。作者通过极其优雅的 **Mixin（混入）模式** 和 **上下文注入** 技术，以**零侵入**的方式实现了标准化的全链路追踪。

## 2.1.1 **优雅的非侵入式设计 (Mixin Pattern)**
这也是 Funboost 架构灵活性的体现。作者没有修改 `Booster` 或 `AbstractConsumer` 的核心源码来硬塞追踪逻辑，而是利用了 `consumer_override_cls` 和 `publisher_override_cls` 接口。
*   **代码位置**: `funboost/contrib/override_publisher_consumer_cls/funboost_otel_mixin.py`
*   **使用demo**：`test_frame/test_otel`
*   **实现方式**:
    *   `AutoOtelPublisherMixin`: 重写 `publish`，在发送消息前创建 `PRODUCER` span，并将 trace context **注入 (Inject)** 到消息体 `msg['extra']` 中。
    *   `AutoOtelConsumerMixin`: 重写 `_run` (同步) 和 `_async_run` (异步)，从消息体取出 context 进行 **提取 (Extract)**，并以此为父节点创建 `CONSUMER` span。
*   **优点**: 这种设计完全解耦。不想用 OTel 的人，核心代码里没有任何 OTel 的痕迹（包体积小）；想用的人，只需替换类即可。

### 2.1.2 **标准化的上下文传播 (Context Propagation)**
这是分布式追踪最难也是最核心的部分。
*   **生产者端**: 使用 `opentelemetry.propagate.inject` 将当前的 TraceID/SpanID 塞入消息字典。
*   **消费者端**: 使用 `opentelemetry.propagate.extract` 从消息中恢复上下文。
*   **效果**: 这保证了 `上游服务 -> Redis/RabbitMQ -> Funboost消费者` 这条链路是不断的。如果没有这一步，消费者生成的 Span 就会是一个新的孤立 Trace，失去了追踪的意义。

### 2.1.3 **极致的扩展性：架构层面完胜 Celery**
这一实现完美诠释了 Funboost 在架构设计上的**高可扩展性与自定义能力**。
在 Celery 中，若想手动侵入核心链路来实现类似 `funboost_otel_mixin.py` 的上下文注入功能，通常需要深入研究复杂的 Signal 信号机制、自定义 Task 类甚至魔改底层 Kombu 库，实现门槛极高且难以维护。
而在 Funboost 中，得益于开放的 `override_cls` 接口，开发者仅需通过标准的 **OOP 继承与 Mixin 模式** 即可轻松切入框架核心流程，实现从简单的日志记录到复杂的全链路追踪等任意定制化需求。

---

# 3.1 funboost_micro_batch_mixin.py，微批消费者 Mixin

微批消费者实现累积 N 条消息后批量处理的功能，适用于批量写入数据库、批量调用 API 等场景。

*   **代码位置**: `funboost/contrib/override_publisher_consumer_cls/funboost_micro_batch_mixin.py`
*   **使用demo**：`test_frame/test_micro_batch`

## 3.1.1 使用方式

```python
from funboost import boost, BoosterParams
from funboost.contrib.override_publisher_consumer_cls.funboost_micro_batch_mixin import MicroBatchConsumerMixin

@boost(BoosterParams(
    queue_name='batch_insert_queue',
    consumer_override_cls=MicroBatchConsumerMixin,
    user_options={
        'micro_batch_size': 100,       # 累积100条消息后处理
        'micro_batch_timeout': 5.0,    # 或等待5秒后处理
    },
    should_check_publish_func_params=False, # 必须关闭入参校验
))
def batch_insert_to_db(items: list):
    """
    items 是一个列表，包含最多 100 个消息的函数参数
    """
    db.bulk_insert(items)
    print(f"批量插入 {len(items)} 条记录")
```

## 3.1.2 核心原理

1. **缓冲区累积**: 重写 `_submit_task` 方法，将消息累积到缓冲区
2. **触发条件**: 达到 `batch_size` 条消息或超过 `timeout` 秒后触发批量处理
3. **批量 ack/requeue**: 成功则批量确认，失败则批量重回队列
4. **函数签名**: 消费函数的入参从单个对象变为 `list[dict]`

## 3.1.3 适用场景

| 场景 | 收益 |
|------|------|
| 批量写入数据库 | 减少 DB 连接开销，吞吐量提升 10-100 倍 |
| 批量调用外部 API | 减少 HTTP 连接开销 |
| 批量发送通知 | 合并推送，减少请求次数 |

## 3.1.4 战略意义

- Funboost 的微批操作是一个**生产级的、高并发优化利器**。它极大地降低了“写批量处理逻辑”的复杂度，你不需要自己写缓冲区、不需要自己写定时器、不需要自己处理锁，只需要配置两个参数，就能把普通的消费者升级为“批量消费者”。 
- 当你把 `Broker` 设置为 **`MEMORY_QUEUE`** (Python 原生 `queue.Queue`)，再配合 **`MicroBatchConsumerMixin`**，Funboost 瞬间就变成了一个**高性能的、进程内的、自动聚合缓冲器 (In-Memory Batch Aggregator)**。

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
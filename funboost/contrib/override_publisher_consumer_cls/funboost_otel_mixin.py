"""
1.
```md
🚀 Funboost：唯一原生支持 OpenTelemetry 分布式链路追踪的 Python 任务队列框架

✅ 1 行代码接入链路追踪（BoosterParams → OtelBoosterParams）
✅ 跨队列、跨服务完整链路可视化
✅ 与 Jaeger/Zipkin/SkyWalking 无缝对接
✅ 生产级可观测性，排查问题如探囊取物
```

2.
非常牛的 opentelemetry 链路追踪 mixin，完美对接知名 opentelemetry 链路追踪中间件，例如 Jaeger/Zipkin/SkyWalking 等。

3.
用法demo见 test_frame/test_otel/test_otel_override.py

4.funboost 中实现的 OTel Mixin，确实是生产环境的救命稻草。没有它，排查分布式死循环基本靠运气和发际线。
例如你fa向fb发布，fb给fc发布，fc给fa发布，无限懵逼死循环，完蛋了传统的taskid排查不够用，不知道消息是哪来的。

fa -> fb -> fc -> fa -> ...

#### 在 Jaeger / SkyWalking / Funboost TreeExporter 中的视觉效果：
你会看到一个 **“死亡阶梯”** (Staircase to Hell)：

```text
└── 📤 fa send
    └── 📥 fa process
        └── 📤 fb send
            └── 📥 fb process
                └── 📤 fc send
                    └── 📥 fc process
                        └── 📤 fa send  <-- 再次调用 fa
                            └── 📥 fa process

"""



from opentelemetry import trace, context
from opentelemetry.propagate import inject, extract
from opentelemetry.trace import Status, StatusCode, SpanKind
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.serialization import Serialization
from funboost.core.func_params_model import BoosterParams
import copy
import typing

tracer = trace.get_tracer("funboost")


def extract_otel_context_from_funboost_msg(msg: dict):
    """
    从 msg 的 extra.otel_context 中提取 OTel 上下文 - Publisher 和 Consumer 公共逻辑
    
    :param msg: 消息字典，包含 extra.otel_context 字段
    :return: OTel Context 对象
    
    使用场景：
    - Publisher: extract_otel_context_from_funboost_msg(msg)
    - Consumer: extract_otel_context_from_funboost_msg(kw['body'])
    """
    carrier = msg.get('extra', {}).get('otel_context')
    if carrier:
        # 【显式】：carrier 存在，从中提取上下文（解决跨线程/手动透传问题）
        return extract(carrier)
    else:
        # 【隐式】：carrier 不存在，使用当前线程上下文
        return context.get_current()


class AutoOtelPublisherMixin(AbstractPublisher):
    """
    智能 OTel 发布者：
    1. 优先检查消息中是否已携带 otel_context (用户手动传递)
    2. 如果没有，则自动使用当前线程的上下文
    3. 生成 Producer Span 并注入/覆盖到消息中
    """
    
    def _get_parent_context(self, msg: dict):
        """确定父级上下文 (Parent Context)"""
        return extract_otel_context_from_funboost_msg(msg)
    
    def _inject_otel_context_to_msg(self, msg: dict):
        """
        将当前线程的 OTel 上下文注入到消息的 extra.otel_context 中
        用于 aio_publish 场景：在 asyncio 线程先捕获上下文，
        然后通过消息传递到 executor 线程
        """
        if 'extra' not in msg:
            msg['extra'] = {}
        
        # 只有当用户没有手动传递 otel_context 时才注入
        if not msg['extra'].get('otel_context'):
            carrier = {}
            inject(carrier)  # 将当前线程的上下文注入到 carrier
            msg['extra']['otel_context'] = carrier
    
    def publish(self, msg, task_id=None, task_options=None):
        msg = copy.deepcopy(msg)  # 字典是可变对象,不要改变影响用户自身的传参字典. 用户可能继续使用这个传参字典.
        msg, msg_function_kw, extra_params, task_id = self._convert_msg(msg, task_id, task_options)
        
        # -------------------------------------------------------
        # 2. 确定父级上下文 (Parent Context)
        # -------------------------------------------------------
        parent_ctx = self._get_parent_context(msg)

        # -------------------------------------------------------
        # 3. 开启 Producer Span (链接到 parent_ctx)
        # -------------------------------------------------------
        span_name = f"{self.queue_name} send"
        
        with tracer.start_as_current_span(
            span_name, 
            context=parent_ctx, # 关键：使用刚才确定的父级
            kind=SpanKind.PRODUCER
        ) as span:
            
            span.set_attribute("messaging.system", "funboost")
            span.set_attribute("messaging.destination", self.queue_name)

            
            # ---------------------------------------------------
            # 4. 注入新的 Context (Inject)
            # ---------------------------------------------------
            # 无论之前有没有 context，这里都要注入当前 Producer Span 的 context
            # 这样下游消费者看到的父节点才是这个 Producer Span，保证链路完整：
            # Upstream -> Producer(Send) -> Consumer(Process)
            
            carrier = {}
            inject(carrier) # 将当前 Span (Producer) 注入到 carrier
            
            if 'extra' not in msg:
                msg['extra'] = {}
            
            # 覆盖/写入最新的链路信息
            msg['extra']['otel_context'] = carrier
            
            # 记录 Task ID
            span.set_attribute("messaging.message_id", task_id)

            try:
                return super().publish(msg, task_id, task_options)
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR))
                raise e

    async def aio_publish(self, msg, task_id=None, task_options=None):
        """
        asyncio 生态下的 OTel 链路追踪发布
        
        关键问题：父类 aio_publish 使用 run_in_executor 在线程池执行 publish，
        但 OTel 上下文是线程本地的，跨线程会丢失。
        
        解决方案：
        1. 在当前 asyncio 线程先捕获 OTel 上下文
        2. 注入到消息的 extra.otel_context 中
        3. 然后调用父类的 aio_publish（在 executor 线程中执行 publish）
        4. publish 方法检测到 otel_context 已存在，会使用它作为父上下文
        """
        msg = copy.deepcopy(msg)  # 字典是可变对象,不要改变影响用户自身的传参字典
        
        # 在当前 asyncio 线程捕获 OTel 上下文并注入到消息中
        # 这样当 publish 在 executor 线程执行时，能从消息中恢复正确的父上下文
        self._inject_otel_context_to_msg(msg) # 这是核心，
        
        # 调用父类的 aio_publish，它会在 executor 中调用 self.publish
        # publish 方法会检测到 msg['extra']['otel_context'] 并使用它
        return await super().aio_publish(msg, task_id, task_options)


class AutoOtelConsumerMixin(AbstractConsumer):
    """
    消费者 OTEL Mixin：从消息中提取 Context 并作为 Parent 运行
    同时支持同步 (_run) 和异步 (_async_run) 消费函数
    """
    
    def _extract_otel_context(self, kw: dict):
        """提取 OTEL 上下文"""
        return extract_otel_context_from_funboost_msg(kw['body'])
    
    def _set_span_attributes(self, span, kw: dict):
        """设置 Span 属性（公共逻辑）"""
        span.set_attribute("messaging.system", "funboost")
        span.set_attribute("messaging.destination", self.queue_name)
        span.set_attribute("messaging.message_id", kw['body']['extra']['task_id'])
        span.set_attribute("messaging.operation", "process")
        span.set_attribute("funboost.function_params", Serialization.to_json_str(kw['function_only_params'])[:200])

    def _run(self, kw: dict):
        """同步消费函数的链路追踪"""
        ctx = self._extract_otel_context(kw)
        span_name = f"{self.queue_name} process"
        
        with tracer.start_as_current_span(span_name, context=ctx, kind=SpanKind.CONSUMER) as span:
            self._set_span_attributes(span, kw)
            try:
                return super()._run(kw)
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR))
                raise 
                # raise e 这个不好，没有直接raise好

    async def _async_run(self, kw: dict):
        """异步消费函数的链路追踪
        
        """
        ctx = self._extract_otel_context(kw)
        span_name = f"{self.queue_name} process"
        
        with tracer.start_as_current_span(span_name, context=ctx, kind=SpanKind.CONSUMER) as span:
            self._set_span_attributes(span, kw)
            try:
                return await super()._async_run(kw)
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR))
                raise 




class OtelBoosterParams(BoosterParams):
    """
    预配置了 OTEL 链路追踪的 BoosterParams
    使用这个类可以省去每次手动指定 consumer_override_cls 和 publisher_override_cls
    """
    consumer_override_cls: typing.Type[AutoOtelConsumerMixin] = AutoOtelConsumerMixin
    publisher_override_cls: typing.Type[AutoOtelPublisherMixin] = AutoOtelPublisherMixin
# -*- coding: utf-8 -*-
"""
Funboost OpenTelemetry 链路追踪 Demo

演示如何使用 AutoOtelPublisherMixin 和 AutoOtelConsumerMixin 实现分布式链路追踪。

运行前请安装依赖:
    pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-exporter-jaeger

可以使用 Jaeger 或其他 OpenTelemetry 兼容的后端查看链路数据。
启动 Jaeger 容器（可选）:
    docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  -p 14250:14250 \
  -p 14268:14268 \
  -p 14269:14269 \
  -p 9411:9411 \
  jaegertracing/all-in-one:latest

然后访问 http://localhost:16686 查看链路追踪数据。
"""

import os
import time

from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# 可选：如果安装了 Jaeger exporter，可以使用以下导入
# from opentelemetry.exporter.jaeger.thrift import JaegerExporter

from funboost import boost, BrokerEnum, fct
from funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin import (
    OtelBoosterParams
)

# 加载 .env 文件（按需改成你自己的路径）
load_dotenv('/my_dotenv.env')


# =============================================================================
# 第1步: 初始化 OpenTelemetry
# =============================================================================
def init_opentelemetry():
    """
    初始化 OpenTelemetry 配置
    - 配置 TracerProvider
    - 添加 SpanProcessor（控制台输出或发送到 Jaeger）
    """
    # 创建资源标识
    resource = Resource.create({
        "service.name": "funboost-otel-demo",
        "service.version": "1.0.0",
    })

    # 创建 TracerProvider
    provider = TracerProvider(resource=resource)

    # 方式1：使用控制台输出（开发调试用）
    # console_exporter = ConsoleSpanExporter()
    # provider.add_span_processor(BatchSpanProcessor(console_exporter))

    # 方式2：使用 Jaeger exporter（生产环境推荐）
    # 需要安装: pip install opentelemetry-exporter-jaeger
    # 推荐安装 pip install opentelemetry-exporter-otlp
    # opentelemetry-python 中类名是 OTLPSpanExporter（全大写 OTLP）
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    # jaeger_exporter = JaegerExporter(
    #     agent_host_name="localhost",
    #     agent_port=6831,
    # )
    otlp_exporter = OTLPSpanExporter(
    endpoint=f"{os.getenv('TENXUNYUN__HOST')}:4317", 
    insecure=True
    )
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # 设置全局 TracerProvider
    trace.set_tracer_provider(provider)

    print("✅ OpenTelemetry 初始化完成")


# =============================================================================
# 第2步: 定义带 OTEL 追踪的任务函数
# =============================================================================

# 任务1：入口任务，会调用任务2
@boost(OtelBoosterParams(
    queue_name='otel_demo_task_entry',
    broker_kind=BrokerEnum.REDIS,  # 使用 SQLite 队列，方便本地测试
    concurrent_num=2,
))
def task_entry(order_id: int, user_name: str):
    """
    入口任务：处理订单入口
    会自动创建 Span 并传播追踪上下文到下游任务
    """
    print(fct.queue_name,fct.full_msg)

    print(f"📦 [任务入口] 开始处理订单 #{order_id}，用户: {user_name}")
    time.sleep(3)  # 模拟业务处理

    # 触发下游任务（链路追踪上下文会自动传播）
    task_process.push(order_id=order_id, step="验证库存")
    task_process.push(order_id=order_id, step="计算价格")

    print(f"✅ [任务入口] 订单 #{order_id} 已分发到处理队列")
    return {"status": "dispatched", "order_id": order_id}


# 任务2：处理任务
@boost(OtelBoosterParams(
    queue_name='otel_demo_task_process',
    broker_kind=BrokerEnum.REDIS,
    concurrent_num=3,
))
def task_process(order_id: int, step: str):
    """
    处理任务：执行具体的订单处理步骤
    链路追踪中会显示为 task_entry 的子 Span
    """

    print(fct.queue_name,fct.full_msg)

    print(f"⚙️ [处理任务] 订单 #{order_id} - 执行步骤: {step}")
    time.sleep(2)  # 模拟处理时间

    # 触发通知任务
    task_notify.push(order_id=order_id, message=f"步骤 '{step}' 已完成")

    print(f"✅ [处理任务] 订单 #{order_id} - 步骤 '{step}' 完成")
    return {"order_id": order_id, "step": step, "status": "completed"}


# 任务3：通知任务
@boost(OtelBoosterParams(
    queue_name='otel_demo_task_notify',
    broker_kind=BrokerEnum.REDIS,
    concurrent_num=2,
))
def task_notify(order_id: int, message: str):
    """
    通知任务：发送通知
    链路追踪中会显示为 task_process 的子 Span
    """

    print(fct.queue_name,fct.full_msg)

    print(f"📧 [通知任务] 订单 #{order_id} - 发送通知: {message}")
    time.sleep(1)  # 模拟发送通知
    print(f"✅ [通知任务] 订单 #{order_id} - 通知发送完成")
    return {"order_id": order_id, "notified": True}


# =============================================================================
# 第3步: 演示手动创建父级 Span（同进程内）
# =============================================================================
def demo_with_manual_parent_span():
    """
    演示从 HTTP 请求或其他入口创建根 Span，
    然后将链路追踪上下文传播到任务队列
    """
    tracer = trace.get_tracer("funboost-demo")

    # 模拟一个 HTTP 请求入口
    with tracer.start_as_current_span("HTTP POST /orders") as span:
        span.set_attribute("http.method", "POST")
        span.set_attribute("http.url", "/orders")

        print("\n🌐 [HTTP 请求] 收到创建订单请求")

        # 发布任务（OTEL Mixin 会自动捕获当前上下文并传播）
        for i in range(3):
            order_id = 1000 + i
            task_entry.push(order_id=order_id, user_name=f"用户_{i}")
            print(f"   ➡️ 已推送订单 #{order_id} 到队列")

        print("🌐 [HTTP 请求] 请求处理完成\n")


# =============================================================================
# 第4步: 演示跨机器/跨服务的上下文传递（伪代码）
# =============================================================================
"""
【场景说明】
当请求来自外部服务（如另一台机器上的 Java/Go 服务），trace context 是通过 HTTP Headers 传递的，
不能自动获取，需要手动从 headers 中 extract 出来，然后传递给 funboost。

典型的 HTTP Headers 格式（W3C Trace Context 标准）:
    traceparent: 00-<trace_id>-<span_id>-<flags>
    tracestate: <vendor-specific data>

例如:
    traceparent: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01
"""

def demo_cross_service_context_propagation():
    """
    伪代码示例：跨机器/跨服务的 trace context 传递
    
    场景：
    - 机器A (Java服务) 发送 HTTP 请求到 机器B (Python Web)
    - 机器B 的 Web 接口接收请求，从 headers 中提取 trace context
    - 然后将任务 push 到 funboost 消息队列，保持链路不断
    """
    from opentelemetry.propagate import extract
    
    # =========================================================================
    # 【伪代码】Flask / FastAPI 接口示例
    # =========================================================================
    
    # ----- Flask 示例 -----
    """
    from flask import Flask, request
    
    app = Flask(__name__)
    
    @app.route('/api/orders', methods=['POST'])
    def create_order():
        # 1. 从 HTTP headers 中提取 trace context
        #    Flask 的 request.headers 是一个类似 dict 的对象
        carrier = dict(request.headers)
        parent_ctx = extract(carrier)
        
        # 2. 方式一：使用 extract 出的 context 创建新 span，然后 push
        #    这样 push 时 OtelMixin 会自动从当前 context 获取上下文
        tracer = trace.get_tracer("order-service")
        with tracer.start_as_current_span("create_order", context=parent_ctx):
            order_data = request.json
            task_entry.push(order_id=order_data['id'], user_name=order_data['user'])
        
        # 2. 方式二：手动将 carrier 传入 extra.otel_context（更底层的方式）
        #    适用于不想创建中间 span 的场景
        task_entry.publish(
            msg={'order_id': 123, 'user_name': '张三'},
            # publish 方法会检查 extra.otel_context，优先使用它作为 parent context
        )
        # 注意：如果 headers 里有 traceparent，OtelMixin.publish 会自动处理
        # 因为 publish 内部调用了 context.get_current()，如果你先 extract 并设置了 context，就会用上
        
        return {'status': 'ok'}
    """
    
    # ----- FastAPI 示例 -----
    """
    from fastapi import FastAPI, Request
    
    app = FastAPI()
    
    @app.post('/api/orders')
    async def create_order(request: Request):
        # 1. 从 HTTP headers 中提取 trace context
        carrier = dict(request.headers)
        parent_ctx = extract(carrier)
        
        # 2. 在提取的 context 下创建 span 并 push 任务
        tracer = trace.get_tracer("order-service")
        with tracer.start_as_current_span("create_order", context=parent_ctx):
            body = await request.json()
            task_entry.push(order_id=body['id'], user_name=body['user'])
        
        return {'status': 'ok'}
    """
    
    # =========================================================================
    # 【实际可运行的模拟代码】模拟外部服务发来的 HTTP headers
    # =========================================================================
    
    # 模拟来自外部服务（如 Java 网关）的 HTTP headers
    # 这些 headers 包含了上游服务的 trace context
    incoming_headers = {
        # W3C Trace Context 格式
        'traceparent': '00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01',
        'tracestate': 'rojo=00f067aa0ba902b7',
        # 其他常见的业务 headers
        'X-Request-ID': 'req-12345',
        'Content-Type': 'application/json',
    }
    
    print("\n🌍 [跨服务] 收到来自外部服务的请求")
    print(f"   📥 traceparent: {incoming_headers.get('traceparent')}")
    
    # 从 headers 中提取 trace context
    parent_ctx = extract(incoming_headers)
    
    # 在提取的 context 下创建本地 span 并 push 任务
    tracer = trace.get_tracer("funboost-demo")
    with tracer.start_as_current_span("handle_external_request", context=parent_ctx) as span:
        span.set_attribute("http.method", "POST")
        span.set_attribute("http.url", "/api/orders")
        span.set_attribute("external.request_id", incoming_headers.get('X-Request-ID', ''))
        
        # push 任务 - OtelMixin 会自动将当前 span 的 context 注入到消息中
        task_entry.push(order_id=9999, user_name="外部服务用户")
        print("   ➡️ 已将任务推送到队列，trace context 已传递")
    
    print("🌍 [跨服务] 请求处理完成\n")


# =============================================================================
# 第5步: 演示 aio_publish 跨线程场景（自动传递 context）
# =============================================================================
"""
【场景说明】
aio_publish 使用 run_in_executor 在线程池中执行 publish，
而 Python 的 contextvars 默认不会跨线程传递，所以 OTEL context 会丢失。

AutoOtelPublisherMixin 的解决方案（自动处理，用户无需手动操作）：
1. aio_publish 在当前 asyncio 线程先捕获 OTel 上下文
2. 自动注入到消息的 extra.otel_context 中
3. 然后调用父类的 aio_publish（在 executor 线程中执行 publish）
4. publish 方法检测到 otel_context 已存在，会使用它作为 parent context

✅ 用户只需正常调用 aio_publish，无需任何额外操作！
"""

async def demo_aio_publish_auto_context():
    """
    演示 aio_publish 场景下 OTel context 的自动传递。
    
    AutoOtelPublisherMixin 已经自动处理了跨线程的上下文传递问题，
    用户只需正常调用 aio_publish，无需手动 inject context。

    这种场景非常接近：外部请求 FastAPI，FastAPI 使用 aio_publish 发布到消息队列。
    """
    from opentelemetry.propagate import extract
    from opentelemetry.trace import SpanKind

    # 模拟来自外部服务（如 Java 网关）的 HTTP headers
    # 这些 headers 包含了上游服务的 trace context
    incoming_headers = {
        # W3C Trace Context 格式
        'traceparent': '00-0af8151916cd43dd8448eb211c80319c-b7ad6b7169203331-01',
        'tracestate': 'rojo=00f067aa0ba902b7',
        # 其他常见的业务 headers
        'X-Request-ID': 'req-12345',
        'Content-Type': 'application/json',
    }
    
    print("\n🌍 [跨服务] 收到来自外部服务的请求")
    print(f"   📥 traceparent: {incoming_headers.get('traceparent')}")
    
    # 从 headers 中提取 trace context
    parent_ctx = extract(incoming_headers)
    
    tracer = trace.get_tracer("funboost-fastapi-aio-publish-demo")
    
    print("\n🔀 [aio_publish] 演示异步发布时自动传递上下文")
    
    # 创建一个父级 span（模拟 FastAPI 请求处理）
    with tracer.start_as_current_span("async_order_handler", context=parent_ctx, kind=SpanKind.SERVER) as span:
        span.set_attribute("handler.type", "async")
        span.set_attribute("external.request_id", incoming_headers.get('X-Request-ID', ''))
        
        # ✅ 直接调用 aio_publish，无需手动传递 otel_context
        # AutoOtelPublisherMixin 会自动：
        # 1. 在当前线程捕获 OTel 上下文
        # 2. 注入到消息的 extra.otel_context 中
        # 3. 传递到 executor 线程中的 publish 方法
        await task_entry.aio_publish(
            msg={
                'order_id': 8888,
                'user_name': 'aio_publish用户',
            },
        )
        print("   ➡️ aio_publish 自动传递上下文完成（无需手动操作）")

    print("🔀 [aio_publish] 异步发布演示完成\n")


# 同步包装函数，方便在 main 中调用
def demo_aio_publish_wrapper():
    """同步包装器，用于在非 async 环境中运行 demo"""
    import asyncio
    asyncio.run(demo_aio_publish_auto_context())


# =============================================================================
# 主程序入口
# =============================================================================
if __name__ == '__main__':
    # 初始化 OpenTelemetry
    init_opentelemetry()

    

    # 启动所有消费者
    task_notify.consume()
    task_process.consume()
    task_entry.consume()  

    time.sleep(5)


    print("\n" + "=" * 60)
    print("🚀 Funboost OpenTelemetry 链路追踪 Demo")
    print("=" * 60 + "\n")

    # # 方式1: 直接发布任务（会自动使用当前线程上下文）
    # print("【测试1】直接发布任务:")
    # task_entry.push(order_id=1, user_name="张三")

    # # 方式2: 从带有父级 Span 的上下文发布任务（同进程）
    # print("\n【测试2】从 HTTP 请求上下文发布任务:")
    # demo_with_manual_parent_span()

    # # 方式3: 跨机器/跨服务的上下文传递（模拟外部 headers）
    # print("\n【测试3】跨服务 trace context 传递:")
    # demo_cross_service_context_propagation()

    # 方式4: aio_publish 跨线程场景（手动传递 context）
    print("\n【测试4】aio_publish 跨线程手动传递 context:")
    demo_aio_publish_wrapper()

    print("\n" + "-" * 60)
    print("📡 开始消费任务（观察控制台输出的 Span 信息）")
    print("-" * 60 + "\n")

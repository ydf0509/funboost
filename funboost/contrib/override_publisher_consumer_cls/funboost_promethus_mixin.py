# -*- coding: utf-8 -*-
"""
Funboost Prometheus 监控指标 Mixin

提供 Prometheus 指标采集能力，自动上报任务执行状态、耗时等指标。

支持两种模式：
1. HTTP Server 模式（单进程）— Prometheus 主动拉取
2. Push Gateway 模式（多进程）— 主动推送到 Pushgateway

用法1：HTTP Server 模式（单进程）
```python
from funboost import boost
from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
    PrometheusBoosterParams,
    start_prometheus_http_server
)

# 启动 Prometheus HTTP 服务（默认端口 8000） 
start_prometheus_http_server(port=8000)

@boost(PrometheusBoosterParams(queue_name='my_task'))
def my_task(x):
    return x * 2

my_task.consume()
```

用法2：Push Gateway 模式（多进程推荐）
```python
from funboost import boost
from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
    PrometheusPushGatewayBoosterParams,
)

@boost(PrometheusPushGatewayBoosterParams(
    queue_name='my_task',
    user_options={
        'prometheus_pushgateway_url': 'localhost:9091',  # Pushgateway 地址
        'prometheus_push_interval': 10.0,                # 推送间隔（秒）
        'prometheus_job_name': 'my_app',                 # Prometheus job 名称
    }
))
def my_task(x):
    return x * 2

my_task.consume()
```

指标说明：
- funboost_task_total: 任务计数 (labels: queue, status)
- funboost_task_latency_seconds: 任务耗时直方图 (labels: queue)
- funboost_task_retries_total: 重试次数计数 (labels: queue)
- funboost_queue_msg_count: 队列剩余消息数量 (labels: queue)
- funboost_publish_total: 发布消息计数 (labels: queue)
"""

import os
import time
import socket
import threading
import typing
import atexit

from prometheus_client import (
    Counter, Histogram, Gauge,
    start_http_server, 
    push_to_gateway, delete_from_gateway,
    REGISTRY
)

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.core.func_params_model import BoosterParams
from funboost.core.function_result_status_saver import FunctionResultStatus


# ============================================================
# Prometheus 指标定义
# ============================================================

# 任务计数器 (按队列和状态分组)
TASK_TOTAL = Counter(
    'funboost_task_total',
    'Total number of tasks processed',
    ['queue', 'status']  # status: success, fail, requeue, dlx
)

# 任务耗时直方图 (按队列分组)
TASK_LATENCY = Histogram(
    'funboost_task_latency_seconds',
    'Task execution latency in seconds',
    ['queue'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, float('inf'))
)

# 重试次数计数器 (按队列分组)
TASK_RETRIES = Counter(
    'funboost_task_retries_total',
    'Total number of task retries',
    ['queue']
)

# 队列剩余消息数量 (按队列分组)
QUEUE_MSG_COUNT = Gauge(
    'funboost_queue_msg_count',
    'Number of messages remaining in the queue',
    ['queue']
)

# 发布消息计数器 (按队列分组)
PUBLISH_TOTAL = Counter(
    'funboost_publish_total',
    'Total number of messages published',
    ['queue']
)


# ============================================================
# Prometheus Publisher Mixin (发布者指标采集)
# ============================================================

class PrometheusPublisherMixin(AbstractPublisher):
    """
    Prometheus 指标采集 Publisher Mixin
    
    自动采集发布消息的数量指标。
    """
    
    def _after_publish(self, msg: dict, msg_function_kw: dict, task_id: str):
        """
        发布消息后的钩子方法，记录 Prometheus 发布指标
        """
        PUBLISH_TOTAL.labels(queue=self.queue_name).inc()


# ============================================================
# Prometheus Consumer Mixin (基础版 - HTTP Server 模式)
# ============================================================

class PrometheusConsumerMixin(AbstractConsumer):
    """
    Prometheus 指标采集 Consumer Mixin (HTTP Server 模式)
    
    自动采集以下指标：
    - 任务成功/失败计数
    - 任务执行耗时
    - 重试次数
    
    通过框架提供的 _sync_and_aio_frame_custom_record_process_info_func 钩子方法实现，
    同步和异步任务都会调用此方法，无需分别实现。
    """
    
    def _sync_and_aio_frame_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus, kw: dict):
        """
        框架回调方法，同步和异步任务执行后都会调用此方法采集 Prometheus 指标
        """
        self._record_prometheus_metrics(current_function_result_status)
    
    def _record_prometheus_metrics(self, function_result_status: FunctionResultStatus):
        """
        记录 Prometheus 指标
        
        :param function_result_status: 函数执行状态，包含 time_start 和 time_cost 等信息
        """
        queue_name = self.queue_name
        
        # 确定任务状态
        if function_result_status is None:
            status = 'unknown'
            latency = 0.0
        else:
            # 使用框架提供的 time_cost，如果没有则计算
            latency = function_result_status.time_cost if function_result_status.time_cost else (time.time() - function_result_status.time_start)
            
            if function_result_status._has_requeue:
                status = 'requeue'
            elif function_result_status._has_to_dlx_queue:
                status = 'dlx'
            elif function_result_status.success:
                status = 'success'
            else:
                status = 'fail'
        
        # 记录任务计数
        TASK_TOTAL.labels(queue=queue_name, status=status).inc()
        
        # 记录任务耗时
        TASK_LATENCY.labels(queue=queue_name).observe(latency)
        
        # 记录重试次数（如果有重试）
        if function_result_status and function_result_status.run_times > 1:
            retry_count = function_result_status.run_times - 1
            TASK_RETRIES.labels(queue=queue_name).inc(retry_count)
        
        # 记录队列剩余消息数量
        msg_num_in_broker = self.metric_calculation.msg_num_in_broker
        if msg_num_in_broker is not None and msg_num_in_broker >= 0:
            QUEUE_MSG_COUNT.labels(queue=queue_name).set(msg_num_in_broker)


# ============================================================
# Push Gateway Consumer Mixin (多进程推荐)
# ============================================================

class PrometheusPushGatewayConsumerMixin(PrometheusConsumerMixin):
    """
    Prometheus Push Gateway 模式 Consumer Mixin
    
    适用于多进程场景，自动定期将指标推送到 Pushgateway。
    
    特性：
    - 后台线程定期推送指标
    - 自动生成实例标识（hostname_pid）
    - 进程退出时自动清理指标
    """
    
    # 类级别变量，确保每个进程只启动一个推送线程
    _push_thread_started: typing.ClassVar[bool] = False
    _push_thread_lock: typing.ClassVar[threading.Lock] = threading.Lock()
    
    def custom_init(self):
        """初始化时启动 Push Gateway 后台线程"""
        super().custom_init()
        self._start_push_gateway_thread_if_needed()
    
    def _start_push_gateway_thread_if_needed(self):
        """启动 Push Gateway 推送线程（确保只启动一次）"""
        # 从 user_options 中获取 Prometheus 配置
        user_options = self.consumer_params.user_options or {}
        pushgateway_url = user_options.get('prometheus_pushgateway_url', None)
        if not pushgateway_url:
            raise ValueError('prometheus_pushgateway_url is required')
        
        with self._push_thread_lock:
            if PrometheusPushGatewayConsumerMixin._push_thread_started:
                return
            PrometheusPushGatewayConsumerMixin._push_thread_started = True
        
        # 从 user_options 中获取配置
        push_interval = user_options.get('prometheus_push_interval', 10.0)
        job_name = user_options.get('prometheus_job_name', 'funboost')
        
        # 生成实例标识
        hostname = socket.gethostname()
        pid = os.getpid()
        instance_id = f'{hostname}_{pid}'
        
        grouping_key = {'instance': instance_id}
        
        # 启动后台推送线程
        def push_loop():
            while True:
                try:
                    push_to_gateway(
                        pushgateway_url,
                        job=job_name,
                        grouping_key=grouping_key,
                        registry=REGISTRY
                    )
                except Exception as e:
                    # 推送失败时静默处理，避免影响主业务
                    pass
                time.sleep(push_interval)
        
        push_thread = threading.Thread(target=push_loop, daemon=True, name='prometheus_push_thread')
        push_thread.start()
        
        # 注册退出时清理
        def cleanup():
            try:
                delete_from_gateway(
                    pushgateway_url,
                    job=job_name,
                    grouping_key=grouping_key
                )
            except Exception:
                pass
        
        atexit.register(cleanup)
        
        self.logger.info(f'🔥 Prometheus Push Gateway started: {pushgateway_url}, interval={push_interval}s, instance={instance_id}')


# ============================================================
# 预配置的 BoosterParams
# ============================================================

class PrometheusBoosterParams(BoosterParams):
    """
    预配置了 Prometheus 指标采集的 BoosterParams (HTTP Server 模式)
    
    适用于单进程场景，需要配合 start_prometheus_http_server() 使用。
    自动采集消费者和发布者的指标。
    """
    consumer_override_cls: typing.Type[PrometheusConsumerMixin] = PrometheusConsumerMixin
    publisher_override_cls: typing.Type[PrometheusPublisherMixin] = PrometheusPublisherMixin


class PrometheusPushGatewayBoosterParams(BoosterParams):
    """
    预配置了 Prometheus Push Gateway 的 BoosterParams (多进程推荐)
    
    适用于多进程场景，自动推送指标到 Pushgateway。
    自动采集消费者和发布者的指标。
    
    Prometheus 配置通过 user_options 传递，支持以下键：
    - prometheus_pushgateway_url: Pushgateway 地址，如 'localhost:9091' (必填)
    - prometheus_push_interval: 推送间隔（秒），默认 10.0
    - prometheus_job_name: Prometheus job 名称，默认 'funboost'
    
    用法：
    ```python
    @boost(PrometheusPushGatewayBoosterParams(
        queue_name='my_task',
        user_options={
            'prometheus_pushgateway_url': 'localhost:9091',
            'prometheus_push_interval': 10.0,
            'prometheus_job_name': 'my_app',
        }
    ))
    def my_task(x):
        return x * 2
    ```
    """
    consumer_override_cls: typing.Type[PrometheusPushGatewayConsumerMixin] = PrometheusPushGatewayConsumerMixin
    publisher_override_cls: typing.Type[PrometheusPublisherMixin] = PrometheusPublisherMixin


# ============================================================
# 辅助函数
# ============================================================

def start_prometheus_http_server(port: int = 8000, addr: str = '0.0.0.0'):
    """
    启动 Prometheus HTTP 服务器 (单进程模式)
    
    启动后可以通过 http://<addr>:<port>/metrics 访问指标
    
    :param port: HTTP 端口，默认 8000
    :param addr: 绑定地址，默认 0.0.0.0
    """
    start_http_server(port, addr)
    print(f'🔥 Prometheus metrics server started at http://{addr}:{port}/metrics')


# ============================================================
# 导出
# ============================================================

__all__ = [
    # Mixin
    'PrometheusConsumerMixin',
    'PrometheusPushGatewayConsumerMixin',
    'PrometheusPublisherMixin',
    
    # Params
    'PrometheusBoosterParams',
    'PrometheusPushGatewayBoosterParams',
    
    # Helper
    'start_prometheus_http_server',
    
    # Metrics
    'TASK_TOTAL',
    'TASK_LATENCY',
    'TASK_RETRIES',
    'QUEUE_MSG_COUNT',
    'PUBLISH_TOTAL',
]

# -*- coding: utf-8 -*-
"""
有界 SimpleQueue 作为 Broker 的 Publisher 和 Consumer 实现

这是按照 funboost 文档 4.21 章节的方式，在用户代码中动态扩展 broker，
不需要修改 funboost/publishers 和 funboost/consumers 目录。

使用方法：
1. 导入此模块（会自动注册 broker）
2. 在 @boost 装饰器中使用 broker_kind='BOUNDED_SIMPLE_QUEUE'
"""

from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.factories.broker_kind__publsiher_consumer_type_map import register_custom_broker
from funboost.queues.bounded_simple_queue import BoundedSimpleQueues, BoundedSimpleQueue
from funboost.core.broker_kind__exclusive_config_default_define import register_broker_exclusive_config_default


# ============================================================================
# Broker 类型常量
# ============================================================================
BOUNDED_SIMPLE_QUEUE = 'BOUNDED_SIMPLE_QUEUE'


# ============================================================================
# Publisher 实现
# ============================================================================
class BoundedSimpleQueuePublisher(AbstractPublisher):
    """
    有界 SimpleQueue 发布者
    
    broker_exclusive_config 支持的配置：
    - maxsize: 队列最大容量，默认 10000
    """
    
    @property
    def _bounded_queue(self) -> BoundedSimpleQueue:
        maxsize = self.publisher_params.broker_exclusive_config['maxsize']
        return BoundedSimpleQueues.get_queue(self._queue_name, maxsize=maxsize)
    
    def _publish_impl(self, msg):
        """发布消息到有界队列"""
        self._bounded_queue.put(msg)
    
    def clear(self):
        """清空队列"""
        self._bounded_queue.clear()
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')
    
    def get_message_count(self):
        """获取队列消息数量"""
        return self._bounded_queue.qsize()
    
    def close(self):
        """关闭连接（内存队列无需关闭）"""
        pass


# ============================================================================
# Consumer 实现
# ============================================================================
class BoundedSimpleQueueConsumer(AbstractConsumer):
    """
    有界 SimpleQueue 消费者
    
    broker_exclusive_config 支持的配置：
    - maxsize: 队列最大容量，默认 10000
    """
    
    @property
    def _bounded_queue(self) -> BoundedSimpleQueue:
        maxsize = self.consumer_params.broker_exclusive_config['maxsize']
        return BoundedSimpleQueues.get_queue(self._queue_name, maxsize=maxsize)
    
    def _dispatch_task(self):
        """从队列获取消息并提交任务"""
        while True:
            task = self._bounded_queue.get()
            kw = {'body': task}
            self._submit_task(kw)
    
    def _confirm_consume(self, kw):
        """确认消费（内存队列无需 ack）"""
        pass
    
    def _requeue(self, kw):
        """消息重入队"""
        self._bounded_queue.put(kw['body'])


# ============================================================================
# 自动注册 Broker
# ============================================================================
def register_bounded_simple_queue_broker():
    """
    注册有界 SimpleQueue 作为 funboost 的 broker
    
    调用此函数后，可以在 @boost 中使用：
    broker_kind='BOUNDED_SIMPLE_QUEUE'
    
    broker_exclusive_config 支持的配置：
    - maxsize: 队列最大容量，默认 10000
    """
    # 1. 注册 broker 的专有配置默认值
    register_broker_exclusive_config_default(
        BOUNDED_SIMPLE_QUEUE,
        {
            "maxsize": 10000,  # 队列最大容量
        }
    )
    
    # 2. 注册 publisher 和 consumer
    register_custom_broker(
        broker_kind=BOUNDED_SIMPLE_QUEUE,
        publisher_class=BoundedSimpleQueuePublisher,
        consumer_class=BoundedSimpleQueueConsumer
    )


# 模块导入时自动注册
register_bounded_simple_queue_broker()

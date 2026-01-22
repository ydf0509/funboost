# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/1/16
"""
微批消费者 asyncio 测试

验证 MicroBatchConsumerMixin 在 ASYNC 模式下的表现
"""
import asyncio
import time
from funboost import boost, BrokerEnum, BoosterParams, ConcurrentModeEnum
from funboost.contrib.override_publisher_consumer_cls.funboost_micro_batch_mixin import (
    MicroBatchConsumerMixin,
)

# 记录批量处理的结果
batch_results = []

@boost(BoosterParams(
    queue_name='test_micro_batch_async_queue',
    broker_kind=BrokerEnum.REDIS,
    concurrent_mode=ConcurrentModeEnum.ASYNC,  # 开启异步模式
    consumer_override_cls=MicroBatchConsumerMixin,
    user_options={
        'micro_batch_size': 10,
        'micro_batch_timeout': 3.0,
    },
    qps=100,
    should_check_publish_func_params=False,
))
async def batch_async_task(items: list):
    """
    模拟异步批量处理任务
    """
    # 模拟异步 I/O 操作
    await asyncio.sleep(0.1)
    
    print(f"✅ [Async] 批量处理 {len(items)} 条消息: {items}")
    return len(items)


def test_async_batch():
    """测试异步批量功能"""
    print("=" * 60)
    print("测试: Asyncio 批量功能")
    print("发布 25 条消息，验证是否通过 _async_run_batch 执行")
    print("=" * 60)
    
    # 发布 25 条消息
    for i in range(25):
        batch_async_task.push(x=i, y=i * 2)
    
    # 启动消费
    batch_async_task.consume()


if __name__ == '__main__':
    test_async_batch()
    
  

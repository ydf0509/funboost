# -*- coding: utf-8 -*-
# @Author  : AI Assistan
"""
微批消费者测试

测试 MicroBatchConsumerMixin 的功能：
1. 基本功能测试：发布消息，验证批量处理
2. 超时触发测试：不足 batch_size 时超时触发

例如可以批量100条插入数据库，做数据库表同步性能好。
"""
from funboost import boost, BrokerEnum, BoosterParams,ctrl_c_recv
from funboost.contrib.override_publisher_consumer_cls.funboost_micro_batch_mixin import (
    MicroBatchConsumerMixin,MicroBatchBoosterParams
)


@boost(MicroBatchBoosterParams(
    queue_name='test_micro_batch_queue',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    user_options={
        'micro_batch_size': 10,        # 每批10条
        'micro_batch_timeout': 3.0,    # 3秒超时
    },
))
def batch_insert_task(items: list):
    """
    模拟批量插入任务
    
    :param items: 消息列表，每个元素是一个字典（函数参数）
    
    items是例如 [{'x': 10, 'y': 20}, {'x': 11, 'y': 22}, {'x': 12, 'y': 24}, ...]
    """
    print(f"✅ 批量处理 {len(items)} 条消息: {items}")
    return len(items)

    
if __name__ == '__main__':
    # 运行基本测试
    # 启动消费
    batch_insert_task.consume() # 消费是自动微批操作
    
    print("发布 25 条消息，batch_size=10，预期触发 2 次完整批次 + 1 次超时批次")
    print("=" * 60)
    
    # 发布 25 条消息, 之所以是25条，是为了让 21 - 25条消息触发 micro_batch_timeout 这个条件
    for i in range(25):  
        batch_insert_task.push(x=i, y=i * 2)  # 发布还是按照单条消息发布，消费是自动微批操作
        print(f"发布消息: x={i}, y={i * 2}")
    ctrl_c_recv()
    
    
    
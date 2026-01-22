# MicroBatch 微批消费测试

本目录包含 funboost **微批消费 (MicroBatch)** 功能的测试和示例代码。

## 功能简介

微批消费是 funboost 的一个高级特性，允许累积 N 条消息后批量处理，而不是逐条消费。

**核心价值**：用极小的延迟换取极高的吞吐量。

## 文件说明

| 文件 | 说明 |
|------|------|
| `test_micro_batch_consumer.py` | 同步模式（THREADING）微批消费测试 |
| `test_micro_batch_async.py` | 异步模式（ASYNC）微批消费测试 |
| `lowb_manul_batch.py` | 对比：不使用 funboost 手动实现批量聚合有多麻烦 |

## 快速开始

```python
from funboost import boost, BoosterParams, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.funboost_micro_batch_mixin import MicroBatchConsumerMixin

@boost(BoosterParams(
    queue_name='my_batch_queue',
    broker_kind=BrokerEnum.REDIS,
    consumer_override_cls=MicroBatchConsumerMixin,
    user_options={
        'micro_batch_size': 100,       # 累积 100 条后处理
        'micro_batch_timeout': 5.0,    # 或等待 5 秒后处理
    },
    should_check_publish_func_params=False,  # 必须关闭
))
def batch_insert(items: list):
    """items 是包含多条消息的列表"""
    db.bulk_insert(items)
```

## 适用场景

| 场景 | 收益 |
|------|------|
| 批量写入数据库 | 减少 DB 连接开销，吞吐量提升 10-100 倍 |
| 批量调用外部 API | 减少 HTTP 连接开销 |
| 批量发送通知 | 合并推送，减少请求次数 |

## 相关文档

- 核心实现：[funboost/contrib/override_publisher_consumer_cls/funboost_micro_batch_mixin.py](../../funboost/contrib/override_publisher_consumer_cls/funboost_micro_batch_mixin.py)
- 使用文档：[funboost/contrib/override_publisher_consumer_cls/README.md](../../funboost/contrib/override_publisher_consumer_cls/README.md)

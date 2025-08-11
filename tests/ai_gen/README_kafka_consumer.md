# KafkaManyThreadsConsumer 

## 简介

这是一个从0实现的Kafka消费类，专门解决多线程环境下的消息不丢失问题。

## 核心特性

✅ **支持超高线程数**: 线程数可以远高于partition数（例如100个线程处理2个分区）

✅ **消息不丢失**: 确保即使kill -9重启程序也不会丢失或跳过消息

✅ **有序offset提交**: 只提交连续已处理完成的消息offset，避免消息空洞

✅ **自动重试机制**: 处理失败的消息会在重启后重新消费

✅ **完善的监控**: 提供详细的统计信息和状态监控

## 问题解决

### 传统方案的问题
```
消息处理时间: msg1(100s) -> msg2(30s) -> msg3(10s)
如果按完成时间提交: msg3先完成并提交offset
突然重启 -> msg1和msg2丢失 ❌
```

### 我们的解决方案
```
有序offset管理器:
- 只提交连续已完成的消息
- msg3完成但不提交，等待msg1和msg2
- 确保重启后从正确位置继续 ✅
```

## 安装依赖

```bash
pip install kafka-python
```

## 基础使用

```python
from kafka_many_threads_consumer import KafkaManyThreadsConsumer

def my_callback(message):
    """你的消息处理逻辑"""
    print(f"处理消息: {message.value}")
    # 你的业务逻辑...

# 创建消费者
consumer = KafkaManyThreadsConsumer(
    kafka_broker_address="localhost:9092",
    topic="my-topic",
    group_id="my-group",
    num_threads=100,  # 支持很多线程
    callback_func=my_callback
)

# 启动消费者
consumer.start()

# 监控状态
stats = consumer.get_stats()
print(f"统计: {stats}")

# 停止消费者
consumer.stop()
```

## 高级配置

### 1. 处理失败重试
```python
def reliable_callback(message):
    try:
        # 你的业务逻辑
        process_business_logic(message)
    except RetryableError as e:
        # 抛出异常，消息会在重启后重新消费
        raise e
    except NonRetryableError as e:
        # 不抛出异常，消息会被跳过
        logging.error(f"无法恢复的错误: {e}")
```

### 2. 数据库事务场景
```python
def database_callback(message):
    with database.transaction():
        try:
            # 解析消息
            data = json.loads(message.value)
            
            # 数据库操作
            save_to_database(data)
            
            # 成功：不抛出异常，offset会被提交
            
        except DatabaseError:
            # 失败：抛出异常，重启后重新处理
            raise
```

### 3. 多消费者实例
```python
# 部署多个实例，自动负载均衡
for i in range(3):
    consumer = KafkaManyThreadsConsumer(
        kafka_broker_address="localhost:9092",
        topic="high-throughput-topic",
        group_id="same-group",  # 相同group_id
        num_threads=50,
        callback_func=my_callback
    )
    consumer.start()
```

## 架构设计

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Kafka消费线程   │────│  OffsetManager   │────│   Offset提交线程  │
│                 │    │    有序管理器     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│   ThreadPool    │    │   消息状态跟踪    │
│   (N个工作线程)  │    │  - 待处理队列     │
└─────────────────┘    │  - 已完成标记     │
                       │  - 连续性检查     │
                       └──────────────────┘
```

## 核心组件

### 1. OffsetManager
- **功能**: 管理每个partition的消息处理状态
- **特性**: 只提交连续已完成的消息offset
- **线程安全**: 使用RLock确保并发安全

### 2. MessageTask
- **功能**: 封装消息处理任务
- **包含**: 消息记录、状态、错误信息等
- **生命周期**: 创建 -> 处理 -> 完成 -> 清理

### 3. 消费循环
- **主线程**: 负责从Kafka poll消息
- **工作线程池**: 并行处理消息
- **提交线程**: 定期提交可安全提交的offset

## 监控和调试

### 获取统计信息
```python
stats = consumer.get_stats()
print(json.dumps(stats, indent=2, ensure_ascii=False))

# 输出示例:
{
  "consumed_count": 1000,      # 已消费消息数
  "processed_count": 995,      # 已处理成功数
  "failed_count": 5,           # 处理失败数
  "committed_count": 990,      # 已提交offset数
  "offset_manager_status": {
    "pending_count": {         # 各分区待处理数量
      "0": 3,
      "1": 2
    },
    "committable_offsets": {   # 可提交的offset
      "0": 500,
      "1": 450
    }
  }
}
```

### 日志级别配置
```python
import logging
logging.getLogger('KafkaConsumer-your-group').setLevel(logging.DEBUG)
```

## 性能优化建议

### 1. 线程数配置
```python
# CPU密集型任务
num_threads = cpu_count() * 2

# I/O密集型任务（数据库、网络）
num_threads = cpu_count() * 4 to 8

# 混合型任务
num_threads = cpu_count() * 3
```

### 2. Kafka配置优化
```python
consumer = KafkaConsumer(
    max_poll_records=500,        # 批量大小
    session_timeout_ms=30000,    # 会话超时
    heartbeat_interval_ms=3000,  # 心跳间隔
    fetch_min_bytes=1024,        # 最小拉取字节
    fetch_max_wait_ms=500        # 最大等待时间
)
```

### 3. 内存管理
- 及时清理已完成的任务
- 监控待处理队列大小
- 设置合适的poll超时时间

## 测试场景

运行测试示例：
```bash
# 基础功能测试
python test_kafka_consumer_example.py basic

# 高并发测试
python test_kafka_consumer_example.py high_concurrency

# 可靠性测试（模拟kill -9）
python test_kafka_consumer_example.py reliability

# 多消费者测试
python test_kafka_consumer_example.py multiple
```

## 故障排查

### 1. 消息处理缓慢
- 检查callback_func的执行时间
- 增加线程数量
- 优化业务逻辑

### 2. Offset提交延迟
- 检查是否有长时间未完成的消息
- 查看pending_count统计
- 确认没有死锁或无限循环

### 3. 重复消费
- 确认消息处理逻辑是幂等的
- 检查是否有未捕获的异常
- 验证offset提交是否正常

### 4. 内存泄漏
- 监控pending_messages队列大小
- 确保异常处理正确
- 定期重启长期运行的实例

## 最佳实践

1. **幂等性**: 确保消息处理逻辑是幂等的
2. **异常处理**: 区分可重试和不可重试的错误
3. **监控**: 定期检查统计信息和队列状态
4. **测试**: 充分测试异常场景和重启恢复
5. **部署**: 使用容器编排工具管理多实例

## 限制和注意事项

1. **内存使用**: 大量线程会增加内存使用
2. **Kafka版本**: 建议使用Kafka 0.10+
3. **网络**: 确保与Kafka集群的网络稳定
4. **磁盘空间**: Kafka日志保留策略要合理

## 贡献

欢迎提交Issue和Pull Request来改进这个实现！
# RabbitMQ Topic 路由模式示例

本示例演示了如何使用 funboost 框架实现 RabbitMQ 的 Topic 路由模式。

## Topic 路由模式特点

Topic 路由模式是 RabbitMQ 中最灵活的路由方式，它允许使用通配符进行消息路由：

- `*` (星号)：匹配恰好一个单词
- `#` (井号)：匹配零个或多个单词
- 路由键使用 `.` (点号) 分隔单词

## 文件说明

- `t_topic_consume.py`: 消费者示例，展示不同的路由键绑定模式
- `t_topic_pub.py`: 发布者示例，展示如何使用动态路由键发布消息

## 路由键绑定规则

### 消费者绑定规则

1. **全部日志消费者** (`q_all_logs`)
   - 绑定键: `#`
   - 说明: 接收所有消息

2. **错误日志消费者** (`q_error_logs`)
   - 绑定键: `*.error`
   - 说明: 接收所有以 `.error` 结尾的消息
   - 匹配示例: `system.error`, `app.error`, `db.error`

3. **系统日志消费者** (`q_system_logs`)
   - 绑定键: `system.*`
   - 说明: 接收所有以 `system.` 开头的消息
   - 匹配示例: `system.info`, `system.warning`, `system.error`

4. **应用关键日志消费者** (`q_app_critical_logs`)
   - 绑定键: `app.*.critical`
   - 说明: 接收格式为 `app.任意单词.critical` 的消息
   - 匹配示例: `app.auth.critical`, `app.payment.critical`

## 运行示例

### 1. 启动消费者

```bash
cd test_frame/test_broker_rabbitmq/test_rabbitmq_complex_routing/t_topic
python t_topic_consume.py
```

### 2. 发布消息

在另一个终端中运行：

```bash
cd test_frame/test_broker_rabbitmq/test_rabbitmq_complex_routing/t_topic
python t_topic_pub.py
```

## 消息路由示例

| 路由键 | 匹配的消费者 |
|--------|-------------|
| `system.info` | 全部日志消费者 + 系统日志消费者 |
| `system.error` | 全部日志消费者 + 系统日志消费者 + 错误日志消费者 |
| `app.auth.critical` | 全部日志消费者 + 应用关键日志消费者 |
| `app.payment.error` | 全部日志消费者 + 错误日志消费者 |
| `db.backup.error` | 全部日志消费者 + 错误日志消费者 |
| `info` | 仅全部日志消费者 |

## 核心配置说明

### 消费者配置

```python
@BoosterParams(
    queue_name='队列名称',
    broker_kind=BrokerEnum.RABBITMQ_COMPLEX_ROUTING,
    broker_exclusive_config={
        'exchange_name': 'topic_log_exchange',
        'exchange_type': 'topic',
        'routing_key_for_bind': '绑定键模式',  # 支持通配符
    })
def consumer_function(timestamp: str, content: str):
    # 消费者函数的参数名必须与发布的字典 keys 完全一致
    pass
```

### 发布者配置

```python
topic_publisher = BoostersManager.get_cross_project_publisher(PublisherParams(
    queue_name='发布者实例名',
    broker_kind=BrokerEnum.RABBITMQ_COMPLEX_ROUTING,
    broker_exclusive_config={
        'exchange_name': 'topic_log_exchange',
        'exchange_type': 'topic',
    }
))

# 动态指定路由键发布消息
topic_publisher.publish(
    {'timestamp': '2025-09-30 12:47:56', 'content': '消息内容'},  # 字典的 keys 必须与消费者函数参数名一致
    priority_control_config=PriorityConsumingControlConfig(
        other_extra_params={'routing_key_for_publish': '动态路由键'}
    )
)
```

## 使用场景

Topic 路由模式特别适合以下场景：

1. **日志系统**: 根据日志级别和来源进行分类处理
2. **事件系统**: 根据事件类型和业务模块进行路由
3. **监控系统**: 根据监控指标的类型和重要性进行分发
4. **微服务通信**: 根据服务名称和操作类型进行消息路由

## 注意事项

1. **参数匹配规则**: 发布者发布的字典 keys 必须与消费者函数的参数名完全一致
   - 发布: `{'timestamp': '...', 'content': '...'}`
   - 消费: `def consumer(timestamp: str, content: str):`
2. 路由键中的单词使用 `.` 分隔
3. `*` 只能匹配一个单词，不能匹配零个或多个单词
4. `#` 可以匹配零个、一个或多个单词
5. 路由键区分大小写
6. 一个消息可以被多个队列接收（如果路由键匹配多个绑定模式）

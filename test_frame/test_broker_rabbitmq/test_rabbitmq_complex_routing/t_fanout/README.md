# RabbitMQ Fanout 路由模式示例

本示例演示了如何使用 funboost 框架实现 RabbitMQ 的 Fanout 路由模式。

## Fanout 路由模式特点

Fanout 路由模式是 RabbitMQ 中最简单的路由方式，具有以下特点：

- 📢 **广播模式**：消息会被发送给所有绑定到交换机的队列
- 🚫 **忽略路由键**：无论发布时使用什么路由键，都会被忽略
- ⚡ **高效简单**：不需要复杂的路由规则匹配
- 🔄 **一对多**：一条消息可以被多个不同的服务同时处理

## 文件说明

- `t_fanout_consume.py`: 消费者示例，展示多个服务同时接收广播消息
- `t_fanout_pub.py`: 发布者示例，展示如何发布广播消息

## 业务场景示例

本示例模拟了一个用户操作事件通知系统，包含以下服务：

### 消费者服务

1. **📧 邮件服务** (`q_email_service`)
   - 处理所有需要发送邮件通知的用户事件
   - 如：注册欢迎邮件、订单确认邮件、安全提醒邮件

2. **📱 短信服务** (`q_sms_service`)
   - 处理所有需要发送短信通知的用户事件
   - 如：验证码短信、重要操作提醒短信

3. **🔔 推送服务** (`q_push_service`)
   - 处理所有需要推送通知的用户事件
   - 如：APP推送、浏览器推送通知

4. **📝 审计服务** (`q_audit_service`)
   - 记录所有用户操作日志，用于安全审计
   - 如：登录记录、敏感操作记录

5. **📊 数据分析服务** (`q_analytics_service`)
   - 收集用户行为数据，用于数据分析
   - 如：用户行为统计、业务指标计算

## 运行示例

### 1. 启动消费者

```bash
cd test_frame/test_broker_rabbitmq/test_rabbitmq_complex_routing/t_fanout
python t_fanout_consume.py
```

### 2. 发布消息

在另一个终端中运行：

```bash
cd test_frame/test_broker_rabbitmq/test_rabbitmq_complex_routing/t_fanout
python t_fanout_pub.py
```

## 消息广播示例

当发布一条用户事件消息时，**所有 5 个服务都会收到相同的消息**：

| 用户事件 | 接收的服务 |
|---------|-----------|
| 用户注册 | 📧邮件 + 📱短信 + 🔔推送 + 📝审计 + 📊分析 |
| 订单支付 | 📧邮件 + 📱短信 + 🔔推送 + 📝审计 + 📊分析 |
| 密码修改 | 📧邮件 + 📱短信 + 🔔推送 + 📝审计 + 📊分析 |
| 会员升级 | 📧邮件 + 📱短信 + 🔔推送 + 📝审计 + 📊分析 |

## 核心配置说明

### 消费者配置

```python
@BoosterParams(
    queue_name='服务队列名',
    broker_kind=BrokerEnum.RABBITMQ_COMPLEX_ROUTING,
    broker_exclusive_config={
        'exchange_name': 'fanout_broadcast_exchange',
        'exchange_type': 'fanout',
        # fanout 模式不需要指定 routing_key_for_bind
        # 系统会自动使用空字符串作为绑定键
    })
def service_consumer(user_id: str, action: str, message: str):
    # 消费者函数的参数名必须与发布的字典 keys 完全一致
    pass
```

### 发布者配置

```python
fanout_publisher = BoostersManager.get_cross_project_publisher(PublisherParams(
    queue_name='发布者实例名',
    broker_kind=BrokerEnum.RABBITMQ_COMPLEX_ROUTING,
    broker_exclusive_config={
        'exchange_name': 'fanout_broadcast_exchange',
        'exchange_type': 'fanout',
        # fanout 模式不需要设置 routing_key_for_publish
    }
))

# 发布消息
fanout_publisher.publish(
    {'user_id': 'user001', 'action': '用户注册', 'message': '欢迎新用户'},
    priority_control_config=PriorityConsumingControlConfig(
        # 即使设置了路由键，fanout 模式也会忽略它
        other_extra_params={'routing_key_for_publish': 'ignored_key'}
    )
)
```

## 使用场景

Fanout 路由模式特别适合以下场景：

1. **通知系统**: 用户操作需要触发多种通知方式（邮件、短信、推送）
2. **日志收集**: 同一条日志需要被多个日志处理服务处理
3. **数据同步**: 数据变更需要同步到多个系统
4. **事件驱动**: 一个事件需要触发多个业务流程
5. **监控告警**: 告警信息需要发送给多个监控系统
6. **缓存更新**: 数据更新需要清理多个缓存系统

## 与其他路由模式的对比

| 路由模式 | 路由规则 | 消息分发 | 适用场景 |
|---------|---------|---------|---------|
| **Fanout** | 忽略路由键，广播给所有队列 | 一对多（广播） | 通知系统、日志收集 |
| **Direct** | 精确匹配路由键 | 一对一或一对多 | 任务分发、点对点通信 |
| **Topic** | 通配符匹配路由键 | 灵活的一对多 | 复杂的消息分类 |
| **Headers** | 根据消息头属性匹配 | 基于属性的路由 | 复杂的条件路由 |

## 注意事项

1. **参数匹配规则**: 发布者发布的字典 keys 必须与消费者函数的参数名完全一致
   - 发布: `{'user_id': '...', 'action': '...', 'message': '...'}`
   - 消费: `def consumer(user_id: str, action: str, message: str):`

2. **路由键被忽略**: 无论发布时设置什么路由键，fanout 模式都会忽略

3. **性能考虑**: 由于是广播模式，消息会被复制到所有队列，需要考虑消息量和处理能力

4. **队列管理**: 所有绑定到 fanout 交换机的队列都会收到消息，注意队列的生命周期管理

5. **消息顺序**: 不同队列中的消息处理顺序可能不同，不要依赖处理顺序

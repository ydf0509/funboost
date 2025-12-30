# -*- coding: utf-8 -*-
# @Author  : ydf

from funboost import BoostersManager, PublisherParams, BrokerEnum, TaskOptions
import time

BROKER_KIND_FOR_TEST = BrokerEnum.RABBITMQ_COMPLEX_ROUTING
EXCHANGE_NAME = 'topic_log_exchange'


if __name__ == '__main__':
    # 创建一个通用的发布者，用于向 topic 交换机发布消息
    # queue_name 在这里仅用于生成发布者实例，实际路由由 routing_key 决定
    topic_publisher = BoostersManager.get_cross_project_publisher(PublisherParams(
        queue_name='topic_publisher_instance', 
        broker_kind=BROKER_KIND_FOR_TEST,
        broker_exclusive_config={
            'exchange_name': EXCHANGE_NAME,
            'exchange_type': 'topic',
            # 不设置默认的 routing_key_for_publish，每次发布时动态指定
        }
    ))

    print("开始发布各种类型的日志消息...")
    print("=" * 60)

    # 发布不同路由键的消息，演示 topic 路由的灵活性
    messages_to_publish = [
        # 系统相关日志
        ('system.info', '系统启动完成'),
        ('system.warning', '系统内存使用率较高'),
        ('system.error', '系统磁盘空间不足'),
        
        # 应用相关日志
        ('app.user.info', '用户登录成功'),
        ('app.order.warning', '订单处理延迟'),
        ('app.payment.error', '支付接口调用失败'),
        ('app.auth.critical', '检测到异常登录尝试'),
        
        # 数据库相关日志
        ('db.connection.info', '数据库连接池初始化'),
        ('db.query.warning', '慢查询检测'),
        ('db.backup.error', '数据库备份失败'),
        
        # 网络相关日志
        ('network.api.info', 'API调用成功'),
        ('network.cdn.error', 'CDN节点异常'),
        
        # 其他格式的日志
        ('critical.system.failure', '系统严重故障'),
        ('info', '简单信息日志'),
    ]

    for i, (routing_key, message_content) in enumerate(messages_to_publish, 1):
        print(f"[{i:2d}] 发布消息 - 路由键: '{routing_key}' - 内容: {message_content}")
        
        # 使用动态路由键发布消息
        topic_publisher.publish(
            {'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'), 'content': message_content},
            task_options=TaskOptions(
                other_extra_params={'routing_key_for_publish': routing_key}
            )
        )
        
        # 稍微延迟，便于观察消费者处理过程
        time.sleep(0.2)

    print("=" * 60)
    print("消息发布完成！")
    print("\n路由匹配说明:")
    print("  - 'system.info' 会被: 全部日志消费者 + 系统日志消费者 接收")
    print("  - 'system.error' 会被: 全部日志消费者 + 系统日志消费者 + 错误日志消费者 接收")
    print("  - 'app.auth.critical' 会被: 全部日志消费者 + 应用关键日志消费者 接收")
    print("  - 'app.payment.error' 会被: 全部日志消费者 + 错误日志消费者 接收")
    print("  - 'db.backup.error' 会被: 全部日志消费者 + 错误日志消费者 接收")
    print("  - 'info' 会被: 全部日志消费者 接收")
    print("\nTopic 路由规则:")
    print("  - '#' : 匹配零个或多个单词")
    print("  - '*' : 匹配恰好一个单词")
    print("  - 单词之间用 '.' 分隔")

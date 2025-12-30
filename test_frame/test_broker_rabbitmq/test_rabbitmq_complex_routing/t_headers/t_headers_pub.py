# -*- coding: utf-8 -*-
# @Author  : ydf

from funboost import BoostersManager, PublisherParams, BrokerEnum, TaskOptions
import time
from typing import Dict, Any, List

BROKER_KIND_FOR_TEST = BrokerEnum.RABBITMQ_COMPLEX_ROUTING
EXCHANGE_NAME = 'headers_notification_exchange'


if __name__ == '__main__':
    # 创建一个 headers 发布者，用于根据消息头属性路由消息
    headers_publisher = BoostersManager.get_cross_project_publisher(PublisherParams(
        queue_name='headers_publisher_instance', 
        broker_kind=BROKER_KIND_FOR_TEST,
        broker_exclusive_config={
            'exchange_name': EXCHANGE_NAME,
            'exchange_type': 'headers',
            # headers 模式不使用路由键，完全基于消息头属性
        }
    ))

    print("开始发布各种类型的通知消息...")
    print("=" * 70)

    # 定义不同类型的通知消息及其头属性
    notifications: List[Dict[str, Any]] = [
        {
            'message': {
                'user_id': 'admin_001',
                'title': '系统严重故障告警',
                'content': '数据库连接池耗尽，需要立即处理',
                'timestamp': '2025-09-30 13:10:00'
            },
            'headers': {
                'priority': 'high',
                'urgent': 'true',
                'category': 'system',
                'role': 'admin',
                'has_user_id': 'true'
            },
            'description': '紧急系统管理员通知'
        },
        {
            'message': {
                'user_id': 'user_123',
                'title': '订单支付成功',
                'content': '您的订单 #12345 已支付成功，金额 ¥299.00',
                'timestamp': '2025-09-30 13:11:00'
            },
            'headers': {
                'priority': 'high',
                'category': 'order',
                'platform': 'mobile',
                'has_user_id': 'true'
            },
            'description': '高优先级移动端通知'
        },
        {
            'message': {
                'user_id': 'user_456',
                'title': '新功能上线通知',
                'content': '我们推出了全新的积分兑换功能，快来体验吧！',
                'timestamp': '2025-09-30 13:12:00'
            },
            'headers': {
                'priority': 'low',
                'category': 'marketing',
                'platform': 'web',
                'has_user_id': 'true'
            },
            'description': '营销推广通知'
        },
        {
            'message': {
                'user_id': 'user_789',
                'title': '账户安全提醒',
                'content': '检测到您的账户在新设备上登录，请确认是否为本人操作',
                'timestamp': '2025-09-30 13:13:00'
            },
            'headers': {
                'priority': 'high',
                'urgent': 'true',
                'category': 'security',
                'device_type': 'phone',
                'has_user_id': 'true'
            },
            'description': '紧急安全通知'
        },
        {
            'message': {
                'user_id': 'admin_002',
                'title': '系统维护通知',
                'content': '系统将于今晚 23:00-01:00 进行维护升级',
                'timestamp': '2025-09-30 13:14:00'
            },
            'headers': {
                'priority': 'medium',
                'category': 'system',
                'role': 'admin',
                'platform': 'web',
                'has_user_id': 'true'
            },
            'description': '系统管理通知'
        },
        {
            'message': {
                'user_id': 'user_101',
                'title': '优惠券到期提醒',
                'content': '您有3张优惠券将于明天到期，请及时使用',
                'timestamp': '2025-09-30 13:15:00'
            },
            'headers': {
                'priority': 'low',
                'category': 'marketing',
                'platform': 'mobile',
                'device_type': 'phone',
                'has_user_id': 'true'
            },
            'description': '营销移动端通知'
        },
        {
            'message': {
                'user_id': 'user_202',
                'title': '会员等级升级',
                'content': '恭喜您升级为黄金会员，享受更多专属权益',
                'timestamp': '2025-09-30 13:16:00'
            },
            'headers': {
                'priority': 'medium',
                'category': 'membership',
                'platform': 'web',
                'has_user_id': 'true'
            },
            'description': '会员相关通知'
        },
        {
            'message': {
                'user_id': 'admin_003',
                'title': '用户举报处理',
                'content': '用户 user_999 举报内容需要审核处理',
                'timestamp': '2025-09-30 13:17:00'
            },
            'headers': {
                'priority': 'high',
                'category': 'system',
                'role': 'admin',
                'urgent': 'false',
                'has_user_id': 'true'
            },
            'description': '系统管理高优先级通知'
        }
    ]

    for i, notification in enumerate(notifications, 1):
        print(f"[{i}] 发布通知: {notification['description']}")
        print(f"    用户: {notification['message']['user_id']}")  # type: ignore
        print(f"    标题: {notification['message']['title']}")  # type: ignore
        print(f"    消息头: {notification['headers']}")
        
        # 使用 headers 进行消息路由
        headers_publisher.publish(
            notification['message'],  # type: ignore
            task_options=TaskOptions(
                other_extra_params={
                    'headers_for_publish': notification['headers']  # type: ignore
                }
            )
        )
        
        print("    ✅ 消息已根据头属性路由")
        print()
        
        # 稍微延迟，便于观察消费者处理过程
        time.sleep(1.5)

    print("=" * 70)
    print("所有通知消息发布完成！")
    print("\nHeaders 路由匹配说明:")
    print("  📨 消息1 (系统严重故障): priority=high + urgent=true + category=system + role=admin")
    print("     → 匹配: 🚨紧急通知 + ⚡高优先级 + 🔧系统管理 + 📋审计记录")
    print()
    print("  📨 消息2 (订单支付成功): priority=high + platform=mobile")  
    print("     → 匹配: ⚡高优先级 + 📱移动端 + 📋审计记录")
    print()
    print("  📨 消息3 (新功能上线): priority=low + category=marketing")
    print("     → 匹配: 📢营销通知 + 📋审计记录")
    print()
    print("  📨 消息4 (账户安全): priority=high + urgent=true + device_type=phone")
    print("     → 匹配: 🚨紧急通知 + ⚡高优先级 + 📱移动端 + 📋审计记录")
    print()
    print("Headers 路由规则:")
    print("  - 🏷️  基于消息头属性，不使用路由键")
    print("  - 🎯 'all' 匹配：必须满足所有指定的头属性")
    print("  - 🎯 'any' 匹配：满足任意一个指定的头属性即可")
    print("  - 🔧 支持复杂的业务逻辑路由条件")

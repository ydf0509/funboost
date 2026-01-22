# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/1/16
"""
PostgreSQL 原生消息队列 Broker 测试

PostgreSQL 相比 MySQL 的独特优势：
1. FOR UPDATE SKIP LOCKED - 高并发无锁竞争，多消费者不阻塞
2. LISTEN/NOTIFY - 原生发布订阅机制，实时推送无需轮询
3. RETURNING - 插入/更新后直接返回数据，减少查询
4. 更强的事务隔离性和并发控制

使用前请确保：
1. 安装 psycopg2: pip install psycopg2-binary
2. 配置 funboost_config.py 中的 POSTGRES_DSN
"""
import time

from funboost import boost, BrokerEnum, BoosterParams

print('可跳转')

@boost(BoosterParams(
    queue_name='test_postgres_broker',
    broker_kind=BrokerEnum.POSTGRES,
    qps=50,  # 每秒50次
    broker_exclusive_config={
        'use_listen_notify': True,  # 使用 LISTEN/NOTIFY 实时推送
        'poll_interval': 30,  # 轮询超时时间
        'timeout_minutes': 10,  # 超时任务自动重回队列
    }
))
def my_postgres_task(x, y):
    """PostgreSQL 消息队列测试任务"""
    time.sleep(2)
    result = x + y
    print(f"PostgreSQL Task: {x} + {y} = {result}")
    return result


@boost(BoosterParams(
    queue_name='test_postgres_priority',
    broker_kind=BrokerEnum.POSTGRES,
    qps=20,
    # 测试优先级功能
))
def priority_task(value, priority_level):
    """优先级任务测试"""
    print(f"Priority Task: value={value}, priority={priority_level}")
    return {'value': value, 'priority': priority_level}


def test_basic_publish_consume():
    """测试基本发布和消费"""
    print("=" * 50)
    print("测试 PostgreSQL Broker 基本功能")
    print("=" * 50)

    # 发布消息
    for i in range(10):
        my_postgres_task.push(i, i * 2)
        print(f"Published: x={i}, y={i * 2}")

    # 启动消费
    my_postgres_task.consume()


def test_priority():
    """测试优先级功能"""
    print("=" * 50)
    print("测试 PostgreSQL Broker 优先级功能")
    print("=" * 50)

    # 发布不同优先级的消息
    for i in range(10):
        # 使用 task_options 设置优先级
        from funboost import TaskOptions
        priority = i % 3  # 0, 1, 2 三种优先级
        priority_task.publish(
            {'value': i, 'priority_level': priority},
            task_options=TaskOptions(other_extra_params={'priority': priority})
        )
        print(f"Published priority task: value={i}, priority={priority}")

    # 启动消费（高优先级的会先被消费）
    priority_task.consume()


def test_concurrent_consumers():
    """测试多消费者并发（FOR UPDATE SKIP LOCKED 特性）"""
    print("=" * 50)
    print("测试 PostgreSQL Broker 多消费者并发")
    print("=" * 50)
    print("使用 FOR UPDATE SKIP LOCKED，多个消费者可以无锁并发获取任务")

    # 发布大量消息
    for i in range(100):
        my_postgres_task.push(i, i * 2)

    # 多进程消费
    my_postgres_task.multi_process_consume(4)


if __name__ == '__main__':
    # 直接运行基本测试 demo
    # test_basic_publish_consume()
    
    # 如需测试其他功能，取消注释相应行：
    # test_priority()           # 测试优先级功能
    test_concurrent_consumers()  # 测试多消费者并发
    
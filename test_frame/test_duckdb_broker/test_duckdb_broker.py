# -*- coding: utf-8 -*-
"""
测试 DuckDB 作为消息队列中间件

DuckDB 是一个嵌入式 OLAP 数据库，特点：
1. 无需部署外部服务
2. 支持文件持久化和内存模式
3. 高性能 SQL 查询
4. 单机场景非常适合
"""
import time
import os
from pathlib import Path

# 导入 DuckDB broker（这会自动注册 BROKER_KIND_DUCKDB）
from duckdb_broker import BROKER_KIND_DUCKDB
from funboost import boost, BoosterParams


# 使用文件存储模式
@boost(BoosterParams(
    queue_name='test_duckdb_file_queue',
    broker_kind=BROKER_KIND_DUCKDB,
    qps=10,
    concurrent_num=5,
    broker_exclusive_config={
        'db_path': Path(__file__).parent / 'test_duckdb_queue.db',  # 文件存储，消息持久化
        'poll_interval': 0.5,
    }
))
def add_numbers(x, y):
    """测试函数：加法运算"""
    result = x + y
    print(f"[文件模式] {x} + {y} = {result}")
    time.sleep(0.2)
    return result


# 使用内存模式（更快，但重启后消息丢失）
@boost(BoosterParams(
    queue_name='test_duckdb_memory_queue',
    broker_kind=BROKER_KIND_DUCKDB,
    qps=20,
    concurrent_num=10,
    broker_exclusive_config={
        'db_path': ':memory:',  # 内存模式
        'poll_interval': 0.1,
    }
))
def multiply_numbers(a, b):
    """测试函数：乘法运算"""
    result = a * b
    print(f"[内存模式] {a} * {b} = {result}")
    time.sleep(0.1)
    return result


def test_publish():
    """测试发布消息"""
    print("=" * 50)
    print("测试发布消息到 DuckDB 队列")
    print("=" * 50)
    
    # 清空队列
    add_numbers.clear()
    multiply_numbers.clear()
    
    # 发布消息到文件模式队列
    for i in range(10):
        add_numbers.push(i, y=i * 2)
    
    # 发布消息到内存模式队列
    for i in range(10):
        multiply_numbers.push(i, b=i + 1)
    
    print(f"文件模式队列消息数量: {add_numbers.publisher.get_message_count()}")
    print(f"内存模式队列消息数量: {multiply_numbers.publisher.get_message_count()}")
    
    print("\n发布完成！")


def test_consume_file_mode():
    """测试文件模式消费"""
    print("=" * 50)
    print("测试文件模式消费")
    print("=" * 50)
    
    # 发布一些消息
    add_numbers.clear()
    for i in range(20):
        add_numbers.push(i, y=i * 3)
    
    print(f"发布了 20 条消息，队列数量: {add_numbers.publisher.get_message_count()}")
    
    # 启动消费
    add_numbers.consume()


def test_consume_memory_mode():
    """测试内存模式消费"""
    print("=" * 50)
    print("测试内存模式消费")
    print("=" * 50)
    
    # 发布一些消息
    multiply_numbers.clear()
    for i in range(30):
        multiply_numbers.push(i, b=i + 5)
    
    print(f"发布了 30 条消息，队列数量: {multiply_numbers.publisher.get_message_count()}")
    
    # 启动消费
    multiply_numbers.consume()


if __name__ == '__main__':
    import sys
    
    print("""
    DuckDB Broker 测试程序
    =====================
    
    用法:
        python test_duckdb_broker.py publish     # 测试发布消息
        python test_duckdb_broker.py file        # 测试文件模式消费
        python test_duckdb_broker.py memory      # 测试内存模式消费
        python test_duckdb_broker.py             # 发布并消费（文件模式）
    """)
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'publish':
            test_publish()
        elif cmd == 'file':
            test_consume_file_mode()
        elif cmd == 'memory':
            test_consume_memory_mode()
        else:
            print(f"未知命令: {cmd}")
    else:
        # 默认：发布并消费
        test_publish()
        print("\n开始消费...")
        test_consume_file_mode()

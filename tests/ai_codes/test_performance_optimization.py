# -*- coding: utf-8 -*-
"""
性能优化测试脚本

测试优化后的 funboost 内存队列发布和消费性能
"""
import time
import threading
from queue import Queue

# 测试优化后的 get_func_only_params 函数性能
def test_delete_keys_performance():
    """测试 get_func_only_params 优化效果"""
    from funboost.core.helper_funs import get_func_only_params
    
    # 模拟消息字典
    test_msg = {
        'a': 1,
        'b': 2,
        'c': {'nested': 'value'},
        'extra': {
            'task_id': 'test_task_123',
            'publish_time': 1234567890.1234,
            'publish_time_format': '2025-01-19 12:00:00'
        }
    }
    
    # 性能测试
    iterations = 100000
    start = time.perf_counter()
    for _ in range(iterations):
        result = get_func_only_params(test_msg)
    end = time.perf_counter()
    
    elapsed = end - start
    ops_per_sec = iterations / elapsed
    print(f"get_func_only_params 性能测试:")
    print(f"  - {iterations} 次操作耗时: {elapsed:.4f} 秒")
    print(f"  - 每秒操作数: {ops_per_sec:,.0f} ops/sec")
    print(f"  - 结果正确性: {'a' in result and 'extra' not in result}")
    print()


def test_function_result_status_performance():
    """测试 FunctionResultStatus 初始化优化效果"""
    from funboost.core.function_result_status_saver import FunctionResultStatus
    
    test_msg = {
        'a': 1,
        'b': 2,
        'extra': {
            'task_id': 'test_task_123',
            'publish_time': 1234567890.1234,
            'publish_time_format': '2025-01-19 12:00:00'
        }
    }
    
    iterations = 50000
    start = time.perf_counter()
    for _ in range(iterations):
        status = FunctionResultStatus('test_queue', 'test_func', test_msg)
    end = time.perf_counter()
    
    elapsed = end - start
    ops_per_sec = iterations / elapsed
    print(f"FunctionResultStatus 初始化性能测试:")
    print(f"  - {iterations} 次操作耗时: {elapsed:.4f} 秒")
    print(f"  - 每秒操作数: {ops_per_sec:,.0f} ops/sec")
    print()
    
    # 测试延迟属性
    status = FunctionResultStatus('test_queue', 'test_func', test_msg)
    start = time.perf_counter()
    for _ in range(iterations):
        _ = status.params_str  # 第一次访问后会缓存
    end = time.perf_counter()
    print(f"  - params_str 属性访问 (已缓存): {(end - start) * 1000:.4f} ms / {iterations} 次")
    print()


def test_async_result_performance():
    """测试 AsyncResult 创建性能（AsyncResult 本身就是懒加载的）"""
    from funboost.core.msg_result_getter import AsyncResult
    
    iterations = 100000
    
    # 测试 AsyncResult 创建性能
    start = time.perf_counter()
    for i in range(iterations):
        result = AsyncResult(f'task_{i}', timeout=1800)
    end = time.perf_counter()
    elapsed = end - start
    
    print(f"AsyncResult 创建性能测试:")
    print(f"  - {iterations} 次创建耗时: {elapsed:.4f} 秒")
    print(f"  - 每秒创建数: {iterations / elapsed:,.0f} ops/sec")
    print()


def test_serialization_performance():
    """测试序列化性能"""
    from funboost.core.serialization import Serialization
    
    test_data = {
        'a': 1,
        'b': 'hello',
        'c': [1, 2, 3],
        'd': {'nested': 'value'},
        'extra': {
            'task_id': 'test_123',
            'publish_time': 1234567890.1234,
        }
    }
    
    iterations = 100000
    
    # JSON 序列化
    start = time.perf_counter()
    for _ in range(iterations):
        json_str = Serialization.to_json_str(test_data)
    end = time.perf_counter()
    serialize_time = end - start
    
    # JSON 反序列化
    start = time.perf_counter()
    for _ in range(iterations):
        data = Serialization.to_dict(json_str)
    end = time.perf_counter()
    deserialize_time = end - start
    
    print(f"Serialization 性能测试:")
    print(f"  - to_json_str: {iterations / serialize_time:,.0f} ops/sec")
    print(f"  - to_dict: {iterations / deserialize_time:,.0f} ops/sec")
    print()


def test_memory_queue_end_to_end():
    """测试内存队列端到端性能"""
    from funboost import boost, BoosterParams, BrokerEnum
    import logging
    
    counter = {'count': 0}
    completed = threading.Event()
    target_count = 10000
    
    @boost(BoosterParams(
        queue_name='perf_test_queue',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=50,
        log_level=logging.WARNING,  # 减少日志输出
    ))
    def test_func(x):
        counter['count'] += 1
        if counter['count'] >= target_count:
            completed.set()
        return x * 2
    
    # 先发布消息
    print(f"内存队列端到端性能测试 ({target_count} 条消息):")
    
    start = time.perf_counter()
    for i in range(target_count):
        test_func.push(i)
    publish_time = time.perf_counter() - start
    print(f"  - 发布 {target_count} 条消息耗时: {publish_time:.4f} 秒")
    print(f"  - 发布速率: {target_count / publish_time:,.0f} msgs/sec")
    
    # 等待消费完成
    completed.wait(timeout=60)
    total_time = time.perf_counter() - start
    
    print(f"  - 总处理时间: {total_time:.4f} 秒")
    print(f"  - 端到端吞吐量: {target_count / total_time:,.0f} msgs/sec")
    print()


if __name__ == '__main__':
    print("=" * 60)
    print("Funboost 性能优化测试")
    print("=" * 60)
    print()
    
    test_delete_keys_performance()
    test_function_result_status_performance()
    test_async_result_performance()
    test_serialization_performance()
    
    # 注意：端到端测试需要完整的 funboost 环境
    # test_memory_queue_end_to_end()
    
    print("=" * 60)
    print("测试完成!")
    print("=" * 60)

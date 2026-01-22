"""
精确定位消费性能瓶颈 - 同步模式直接 profiling
"""
import time
import cProfile
import pstats
from io import StringIO

# 直接测试消费者内部方法
from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum
from funboost.core.serialization import Serialization
from funboost.core.helper_funs import get_func_only_params, MsgGenerater
from funboost.core.function_result_status_saver import FunctionResultStatus


def test_consume_overhead():
    """测试消费过程中各环节的开销"""
    n = 100000
    
    # 模拟消息
    msg = {'x': 1, 'extra': {'task_id': 'test_123', 'publish_time': time.time(), 'publish_time_format': '2026-01-21 18:00:00'}}
    msg_str = Serialization.to_json_str(msg)
    
    print(f"=== 测试各环节开销 ({n} 次) ===\n")
    
    # 1. Serialization.to_dict
    t = time.time()
    for _ in range(n):
        Serialization.to_dict(msg_str)
    print(f"Serialization.to_dict(str): {time.time()-t:.3f} 秒")
    
    # 2. Serialization.to_dict (已经是 dict)
    t = time.time()
    for _ in range(n):
        Serialization.to_dict(msg)
    print(f"Serialization.to_dict(dict): {time.time()-t:.3f} 秒")
    
    # 3. get_func_only_params
    t = time.time()
    for _ in range(n):
        get_func_only_params(msg)
    print(f"get_func_only_params: {time.time()-t:.3f} 秒")
    
    # 4. FunctionResultStatus 创建
    t = time.time()
    for _ in range(n):
        FunctionResultStatus('test_queue', 'test_func', msg)
    print(f"FunctionResultStatus 创建: {time.time()-t:.3f} 秒")
    
    # 5. dict.get 操作
    t = time.time()
    for _ in range(n):
        msg.get('extra', {}).get('task_id')
        msg.get('extra', {}).get('publish_time')
    print(f"dict.get 操作: {time.time()-t:.3f} 秒")
    
    # 6. 简单函数调用
    def simple_func(x):
        pass
    t = time.time()
    for _ in range(n):
        simple_func(1)
    print(f"简单函数调用: {time.time()-t:.3f} 秒")
    
    # 7. queue.Queue.get + put
    from queue import Queue
    q = Queue()
    for _ in range(n):
        q.put(msg)
    t = time.time()
    for _ in range(n):
        q.get()
    print(f"queue.Queue.get: {time.time()-t:.3f} 秒")


if __name__ == '__main__':
    test_consume_overhead()

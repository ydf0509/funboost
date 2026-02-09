# -*- coding: utf-8 -*-
"""
测试 MEMORY_QUEUE 的有界队列大小设置功能

通过 broker_exclusive_config={'maxsize': N} 设置队列最大容量
"""
import threading
import time
from funboost import boost, BrokerEnum, BoosterParams, run_forever

# 测试1: 使用有界队列，maxsize=3
@boost(BoosterParams(
    queue_name='test_memory_queue_maxsize',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=1,  # 使用单线程来方便观察阻塞效果
    log_level=20,
    broker_exclusive_config={'maxsize': 3},  # 设置有界队列，最多3条消息
))
def process_task(num):
    print(f"处理任务: {num}, 当前时间: {time.strftime('%H:%M:%S')}")
    time.sleep(1)  # 模拟耗时操作
    return num * 2


def test_bounded_queue():
    """测试有界队列阻塞效果"""
    print("=" * 50)
    print("测试有界队列 (maxsize=3)")
    print("=" * 50)
    
    # 获取队列信息
    from funboost.queues.memory_queues_map import PythonQueues
    
    # 先发布一些消息（会创建队列）
    for i in range(3):
        process_task.pub({'num': i})
        print(f"发布消息 {i}, 队列大小: {process_task.publisher.get_message_count()}")
    
    # 此时队列应该已满
    queue_obj = PythonQueues.get_queue('test_memory_queue_maxsize')
    print(f"队列 maxsize: {queue_obj.maxsize}")
    print(f"队列当前大小: {queue_obj.qsize()}")
    print(f"队列是否已满: {queue_obj.full()}")
    
    # 尝试在另一个线程中发布第4条消息，应该会阻塞
    def publish_one_more():
        print(f"尝试发布第4条消息... (应该会阻塞直到有空位)")
        start_time = time.time()
        process_task.pub({'num': 100})
        elapsed = time.time() - start_time
        print(f"第4条消息发布成功，等待了 {elapsed:.2f} 秒")
    
    # 启动线程发布第4条消息
    t = threading.Thread(target=publish_one_more)
    t.start()
    
    # 启动消费者消费队列中的消息
    print("\n启动消费者...")
    process_task.consume()
    
    # 等待发布线程完成
    t.join(timeout=10)
    
    print("\n测试完成！")


# 测试2: 使用默认无界队列（maxsize=0）
@boost(BoosterParams(
    queue_name='test_memory_queue_unbounded',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
    log_level=20,
    # 不指定 maxsize，使用默认值 0（无界队列）
))
def process_unbounded_task(num):
    print(f"无界队列任务: {num}")
    return num


def test_unbounded_queue():
    """测试默认无界队列"""
    print("=" * 50)
    print("测试默认无界队列 (maxsize=0)")
    print("=" * 50)
    
    # 快速发布大量消息，不会阻塞
    for i in range(100):
        process_unbounded_task.pub({'num': i})
    
    print(f"成功发布 100 条消息，队列大小: {process_unbounded_task.publisher.get_message_count()}")
    
    from funboost.queues.memory_queues_map import PythonQueues
    queue_obj = PythonQueues.get_queue('test_memory_queue_unbounded')
    print(f"队列 maxsize: {queue_obj.maxsize}")
    print(f"队列是否已满: {queue_obj.full()}")  # 无界队列永远不会满


if __name__ == '__main__':
    # 先测试无界队列
    test_unbounded_queue()
    
    print("\n" + "=" * 70 + "\n")
    
    # 再测试有界队列
    test_bounded_queue()

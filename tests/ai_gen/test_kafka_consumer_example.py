"""
KafkaManyThreadsConsumer 使用示例和测试
演示如何使用有序offset提交的多线程Kafka消费者
"""

import time
import random
import threading
import json
from kafka_many_threads_consumer import KafkaManyThreadsConsumer


def simple_callback(message):
    """简单的消息处理回调"""
    print(f"处理消息: partition={message.partition}, offset={message.offset}, "
          f"value={message.value[:100] if message.value else None}...")


def complex_callback(message):
    """复杂的消息处理回调 - 模拟实际业务场景"""
    import random
    
    # 模拟不同的处理时间（0.1秒到5秒）
    processing_time = random.uniform(0.1, 5.0)
    
    print(f"开始处理消息: partition={message.partition}, offset={message.offset}, "
          f"预计耗时={processing_time:.2f}s")
    
    # 模拟处理过程
    time.sleep(processing_time)
    
    # 模拟偶尔的处理失败
    if random.random() < 0.03:  # 3%失败率
        raise Exception(f"模拟处理失败: partition={message.partition}, offset={message.offset}")
    
    print(f"完成处理消息: partition={message.partition}, offset={message.offset}, "
          f"实际耗时={processing_time:.2f}s")


def database_callback(message):
    """模拟数据库写入场景"""
    try:
        # 解析消息内容
        if message.value:
            data = json.loads(message.value)
        else:
            data = {"empty": True}
        
        # 模拟数据库操作
        time.sleep(random.uniform(0.2, 1.0))
        
        # 模拟偶尔的数据库连接失败
        if random.random() < 0.02:  # 2%失败率
            raise Exception("数据库连接失败")
        
        print(f"数据已保存到数据库: partition={message.partition}, offset={message.offset}")
        
    except json.JSONDecodeError:
        print(f"消息格式错误: partition={message.partition}, offset={message.offset}")
        # 对于格式错误的消息，我们选择跳过（不抛出异常）
    except Exception as e:
        print(f"数据库操作失败: {e}")
        raise  # 重新抛出异常，这样消息会标记为失败


def run_basic_example():
    """基础使用示例"""
    print("=== 基础使用示例 ===")
    
    consumer = KafkaManyThreadsConsumer(
        kafka_broker_address="localhost:9092",
        topic="test-topic",
        group_id="basic-group",
        num_threads=10,
        callback_func=simple_callback
    )
    
    try:
        consumer.start()
        
        # 运行30秒
        for i in range(6):
            time.sleep(5)
            stats = consumer.get_stats()
            print(f"统计信息 [{i+1}/6]: 消费={stats['consumed_count']}, "
                  f"处理成功={stats['processed_count']}, 失败={stats['failed_count']}, "
                  f"已提交={stats['committed_count']}")
            
    except KeyboardInterrupt:
        print("接收到中断信号")
    finally:
        consumer.stop()


def run_high_concurrency_example():
    """高并发场景示例"""
    print("=== 高并发场景示例 ===")
    
    consumer = KafkaManyThreadsConsumer(
        kafka_broker_address="localhost:9092",
        topic="high-throughput-topic",
        group_id="high-concurrency-group",
        num_threads=100,  # 100个线程
        callback_func=complex_callback
    )
    
    try:
        consumer.start()
        
        # 运行60秒，观察高并发下的表现
        for i in range(12):
            time.sleep(5)
            stats = consumer.get_stats()
            offset_status = stats['offset_manager_status']
            
            print(f"高并发统计 [{i+1}/12]:")
            print(f"  消费: {stats['consumed_count']}")
            print(f"  处理成功: {stats['processed_count']}")
            print(f"  处理失败: {stats['failed_count']}")
            print(f"  已提交: {stats['committed_count']}")
            print(f"  待处理队列: {offset_status['pending_count']}")
            print(f"  可提交offset: {offset_status['committable_offsets']}")
            print("---")
            
    except KeyboardInterrupt:
        print("接收到中断信号")
    finally:
        consumer.stop()


def run_reliability_test():
    """可靠性测试 - 模拟kill -9场景"""
    print("=== 可靠性测试 ===")
    print("这个测试会在30秒后自动停止，模拟突然中断的场景")
    
    consumer = KafkaManyThreadsConsumer(
        kafka_broker_address="localhost:9092",
        topic="reliability-topic",
        group_id="reliability-group",
        num_threads=50,
        callback_func=database_callback
    )
    
    def auto_stop():
        """30秒后自动停止"""
        time.sleep(30)
        print("30秒到，模拟突然停止...")
        consumer.stop()
    
    try:
        consumer.start()
        
        # 启动自动停止线程
        stop_thread = threading.Thread(target=auto_stop, daemon=True)
        stop_thread.start()
        
        # 监控状态
        start_time = time.time()
        while consumer.running:
            time.sleep(2)
            elapsed = time.time() - start_time
            stats = consumer.get_stats()
            
            print(f"运行时间: {elapsed:.1f}s, 消费: {stats['consumed_count']}, "
                  f"处理: {stats['processed_count']}, 失败: {stats['failed_count']}")
            
            if elapsed > 35:  # 安全退出
                break
                
        print("可靠性测试完成")
        
    except KeyboardInterrupt:
        print("接收到中断信号")
    finally:
        if consumer.running:
            consumer.stop()


def run_multiple_consumers():
    """多消费者实例测试"""
    print("=== 多消费者实例测试 ===")
    print("启动3个消费者实例，测试负载均衡")
    
    consumers = []
    
    for i in range(3):
        consumer = KafkaManyThreadsConsumer(
            kafka_broker_address="localhost:9092",
            topic="multi-consumer-topic",
            group_id="multi-consumer-group",  # 同一个group
            num_threads=20,
            callback_func=lambda msg, idx=i: print(f"消费者{idx}: partition={msg.partition}, offset={msg.offset}")
        )
        consumers.append(consumer)
    
    try:
        # 启动所有消费者
        for i, consumer in enumerate(consumers):
            consumer.start()
            print(f"消费者{i}已启动")
            time.sleep(1)  # 错开启动时间
        
        # 运行40秒
        for second in range(40):
            time.sleep(1)
            if second % 10 == 9:  # 每10秒打印一次统计
                print(f"\n=== {second+1}秒统计 ===")
                for i, consumer in enumerate(consumers):
                    stats = consumer.get_stats()
                    print(f"消费者{i}: 消费={stats['consumed_count']}, "
                          f"处理={stats['processed_count']}")
        
    except KeyboardInterrupt:
        print("接收到中断信号")
    finally:
        for i, consumer in enumerate(consumers):
            print(f"停止消费者{i}...")
            consumer.stop()


if __name__ == "__main__":
    import sys
    
    print("KafkaManyThreadsConsumer 测试程序")
    print("请确保Kafka服务器运行在 localhost:9092")
    print("并且已创建相应的topic")
    print()
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
    else:
        print("可用的测试类型:")
        print("1. basic - 基础使用示例")
        print("2. high_concurrency - 高并发场景")
        print("3. reliability - 可靠性测试")
        print("4. multiple - 多消费者测试")
        test_type = input("请选择测试类型 (1-4): ").strip()
    
    test_mapping = {
        "1": run_basic_example,
        "basic": run_basic_example,
        "2": run_high_concurrency_example,
        "high_concurrency": run_high_concurrency_example,
        "3": run_reliability_test,
        "reliability": run_reliability_test,
        "4": run_multiple_consumers,
        "multiple": run_multiple_consumers
    }
    
    test_func = test_mapping.get(test_type)
    if test_func:
        test_func()
    else:
        print(f"未知的测试类型: {test_type}")
        sys.exit(1)
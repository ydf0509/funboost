#!/usr/bin/env python3
"""
Kafka生产者测试工具
用于测试 KafkaManyThreadsConsumer 的消息生产

使用方法:
python producer_for_testing.py
"""

import time
import json
import random
from datetime import datetime
try:
    from kafka import KafkaProducer
except ImportError:
    print("请安装kafka-python: pip install kafka-python")
    exit(1)


class TestMessageProducer:
    """测试消息生产者"""
    
    def __init__(self, kafka_broker="localhost:9092", topic="test-topic"):
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=[kafka_broker],
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
            key_serializer=lambda k: str(k).encode('utf-8') if k else None,
            acks='all',  # 等待所有副本确认
            retries=3,
            batch_size=16384,
            linger_ms=10,
            compression_type='gzip'
        )
        self.message_count = 0
    
    def generate_test_message(self):
        """生成测试消息"""
        self.message_count += 1
        
        message_types = [
            "user_action",
            "order_event", 
            "system_log",
            "sensor_data",
            "notification"
        ]
        
        return {
            "id": self.message_count,
            "timestamp": datetime.now().isoformat(),
            "type": random.choice(message_types),
            "user_id": random.randint(1000, 9999),
            "data": {
                "action": random.choice(["click", "view", "purchase", "login", "logout"]),
                "value": random.uniform(1.0, 100.0),
                "metadata": {
                    "source": "test_producer",
                    "version": "1.0",
                    "batch": random.randint(1, 10)
                }
            },
            "processing_hint": {
                "estimated_time": random.uniform(0.1, 5.0),  # 预期处理时间
                "priority": random.choice(["low", "normal", "high"]),
                "retryable": random.choice([True, False])
            }
        }
    
    def send_message(self, message=None, key=None):
        """发送单条消息"""
        if message is None:
            message = self.generate_test_message()
        
        if key is None:
            key = message.get("user_id", self.message_count)
        
        try:
            future = self.producer.send(self.topic, value=message, key=key)
            # 等待发送结果
            record_metadata = future.get(timeout=10)
            
            print(f"✅ 消息已发送: partition={record_metadata.partition}, "
                  f"offset={record_metadata.offset}, key={key}")
            return True
            
        except Exception as e:
            print(f"❌ 发送失败: {e}")
            return False
    
    def send_batch(self, count=10, interval=0.5):
        """批量发送消息"""
        print(f"📤 开始发送 {count} 条消息，间隔 {interval} 秒")
        
        success_count = 0
        start_time = time.time()
        
        for i in range(count):
            message = self.generate_test_message()
            if self.send_message(message):
                success_count += 1
            
            if i < count - 1:  # 最后一条消息不等待
                time.sleep(interval)
        
        elapsed = time.time() - start_time
        print(f"📊 发送完成: 成功 {success_count}/{count}, 耗时 {elapsed:.2f}s")
        
        # 确保所有消息都发送
        self.producer.flush()
        
    def send_continuous(self, duration_seconds=60, rate_per_second=2):
        """持续发送消息"""
        print(f"🔄 持续发送消息 {duration_seconds} 秒，速率 {rate_per_second} 条/秒")
        
        interval = 1.0 / rate_per_second
        end_time = time.time() + duration_seconds
        sent_count = 0
        
        while time.time() < end_time:
            message = self.generate_test_message()
            if self.send_message(message):
                sent_count += 1
            
            time.sleep(interval)
        
        print(f"📊 持续发送完成: 总共发送 {sent_count} 条消息")
        self.producer.flush()
    
    def send_burst(self, burst_size=100, burst_count=3, burst_interval=10):
        """突发发送模式"""
        print(f"💥 突发发送模式: {burst_count}轮，每轮{burst_size}条，间隔{burst_interval}秒")
        
        for burst in range(burst_count):
            print(f"💥 第 {burst + 1} 轮突发...")
            
            # 快速发送一批消息
            for i in range(burst_size):
                message = self.generate_test_message()
                self.send_message(message)
                
                if i % 10 == 9:  # 每10条刷新一次
                    self.producer.flush()
            
            self.producer.flush()
            print(f"✅ 第 {burst + 1} 轮完成，发送了 {burst_size} 条消息")
            
            if burst < burst_count - 1:  # 最后一轮不等待
                print(f"⏳ 等待 {burst_interval} 秒...")
                time.sleep(burst_interval)
    
    def close(self):
        """关闭生产者"""
        self.producer.close()


def main():
    print("🚀 Kafka测试消息生产者")
    print("=" * 50)
    
    # 创建生产者
    producer = TestMessageProducer()
    
    try:
        print("📋 选择发送模式:")
        print("1. 发送10条测试消息")
        print("2. 持续发送60秒 (2条/秒)")
        print("3. 突发模式 (3轮x100条)")
        print("4. 自定义批量发送")
        
        choice = input("请选择 (1-4): ").strip()
        
        if choice == "1":
            producer.send_batch(count=10, interval=1.0)
            
        elif choice == "2":
            producer.send_continuous(duration_seconds=60, rate_per_second=2)
            
        elif choice == "3":
            producer.send_burst(burst_size=100, burst_count=3, burst_interval=10)
            
        elif choice == "4":
            count = int(input("发送数量: "))
            interval = float(input("间隔秒数: "))
            producer.send_batch(count=count, interval=interval)
            
        else:
            print("❌ 无效选择")
            return
            
    except KeyboardInterrupt:
        print("\n🛑 接收到中断信号")
        
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        
    finally:
        print("🔚 关闭生产者...")
        producer.close()
        print("✅ 生产者已关闭")


if __name__ == "__main__":
    print("🔧 配置:")
    print("   Kafka地址: localhost:9092")
    print("   主题: test-topic")
    print()
    
    main()
    
    print("\n💡 提示:")
    print("   现在可以运行消费者来处理这些消息:")
    print("   python quick_start.py")
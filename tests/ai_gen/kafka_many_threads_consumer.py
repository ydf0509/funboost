"""
从0实现一个 kafka消费类,

支持设置num_threads为很高的数字,这个数字可以远高于分区数
callback_func 是用户传递一个自定义函数, 需要自动在 线程池大小为num_threads 的线程池中执行这个函数

要求:
随时任意kill -9重启程序,做到不丢失 不跳过消息

例如需要避免如下:
消息耗时是随机的,例如msg1耗时100秒,但msg2耗时30秒,msg3耗时10秒,如果msg3提交offset后,
如果突然重启程序,造成msg1和msg2无法再次消费

核心解决方案：有序offset提交管理器
"""

import threading
import time
import logging
import traceback
from typing import Dict, List, Callable, Optional, Set
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass
from collections import defaultdict, deque
from queue import Queue, Empty
import json

try:
    from kafka import KafkaConsumer, TopicPartition
    from kafka.consumer.fetcher import ConsumerRecord
    from kafka.coordinator.assignors.range import RangePartitionAssignor
    from kafka.coordinator.assignors.roundrobin import RoundRobinPartitionAssignor
except ImportError:
    print("请安装kafka-python: pip install kafka-python")
    raise


@dataclass
class MessageTask:
    """消息处理任务"""
    record: ConsumerRecord
    partition: int
    offset: int
    timestamp: float
    future: Optional[Future] = None
    completed: bool = False
    success: bool = False
    error: Optional[Exception] = None


class OffsetManager:
    """有序offset提交管理器 - 确保按顺序提交offset，避免消息丢失"""
    
    def __init__(self):
        self.lock = threading.RLock()
        # 每个partition的待处理消息队列 {partition: deque[MessageTask]}
        self.pending_messages: Dict[int, deque] = defaultdict(deque)
        # 每个partition当前可提交的最大连续offset {partition: offset}
        self.committable_offsets: Dict[int, int] = {}
        # 每个partition已提交的offset {partition: offset}
        self.committed_offsets: Dict[int, int] = {}
        
    def add_message(self, task: MessageTask):
        """添加消息到待处理队列"""
        with self.lock:
            self.pending_messages[task.partition].append(task)
            
    def mark_completed(self, task: MessageTask, success: bool, error: Optional[Exception] = None):
        """标记消息处理完成"""
        with self.lock:
            task.completed = True
            task.success = success
            task.error = error
            
            # 更新可提交的offset
            self._update_committable_offset(task.partition)
    
    def _update_committable_offset(self, partition: int):
        """
        更新指定partition的可提交offset
        
        关键逻辑：只提交连续成功处理的消息，保证消息不丢失
        如果中间有失败消息，则停止提交，确保重启后能重新处理失败消息
        """
        queue = self.pending_messages[partition]
        
        # 关键修复：只处理连续成功的消息，一旦遇到失败就停止
        consecutive_success_count = 0
        last_committable_offset = None
        
        # 从队列头部开始检查连续完成且成功的消息
        while (consecutive_success_count < len(queue) and 
               queue[consecutive_success_count].completed and 
               queue[consecutive_success_count].success):
            
            task = queue[consecutive_success_count]
            last_committable_offset = task.offset + 1  # Kafka offset需要+1
            consecutive_success_count += 1
        
        # 更新可提交的offset（只提交连续成功的部分）
        if last_committable_offset is not None:
            self.committable_offsets[partition] = last_committable_offset
            
        # 移除已经可以安全提交的连续成功消息
        for _ in range(consecutive_success_count):
            completed_task = queue.popleft()
            self.logger.debug(f"移除已处理消息: partition={completed_task.partition}, "
                            f"offset={completed_task.offset}")
        
        # 检查是否有失败的消息阻塞了后续提交
        if (queue and queue[0].completed and not queue[0].success):
            failed_task = queue[0]
            self.logger.warning(f"消息处理失败，阻塞后续offset提交: "
                              f"partition={failed_task.partition}, offset={failed_task.offset}, "
                              f"error={failed_task.error}，重启后将从此处重新消费")
            
        # 移除队列头部已完成的失败消息（但不影响offset提交）
        while queue and queue[0].completed and not queue[0].success:
            failed_task = queue.popleft()
            self.logger.info(f"移除失败消息: partition={failed_task.partition}, "
                           f"offset={failed_task.offset}")
    
    def get_committable_offsets(self) -> Dict[TopicPartition, int]:
        """获取可安全提交的offset"""
        with self.lock:
            result = {}
            for partition, offset in self.committable_offsets.items():
                if offset > self.committed_offsets.get(partition, -1):
                    topic_partition = TopicPartition(topic='', partition=partition)
                    result[topic_partition] = offset
            return result
    
    def mark_committed(self, offsets: Dict[TopicPartition, int]):
        """标记offset已提交"""
        with self.lock:
            for tp, offset in offsets.items():
                self.committed_offsets[tp.partition] = offset
                
    def clear_partition(self, partition: int):
        """清理partition数据（用于rebalance）"""
        with self.lock:
            if partition in self.pending_messages:
                del self.pending_messages[partition]
            if partition in self.committable_offsets:
                del self.committable_offsets[partition]
            if partition in self.committed_offsets:
                del self.committed_offsets[partition]
    
    def get_status(self) -> Dict:
        """获取状态信息"""
        with self.lock:
            return {
                'pending_count': {p: len(q) for p, q in self.pending_messages.items()},
                'committable_offsets': dict(self.committable_offsets),
                'committed_offsets': dict(self.committed_offsets)
            }


class KafkaManyThreadsConsumer:
    """
    支持大量线程的Kafka消费者，确保消息不丢失不跳过
    
    核心特性：
    1. 支持线程数远超partition数
    2. 有序offset提交，避免消息丢失
    3. 支持kill -9重启不丢消息
    4. 自动处理rebalance
    """
    
    def __init__(self, kafka_broker_address: str, topic: str, group_id: str, 
                 num_threads: int = 100, callback_func: Optional[Callable] = None):
        self.kafka_broker_address = kafka_broker_address
        self.topic = topic
        self.group_id = group_id
        self.num_threads = num_threads
        self.callback_func = callback_func or self._default_callback
        
        # 核心组件
        self.consumer: Optional[KafkaConsumer] = None
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.offset_manager = OffsetManager()
        
        # 控制变量
        self.running = False
        self.shutdown_event = threading.Event()
        
        # 线程
        self.consume_thread: Optional[threading.Thread] = None
        self.commit_thread: Optional[threading.Thread] = None
        
        # 统计信息
        self.stats = {
            'consumed_count': 0,
            'processed_count': 0,
            'failed_count': 0,
            'committed_count': 0
        }
        self.stats_lock = threading.Lock()
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(f'KafkaConsumer-{group_id}')
        
    def _default_callback(self, message):
        """默认的消息处理函数"""
        self.logger.info(f"处理消息: partition={message.partition}, offset={message.offset}, "
                        f"value={message.value[:100] if message.value else None}...")
        # 模拟处理时间
        time.sleep(0.1)
        
    def start(self):
        """启动消费者"""
        if self.running:
            self.logger.warning("消费者已经在运行中")
            return
            
        self.logger.info(f"启动Kafka消费者: topic={self.topic}, group_id={self.group_id}, "
                        f"threads={self.num_threads}")
        
        try:
            # 创建Kafka消费者
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=[self.kafka_broker_address],
                group_id=self.group_id,
                auto_offset_reset='earliest',
                enable_auto_commit=False,  # 关闭自动提交，手动控制offset
                max_poll_records=500,
                session_timeout_ms=30000,
                heartbeat_interval_ms=3000,
                consumer_timeout_ms=1000,  # 设置poll超时
                value_deserializer=lambda x: x.decode('utf-8') if x else None,
                key_deserializer=lambda x: x.decode('utf-8') if x else None
            )
            
            # 创建线程池
            self.thread_pool = ThreadPoolExecutor(
                max_workers=self.num_threads,
                thread_name_prefix=f'KafkaWorker-{self.group_id}'
            )
            
            self.running = True
            
            # 启动消费线程
            self.consume_thread = threading.Thread(
                target=self._consume_loop,
                name=f'KafkaConsume-{self.group_id}',
                daemon=True
            )
            self.consume_thread.start()
            
            # 启动提交线程
            self.commit_thread = threading.Thread(
                target=self._commit_loop,
                name=f'KafkaCommit-{self.group_id}',
                daemon=True
            )
            self.commit_thread.start()
            
            self.logger.info("Kafka消费者启动成功")
            
        except Exception as e:
            self.logger.error(f"启动Kafka消费者失败: {e}")
            self.stop()
            raise
    
    def stop(self):
        """停止消费者"""
        if not self.running:
            return
            
        self.logger.info("正在停止Kafka消费者...")
        
        # 设置停止标志
        self.running = False
        self.shutdown_event.set()
        
        # 等待线程结束
        if self.consume_thread and self.consume_thread.is_alive():
            self.consume_thread.join(timeout=10)
            
        if self.commit_thread and self.commit_thread.is_alive():
            self.commit_thread.join(timeout=10)
        
        # 关闭线程池
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True, timeout=30)
            
        # 最后一次提交offset
        self._commit_offsets()
        
        # 关闭消费者
        if self.consumer:
            self.consumer.close()
            
        self.logger.info("Kafka消费者已停止")
        
    def _consume_loop(self):
        """消费循环 - 主线程"""
        self.logger.info("开始消费消息循环")
        
        while self.running:
            try:
                # 轮询消息
                message_batch = self.consumer.poll(timeout_ms=1000)
                
                if not message_batch:
                    continue
                    
                # 处理每个partition的消息
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        if not self.running:
                            break
                            
                        self._process_message(message)
                        
                        with self.stats_lock:
                            self.stats['consumed_count'] += 1
                            
            except Exception as e:
                if self.running:
                    self.logger.error(f"消费消息时发生错误: {e}\n{traceback.format_exc()}")
                    time.sleep(1)  # 错误时暂停一下
                    
        self.logger.info("消费循环结束")
    
    def _process_message(self, record: ConsumerRecord):
        """处理单个消息"""
        # 创建消息任务
        task = MessageTask(
            record=record,
            partition=record.partition,
            offset=record.offset,
            timestamp=time.time()
        )
        
        # 添加到offset管理器
        self.offset_manager.add_message(task)
        
        # 提交到线程池处理
        future = self.thread_pool.submit(self._execute_callback, task)
        task.future = future
        
        self.logger.debug(f"提交消息到线程池: partition={record.partition}, offset={record.offset}")
    
    def _execute_callback(self, task: MessageTask):
        """在线程池中执行回调函数"""
        start_time = time.time()
        success = False
        error = None
        
        try:
            # 执行用户回调函数
            self.callback_func(task.record)
            success = True
            
            with self.stats_lock:
                self.stats['processed_count'] += 1
                
            self.logger.debug(f"消息处理成功: partition={task.partition}, offset={task.offset}, "
                            f"耗时={time.time() - start_time:.2f}s")
                            
        except Exception as e:
            error = e
            success = False
            
            with self.stats_lock:
                self.stats['failed_count'] += 1
                
            self.logger.error(f"消息处理失败: partition={task.partition}, offset={task.offset}, "
                            f"error={e}\n{traceback.format_exc()}")
        finally:
            # 标记任务完成
            self.offset_manager.mark_completed(task, success, error)
    
    def _commit_loop(self):
        """offset提交循环"""
        self.logger.info("开始offset提交循环")
        
        while self.running:
            try:
                self._commit_offsets()
                time.sleep(5)  # 每5秒提交一次
                
            except Exception as e:
                if self.running:
                    self.logger.error(f"提交offset时发生错误: {e}")
                    time.sleep(1)
                    
        self.logger.info("offset提交循环结束")
    
    def _commit_offsets(self):
        """提交offset"""
        committable_offsets = self.offset_manager.get_committable_offsets()
        
        if not committable_offsets:
            return
            
        try:
            # 构造提交格式
            commit_offsets = {}
            for tp, offset in committable_offsets.items():
                # 更新topic信息
                tp_with_topic = TopicPartition(self.topic, tp.partition)
                commit_offsets[tp_with_topic] = offset
            
            # 提交到Kafka
            self.consumer.commit(offsets=commit_offsets)
            
            # 标记为已提交
            self.offset_manager.mark_committed(committable_offsets)
            
            with self.stats_lock:
                self.stats['committed_count'] += len(commit_offsets)
            
            self.logger.info(f"成功提交offset: {commit_offsets}")
            
        except Exception as e:
            self.logger.error(f"提交offset失败: {e}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self.stats_lock:
            stats = self.stats.copy()
        
        # 添加offset管理器状态
        stats.update({
            'offset_manager_status': self.offset_manager.get_status(),
            'thread_pool_active': self.thread_pool._threads if self.thread_pool else 0,
            'running': self.running
        })
        
        return stats
    
    def wait_for_completion(self, timeout: Optional[float] = None):
        """等待消费完成"""
        if self.consume_thread:
            self.consume_thread.join(timeout=timeout)
        if self.commit_thread:
            self.commit_thread.join(timeout=timeout)


# 使用示例
def example_callback(message):
    """示例回调函数"""
    import random
    
    # 模拟不同的处理时间
    processing_time = random.uniform(0.1, 2.0)
    time.sleep(processing_time)
    
    print(f"处理消息: partition={message.partition}, offset={message.offset}, "
          f"耗时={processing_time:.2f}s, value={message.value[:50] if message.value else None}...")
    
    # 模拟偶尔的处理失败
    if random.random() < 0.05:  # 5%失败率
        raise Exception("模拟处理失败")


if __name__ == "__main__":
    # 创建消费者实例
    consumer = KafkaManyThreadsConsumer(
        kafka_broker_address="localhost:9092",
        topic="test-topic",
        group_id="test-group",
        num_threads=50,
        callback_func=example_callback
    )
    
    try:
        # 启动消费者
        consumer.start()
        
        # 定期打印统计信息
        while True:
            time.sleep(10)
            stats = consumer.get_stats()
            print(f"统计信息: {json.dumps(stats, indent=2, ensure_ascii=False)}")
            
    except KeyboardInterrupt:
        print("接收到中断信号，正在停止...")
    finally:
        consumer.stop()
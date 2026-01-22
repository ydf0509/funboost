# -*- coding: utf-8 -*-
"""
高性能内存队列发布者

支持两种模式：
1. 标准模式（默认）：完整的 funboost 功能支持
2. 极速模式（ultra_fast_mode=True）：跳过大部分框架开销，直接发布消息
   - 极速模式下会自动生成简化的 extra 字段
   - 适用于对性能要求极高的场景
"""
import time
import typing
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.queues.fastest_mem_queue import FastestMemQueues, FastestMemQueue
from funboost.core.msg_result_getter import AsyncResult


class FastestMemQueuePublisher(AbstractPublisher):
    """
    高性能内存队列发布者。
    
    broker_exclusive_config 配置项：
    - ultra_fast_mode: 是否启用极速模式，默认 False
      极速模式跳过大部分框架开销（序列化、装饰器、日志等），性能提升 3-5 倍
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        super().custom_init()
        self._ultra_fast = self.publisher_params.broker_exclusive_config.get('ultra_fast_mode', False)
        if self._ultra_fast:
            # 极速模式：预生成一些常量，减少运行时开销
            self._task_id_counter = 0
            self._count = 0
            self._last_log_time = time.time()

    @property
    def _mem_queue(self) -> FastestMemQueue:
        return FastestMemQueues.get_queue(self._queue_name)

    def publish(self, msg: typing.Union[str, dict], task_id=None, task_options=None):
        """
        发布消息到队列。
        
        极速模式下跳过大部分框架开销，直接将消息放入队列。
        """
        if self._ultra_fast:
            return self._publish_ultra_fast(msg)
        else:
            return super().publish(msg, task_id, task_options)

    def _publish_ultra_fast(self, msg: typing.Union[str, dict]):
        """
        极速发布模式：跳过序列化、装饰器、日志等开销
        """
        # 直接构建消息，不做任何转换
        if isinstance(msg, dict):
            # 添加最小化的 extra 字段（消费者极速模式需要）
            if 'extra' not in msg:
                self._task_id_counter += 1
                msg['extra'] = {
                    'task_id': f'ultra_{self._task_id_counter}',
                    'publish_time': time.time(),
                }
            self._mem_queue.put(msg)
        else:
            # 字符串消息直接放入
            self._mem_queue.put(msg)
        
        # 简化的计数统计
        self._count += 1
        current_time = time.time()
        if current_time - self._last_log_time > 10:
            self.logger.info(f'[极速模式] 10秒内发布了 {self._count} 条消息到 {self._queue_name}')
            self._count = 0
            self._last_log_time = current_time
        
        return AsyncResult(f'ultra_{self._task_id_counter}', timeout=self.publisher_params.rpc_timeout)

    def _publish_impl(self, msg):
        self._mem_queue.put(msg)

    def clear(self):
        self._mem_queue.clear()
        self.logger.warning(f'清除 高性能内存队列 {self._queue_name} 中的消息成功')

    def get_message_count(self):
        return self._mem_queue.qsize()

    def close(self):
        pass

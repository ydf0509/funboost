# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/1/16
"""
微批消费者 Mixin (Micro-Batch Consumer Mixin)

功能：累积 N 条消息后批量处理，而不是逐条消费。
适用场景：批量写入数据库、批量调用 API、批量发送通知等。

用法见 test_frame/test_micro_batch/test_micro_batch_consumer.py

使用方式：
1. 使用 BoosterParams + MicroBatchConsumerMixin (推荐)
   @boost(BoosterParams(
       queue_name='batch_queue',
       consumer_override_cls=MicroBatchConsumerMixin,
       user_options={
           'micro_batch_size': 100,
           'micro_batch_timeout': 5.0,
       }
   ))
   def batch_task(items: list):
       db.bulk_insert(items)
"""

import asyncio
import inspect
import threading
import time
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.concurrent_pool.async_helper import simple_run_in_executor
from funboost.constant import ConcurrentModeEnum,BrokerEnum
from funboost.core.func_params_model import BoosterParams


class MicroBatchConsumerMixin(AbstractConsumer):
    """
    微批消费者 Mixin
    
    核心原理：
    1. 重写 _submit_task 方法，将消息累积到缓冲区
    2. 达到 batch_size 条消息或超过 timeout 秒后，批量调用消费函数
    3. 消费函数的入参从单个对象变为 list[dict]
    
    配置参数（通过 user_options 传递）：
    - micro_batch_size: 批量大小，默认 100
    - micro_batch_timeout: 超时时间（秒），默认 5.0
    
    支持的并发模式：
    - THREADING: 使用 _run_batch (同步)
    - ASYNC: 使用 _async_run_batch (异步)
    """
    
    def custom_init(self):
        """初始化微批相关配置"""
        super().custom_init()
        
        # 从 user_options 读取配置（funboost 推荐用 user_options 传递自定义配置）
        user_options = self.consumer_params.user_options
        self._batch_size = user_options.get('micro_batch_size', 100)
        self._batch_timeout = user_options.get('micro_batch_timeout', 5.0)
        
        # 消息缓冲区和锁
        self._batch_buffer: list = []
        self._batch_lock = threading.Lock()
        self._last_batch_time = time.time()
        
        # 判断是否使用异步模式
        self._is_async_mode = self.consumer_params.concurrent_mode == ConcurrentModeEnum.ASYNC
        
        # 启动超时刷新线程
        self._start_timeout_flush_thread()
        
        self.logger.info(
            f"MicroBatch consumer initialized, batch_size={self._batch_size}, timeout={self._batch_timeout}s, async_mode={self._is_async_mode}"
        )
    
    def _start_timeout_flush_thread(self):
        """启动超时刷新后台线程"""
        def timeout_flush_loop():
            while True:
                time.sleep(min(1.0, self._batch_timeout / 2))
                with self._batch_lock:
                    if self._batch_buffer and self._is_timeout():
                        self._flush_batch()
        
        t = threading.Thread(
            target=timeout_flush_loop,
            daemon=True,
            name=f"micro_batch_flush_{self._queue_name}"
        )
        t.start()
    
    def _is_timeout(self) -> bool:
        """判断是否超时"""
        return time.time() - self._last_batch_time >= self._batch_timeout
    
    def _should_flush_batch(self) -> bool:
        """判断是否应该刷新批次"""
        return len(self._batch_buffer) >= self._batch_size
    
    def _submit_task(self, kw):
        """
        重写 _submit_task 方法，累积消息到缓冲区
        而不是立即提交到并发池执行
        """
        # 先进行消息转换和过滤（复用父类逻辑）
        kw['body'] = self._convert_msg_before_run(kw['body'])
        self._print_message_get_from_broker(kw['body'])
        
        # 暂停消费检查
        if self._judge_is_daylight():
            self._requeue(kw)
            time.sleep(self.time_interval_for_check_do_not_run_time)
            return
        
        # 提取函数参数
        from funboost.core.helper_funs import delete_keys_and_return_new_dict
        function_only_params = delete_keys_and_return_new_dict(kw['body'])
        kw['function_only_params'] = function_only_params
        
        # 累积到缓冲区
        with self._batch_lock:
            self._batch_buffer.append(kw)
            
            # 检查是否触发批量处理
            if self._should_flush_batch():
                self._flush_batch()
        
        # 频率控制
        if self.consumer_params.is_using_distributed_frequency_control:
            active_num = self._distributed_consumer_statistics.active_consumer_num
            self._frequency_control(self.consumer_params.qps / active_num, self._msg_schedule_time_intercal * active_num)
        else:
            self._frequency_control(self.consumer_params.qps, self._msg_schedule_time_intercal)
    
    def _flush_batch(self):
        """
        执行批量处理
        
        注意：调用此方法时必须已持有 _batch_lock 锁
        """
        if not self._batch_buffer:
            return
        
        # 取出所有缓冲消息
        batch = self._batch_buffer[:]
        self._batch_buffer.clear()
        self._last_batch_time = time.time()
        
        batch_size = len(batch)
        self.logger.debug(f"Starting batch processing for {batch_size} messages")
        
        # 根据并发模式选择同步或异步执行
        if self._is_async_mode:
            self.concurrent_pool.submit(self._async_run_batch, batch)
        else:
            self.concurrent_pool.submit(self._run_batch, batch)
    
    def _run_batch(self, batch: list):
        """
        同步批量运行消费函数
        
        :param batch: 包含多个 kw 字典的列表
        """
        t_start = time.time()
        batch_size = len(batch)
        
        # 提取所有消息的函数参数
        items = [kw['function_only_params'] for kw in batch]
        
        try:
            # 调用消费函数（入参是 list）
            result = self.consuming_function(items)
            
            # 批量确认消费
            for kw in batch:
                self._confirm_consume(kw)
            
            t_cost = round(time.time() - t_start, 4)
            self.logger.info(f"Batch processing succeeded: {batch_size} messages, took {t_cost}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {batch_size} messages, error: {e}", exc_info=True)
            
            # 批量重回队列
            for kw in batch:
                try:
                    self._requeue(kw)
                except Exception as requeue_error:
                    self.logger.error(f"Failed to requeue message: {requeue_error}")
            
            # raise

    async def _async_run_batch(self, batch: list):
        """
        异步批量运行消费函数（支持 async def 消费函数）
        
        :param batch: 包含多个 kw 字典的列表
        """
        t_start = time.time()
        batch_size = len(batch)
        
        # 提取所有消息的函数参数
        items = [kw['function_only_params'] for kw in batch]
        
        try:
            # 调用消费函数（入参是 list）
            if asyncio.iscoroutinefunction(self.consuming_function):
                result = await self.consuming_function(items)
            else:
                # 同步函数在 executor 中运行
                result = await simple_run_in_executor(self.consuming_function, items)
            
            # 批量确认消费
            for kw in batch:
                await simple_run_in_executor(self._confirm_consume, kw)
            
            t_cost = round(time.time() - t_start, 4)
            self.logger.info(f"Batch processing succeeded (async): {batch_size} messages, took {t_cost}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Batch processing failed (async): {batch_size} messages, error: {e}", exc_info=True)
            
            # 批量重回队列
            for kw in batch:
                try:
                    await simple_run_in_executor(self._requeue, kw)
                except Exception as requeue_error:
                    self.logger.error(f"Failed to requeue message (async): {requeue_error}")
            
            # raise



class MicroBatchBoosterParams(BoosterParams):
    broker_kind:str=BrokerEnum.MEMORY_QUEUE,
    consumer_override_cls:AbstractConsumer=MicroBatchConsumerMixin,
    user_options:dict ={
        'micro_batch_size': 10,        # 每批10条
        'micro_batch_timeout': 1.0,    # 1秒超时
    },
    qps:float=100,
    should_check_publish_func_params:bool=False,  # 微批模式需要关闭入参校验

# -*- coding: utf-8 -*-
"""
高性能内存队列消费者

支持两种模式：
1. 标准模式（默认）：完整的 funboost 功能支持
2. 极速模式（ultra_fast_mode=True）：跳过大部分框架开销，直接调用函数
   - 极速模式下不支持：重试、过滤、延时任务、RPC、结果持久化等功能
   - 适用于对性能要求极高且不需要这些功能的场景
"""
import time
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.queues.fastest_mem_queue import FastestMemQueues, FastestMemQueue
from funboost.core.helper_funs import get_func_only_params


class FastestMemQueueConsumer(AbstractConsumer):
    """
    高性能内存队列消费者。
    
    broker_exclusive_config 配置项：
    - pull_msg_batch_size: 每次批量拉取的消息数量，默认 1
    - ultra_fast_mode: 是否启用极速模式，默认 False
      极速模式跳过大部分框架开销，性能可提升 3-10 倍，但失去重试/过滤/延时等功能
    """

    @property
    def _mem_queue(self) -> FastestMemQueue:
        return FastestMemQueues.get_queue(self._queue_name)

    def _dispatch_task(self):
        batch_size = self.consumer_params.broker_exclusive_config.get('pull_msg_batch_size', 1)
        ultra_fast = self.consumer_params.broker_exclusive_config.get('ultra_fast_mode', False)
        
        if ultra_fast:
            self._dispatch_task_ultra_fast(batch_size)
        elif batch_size <= 1:
            self._dispatch_task_single()
        else:
            self._dispatch_task_batch(batch_size)

    def _dispatch_task_single(self):
        """单条拉取模式"""
        while True:
            task = self._mem_queue.get()
            kw = {'body': task}
            self._submit_task(kw)

    def _dispatch_task_batch(self, batch_size: int):
        """批量拉取模式"""
        while True:
            tasks = self._mem_queue.get_batch_block(max_count=batch_size)
            for task in tasks:
                kw = {'body': task}
                self._submit_task(kw)

    def _dispatch_task_ultra_fast(self, batch_size: int):
        """
        极速模式：跳过大部分框架开销，直接调用函数
        
        不支持的功能：重试、过滤、延时任务、RPC、结果持久化、指标统计等
        """
        func = self.consuming_function
        queue = self._mem_queue
        
        # 缓存常用变量，避免属性访问开销
        count = 0
        last_log_time = time.time()
        
        if batch_size <= 1:
            # 单条极速模式
            while True:
                task = queue.get()
                # 直接提取函数参数并调用
                if isinstance(task, dict):
                    params = get_func_only_params(task)
                    func(**params)
                else:
                    # 如果是字符串，需要转换
                    from funboost.core.serialization import Serialization
                    task_dict = Serialization.to_dict(task)
                    params = get_func_only_params(task_dict)
                    func(**params)
                
                count += 1
                # 每10秒输出一次统计
                current_time = time.time()
                if current_time - last_log_time > 10:
                    self.logger.info(f'[极速模式] 10秒内执行了 {count} 次函数 [{func.__name__}]')
                    count = 0
                    last_log_time = current_time
        else:
            # 批量极速模式
            while True:
                tasks = queue.get_batch_block(max_count=batch_size)
                for task in tasks:
                    if isinstance(task, dict):
                        params = get_func_only_params(task)
                        func(**params)
                    else:
                        from funboost.core.serialization import Serialization
                        task_dict = Serialization.to_dict(task)
                        params = get_func_only_params(task_dict)
                        func(**params)
                    count += 1
                
                current_time = time.time()
                if current_time - last_log_time > 10:
                    self.logger.info(f'[极速模式] 10秒内执行了 {count} 次函数 [{func.__name__}]')
                    count = 0
                    last_log_time = current_time

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        self._mem_queue.put(kw['body'])

# -*- coding: utf-8 -*-
"""
Funboost Workflow - Signature 任务签名

Signature 表示一个"待执行"的任务，包含：
- 对 booster（@boost 装饰的函数）的引用
- 调用时的参数 (args, kwargs)
- 是否忽略上游结果 (immutable)

类似 Celery 的 signature / s() 概念。
"""

import typing
from funboost.core.msg_result_getter import AsyncResult
from funboost.core.function_result_status_saver import FunctionResultStatus


class Signature:
    """
    任务签名 - 表示一个待执行的任务及其参数
    
    用法：
    ```python
    # 方式1：直接创建
    sig = Signature(my_task, args=(1, 2), kwargs={'name': 'test'})
    
    # 方式2：通过便捷函数（推荐）
    sig = my_task.s(1, 2, name='test')
    
    # 执行签名
    result = sig.apply()  # 同步
    async_result = sig.apply_async()  # 异步
    ```
    """
    
    def __init__(self, 
                 booster, 
                 args: tuple = None, 
                 kwargs: dict = None, 
                 immutable: bool = False):
        """
        :param booster: @boost 装饰的函数
        :param args: 位置参数
        :param kwargs: 关键字参数
        :param immutable: 是否忽略上游传入的结果（用于 chain 场景）
        """
        self.booster = booster
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.immutable = immutable
    
    def s(self, *args, **kwargs) -> 'Signature':
        """
        创建新的签名，合并参数（类似 Celery 的 .s() 方法）
        
        用法：
        ```python
        sig = my_task.s(1, 2, name='test')
        ```
        """
        merged_args = self.args + args
        merged_kwargs = {**self.kwargs, **kwargs}
        return Signature(self.booster, merged_args, merged_kwargs, self.immutable)
    
    def si(self, *args, **kwargs) -> 'Signature':
        """
        创建不可变签名（忽略上游结果）
        
        在 chain 中使用时，不会将上游任务的结果作为第一个参数传入。
        """
        merged_args = self.args + args
        merged_kwargs = {**self.kwargs, **kwargs}
        return Signature(self.booster, merged_args, merged_kwargs, immutable=True)
    
    def set_immutable(self, immutable: bool = True) -> 'Signature':
        """设置是否忽略上游结果"""
        self.immutable = immutable
        return self
    
    def clone(self) -> 'Signature':
        """克隆当前签名"""
        return Signature(
            self.booster, 
            self.args, 
            self.kwargs.copy(), 
            self.immutable
        )
    
    def _build_args(self, prev_result=None) -> tuple:
        """构建实际执行时的参数，处理上游结果传递"""
        if prev_result is not None and not self.immutable:
            # 将上游结果作为第一个参数
            return (prev_result,) + self.args
        return self.args
    
    def apply(self, prev_result=None) -> FunctionResultStatus:
        """
        同步执行任务并等待结果
        
        :param prev_result: 上游任务的结果（用于 chain 场景）
        :return: FunctionResultStatus 包含执行结果
        """
        args = self._build_args(prev_result)
        async_result = self.booster.push(*args, **self.kwargs)
        return async_result.wait_rpc_data_or_raise(raise_exception=True)
    
    def apply_async(self, prev_result=None) -> AsyncResult:
        """
        异步执行任务，返回 AsyncResult
        
        :param prev_result: 上游任务的结果（用于 chain 场景）
        :return: AsyncResult 可用于后续等待结果
        """
        args = self._build_args(prev_result)
        return self.booster.push(*args, **self.kwargs)
    
    def __repr__(self):
        return f"Signature({self.booster.queue_name}, args={self.args}, kwargs={self.kwargs}, immutable={self.immutable})"
    
    def __or__(self, other):
        """
        支持 | 运算符创建 Chain
        
        用法：task1.s() | task2.s() | task3.s()
        """
        from .primitives import Chain
        if isinstance(other, Signature):
            return Chain(self, other)
        elif isinstance(other, Chain):
            return Chain(self, *other.tasks)
        else:
            raise TypeError(f"unsupported operand type(s) for |: 'Signature' and '{type(other).__name__}'")


def signature(booster, *args, **kwargs) -> Signature:
    """
    便捷函数：创建任务签名
    
    用法：
    ```python
    sig = signature(my_task, 1, 2, name='test')
    ```
    """
    return Signature(booster, args, kwargs)

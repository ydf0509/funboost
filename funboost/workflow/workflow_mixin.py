# -*- coding: utf-8 -*-
"""
Funboost Workflow - Publisher/Consumer Mixin

提供 WorkflowPublisherMixin 和 WorkflowConsumerMixin，
用于在消息中注入和提取工作流上下文，实现跨任务的上下文传递。

使用方式：
1. 直接使用预配置的 WorkflowBoosterParams（推荐）
2. 或手动指定 consumer_override_cls 和 publisher_override_cls
"""

import copy
import typing

from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.serialization import Serialization


class WorkflowPublisherMixin(AbstractPublisher):
    """
    工作流发布者 Mixin
    
    功能：
    1. 在发布消息时，检查当前上下文中是否有工作流信息
    2. 如果有，将工作流上下文注入到消息的 extra 字段中
    3. 支持链路追踪：可以追踪任务是由哪个上游任务触发的
    
    工作流上下文包含：
    - workflow_id: 工作流唯一标识
    - parent_task_id: 父任务 ID
    - chain_depth: 链条深度（用于调试）
    """
    
    # 线程本地存储，用于保存当前任务的工作流上下文
    _workflow_context_storage: typing.ClassVar[dict] = {}
    
    @classmethod
    def set_workflow_context(cls, workflow_ctx: dict):
        """设置当前线程的工作流上下文"""
        import threading
        thread_id = threading.current_thread().ident
        cls._workflow_context_storage[thread_id] = workflow_ctx
    
    @classmethod
    def get_workflow_context(cls) -> typing.Optional[dict]:
        """获取当前线程的工作流上下文"""
        import threading
        thread_id = threading.current_thread().ident
        return cls._workflow_context_storage.get(thread_id)
    
    @classmethod
    def clear_workflow_context(cls):
        """清除当前线程的工作流上下文"""
        import threading
        thread_id = threading.current_thread().ident
        cls._workflow_context_storage.pop(thread_id, None)
    
    def publish(self, msg, task_id=None, task_options=None):
        """
        发布消息，注入工作流上下文
        """
        msg = copy.deepcopy(msg)  # 防止修改用户原始字典
        
        # 获取当前工作流上下文
        workflow_ctx = self.get_workflow_context()
        
        if workflow_ctx:
            if 'extra' not in msg:
                msg['extra'] = {}
            
            # 创建新的上下文（更新 parent_task_id 和 chain_depth）
            new_ctx = workflow_ctx.copy()
            new_ctx['parent_task_id'] = workflow_ctx.get('current_task_id')
            new_ctx['chain_depth'] = workflow_ctx.get('chain_depth', 0) + 1
            
            msg['extra']['workflow_context'] = new_ctx
        
        return super().publish(msg, task_id, task_options)


class WorkflowConsumerMixin(AbstractConsumer):
    """
    工作流消费者 Mixin
    
    功能：
    1. 在执行任务前，从消息中提取工作流上下文
    2. 将上下文保存到线程本地存储，以便子任务继承
    3. 执行完成后清理上下文
    
    这样，当消费函数内部调用 other_task.push() 时，
    WorkflowPublisherMixin 可以从线程本地存储获取上下文并注入到子任务消息中。
    """
    
    def _extract_workflow_context(self, kw: dict) -> typing.Optional[dict]:
        """从消息中提取工作流上下文"""
        return kw['body'].get('extra', {}).get('workflow_context')
    
    def _run(self, kw: dict):
        """
        同步消费函数执行，注入工作流上下文
        """
        # 1. 提取工作流上下文
        workflow_ctx = self._extract_workflow_context(kw)
        
        if workflow_ctx:
            # 更新当前任务 ID
            workflow_ctx = workflow_ctx.copy()
            workflow_ctx['current_task_id'] = kw['body']['extra'].get('task_id')
            
            # 保存到线程本地存储
            WorkflowPublisherMixin.set_workflow_context(workflow_ctx)
        
        try:
            return super()._run(kw)
        finally:
            # 清理上下文
            WorkflowPublisherMixin.clear_workflow_context()
    
    async def _async_run(self, kw: dict):
        """
        异步消费函数执行，注入工作流上下文
        """
        # 1. 提取工作流上下文
        workflow_ctx = self._extract_workflow_context(kw)
        
        if workflow_ctx:
            # 更新当前任务 ID
            workflow_ctx = workflow_ctx.copy()
            workflow_ctx['current_task_id'] = kw['body']['extra'].get('task_id')
            
            # 保存到线程本地存储（asyncio 场景下可能需要更精细的处理）
            WorkflowPublisherMixin.set_workflow_context(workflow_ctx)
        
        try:
            return await super()._async_run(kw)
        finally:
            # 清理上下文
            WorkflowPublisherMixin.clear_workflow_context()


def get_current_workflow_context() -> typing.Optional[dict]:
    """
    获取当前工作流上下文（供用户代码使用）
    
    用法：
    ```python
    from funboost.workflow import get_current_workflow_context
    
    @boost(WorkflowBoosterParams(queue_name='my_task'))
    def my_task(x):
        ctx = get_current_workflow_context()
        if ctx:
            print(f"Workflow ID: {ctx.get('workflow_id')}")
            print(f"Parent Task: {ctx.get('parent_task_id')}")
    ```
    """
    return WorkflowPublisherMixin.get_workflow_context()

# -*- coding: utf-8 -*-
"""
Funboost Workflow - 编排原语 (Primitives)

提供类似 Celery Canvas 的编排原语：
- Chain: 链式执行
- Group: 并行执行
- Chord: 并行 + 汇总

设计哲学：
- 声明式定义，命令式执行
- 复用 funboost 现有的 RPC 机制
- 不修改 funboost 核心代码
"""

import typing
import uuid
from .signature import Signature
from .workflow_mixin import WorkflowPublisherMixin
from funboost.core.msg_result_getter import AsyncResult
from funboost.core.function_result_status_saver import FunctionResultStatus


def _ensure_workflow_context() -> bool:
    """
    确保存在工作流上下文，如果不存在则创建初始上下文
    
    :return: True 表示创建了新上下文（调用者需要在结束时清理），False 表示已存在上下文
    """
    existing = WorkflowPublisherMixin.get_workflow_context()
    if existing:
        return False  # 已存在，不需要创建
    
    # 创建初始工作流上下文
    initial_ctx = {
        'workflow_id': str(uuid.uuid4()),
        'chain_depth': 0,
        'current_task_id': None,
        'parent_task_id': None,
    }
    WorkflowPublisherMixin.set_workflow_context(initial_ctx)
    return True  # 新创建的，调用者需要清理


class Chain:
    """
    链式执行：顺序执行多个任务，上游结果自动传给下游
    
    用法：
    ```python
    # 方式1：构造函数
    workflow = Chain(task1.s(x), task2.s(), task3.s())
    
    # 方式2：便捷函数
    workflow = chain(task1.s(x), task2.s(), task3.s())
    
    # 方式3：| 运算符
    workflow = task1.s(x) | task2.s() | task3.s()
    
    # 执行
    result = workflow.apply()
    ```
    
    执行流程：
    1. 执行 task1，获取结果 r1
    2. 将 r1 作为 task2 的第一个参数，执行 task2，获取结果 r2
    3. 将 r2 作为 task3 的第一个参数，执行 task3，获取结果 r3
    4. 返回 r3
    """
    
    def __init__(self, *tasks):
        """
        :param tasks: 任务列表，可以是 Signature、Chain、Group、Chord
        """
        self.tasks = []
        for task in tasks:
            if isinstance(task, Chain):
                # 展平嵌套的 Chain
                self.tasks.extend(task.tasks)
            else:
                self.tasks.append(task)
    
    def apply(self, prev_result=None) -> FunctionResultStatus:
        """
        同步执行整个链条
        
        :param prev_result: 外部传入的初始结果（可选）
        :return: 最后一个任务的执行结果
        """
        # 确保存在工作流上下文（如果不存在则自动创建）
        created_new_ctx = _ensure_workflow_context()
        
        try:
            result = prev_result
            result_status = None
            
            for task in self.tasks:
                if isinstance(task, (Chain, Group, Chord)):
                    result_status = task.apply(prev_result=result)
                    result = result_status.result if isinstance(result_status, FunctionResultStatus) else result_status
                elif isinstance(task, Signature):
                    result_status = task.apply(prev_result=result)
                    result = result_status.result
                else:
                    raise TypeError(f"Unsupported task type: {type(task)}")
            
            return result_status
        finally:
            # 只有当本方法创建了上下文时才清理
            if created_new_ctx:
                WorkflowPublisherMixin.clear_workflow_context()
    
    def apply_async(self, prev_result=None) -> AsyncResult:
        """
        异步执行第一个任务，返回 AsyncResult
        
        注意：对于 Chain，完整的异步执行需要配合回调机制
        当前实现仅启动第一个任务
        """
        if not self.tasks:
            raise ValueError("Chain is empty")
        
        first_task = self.tasks[0]
        if isinstance(first_task, Signature):
            return first_task.apply_async(prev_result)
        else:
            raise NotImplementedError("Async chain with nested primitives not yet supported")
    
    def __or__(self, other):
        """支持 | 运算符追加任务"""
        if isinstance(other, Signature):
            return Chain(*self.tasks, other)
        elif isinstance(other, Chain):
            return Chain(*self.tasks, *other.tasks)
        else:
            raise TypeError(f"unsupported operand type(s) for |: 'Chain' and '{type(other).__name__}'")
    
    def __repr__(self):
        task_names = [repr(t) for t in self.tasks]
        return f"Chain({', '.join(task_names)})"


class Group:
    """
    并行执行：同时执行多个任务，收集所有结果
    
    用法：
    ```python
    # 方式1：构造函数
    g = Group(task.s(1), task.s(2), task.s(3))
    
    # 方式2：便捷函数
    g = group(task.s(1), task.s(2), task.s(3))
    
    # 方式3：生成器
    g = group(task.s(i) for i in range(10))
    
    # 执行
    results = g.apply()  # 返回结果列表 [r1, r2, r3]
    ```
    """
    
    def __init__(self, *tasks):
        """
        :param tasks: 任务列表，支持生成器
        """
        # 支持传入生成器
        if len(tasks) == 1 and hasattr(tasks[0], '__iter__') and not isinstance(tasks[0], (Signature, Chain, Chord)):
            self.tasks = list(tasks[0])
        else:
            self.tasks = list(tasks)
    
    def apply(self, prev_result=None) -> typing.List:
        """
        并行执行所有任务，等待全部完成
        
        :param prev_result: 传递给每个任务的初始结果（可选）
        :return: 所有任务结果的列表
        """
        if not self.tasks:
            return []
        
        # 确保存在工作流上下文（如果不存在则自动创建）
        created_new_ctx = _ensure_workflow_context()
        
        try:
            # 并行发布所有任务
            async_results = []
            for task in self.tasks:
                if isinstance(task, Signature):
                    async_results.append(task.apply_async(prev_result))
                elif isinstance(task, (Chain, Group, Chord)):
                    # 对于嵌套结构，同步执行（简化实现）
                    result = task.apply(prev_result)
                    # 包装成类似 AsyncResult 的结构以统一处理
                    async_results.append(_WrapperResult(result))
                else:
                    raise TypeError(f"Unsupported task type: {type(task)}")
            
            # 等待所有结果
            results = []
            last_task_id = None
            for ar in async_results:
                if isinstance(ar, _WrapperResult):
                    results.append(ar.result)
                else:
                    # AsyncResult
                    status = ar.wait_rpc_data_or_raise(raise_exception=True)
                    results.append(status.result)
                    last_task_id = status.task_id
            
            # Group 完成后更新 workflow context
            # 使用最后一个任务的 task_id 作为 current_task_id，
            # 这样 chord callback 的 parent_task_id 能指向 group 中的某个任务
            # 注意：_update_workflow_context_after_task 会同时递增 chain_depth
            if last_task_id:
                from .signature import _update_workflow_context_after_task
                _update_workflow_context_after_task(last_task_id)
            
            return results
        finally:
            # 只有当本方法创建了上下文时才清理
            if created_new_ctx:
                WorkflowPublisherMixin.clear_workflow_context()
    
    def apply_async(self, prev_result=None) -> typing.List[AsyncResult]:
        """
        异步发布所有任务
        
        :return: AsyncResult 列表
        """
        async_results = []
        for task in self.tasks:
            if isinstance(task, Signature):
                async_results.append(task.apply_async(prev_result))
            else:
                raise NotImplementedError("Async group with nested primitives not yet supported")
        return async_results
    
    def __repr__(self):
        return f"Group({len(self.tasks)} tasks)"


class _WrapperResult:
    """用于包装同步执行结果的辅助类"""
    def __init__(self, result):
        if isinstance(result, FunctionResultStatus):
            self.result = result.result
        else:
            self.result = result


class Chord:
    """
    并行 + 汇总：header 并行执行，结果列表传给 body
    
    用法：
    ```python
    # 定义 chord
    c = chord(
        group(task.s(i) for i in range(3)),  # header: 并行执行
        callback.s()  # body: 接收结果列表
    )
    
    # 执行
    result = c.apply()
    ```
    
    执行流程：
    1. 并行执行 header 中的所有任务
    2. 收集所有结果到列表 [r0, r1, r2]
    3. 将结果列表作为 body 的第一个参数执行
    4. 返回 body 的执行结果
    """
    
    def __init__(self, header: Group, body: Signature):
        """
        :param header: 并行执行的任务组 (Group)
        :param body: 汇总回调任务 (Signature)
        """
        if not isinstance(header, Group):
            # 自动包装成 Group
            if isinstance(header, (list, tuple)):
                header = Group(*header)
            else:
                raise TypeError(f"header must be a Group, got {type(header)}")
        
        self.header = header
        self.body = body
    
    def apply(self, prev_result=None) -> FunctionResultStatus:
        """
        执行 chord
        
        :param prev_result: 传递给 header 每个任务的初始结果
        :return: body 任务的执行结果
        """
        # 确保存在工作流上下文（如果不存在则自动创建）
        created_new_ctx = _ensure_workflow_context()
        
        try:
            # 1. 执行 header（并行）
            header_results = self.header.apply(prev_result)
            
            # 2. 将 header 结果列表作为 body 的第一个参数执行
            return self.body.apply(prev_result=header_results)
        finally:
            # 只有当本方法创建了上下文时才清理
            if created_new_ctx:
                WorkflowPublisherMixin.clear_workflow_context()
    
    def __repr__(self):
        return f"Chord(header={self.header}, body={self.body})"


# ============================================================
# 便捷函数
# ============================================================

def chain(*tasks) -> Chain:
    """
    创建链式执行工作流
    
    用法：
    ```python
    workflow = chain(task1.s(x), task2.s(), task3.s())
    result = workflow.apply()
    ```
    """
    return Chain(*tasks)


def group(*tasks) -> Group:
    """
    创建并行执行工作流
    
    用法：
    ```python
    g = group(task.s(1), task.s(2), task.s(3))
    results = g.apply()  # [r1, r2, r3]
    
    # 支持生成器
    g = group(task.s(i) for i in range(10))
    ```
    """
    return Group(*tasks)


def chord(header, body) -> Chord:
    """
    创建 并行+汇总 工作流
    
    用法：
    ```python
    c = chord(
        group(task.s(i) for i in range(3)),
        callback.s()
    )
    result = c.apply()
    ```
    """
    if not isinstance(header, Group):
        header = Group(header) if not isinstance(header, (list, tuple)) else Group(*header)
    return Chord(header, body)

# -*- coding: utf-8 -*-
"""
Funboost Workflow - 声明式任务编排模块

提供类似 Celery Canvas 的声明式任务编排 API，让用户可以用简洁的语法定义工作流。

核心概念：
- Signature: 任务签名，表示一个待执行的任务及其参数
- Chain: 链式执行，顺序执行多个任务，上游结果自动传给下游
- Group: 并行执行，同时执行多个任务，收集所有结果
- Chord: 并行 + 汇总，header 并行执行，结果列表传给 body

用法示例：
```python
from funboost.workflow import chain, group, chord, WorkflowBoosterParams

@boost(WorkflowBoosterParams(queue_name='my_task'))
def my_task(x):
    return x * 2

# 定义工作流
workflow = chain(
    task1.s(input_data),
    group(task2.s(), task3.s()),
    task4.s()
)

# 执行
result = workflow.apply()
```

详细文档见 funboost/workflow/examples/
"""

from .signature import Signature, signature
from .primitives import Chain, Group, Chord, chain, group, chord
from .workflow_mixin import WorkflowPublisherMixin, WorkflowConsumerMixin
from .params import WorkflowBoosterParams


# ============================================================
# 猴子补丁：为 Booster 类添加 .s() 和 .si() 方法
# 这样所有 @boost 装饰的消费函数自动拥有签名创建方法
# ============================================================

def _patch_booster_with_signature_methods():
    """
    为 Booster 类打补丁，添加 .s() 和 .si() 方法
    
    这样用户无需手动为每个 booster 添加 .s() 方法：
    
    Before (需要手动添加):
        download_video.s = lambda *args, **kw: Signature(download_video, args, kw)
    
    After (自动拥有):
        sig = download_video.s(url)  # 直接可用
    """
    from funboost.core.booster import Booster
    
    def s(self, *args, **kwargs) -> Signature:
        """
        创建任务签名（类似 Celery 的 .s() 方法）
        
        用法：
            sig = my_task.s(1, 2, name='test')
            workflow = chain(task1.s(), task2.s())
        """
        return Signature(self, args, kwargs, immutable=False)
    
    def si(self, *args, **kwargs) -> Signature:
        """
        创建不可变任务签名（忽略上游结果）
        
        在 chain 中使用时，不会将上游任务的结果作为第一个参数传入。
        
        用法：
            sig = my_task.si(1, 2)  # 忽略上游结果
        """
        return Signature(self, args, kwargs, immutable=True)
    
    # 打补丁
    Booster.s = s
    Booster.si = si


# 模块导入时自动执行补丁
_patch_booster_with_signature_methods()


__all__ = [
    # Signature
    'Signature',
    'signature',
    
    # Primitives
    'Chain',
    'Group', 
    'Chord',
    'chain',
    'group',
    'chord',
    
    # Mixin
    'WorkflowPublisherMixin',
    'WorkflowConsumerMixin',
    
    # Params
    'WorkflowBoosterParams',
]

# -*- coding: utf-8 -*-
"""
Funboost Workflow - 预配置的 BoosterParams

提供 WorkflowBoosterParams，预配置了工作流编排所需的设置：
1. 启用 RPC 模式（工作流编排依赖 RPC 获取结果）
2. 注入 WorkflowPublisherMixin 和 WorkflowConsumerMixin

用法：
```python
from funboost import boost
from funboost.workflow import WorkflowBoosterParams

@boost(WorkflowBoosterParams(queue_name='my_task'))
def my_task(x):
    return x * 2
```
"""

import typing
from funboost.core.func_params_model import BoosterParams
from .workflow_mixin import WorkflowPublisherMixin, WorkflowConsumerMixin


class WorkflowBoosterParams(BoosterParams):
    """
    预配置了工作流编排支持的 BoosterParams
    
    特性：
    1. is_using_rpc_mode=True: 启用 RPC 模式，用于获取任务执行结果
    2. consumer_override_cls: WorkflowConsumerMixin，提取工作流上下文
    3. publisher_override_cls: WorkflowPublisherMixin，注入工作流上下文
    
    使用场景：
    - 需要使用 chain/group/chord 编排的任务
    - 需要在任务间传递上下文的场景
    
    示例：
    ```python
    @boost(WorkflowBoosterParams(queue_name='download_task'))
    def download(url):
        # ...
        return file_path
    
    @boost(WorkflowBoosterParams(queue_name='process_task'))
    def process(file_path):
        # ...
        return result
    
    # 工作流编排
    workflow = chain(download.s(url), process.s())
    result = workflow.apply()
    ```
    """
    
    # 启用 RPC 模式 - 工作流编排需要获取任务结果
    is_using_rpc_mode: bool = True
    
    # 注入 Mixin
    consumer_override_cls: typing.Type[WorkflowConsumerMixin] = WorkflowConsumerMixin
    publisher_override_cls: typing.Type[WorkflowPublisherMixin] = WorkflowPublisherMixin

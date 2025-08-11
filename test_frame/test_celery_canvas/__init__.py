"""Celery Canvas 复杂编排示例入口。

提供如下导出：
- app: Celery 应用实例
- FLOWS: 可运行编排流名称到函数的映射
- run_flow_by_name: 按名称运行某个编排流
"""

from .celery_app import app
from .flows import FLOWS, run_flow_by_name

__all__ = ["app", "FLOWS", "run_flow_by_name"]



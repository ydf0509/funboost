# -*- coding: utf-8 -*-
"""
CLI 模块 - Funboost Web Manager 命令行工具

支持通过 python -m funboost.funboost_web_manager.cli 方式调用
"""

__version__ = "1.0.0"

from .main import main

__all__ = ['main', '__version__']

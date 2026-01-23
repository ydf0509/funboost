# -*- coding: utf-8 -*-
"""
模块导入测试

**Property 2: 模块导入成功性**
**Validates: Requirements 2.4**

For any 模块在 CLI_Module 中，通过 importlib.import_module() 导入该模块
应该成功且不抛出 ImportError 或 ModuleNotFoundError。
"""

import importlib
import pytest
from hypothesis import given, strategies as st, settings


# CLI 模块列表
CLI_MODULES = [
    'funboost.funboost_web_manager.cli',
    'funboost.funboost_web_manager.cli.main',
    'funboost.funboost_web_manager.cli.utils',
    'funboost.funboost_web_manager.cli.utils.console',
    'funboost.funboost_web_manager.cli.utils.platform',
    'funboost.funboost_web_manager.cli.utils.process',
    'funboost.funboost_web_manager.cli.utils.network',
    'funboost.funboost_web_manager.cli.utils.config',
    'funboost.funboost_web_manager.cli.commands',
    'funboost.funboost_web_manager.cli.commands.db',
    'funboost.funboost_web_manager.cli.commands.user',
    'funboost.funboost_web_manager.cli.commands.service',
    'funboost.funboost_web_manager.cli.commands.init',
]


class TestModuleImports:
    """模块导入测试类
    
    **Feature: cli-migration, Property 2: 模块导入成功性**
    """
    
    @pytest.mark.parametrize('module_name', CLI_MODULES)
    def test_module_import_success(self, module_name: str):
        """测试每个模块都能成功导入
        
        **Validates: Requirements 2.4**
        """
        try:
            module = importlib.import_module(module_name)
            assert module is not None
        except (ImportError, ModuleNotFoundError) as e:
            pytest.fail(f"Failed to import {module_name}: {e}")
    
    def test_cli_version_exists(self):
        """测试 CLI 模块有版本号"""
        from funboost.funboost_web_manager.cli import __version__
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0
    
    def test_cli_main_function_exists(self):
        """测试 CLI 模块有 main 函数"""
        from funboost.funboost_web_manager.cli import main
        assert main is not None
        assert callable(main)
    
    def test_utils_exports(self):
        """测试 utils 模块导出所有工具类"""
        from funboost.funboost_web_manager.cli.utils import (
            Console, Colors, Platform, ProcessManager, 
            NetworkChecker, ConfigManager, get_config_manager
        )
        
        assert Console is not None
        assert Colors is not None
        assert Platform is not None
        assert ProcessManager is not None
        assert NetworkChecker is not None
        assert ConfigManager is not None
        assert get_config_manager is not None
    
    def test_commands_exports(self):
        """测试 commands 模块导出所有命令类"""
        from funboost.funboost_web_manager.cli.commands import (
            DbCommand, UserCommand, ServiceCommand, InitCommand
        )
        
        assert DbCommand is not None
        assert UserCommand is not None
        assert ServiceCommand is not None
        assert InitCommand is not None


@given(module_idx=st.integers(min_value=0, max_value=len(CLI_MODULES) - 1))
@settings(max_examples=100)
def test_property_module_import_success(module_idx: int):
    """属性测试：任意模块都能成功导入
    
    **Feature: cli-migration, Property 2: 模块导入成功性**
    **Validates: Requirements 2.4**
    """
    module_name = CLI_MODULES[module_idx]
    try:
        module = importlib.import_module(module_name)
        assert module is not None
    except (ImportError, ModuleNotFoundError) as e:
        pytest.fail(f"Failed to import {module_name}: {e}")

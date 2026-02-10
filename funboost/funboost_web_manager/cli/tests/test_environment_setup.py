# -*- coding: utf-8 -*-
"""
测试环境验证

验证测试环境是否正确配置，包括：
- Python 版本
- 必需的依赖包
- Flask 应用可以导入
- 测试框架可用
"""

import sys
import pytest


class TestEnvironmentSetup:
    """测试环境设置验证"""
    
    def test_python_version(self):
        """验证 Python 版本 >= 3.7"""
        assert sys.version_info >= (3, 7), \
            f"Python version {sys.version_info} is too old, need >= 3.7"
    
    def test_pytest_available(self):
        """验证 pytest 可用"""
        import pytest
        assert pytest.__version__ is not None
    
    def test_hypothesis_available(self):
        """验证 hypothesis 可用"""
        import hypothesis
        assert hypothesis.__version__ is not None
    
    def test_flask_available(self):
        """验证 Flask 及相关包可用"""
        import flask
        import flask_login
        import flask_bootstrap
        
        assert flask.__version__ is not None
        assert flask_login.__version__ is not None
    
    def test_sqlalchemy_available(self):
        """验证 SQLAlchemy 可用"""
        import sqlalchemy
        assert sqlalchemy.__version__ is not None
    
    def test_funboost_importable(self):
        """验证 funboost 核心模块可导入"""
        import funboost
        from funboost.core.booster import boost
        from funboost.constant import BrokerEnum
        
        assert funboost.__version__ is not None
    
    def test_web_manager_app_importable(self):
        """验证 Web Manager 应用可导入"""
        from funboost.funboost_web_manager.app import app
        
        assert app is not None
        assert app.name == 'funboost_web_manager'
    
    def test_faas_blueprint_importable(self):
        """验证 FaaS blueprint 可导入"""
        from funboost.faas import flask_blueprint
        
        assert flask_blueprint is not None
        assert flask_blueprint.name == 'funboost'
    
    def test_web_manager_models_importable(self):
        """验证 Web Manager 模型可导入"""
        from funboost.funboost_web_manager.models import User, Role, Permission
        
        assert User is not None
        assert Role is not None
        assert Permission is not None
    
    def test_web_manager_services_importable(self):
        """验证 Web Manager 服务可导入"""
        from funboost.funboost_web_manager.services import (
            AuthService,
            PermissionService,
            ProjectService
        )
        
        assert AuthService is not None
        assert PermissionService is not None
        assert ProjectService is not None


class TestDependencyVersions:
    """依赖版本检查"""
    
    def test_flask_version(self):
        """验证 Flask 版本"""
        import flask
        major_version = int(flask.__version__.split('.')[0])
        assert major_version >= 2, f"Flask version {flask.__version__} is too old"
    
    def test_pytest_version(self):
        """验证 pytest 版本"""
        import pytest
        major_version = int(pytest.__version__.split('.')[0])
        assert major_version >= 7, f"pytest version {pytest.__version__} is too old"
    
    def test_hypothesis_version(self):
        """验证 hypothesis 版本"""
        import hypothesis
        major_version = int(hypothesis.__version__.split('.')[0])
        assert major_version >= 6, f"hypothesis version {hypothesis.__version__} is too old"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

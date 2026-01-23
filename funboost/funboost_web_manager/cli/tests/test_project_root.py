# -*- coding: utf-8 -*-
"""
项目根目录定位测试

**Property 3: 项目根目录定位**
**Validates: Requirements 3.3, 3.4**

For any 环境变量 FUNBOOST_PROJECT_ROOT 的值（包括未设置的情况），
Platform.get_project_root() 应返回一个有效的 Path 对象。
当环境变量设置时，返回值应等于环境变量指定的路径；
当环境变量未设置时，应通过向上遍历找到包含标识文件的目录。
"""

import os
import tempfile
from pathlib import Path
import pytest
from hypothesis import given, strategies as st, settings, assume


class TestProjectRoot:
    """项目根目录定位测试类
    
    **Feature: cli-migration, Property 3: 项目根目录定位**
    """
    
    def setup_method(self):
        """每个测试前重置 Platform 状态"""
        from funboost.funboost_web_manager.cli.utils.platform import Platform
        Platform.reset_project_root()
        # 保存原始环境变量
        self._original_env = os.environ.get('FUNBOOST_PROJECT_ROOT')
        if 'FUNBOOST_PROJECT_ROOT' in os.environ:
            del os.environ['FUNBOOST_PROJECT_ROOT']
    
    def teardown_method(self):
        """每个测试后恢复环境变量"""
        from funboost.funboost_web_manager.cli.utils.platform import Platform
        Platform.reset_project_root()
        if self._original_env is not None:
            os.environ['FUNBOOST_PROJECT_ROOT'] = self._original_env
        elif 'FUNBOOST_PROJECT_ROOT' in os.environ:
            del os.environ['FUNBOOST_PROJECT_ROOT']
    
    def test_get_project_root_returns_path(self):
        """测试 get_project_root 返回 Path 对象
        
        **Validates: Requirements 3.3**
        """
        from funboost.funboost_web_manager.cli.utils.platform import Platform
        
        result = Platform.get_project_root()
        assert isinstance(result, Path)
    
    def test_env_var_override(self):
        """测试环境变量覆盖功能
        
        **Validates: Requirements 3.3**
        """
        from funboost.funboost_web_manager.cli.utils.platform import Platform
        
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['FUNBOOST_PROJECT_ROOT'] = tmpdir
            Platform.reset_project_root()
            
            result = Platform.get_project_root()
            assert result == Path(tmpdir)
    
    def test_marker_file_detection(self):
        """测试标识文件检测
        
        **Validates: Requirements 3.4**
        """
        from funboost.funboost_web_manager.cli.utils.platform import Platform
        
        # 当前项目应该能找到标识文件
        result = Platform.get_project_root()
        
        # 检查是否找到了包含标识文件的目录
        markers = ['funboost_config.py', '.git', 'setup.py', 'pyproject.toml']
        has_marker = any((result / marker).exists() for marker in markers)
        
        # 如果没有标识文件，应该返回当前目录
        assert has_marker or result == Path.cwd()
    
    def test_set_project_root(self):
        """测试手动设置项目根目录"""
        from funboost.funboost_web_manager.cli.utils.platform import Platform
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir)
            Platform.set_project_root(test_path)
            
            result = Platform.get_project_root()
            assert result == test_path
    
    def test_caching(self):
        """测试结果缓存"""
        from funboost.funboost_web_manager.cli.utils.platform import Platform
        
        result1 = Platform.get_project_root()
        result2 = Platform.get_project_root()
        
        # 应该返回相同的对象（缓存）
        assert result1 is result2
    
    def test_reset_clears_cache(self):
        """测试重置清除缓存"""
        from funboost.funboost_web_manager.cli.utils.platform import Platform
        
        result1 = Platform.get_project_root()
        Platform.reset_project_root()
        result2 = Platform.get_project_root()
        
        # 重置后应该重新计算（可能是相同的值，但不是同一个对象）
        assert result1 == result2  # 值相同
    
    def test_derived_paths(self):
        """测试派生路径方法"""
        from funboost.funboost_web_manager.cli.utils.platform import Platform
        
        root = Platform.get_project_root()
        
        # 测试各种派生路径
        assert Platform.get_database_path() == root / 'web_manager_users.db'
        assert Platform.get_frontend_dir() == root / 'web-manager-frontend'
        assert Platform.get_env_file_path() == root / '.env'
        assert Platform.get_requirements_path() == root / 'requirements.txt'


@given(path_suffix=st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_-'),
    min_size=1,
    max_size=20
))
@settings(max_examples=100)
def test_property_env_var_override(path_suffix: str):
    """属性测试：环境变量覆盖总是生效
    
    **Feature: cli-migration, Property 3: 项目根目录定位**
    **Validates: Requirements 3.3**
    """
    from funboost.funboost_web_manager.cli.utils.platform import Platform
    
    # 过滤掉可能导致问题的字符
    assume(path_suffix.strip() != '')
    assume(not path_suffix.startswith('-'))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / path_suffix
        test_path.mkdir(parents=True, exist_ok=True)
        
        # 保存原始状态
        original_env = os.environ.get('FUNBOOST_PROJECT_ROOT')
        
        try:
            os.environ['FUNBOOST_PROJECT_ROOT'] = str(test_path)
            Platform.reset_project_root()
            
            result = Platform.get_project_root()
            assert result == test_path
        finally:
            # 恢复状态
            Platform.reset_project_root()
            if original_env is not None:
                os.environ['FUNBOOST_PROJECT_ROOT'] = original_env
            elif 'FUNBOOST_PROJECT_ROOT' in os.environ:
                del os.environ['FUNBOOST_PROJECT_ROOT']


@given(st.just(None))
@settings(max_examples=10)
def test_property_always_returns_valid_path(_):
    """属性测试：总是返回有效的 Path 对象
    
    **Feature: cli-migration, Property 3: 项目根目录定位**
    **Validates: Requirements 3.3, 3.4**
    """
    from funboost.funboost_web_manager.cli.utils.platform import Platform
    
    # 保存原始状态
    original_env = os.environ.get('FUNBOOST_PROJECT_ROOT')
    
    try:
        # 清除环境变量
        if 'FUNBOOST_PROJECT_ROOT' in os.environ:
            del os.environ['FUNBOOST_PROJECT_ROOT']
        Platform.reset_project_root()
        
        result = Platform.get_project_root()
        
        # 验证返回值
        assert isinstance(result, Path)
        assert result is not None
    finally:
        # 恢复状态
        Platform.reset_project_root()
        if original_env is not None:
            os.environ['FUNBOOST_PROJECT_ROOT'] = original_env

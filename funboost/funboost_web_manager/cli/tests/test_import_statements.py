# -*- coding: utf-8 -*-
"""
导入语句检查测试

**Property 1: 导入语句正确性**
**Validates: Requirements 2.1, 2.2, 2.3**

For any Python 文件在 CLI_Module 中，该文件不应包含 sys.path.insert 或 
sys.path.append 语句，且所有导入语句应使用相对导入（以 . 开头）或基于 
funboost 的绝对导入。
"""

import ast
import re
from pathlib import Path
import pytest
from hypothesis import given, strategies as st, settings


# CLI 模块目录
CLI_DIR = Path(__file__).parent.parent


def get_python_files() -> list:
    """获取 CLI 模块中的所有 Python 文件"""
    files = []
    for py_file in CLI_DIR.rglob('*.py'):
        # 排除测试文件和 __pycache__
        if '__pycache__' not in str(py_file) and 'tests' not in str(py_file):
            files.append(py_file)
    return files


PYTHON_FILES = get_python_files()


class TestImportStatements:
    """导入语句检查测试类
    
    **Feature: cli-migration, Property 1: 导入语句正确性**
    """
    
    @pytest.mark.parametrize('py_file', PYTHON_FILES, ids=lambda f: f.name)
    def test_no_sys_path_manipulation(self, py_file: Path):
        """测试文件不包含 sys.path 操作
        
        **Validates: Requirements 2.3**
        """
        content = py_file.read_text(encoding='utf-8')
        
        # 检查 sys.path.insert
        assert 'sys.path.insert' not in content, \
            f"{py_file.name} contains sys.path.insert"
        
        # 检查 sys.path.append
        assert 'sys.path.append' not in content, \
            f"{py_file.name} contains sys.path.append"
    
    @pytest.mark.parametrize('py_file', PYTHON_FILES, ids=lambda f: f.name)
    def test_valid_import_paths(self, py_file: Path):
        """测试导入路径有效性
        
        **Validates: Requirements 2.1, 2.2**
        """
        content = py_file.read_text(encoding='utf-8')
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            pytest.fail(f"Syntax error in {py_file.name}")
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # 标准库和第三方库导入是允许的
                    # 只检查不是以 scripts.cli 开头（旧路径）
                    assert not alias.name.startswith('scripts.cli'), \
                        f"{py_file.name} imports from old path: {alias.name}"
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # 相对导入是允许的（level > 0）
                    if node.level > 0:
                        continue
                    
                    # 绝对导入应该是 funboost 开头或标准库
                    # 不应该是 scripts.cli 开头
                    assert not node.module.startswith('scripts.cli'), \
                        f"{py_file.name} imports from old path: {node.module}"
    
    def test_all_files_have_encoding_declaration(self):
        """测试所有文件都有编码声明"""
        for py_file in PYTHON_FILES:
            content = py_file.read_text(encoding='utf-8')
            first_lines = content.split('\n')[:2]
            has_encoding = any('coding' in line for line in first_lines)
            assert has_encoding, f"{py_file.name} missing encoding declaration"


def check_file_imports(py_file: Path) -> tuple:
    """检查单个文件的导入语句
    
    Returns:
        (has_sys_path_manipulation, has_old_imports)
    """
    content = py_file.read_text(encoding='utf-8')
    
    has_sys_path = 'sys.path.insert' in content or 'sys.path.append' in content
    has_old_imports = 'scripts.cli' in content
    
    return has_sys_path, has_old_imports


@given(file_idx=st.integers(min_value=0, max_value=max(0, len(PYTHON_FILES) - 1)))
@settings(max_examples=100)
def test_property_import_correctness(file_idx: int):
    """属性测试：任意文件的导入语句都正确
    
    **Feature: cli-migration, Property 1: 导入语句正确性**
    **Validates: Requirements 2.1, 2.2, 2.3**
    """
    if not PYTHON_FILES:
        pytest.skip("No Python files found")
    
    py_file = PYTHON_FILES[file_idx]
    has_sys_path, has_old_imports = check_file_imports(py_file)
    
    assert not has_sys_path, f"{py_file.name} contains sys.path manipulation"
    assert not has_old_imports, f"{py_file.name} imports from old scripts.cli path"

# -*- coding: utf-8 -*-
"""
权限代码解析器模块

提供权限代码的解析和构建功能，支持扩展的权限代码格式：
- module:action (如 user:read)
- module:submodule:action (如 user:role:assign)
- project:module:action (如 projectA:queue:read)
- project:module:submodule:action (如 projectA:queue:task:create)

Requirements:
- 4.1: 支持 [project:]module[:submodule]:action 格式
- 4.2: 解析时提取 project, module, submodule, action
- 4.3: 验证权限代码至少包含两段 (module:action)
- 4.4: 包含项目前缀时使用其作为 project_scope
- 4.5: 向后兼容现有 module:action 格式
"""

from dataclasses import dataclass
from typing import Optional
import re


# 标准操作类型，用于判断三段格式是 project:module:action 还是 module:submodule:action
STANDARD_ACTION_TYPES = frozenset({
    'create', 'read', 'update', 'delete', 'execute', 'export'
})


@dataclass
class ParsedPermissionCode:
    """解析后的权限代码
    
    Attributes:
        project: 项目作用域（可选）
        module: 模块名称
        submodule: 子模块名称（可选）
        action: 操作类型
        raw_code: 原始权限代码字符串
    """
    project: Optional[str]      # 项目作用域
    module: str                 # 模块
    submodule: Optional[str]    # 子模块
    action: str                 # 操作
    raw_code: str               # 原始代码
    
    def to_dict(self) -> dict:
        """转换为字典格式
        
        Returns:
            dict: 包含所有字段的字典
        """
        return {
            'project': self.project,
            'module': self.module,
            'submodule': self.submodule,
            'action': self.action,
            'raw_code': self.raw_code
        }


class PermissionCodeParser:
    """权限代码解析器
    
    支持格式：
    - module:action (如 user:read)
    - module:submodule:action (如 user:role:assign)
    - project:module:action (如 projectA:queue:read)
    - project:module:submodule:action (如 projectA:queue:task:create)
    
    解析规则：
    - 两段格式：module:action
    - 三段格式：如果最后一段是标准操作类型，则为 project:module:action
                否则为 module:submodule:action
    - 四段格式：project:module:submodule:action
    
    Requirements:
    - 4.1: 支持 [project:]module[:submodule]:action 格式
    - 4.2: 解析时提取 project, module, submodule, action
    - 4.3: 验证权限代码至少包含两段 (module:action)
    - 4.4: 包含项目前缀时使用其作为 project_scope
    - 4.5: 向后兼容现有 module:action 格式
    """
    
    # 权限代码正则：至少两段，最多四段
    # 每段只允许字母、数字、下划线和连字符
    PATTERN = re.compile(
        r'^([a-zA-Z0-9_-]+):([a-zA-Z0-9_-]+)(?::([a-zA-Z0-9_-]+))?(?::([a-zA-Z0-9_-]+))?$'
    )
    
    # 单段验证正则
    SEGMENT_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    
    @classmethod
    def parse(cls, code: str) -> ParsedPermissionCode:
        """解析权限代码
        
        将权限代码字符串解析为结构化的 ParsedPermissionCode 对象。
        
        Args:
            code: 权限代码字符串，格式为 [project:]module[:submodule]:action
            
        Returns:
            ParsedPermissionCode: 解析后的权限代码对象
            
        Raises:
            ValueError: 当权限代码格式无效时
            
        Examples:
            >>> PermissionCodeParser.parse('user:read')
            ParsedPermissionCode(project=None, module='user', submodule=None, action='read', raw_code='user:read')
            
            >>> PermissionCodeParser.parse('user:role:assign')
            ParsedPermissionCode(project=None, module='user', submodule='role', action='assign', raw_code='user:role:assign')
            
            >>> PermissionCodeParser.parse('projectA:queue:read')
            ParsedPermissionCode(project='projectA', module='queue', submodule=None, action='read', raw_code='projectA:queue:read')
            
            >>> PermissionCodeParser.parse('projectA:queue:task:create')
            ParsedPermissionCode(project='projectA', module='queue', submodule='task', action='create', raw_code='projectA:queue:task:create')
        """
        if not code or not isinstance(code, str):
            raise ValueError(f"Invalid permission code format: {code}")
        
        # 去除首尾空白
        code = code.strip()
        
        match = cls.PATTERN.match(code)
        if not match:
            raise ValueError(f"Invalid permission code format: {code}")
        
        # 提取非空的匹配组
        parts = [p for p in match.groups() if p]
        
        if len(parts) == 2:
            # module:action 格式
            # Requirement 4.5: 向后兼容现有 module:action 格式
            return ParsedPermissionCode(
                project=None,
                module=parts[0],
                submodule=None,
                action=parts[1],
                raw_code=code
            )
        elif len(parts) == 3:
            # 三段格式：需要判断是 project:module:action 还是 module:submodule:action
            # 判断规则：如果最后一段是标准操作类型，则为 project:module:action
            #          否则为 module:submodule:action
            if parts[2] in STANDARD_ACTION_TYPES:
                # project:module:action 格式
                # Requirement 4.4: 包含项目前缀时使用其作为 project_scope
                return ParsedPermissionCode(
                    project=parts[0],
                    module=parts[1],
                    submodule=None,
                    action=parts[2],
                    raw_code=code
                )
            else:
                # module:submodule:action 格式
                return ParsedPermissionCode(
                    project=None,
                    module=parts[0],
                    submodule=parts[1],
                    action=parts[2],
                    raw_code=code
                )
        elif len(parts) == 4:
            # project:module:submodule:action 格式
            return ParsedPermissionCode(
                project=parts[0],
                module=parts[1],
                submodule=parts[2],
                action=parts[3],
                raw_code=code
            )
        
        # Requirement 4.3: 验证权限代码至少包含两段
        raise ValueError(f"Invalid permission code format: {code}")
    
    @classmethod
    def build(cls, module: str, action: str, 
              submodule: Optional[str] = None, 
              project: Optional[str] = None) -> str:
        """构建权限代码
        
        根据提供的组件构建权限代码字符串。
        
        Args:
            module: 模块名称（必需）
            action: 操作类型（必需）
            submodule: 子模块名称（可选）
            project: 项目作用域（可选）
            
        Returns:
            str: 构建的权限代码字符串
            
        Raises:
            ValueError: 当 module 或 action 为空或包含无效字符时
            
        Examples:
            >>> PermissionCodeParser.build('user', 'read')
            'user:read'
            
            >>> PermissionCodeParser.build('user', 'assign', submodule='role')
            'user:role:assign'
            
            >>> PermissionCodeParser.build('queue', 'read', project='projectA')
            'projectA:queue:read'
            
            >>> PermissionCodeParser.build('queue', 'create', submodule='task', project='projectA')
            'projectA:queue:task:create'
        """
        # 验证必需参数
        if not module or not isinstance(module, str):
            raise ValueError("Module is required and must be a non-empty string")
        if not action or not isinstance(action, str):
            raise ValueError("Action is required and must be a non-empty string")
        
        # 去除空白
        module = module.strip()
        action = action.strip()
        
        # 验证格式
        if not cls.SEGMENT_PATTERN.match(module):
            raise ValueError(f"Invalid module format: {module}")
        if not cls.SEGMENT_PATTERN.match(action):
            raise ValueError(f"Invalid action format: {action}")
        
        # 验证可选参数格式
        if submodule:
            submodule = submodule.strip()
            if not cls.SEGMENT_PATTERN.match(submodule):
                raise ValueError(f"Invalid submodule format: {submodule}")
        
        if project:
            project = project.strip()
            if not cls.SEGMENT_PATTERN.match(project):
                raise ValueError(f"Invalid project format: {project}")
        
        # 构建权限代码
        parts = []
        if project:
            parts.append(project)
        parts.append(module)
        if submodule:
            parts.append(submodule)
        parts.append(action)
        
        return ':'.join(parts)
    
    @classmethod
    def extract_action_type(cls, code: str) -> str:
        """从权限代码提取操作类型
        
        解析权限代码并返回其操作类型（action）部分。
        
        Args:
            code: 权限代码字符串
            
        Returns:
            str: 操作类型
            
        Raises:
            ValueError: 当权限代码格式无效时
            
        Examples:
            >>> PermissionCodeParser.extract_action_type('user:read')
            'read'
            
            >>> PermissionCodeParser.extract_action_type('user:role:assign')
            'assign'
            
            >>> PermissionCodeParser.extract_action_type('projectA:queue:task:create')
            'create'
        """
        parsed = cls.parse(code)
        return parsed.action
    
    @classmethod
    def extract_module(cls, code: str) -> str:
        """从权限代码提取模块名称
        
        解析权限代码并返回其模块（module）部分。
        
        Args:
            code: 权限代码字符串
            
        Returns:
            str: 模块名称
            
        Raises:
            ValueError: 当权限代码格式无效时
            
        Examples:
            >>> PermissionCodeParser.extract_module('user:read')
            'user'
            
            >>> PermissionCodeParser.extract_module('projectA:queue:read')
            'queue'
        """
        parsed = cls.parse(code)
        return parsed.module
    
    @classmethod
    def extract_project(cls, code: str) -> Optional[str]:
        """从权限代码提取项目作用域
        
        解析权限代码并返回其项目（project）部分。
        
        Args:
            code: 权限代码字符串
            
        Returns:
            Optional[str]: 项目作用域，如果没有则返回 None
            
        Raises:
            ValueError: 当权限代码格式无效时
            
        Examples:
            >>> PermissionCodeParser.extract_project('user:read')
            None
            
            >>> PermissionCodeParser.extract_project('projectA:queue:read')
            'projectA'
        """
        parsed = cls.parse(code)
        return parsed.project
    
    @classmethod
    def is_valid(cls, code: str) -> bool:
        """验证权限代码格式是否有效
        
        Args:
            code: 权限代码字符串
            
        Returns:
            bool: 格式是否有效
            
        Examples:
            >>> PermissionCodeParser.is_valid('user:read')
            True
            
            >>> PermissionCodeParser.is_valid('invalid')
            False
            
            >>> PermissionCodeParser.is_valid('user:role:assign')
            True
        """
        try:
            cls.parse(code)
            return True
        except ValueError:
            return False
    
    @classmethod
    def is_project_scoped(cls, code: str) -> bool:
        """检查权限代码是否包含项目作用域
        
        Args:
            code: 权限代码字符串
            
        Returns:
            bool: 是否包含项目作用域
            
        Raises:
            ValueError: 当权限代码格式无效时
            
        Examples:
            >>> PermissionCodeParser.is_project_scoped('user:read')
            False
            
            >>> PermissionCodeParser.is_project_scoped('projectA:queue:read')
            True
        """
        parsed = cls.parse(code)
        return parsed.project is not None
    
    @classmethod
    def has_submodule(cls, code: str) -> bool:
        """检查权限代码是否包含子模块
        
        Args:
            code: 权限代码字符串
            
        Returns:
            bool: 是否包含子模块
            
        Raises:
            ValueError: 当权限代码格式无效时
            
        Examples:
            >>> PermissionCodeParser.has_submodule('user:read')
            False
            
            >>> PermissionCodeParser.has_submodule('user:role:assign')
            True
        """
        parsed = cls.parse(code)
        return parsed.submodule is not None
    
    @classmethod
    def normalize(cls, code: str) -> str:
        """规范化权限代码
        
        解析并重新构建权限代码，确保格式一致。
        
        Args:
            code: 权限代码字符串
            
        Returns:
            str: 规范化后的权限代码
            
        Raises:
            ValueError: 当权限代码格式无效时
            
        Examples:
            >>> PermissionCodeParser.normalize('  user:read  ')
            'user:read'
        """
        parsed = cls.parse(code)
        return cls.build(
            module=parsed.module,
            action=parsed.action,
            submodule=parsed.submodule,
            project=parsed.project
        )

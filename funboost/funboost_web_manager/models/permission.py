# -*- coding: utf-8 -*-
# @Author  : kiro
# @Time    : 2026/1/13
"""
权限模型模块

本模块定义权限系统的核心模型，包括权限、权限分类、权限模板和角色-权限关联表。

Models:
    - Permission: 权限模型，支持细粒度权限控制
    - PermissionCategory: 权限分类模型，支持多层级结构
    - PermissionTemplate: 权限模板模型，支持快速配置角色权限
    - role_permissions: 角色-权限多对多关联表

Dependencies:
    - models.base.Base: SQLAlchemy declarative base
    - models.enums.ACTION_TYPE_DISPLAY: 操作类型显示名称映射
    - Forward references to Role model
"""

from typing import Dict, Any

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table
from sqlalchemy.orm import relationship

from .base import Base, datetime
from .enums import ACTION_TYPE_DISPLAY


# 关联表：角色-权限多对多关系
role_permissions = Table('role_permissions', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class PermissionCategory(Base):
    """权限分类模型（增强版）
    
    支持多层级结构：通过 parent_code 实现子分类。
    用于将权限按功能模块分组，以树形结构展示。
    
    Attributes:
        id: 自增主键
        code: 分类代码，唯一 (e.g., 'user', 'role', 'queue')
        name: 分类名称 (e.g., '用户管理', '角色管理')
        description: 分类描述
        sort_order: 排序顺序，用于控制显示顺序
        icon: 图标（emoji 或图标类名）
        parent_code: 父分类代码，null 表示顶级分类
        created_at: 创建时间
        parent: 父分类（自引用关系）
        subcategories: 子分类列表（自引用关系）
        permissions: 该分类下的权限列表（一对多关系）
    """
    __tablename__ = 'permission_categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(64), nullable=False)
    description = Column(String(256), nullable=True)
    sort_order = Column(Integer, default=0)
    icon = Column(String(16), nullable=True)
    parent_code = Column(String(64), ForeignKey('permission_categories.code'), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # 自引用关系：子分类
    parent = relationship('PermissionCategory', remote_side=[code], backref='subcategories', foreign_keys=[parent_code])
    # 一对多关系：分类 -> 权限
    permissions = relationship('Permission', back_populates='category', order_by='Permission.sort_order')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'sort_order': self.sort_order,
            'icon': self.icon,
            'parent_code': self.parent_code,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def to_tree_dict(self) -> Dict[str, Any]:
        """转换为树形结构字典格式（包含子分类和权限列表）"""
        return {
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'sort_order': self.sort_order,
            'icon': self.icon,
            'parent_code': self.parent_code,
            'subcategories': [sub.to_tree_dict() for sub in self.subcategories] if self.subcategories else [],
            'permissions': [perm.to_dict() for perm in self.permissions] if self.permissions else []
        }
    
    def is_subcategory(self) -> bool:
        """判断是否为子分类（parent_code 非空）"""
        return self.parent_code is not None
    
    def __repr__(self) -> str:
        return f"<PermissionCategory(code='{self.code}', name='{self.name}', parent_code={self.parent_code!r})>"


class Permission(Base):
    """权限模型（增强版）
    
    支持细粒度权限控制，包括操作类型和项目作用域。
    
    Attributes:
        id: 自增主键
        code: 权限代码，唯一 (e.g., 'user:read', 'user:write', 'projectA:queue:task:create')
        name: 权限名称
        description: 权限描述
        category_code: 所属分类代码（外键）
        sort_order: 排序顺序，用于控制在分类内的显示顺序
        action_type: 操作类型 (create, read, update, delete, execute, export)，支持索引查询
        project_scope: 项目作用域，null 表示全局权限，非空表示项目特定权限
        roles: 拥有此权限的角色（多对多关系）
        category: 所属分类（多对一关系）
    """
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(128), unique=True, nullable=False, index=True)  # 扩展长度以支持更长的权限代码
    name = Column(String(128), nullable=False)
    description = Column(String(256), nullable=True)
    category_code = Column(String(64), ForeignKey('permission_categories.code'), nullable=True, index=True)
    sort_order = Column(Integer, default=0)
    
    # 新增字段：操作类型和项目作用域
    action_type = Column(String(32), nullable=True, index=True)  # create, read, update, delete, execute, export
    project_scope = Column(String(64), nullable=True, index=True)  # 项目作用域，null 表示全局
    
    # 多对多关系
    roles = relationship('Role', secondary=role_permissions, back_populates='permissions')
    # 多对一关系：权限 -> 分类
    category = relationship('PermissionCategory', back_populates='permissions')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            包含所有权限字段的字典，包括新增的 action_type 和 project_scope 字段
        """
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'category_code': self.category_code,
            'sort_order': self.sort_order,
            'action_type': self.action_type,
            'action_type_display': ACTION_TYPE_DISPLAY.get(self.action_type, self.action_type) if self.action_type else None,
            'project_scope': self.project_scope
        }
    
    def is_global(self) -> bool:
        """判断是否为全局权限（project_scope 为空）
        
        Returns:
            True 如果是全局权限，False 如果是项目特定权限
        """
        return self.project_scope is None
    
    def is_project_specific(self) -> bool:
        """判断是否为项目特定权限（project_scope 非空）
        
        Returns:
            True 如果是项目特定权限，False 如果是全局权限
        """
        return self.project_scope is not None
    
    def __repr__(self) -> str:
        return f"<Permission(code='{self.code}', name='{self.name}', action_type={self.action_type!r}, project_scope={self.project_scope!r})>"


class PermissionTemplate(Base):
    """权限模板模型
    
    用于快速配置角色权限，支持预定义模板和自定义模板。
    支持模板继承，子模板可以继承父模板的所有权限。
    
    预定义模板包括：
    - 只读用户 (readonly): 只有查看权限
    - 操作员 (operator): 查看和执行权限
    - 管理员 (admin): 所有权限
    - 项目管理员 (project_admin): 项目级别的所有权限
    
    Attributes:
        id: 自增主键
        code: 模板代码，唯一标识 (e.g., 'readonly', 'operator', 'admin')
        name: 模板名称 (e.g., '只读用户', '操作员', '管理员')
        description: 模板描述
        permissions: 权限代码列表，JSON 数组格式存储
        parent_template_code: 父模板代码，用于模板继承
        is_builtin: 是否为内置模板（内置模板不可删除）
        created_at: 创建时间
    """
    __tablename__ = 'permission_templates'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(64), nullable=False)
    description = Column(String(256), nullable=True)
    permissions = Column(Text, nullable=False)  # JSON array of permission codes
    parent_template_code = Column(String(64), nullable=True, index=True)  # 继承的父模板
    is_builtin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    def get_permissions(self) -> list:
        """获取模板包含的权限列表（不包含继承的权限）
        
        Returns:
            权限代码字符串列表，如果 permissions 为空则返回空列表
        """
        import json
        if not self.permissions:
            return []
        try:
            return json.loads(self.permissions)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def get_all_permissions(self, session) -> list:
        """获取包含继承的所有权限
        
        递归获取父模板的权限，合并后返回去重的权限列表。
        支持多级继承（如：管理员 extends 操作员 extends 只读用户）。
        
        Args:
            session: SQLAlchemy 数据库会话，用于查询父模板
            
        Returns:
            包含所有权限（含继承）的字符串列表，已去重
        """
        # 获取当前模板的权限
        perms = set(self.get_permissions())
        
        # 如果有父模板，递归获取父模板的权限
        if self.parent_template_code:
            parent = session.query(PermissionTemplate).filter_by(
                code=self.parent_template_code
            ).first()
            if parent:
                # 递归获取父模板的所有权限并合并
                perms.update(parent.get_all_permissions(session))
        
        return list(perms)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            包含所有模板字段的字典
        """
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'permissions': self.get_permissions(),
            'parent_template_code': self.parent_template_code,
            'is_builtin': self.is_builtin,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self) -> str:
        return f"<PermissionTemplate(code='{self.code}', name='{self.name}', builtin={self.is_builtin})>"

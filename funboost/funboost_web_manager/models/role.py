# -*- coding: utf-8 -*-
# @Author  : kiro
# @Time    : 2026/1/13
"""
Role model module.

This module defines the Role model and the user_roles association table
for the many-to-many relationship between users and roles.

Exports:
    - Role: Role model class with permissions and user associations
    - user_roles: Association table for user-role many-to-many relationship
"""

from datetime import datetime
from typing import Dict, Any

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship

from .base import Base


# 关联表：用户-角色多对多关系
user_roles = Table('user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('web_manager_users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)


class Role(Base):
    """角色模型
    
    Attributes:
        id: 自增主键
        name: 角色名称，唯一
        description: 角色描述
        is_builtin: 是否为内置角色（内置角色不可删除）
        created_at: 创建时间
        permissions: 角色权限（多对多关系）
        users: 拥有此角色的用户（多对多关系）
        projects: 角色关联的项目（多对多关系）
    """
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False)
    description = Column(String(256), nullable=True)
    is_builtin = Column(Boolean, default=False)  # 内置角色不可删除
    created_at = Column(DateTime, default=datetime.now)
    
    # 多对多关系
    permissions = relationship('Permission', secondary='role_permissions', back_populates='roles')
    users = relationship('WebManagerUser', secondary='user_roles', back_populates='roles')
    projects = relationship('Project', secondary='role_projects', back_populates='roles')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_builtin': self.is_builtin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'permissions': [perm.code for perm in self.permissions] if self.permissions else [],
            'projects': [{'id': p.id, 'code': p.code, 'name': p.name} for p in self.projects] if self.projects else []
        }
    
    def __repr__(self) -> str:
        return f"<Role(name='{self.name}', builtin={self.is_builtin})>"

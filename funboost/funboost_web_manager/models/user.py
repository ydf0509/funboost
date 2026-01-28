# -*- coding: utf-8 -*-
# @Author  : kiro
# @Time    : 2026/1/13
"""
User model module.

This module defines the WebManagerUser model for user authentication and management.

Exports:
    - WebManagerUser: User model class with authentication and profile information
"""

from datetime import datetime
from typing import Dict, Any

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship

from .base import Base


class WebManagerUser(Base):
    """Web Manager 用户模型
    
    Attributes:
        id: 自增主键
        user_name: 用户名，唯一索引
        password: 密码（支持 bcrypt 哈希和明文兼容）
        email: 邮箱地址
        status: 用户状态 (active, disabled, locked)
        force_password_change: 是否强制修改密码
        failed_login_count: 登录失败次数
        locked_until: 锁定到期时间
        created_at: 创建时间
        updated_at: 更新时间
        roles: 用户角色（多对多关系）
    """
    __tablename__ = 'web_manager_users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(64), unique=True, nullable=False, index=True)
    password = Column(String(128), nullable=False)
    email = Column(String(128), nullable=True)
    status = Column(String(20), default='active')  # active, disabled, locked
    force_password_change = Column(Boolean, default=False)
    failed_login_count = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 多对多关系：用户-角色
    roles = relationship('Role', secondary='user_roles', back_populates='users')
    
    # 一对多关系：用户 -> 用户项目关联
    user_projects = relationship('UserProject', back_populates='user', cascade='all, delete-orphan')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，保持与原有 users 列表格式兼容"""
        return {
            'id': self.id,  # 返回数据库主键，用于项目用户管理等功能
            'user_name': self.user_name,
            'password': self.password,
            'email': self.email,
            'status': self.status,
            'force_password_change': self.force_password_change,
            'failed_login_count': self.failed_login_count,
            'locked_until': self.locked_until.isoformat() if self.locked_until else None,
            'roles': [role.name for role in self.roles] if self.roles else []
        }
    
    def __repr__(self) -> str:
        return f"<WebManagerUser(user_name='{self.user_name}', status='{self.status}')>"

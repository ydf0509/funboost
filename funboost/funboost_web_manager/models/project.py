# -*- coding: utf-8 -*-
# @Author  : kiro
# @Time    : 2026/1/18
"""
Project models module.

This module contains project-related models for the Web Manager,
including projects and user-project associations.

Models:
    - Project: Project model for multi-project data isolation
    - UserProject: User-project association model with permission levels
    - role_projects: Association table for role-project many-to-many relationship

Dependencies:
    - models.base.Base: SQLAlchemy declarative base
    - Forward references to WebManagerUser and Role for relationships
"""

from datetime import datetime
from typing import Dict, Any

from .base import Base, Column, Integer, String, DateTime, ForeignKey, Table, UniqueConstraint
from sqlalchemy.orm import relationship


# 关联表：角色-项目多对多关系
role_projects = Table('role_projects', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('project_id', Integer, ForeignKey('projects.id'), primary_key=True)
)


class Project(Base):
    """项目模型
    
    用于实现多项目数据隔离，允许不同项目的队列数据相互独立。
    用户可以被分配特定项目的访问权限。
    
    Attributes:
        id: 自增主键
        name: 项目名称，唯一，用于显示
        code: 项目代码，唯一，用于权限标识（如 projectA:queue:read）
        description: 项目描述
        status: 项目状态 (active, archived)
        created_at: 创建时间
        updated_at: 更新时间
        user_projects: 用户-项目关联关系（一对多）
        roles: 关联的角色（多对多关系）
    
    Requirements:
        - US-1.1: 创建、编辑和删除项目
        - US-1.2: 为项目设置名称、描述和状态
    """
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False, index=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    description = Column(String(256), nullable=True)
    status = Column(String(20), default='active')  # active, archived
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 一对多关系：项目 -> 用户项目关联
    user_projects = relationship('UserProject', back_populates='project', cascade='all, delete-orphan')
    # 多对多关系：项目 -> 角色
    roles = relationship('Role', secondary=role_projects, back_populates='projects')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            包含所有项目字段的字典
        """
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def is_active(self) -> bool:
        """判断项目是否为活跃状态
        
        Returns:
            True 如果项目状态为 active，否则 False
        """
        return self.status == 'active'
    
    def is_archived(self) -> bool:
        """判断项目是否已归档
        
        Returns:
            True 如果项目状态为 archived，否则 False
        """
        return self.status == 'archived'
    
    def __repr__(self) -> str:
        return f"<Project(name='{self.name}', code='{self.code}', status='{self.status}')>"


class UserProject(Base):
    """用户-项目关联模型
    
    用于实现用户与项目的多对多关系，并记录用户在项目中的权限级别。
    支持细粒度的项目级权限控制。
    
    Attributes:
        id: 自增主键
        user_id: 用户ID（外键，关联 web_manager_users.id）
        project_id: 项目ID（外键，关联 projects.id）
        permission_level: 权限级别 (read, write, admin)
        created_at: 创建时间
        user: 关联的用户对象（多对一关系）
        project: 关联的项目对象（多对一关系）
    
    唯一约束:
        (user_id, project_id) - 确保每个用户在每个项目中只有一条记录
    
    Requirements:
        - US-2.1: 将用户分配到特定项目
        - US-2.2: 为用户设置项目级别的权限
    """
    __tablename__ = 'user_projects'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('web_manager_users.id'), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True)
    permission_level = Column(String(20), default='read', nullable=False)  # read, write, admin
    created_at = Column(DateTime, default=datetime.now)
    
    # 唯一约束：确保每个用户在每个项目中只有一条记录
    __table_args__ = (
        UniqueConstraint('user_id', 'project_id', name='uq_user_project'),
    )
    
    # 多对一关系
    user = relationship('WebManagerUser', back_populates='user_projects')
    project = relationship('Project', back_populates='user_projects')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            包含所有字段的字典，包括关联的用户名和项目名
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'project_id': self.project_id,
            'permission_level': self.permission_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_name': self.user.user_name if self.user else None,
            'project_name': self.project.name if self.project else None,
            'project_code': self.project.code if self.project else None
        }
    
    def has_read_access(self) -> bool:
        """判断是否有读取权限
        
        Returns:
            True 如果权限级别为 read、write 或 admin
        """
        return self.permission_level in ('read', 'write', 'admin')
    
    def has_write_access(self) -> bool:
        """判断是否有写入权限
        
        Returns:
            True 如果权限级别为 write 或 admin
        """
        return self.permission_level in ('write', 'admin')
    
    def has_admin_access(self) -> bool:
        """判断是否有管理权限
        
        Returns:
            True 如果权限级别为 admin
        """
        return self.permission_level == 'admin'
    
    def __repr__(self) -> str:
        return f"<UserProject(user_id={self.user_id}, project_id={self.project_id}, level='{self.permission_level}')>"

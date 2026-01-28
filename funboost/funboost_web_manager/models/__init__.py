# -*- coding: utf-8 -*-
# @Author  : kiro
# @Time    : 2026/1/18
"""
Models package for Web Manager.

This package contains all ORM models for the Web Manager application,
organized by domain for better maintainability.

Modules:
    - base: SQLAlchemy declarative base and common imports
    - enums: Enums and constant mappings
    - user: User model
    - role: Role model and user_roles association table
    - permission: Permission models and role_permissions association table
    - audit: Audit and logging models
    - security: Security-related models
    - config: Configuration models
    - project: Project models and role_projects association table

Usage:
    # Import models directly from the package
    from funboost.funboost_web_manager.models import WebManagerUser, Role, Permission
    
    # Import association tables
    from funboost.funboost_web_manager.models import user_roles, role_permissions, role_projects
    
    # Import enums and constants
    from funboost.funboost_web_manager.models import ActionType, ACTION_TYPE_DISPLAY
"""

# Import base
from .base import Base

# Import enums and constants
from .enums import ActionType, ACTION_TYPE_DISPLAY

# Import models
from .user import WebManagerUser
from .role import Role, user_roles
from .permission import (
    Permission,
    PermissionCategory,
    PermissionTemplate,
    role_permissions
)
from .audit import LoginAttempt, AuditLog
from .security import PasswordResetToken
from .config import EmailConfig, SystemConfig
from .project import Project, UserProject, role_projects

# Define __all__ for explicit exports
__all__ = [
    # Base
    'Base',
    
    # Enums and constants
    'ActionType',
    'ACTION_TYPE_DISPLAY',
    
    # User models
    'WebManagerUser',
    
    # Role models
    'Role',
    'user_roles',
    
    # Permission models
    'Permission',
    'PermissionCategory',
    'PermissionTemplate',
    'role_permissions',
    
    # Audit models
    'LoginAttempt',
    'AuditLog',
    
    # Security models
    'PasswordResetToken',
    
    # Config models
    'EmailConfig',
    'SystemConfig',
    
    # Project models
    'Project',
    'UserProject',
    'role_projects',
]

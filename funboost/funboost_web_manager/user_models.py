# -*- coding: utf-8 -*-
"""
Web Manager 用户数据模型模块 (Compatibility Layer)

本模块已重构为多个子模块以提高可维护性。
为保持向后兼容，所有原有的导出仍然可用。

新代码建议直接从子模块导入：
from funboost.funboost_web_manager.models import WebManagerUser, Role, Permission
from funboost.funboost_web_manager.database import get_session, init_db

旧代码可以继续使用（向后兼容）：
from funboost.funboost_web_manager.user_models import WebManagerUser, get_session
"""

# 重新导出所有模型
from .models import (
    Base, ActionType, ACTION_TYPE_DISPLAY,
    WebManagerUser, Role, user_roles,
    Permission, PermissionCategory, PermissionTemplate, role_permissions,
    LoginAttempt, AuditLog, PasswordResetToken,
    EmailConfig, SystemConfig, Project, UserProject, role_projects,
)

# 重新导出数据库函数
from .database import get_db_url, get_engine, get_session, reset_engine, init_db

# 重新导出查询函数
from .queries import query_user_by_name, query_user_by_id, add_user, count_users

# 重新导出初始化函数和常量
from .initialization import (
    init_default_users, migrate_database,
    DEFAULT_PERMISSION_CATEGORIES, DEFAULT_PERMISSIONS, DEFAULT_PERMISSION_TEMPLATES
)

__all__ = [
    'Base', 'ActionType', 'ACTION_TYPE_DISPLAY',
    'WebManagerUser', 'Role', 'user_roles',
    'Permission', 'PermissionCategory', 'PermissionTemplate', 'role_permissions',
    'LoginAttempt', 'AuditLog', 'PasswordResetToken',
    'EmailConfig', 'SystemConfig', 'Project', 'UserProject', 'role_projects',
    'get_db_url', 'get_engine', 'get_session', 'reset_engine', 'init_db',
    'init_default_users', 'migrate_database',
    'DEFAULT_PERMISSION_CATEGORIES', 'DEFAULT_PERMISSIONS', 'DEFAULT_PERMISSION_TEMPLATES',
    'query_user_by_name', 'query_user_by_id', 'add_user', 'count_users',
]

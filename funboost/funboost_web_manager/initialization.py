# -*- coding: utf-8 -*-
"""
Web Manager 初始化模块

本模块包含数据库初始化、迁移和默认数据创建功能。
包括：
- 默认用户初始化
- 数据库迁移
- 默认权限分类、权限、角色、模板的创建
- 默认项目初始化
"""

from typing import Optional
from sqlalchemy import inspect, text

# 导入数据库函数
from .database import get_engine, get_session, init_db

# 导入所有模型
from .models import (
    WebManagerUser, Role, Permission, PermissionCategory, 
    PermissionTemplate, SystemConfig, Project, UserProject
)


def _is_password_hashed(password: str) -> bool:
    """检查密码是否已经是哈希格式"""
    return password.startswith('$2b$') or password.startswith('$2a$')


def init_default_users(db_url: Optional[str] = None, create_defaults: bool = False) -> None:
    """初始化默认用户（已废弃，保留用于向后兼容）
    
    注意：此函数已不再创建硬编码的默认用户。
    请使用 CLI 工具交互式创建管理员：python manage.py db init
    
    Args:
        db_url: 可选的数据库 URL，如果不提供则从配置获取
        create_defaults: 已废弃，不再使用
    """
    # 延迟导入避免循环依赖
    from funboost.funboost_web_manager.services.password_service import PasswordService
    
    # 只处理现有用户的密码升级，不创建新的默认用户
    session = get_session(db_url)
    try:
        users = session.query(WebManagerUser).all()
        for user in users:
            if not _is_password_hashed(user.password):
                # 如果是明文密码，标记需要强制修改
                user.force_password_change = True
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()



# 默认权限分类配置（增强版：支持多层级结构）
# 支持三级层次结构：Category > Subcategory > Permission_Item
# 通过 parent_code 字段实现子分类关系
DEFAULT_PERMISSION_CATEGORIES = [
    # 顶级分类
    {"code": "system", "name": "系统管理", "description": "系统级别管理功能", "sort_order": 1, "icon": "⚙️", "parent_code": None},
    {"code": "queue", "name": "队列管理", "description": "消息队列操作", "sort_order": 2, "icon": "📦", "parent_code": None},
    {"code": "monitor", "name": "监控", "description": "系统监控功能", "sort_order": 3, "icon": "📊", "parent_code": None},
    
    # 系统管理子分类
    {"code": "user", "name": "用户管理", "description": "用户账户相关权限", "sort_order": 1, "icon": "👤", "parent_code": "system"},
    {"code": "role", "name": "角色管理", "description": "角色和权限配置", "sort_order": 2, "icon": "🎭", "parent_code": "system"},
    {"code": "audit", "name": "审计日志", "description": "系统审计和日志查看", "sort_order": 3, "icon": "📋", "parent_code": "system"},
    {"code": "config", "name": "系统配置", "description": "系统设置和配置", "sort_order": 4, "icon": "🔧", "parent_code": "system"},
    {"code": "project", "name": "项目管理", "description": "项目管理相关权限", "sort_order": 5, "icon": "📁", "parent_code": "system"},
    
    # 队列管理子分类
    {"code": "queue:task", "name": "任务管理", "description": "队列任务操作", "sort_order": 1, "icon": "📝", "parent_code": "queue"},
    {"code": "queue:consumer", "name": "消费者管理", "description": "消费者操作", "sort_order": 2, "icon": "🔄", "parent_code": "queue"},
]

# 默认权限配置（增强版：包含 action_type 字段）
# 支持标准操作类型：create, read, update, delete, execute, export
DEFAULT_PERMISSIONS = [
    # 用户管理权限
    {"code": "user:create", "name": "创建用户", "description": "创建新用户账户", "category_code": "user", "action_type": "create", "sort_order": 1},
    {"code": "user:read", "name": "查看用户", "description": "查看用户列表和详情", "category_code": "user", "action_type": "read", "sort_order": 2},
    {"code": "user:update", "name": "编辑用户", "description": "编辑用户信息", "category_code": "user", "action_type": "update", "sort_order": 3},
    {"code": "user:delete", "name": "删除用户", "description": "删除用户账户", "category_code": "user", "action_type": "delete", "sort_order": 4},
    {"code": "user:export", "name": "导出用户", "description": "导出用户数据", "category_code": "user", "action_type": "export", "sort_order": 5},
    
    # 角色管理权限
    {"code": "role:create", "name": "创建角色", "description": "创建新角色", "category_code": "role", "action_type": "create", "sort_order": 1},
    {"code": "role:read", "name": "查看角色", "description": "查看角色列表和详情", "category_code": "role", "action_type": "read", "sort_order": 2},
    {"code": "role:update", "name": "编辑角色", "description": "编辑角色信息和权限", "category_code": "role", "action_type": "update", "sort_order": 3},
    {"code": "role:delete", "name": "删除角色", "description": "删除角色", "category_code": "role", "action_type": "delete", "sort_order": 4},
    
    # 审计日志权限
    {"code": "audit:read", "name": "查看审计日志", "description": "查看系统审计日志", "category_code": "audit", "action_type": "read", "sort_order": 1},
    {"code": "audit:export", "name": "导出审计日志", "description": "导出审计日志数据", "category_code": "audit", "action_type": "export", "sort_order": 2},
    
    # 系统配置权限
    {"code": "config:read", "name": "查看系统配置", "description": "查看系统配置", "category_code": "config", "action_type": "read", "sort_order": 1},
    {"code": "config:update", "name": "修改系统配置", "description": "修改系统配置", "category_code": "config", "action_type": "update", "sort_order": 2},
    
    # 项目管理权限
    {"code": "project:create", "name": "创建项目", "description": "创建新项目", "category_code": "project", "action_type": "create", "sort_order": 1},
    {"code": "project:read", "name": "查看项目", "description": "查看项目列表和详情", "category_code": "project", "action_type": "read", "sort_order": 2},
    {"code": "project:update", "name": "编辑项目", "description": "编辑项目信息", "category_code": "project", "action_type": "update", "sort_order": 3},
    {"code": "project:delete", "name": "删除项目", "description": "删除项目", "category_code": "project", "action_type": "delete", "sort_order": 4},
    {"code": "project:admin", "name": "项目管理员", "description": "管理项目用户和权限", "category_code": "project", "action_type": "execute", "sort_order": 5},
    
    # 队列管理权限
    {"code": "queue:read", "name": "查看队列", "description": "查看队列状态", "category_code": "queue", "action_type": "read", "sort_order": 1},
    {"code": "queue:execute", "name": "执行队列操作", "description": "执行队列相关操作", "category_code": "queue", "action_type": "execute", "sort_order": 2},
    {"code": "queue:task:create", "name": "创建任务", "description": "创建队列任务", "category_code": "queue:task", "action_type": "create", "sort_order": 1},
    {"code": "queue:task:read", "name": "查看任务", "description": "查看队列任务", "category_code": "queue:task", "action_type": "read", "sort_order": 2},
    {"code": "queue:task:delete", "name": "删除任务", "description": "删除队列任务", "category_code": "queue:task", "action_type": "delete", "sort_order": 3},
]

# 默认权限模板配置
# 支持模板继承：通过 parent_template_code 实现
DEFAULT_PERMISSION_TEMPLATES = [
    {
        "code": "viewer",
        "name": "只读用户",
        "description": "只能查看，不能修改",
        "permissions": ["user:read", "role:read", "audit:read", "config:read", "queue:read", "queue:task:read"],
        "parent_template_code": None,
        "is_builtin": True
    },
    {
        "code": "operator",
        "name": "操作员",
        "description": "可以执行队列操作",
        "permissions": ["queue:execute", "queue:task:create", "queue:task:delete"],
        "parent_template_code": "viewer",
        "is_builtin": True
    },
    {
        "code": "admin",
        "name": "管理员",
        "description": "拥有所有权限",
        "permissions": ["user:*", "role:*", "audit:*", "config:*", "queue:*", "project:*"],
        "parent_template_code": None,
        "is_builtin": True
    },
    {
        "code": "project_admin",
        "name": "项目管理员",
        "description": "项目级别的管理权限",
        "permissions": ["queue:*", "queue:task:*"],
        "parent_template_code": "viewer",
        "is_builtin": True
    }
]



def migrate_database(db_url: Optional[str] = None) -> None:
    """数据库迁移脚本
    
    处理从旧版本到新版本的数据库升级：
    1. 创建所有新表
    2. 为现有表添加新列（如果不存在）
    3. 为现有用户添加新字段的默认值
    4. 标记明文密码用户需要强制修改密码
    5. 初始化默认权限分类（含子分类）
    6. 初始化默认权限（含 action_type）
    7. 初始化默认角色
    8. 为admin用户分配admin角色
    9. 初始化系统配置
    10. 初始化默认权限模板
    
    新增字段处理：
    - permission_categories.parent_code: 支持子分类
    - permissions.action_type: 操作类型
    - permissions.project_scope: 项目作用域
    
    Args:
        db_url: 可选的数据库 URL，如果不提供则从配置获取
        
    Requirements:
    - 1.1: 支持三级层次结构 Category > Subcategory > Permission_Item
    - 2.1: 定义标准操作类型 create, read, update, delete, execute, export
    - 14.1: 提供预定义权限模板
    """
    engine = get_engine(db_url)
    session = get_session(db_url)
    
    try:
        # 1. 创建所有表（如果不存在）
        init_db(db_url)
        
        # 1.1 创建 role_projects 关联表（如果不存在）
        inspector = inspect(engine)
        if 'role_projects' not in inspector.get_table_names():
            with engine.connect() as conn:
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS role_projects (
                        role_id INTEGER NOT NULL,
                        project_id INTEGER NOT NULL,
                        PRIMARY KEY (role_id, project_id),
                        FOREIGN KEY (role_id) REFERENCES roles(id),
                        FOREIGN KEY (project_id) REFERENCES projects(id)
                    )
                '''))
                conn.commit()
        
        # 2. 检查并添加 permissions 表的新列
        inspector = inspect(engine)
        if 'permissions' in inspector.get_table_names():
            existing_columns = [col['name'] for col in inspector.get_columns('permissions')]
            
            # 添加 category_code 列（如果不存在）
            if 'category_code' not in existing_columns:
                with engine.connect() as conn:
                    conn.execute(text('ALTER TABLE permissions ADD COLUMN category_code VARCHAR(64)'))
                    conn.commit()
            
            # 添加 sort_order 列（如果不存在）
            if 'sort_order' not in existing_columns:
                with engine.connect() as conn:
                    conn.execute(text('ALTER TABLE permissions ADD COLUMN sort_order INTEGER DEFAULT 0'))
                    conn.commit()
            
            # 添加 action_type 列（如果不存在）- 新增字段
            if 'action_type' not in existing_columns:
                with engine.connect() as conn:
                    conn.execute(text('ALTER TABLE permissions ADD COLUMN action_type VARCHAR(32)'))
                    conn.commit()
            
            # 添加 project_scope 列（如果不存在）- 新增字段
            if 'project_scope' not in existing_columns:
                with engine.connect() as conn:
                    conn.execute(text('ALTER TABLE permissions ADD COLUMN project_scope VARCHAR(64)'))
                    conn.commit()
        
        # 3. 检查并添加 permission_categories 表的新列
        if 'permission_categories' in inspector.get_table_names():
            existing_columns = [col['name'] for col in inspector.get_columns('permission_categories')]
            
            # 添加 parent_code 列（如果不存在）- 支持子分类
            if 'parent_code' not in existing_columns:
                with engine.connect() as conn:
                    conn.execute(text('ALTER TABLE permission_categories ADD COLUMN parent_code VARCHAR(64)'))
                    conn.commit()
        
        # 4. 检查并更新现有用户的新字段
        users = session.query(WebManagerUser).all()
        for user in users:
            # 如果是明文密码，标记需要强制修改
            if not _is_password_hashed(user.password):
                user.force_password_change = True
            
            # 确保状态字段有默认值
            if not user.status:
                user.status = 'active'
            
            # 确保失败计数有默认值
            if user.failed_login_count is None:
                user.failed_login_count = 0
        
        # 5. 初始化默认权限分类（必须在权限之前，支持子分类）
        _init_default_categories(session)
        
        # 6. 初始化默认权限（含 action_type）
        _init_default_permissions(session)
        
        # 7. 为现有权限自动分配分类和操作类型
        _auto_assign_permission_categories(session)
        _auto_assign_permission_action_types(session)
        
        # 8. 初始化默认角色
        _init_default_roles(session)
        
        # 9. 为admin用户分配admin角色
        _assign_admin_role(session)
        
        # 10. 初始化系统配置
        _init_system_config(session)
        
        # 11. 初始化默认权限模板
        _init_default_permission_templates(session)

        # 11.1 清理已废弃的代码编辑器权限
        _purge_code_editor_permissions(session)
        
        # 12. 初始化默认项目并将现有用户添加到默认项目
        _init_default_project(session)
        
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()



def _init_default_categories(session) -> None:
    """初始化默认权限分类（幂等操作）
    
    支持多层级结构：先创建顶级分类，再创建子分类。
    通过 parent_code 字段实现分类层级关系。
    """
    # 分离顶级分类和子分类，确保先创建顶级分类
    top_level_categories = [cat for cat in DEFAULT_PERMISSION_CATEGORIES if cat.get('parent_code') is None]
    sub_categories = [cat for cat in DEFAULT_PERMISSION_CATEGORIES if cat.get('parent_code') is not None]
    
    # 先创建顶级分类
    for cat_data in top_level_categories:
        existing = session.query(PermissionCategory).filter_by(code=cat_data['code']).first()
        if not existing:
            category = PermissionCategory(**cat_data)
            session.add(category)
        else:
            # 更新现有分类的字段（如果需要）
            if existing.icon != cat_data.get('icon'):
                existing.icon = cat_data.get('icon')
            if existing.sort_order != cat_data.get('sort_order', 0):
                existing.sort_order = cat_data.get('sort_order', 0)
    
    # 提交顶级分类，确保外键约束可以满足
    session.flush()
    
    # 再创建子分类
    for cat_data in sub_categories:
        existing = session.query(PermissionCategory).filter_by(code=cat_data['code']).first()
        if not existing:
            category = PermissionCategory(**cat_data)
            session.add(category)
        else:
            # 更新现有分类的字段（如果需要）
            if existing.parent_code != cat_data.get('parent_code'):
                existing.parent_code = cat_data.get('parent_code')
            if existing.icon != cat_data.get('icon'):
                existing.icon = cat_data.get('icon')
            if existing.sort_order != cat_data.get('sort_order', 0):
                existing.sort_order = cat_data.get('sort_order', 0)


def _auto_assign_permission_categories(session) -> None:
    """为现有权限自动分配分类
    
    根据权限代码前缀（如 user:read -> user）自动分配到对应分类
    """
    permissions = session.query(Permission).filter(Permission.category_code.is_(None)).all()
    for perm in permissions:
        # 从权限代码提取分类代码（如 user:read -> user）
        if ':' in perm.code:
            category_code = perm.code.split(':')[0]
            # 检查分类是否存在
            category = session.query(PermissionCategory).filter_by(code=category_code).first()
            if category:
                perm.category_code = category_code


def _auto_assign_permission_action_types(session) -> None:
    """为现有权限自动分配操作类型
    
    根据权限代码后缀（如 user:read -> read）自动分配操作类型。
    支持标准操作类型：create, read, update, delete, execute, export
    以及旧版本的 write 类型（映射到 update）。
    
    Requirements:
    - 2.1: 定义标准操作类型
    - 2.4: 从权限代码提取操作类型
    """
    # 标准操作类型
    standard_action_types = {'create', 'read', 'update', 'delete', 'execute', 'export'}
    # 旧版本操作类型映射
    legacy_action_mapping = {
        'write': 'update',  # 旧版 write 映射到 update
    }
    
    permissions = session.query(Permission).filter(Permission.action_type.is_(None)).all()
    for perm in permissions:
        if ':' in perm.code:
            # 从权限代码提取操作类型（最后一段）
            action = perm.code.split(':')[-1]
            
            # 检查是否为标准操作类型
            if action in standard_action_types:
                perm.action_type = action
            # 检查是否为旧版操作类型
            elif action in legacy_action_mapping:
                perm.action_type = legacy_action_mapping[action]
            # 其他自定义操作类型保持原样
            else:
                perm.action_type = action


def _init_default_permissions(session) -> None:
    """初始化默认权限（包含分类、操作类型和排序信息）
    
    使用 DEFAULT_PERMISSIONS 配置，支持：
    - category_code: 权限所属分类
    - action_type: 操作类型（create, read, update, delete, execute, export）
    - sort_order: 排序顺序
    - project_scope: 项目作用域（可选）
    """
    for perm_data in DEFAULT_PERMISSIONS:
        existing = session.query(Permission).filter_by(code=perm_data['code']).first()
        if not existing:
            permission = Permission(**perm_data)
            session.add(permission)
        else:
            # 更新现有权限的字段（如果未设置或需要更新）
            if existing.category_code is None and 'category_code' in perm_data:
                existing.category_code = perm_data['category_code']
            if existing.sort_order == 0 and 'sort_order' in perm_data:
                existing.sort_order = perm_data['sort_order']
            # 更新 action_type（新增字段）
            if existing.action_type is None and 'action_type' in perm_data:
                existing.action_type = perm_data['action_type']
            # 更新 project_scope（新增字段）
            if existing.project_scope is None and 'project_scope' in perm_data:
                existing.project_scope = perm_data.get('project_scope')
            # 更新描述（如果为空）
            if existing.description is None and 'description' in perm_data:
                existing.description = perm_data['description']



def _init_default_roles(session) -> None:
    """初始化默认角色
    
    使用新的细粒度权限代码（包含 action_type）。
    """
    default_roles = [
        {
            "name": "admin",
            "description": "系统管理员，拥有所有权限",
            "is_builtin": True,
            "permissions": [
                "user:create", "user:read", "user:update", "user:delete", "user:export",
                "role:create", "role:read", "role:update", "role:delete",
                "audit:read", "audit:export",
                "config:read", "config:update",
                "project:create", "project:read", "project:update", "project:delete", "project:admin",
                "queue:read", "queue:execute",
                "queue:task:create", "queue:task:read", "queue:task:delete"
            ]
        },
        {
            "name": "operator",
            "description": "操作员，可以管理队列",
            "is_builtin": True,
            "permissions": [
                "user:read",
                "queue:read", "queue:execute",
                "queue:task:create", "queue:task:read", "queue:task:delete"
            ]
        },
        {
            "name": "viewer",
            "description": "只读用户，只能查看",
            "is_builtin": True,
            "permissions": [
                "user:read", "role:read", "audit:read", "config:read",
                "queue:read", "queue:task:read"
            ]
        }
    ]
    
    for role_data in default_roles:
        existing = session.query(Role).filter_by(name=role_data['name']).first()
        if not existing:
            role = Role(
                name=role_data['name'],
                description=role_data['description'],
                is_builtin=role_data['is_builtin']
            )
            
            # 先添加 role 到 session，避免 SAWarning
            session.add(role)
            session.flush()  # 刷新以获取 role.id
            
            # 分配权限
            for perm_code in role_data['permissions']:
                permission = session.query(Permission).filter_by(code=perm_code).first()
                if permission:
                    role.permissions.append(permission)


def _assign_admin_role(session) -> None:
    """为admin用户分配admin角色"""
    admin_user = session.query(WebManagerUser).filter_by(user_name='admin').first()
    admin_role = session.query(Role).filter_by(name='admin').first()
    
    if admin_user and admin_role:
        # 检查是否已经有admin角色
        if admin_role not in admin_user.roles:
            admin_user.roles.append(admin_role)


def _init_system_config(session) -> None:
    """初始化系统配置"""
    default_configs = [
        {"key": "audit_retention_days", "value": "30", "description": "审计日志保留天数"}
    ]
    
    for config_data in default_configs:
        existing = session.query(SystemConfig).filter_by(key=config_data['key']).first()
        if not existing:
            config = SystemConfig(**config_data)
            session.add(config)


def _init_default_permission_templates(session) -> None:
    """初始化默认权限模板（幂等操作）
    
    创建预定义的权限模板，支持模板继承。
    模板包括：只读用户、操作员、管理员、项目管理员
    
    Requirements:
    - 14.1: 提供预定义权限模板
    """
    import json
    
    for template_data in DEFAULT_PERMISSION_TEMPLATES:
        existing = session.query(PermissionTemplate).filter_by(code=template_data['code']).first()
        if not existing:
            template = PermissionTemplate(
                code=template_data['code'],
                name=template_data['name'],
                description=template_data.get('description'),
                permissions=json.dumps(template_data['permissions']),
                parent_template_code=template_data.get('parent_template_code'),
                is_builtin=template_data.get('is_builtin', False)
            )
            session.add(template)
        else:
            # 更新现有模板的字段（如果需要）
            if existing.description != template_data.get('description'):
                existing.description = template_data.get('description')
            if existing.parent_template_code != template_data.get('parent_template_code'):
                existing.parent_template_code = template_data.get('parent_template_code')
            # 更新权限列表（仅对内置模板）
            if existing.is_builtin:
                existing.permissions = json.dumps(template_data['permissions'])


def _purge_code_editor_permissions(session) -> None:
    """清理已废弃的代码编辑器权限与分类（幂等）"""
    import json

    permission_codes = {"code_editor:read", "code_editor:write", "code_editor:execute"}

    # 从角色中移除权限
    for role in session.query(Role).all():
        for perm in list(role.permissions):
            if perm.code in permission_codes:
                role.permissions.remove(perm)

    # 清理权限模板中的 code_editor 权限
    templates = session.query(PermissionTemplate).all()
    for template in templates:
        try:
            raw = template.permissions or "[]"
            permissions = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            continue

        if not isinstance(permissions, list):
            continue

        filtered = [
            perm for perm in permissions
            if not perm.startswith("code_editor:") and perm != "code_editor:*"
        ]

        if filtered != permissions:
            template.permissions = json.dumps(filtered, ensure_ascii=False)

    # 删除权限记录
    for perm in session.query(Permission).filter(Permission.code.in_(permission_codes)).all():
        session.delete(perm)

    # 删除分类（先子后父）
    code_editor_category = session.query(PermissionCategory).filter_by(code="code_editor").first()
    if code_editor_category:
        session.delete(code_editor_category)

    devtools_category = session.query(PermissionCategory).filter_by(code="devtools").first()
    if devtools_category:
        session.delete(devtools_category)


def _init_default_project(session) -> None:
    """初始化默认项目并将现有用户添加到默认项目（幂等操作）
    
    创建默认项目 "default"（code: "default", name: "默认项目"），
    并将所有现有用户添加到默认项目，以保持向后兼容。
    
    迁移策略：
    1. 创建默认项目（如果不存在）
    2. 将所有现有用户添加到默认项目（permission_level="admin"）
    3. 确保操作幂等（可多次运行而不产生重复数据）
    
    Requirements:
    - AC-1: 项目 CRUD - 创建默认项目
    - 迁移策略: 将所有用户添加到默认项目（保持向后兼容）
    """
    # 1. 创建默认项目（如果不存在）
    default_project = session.query(Project).filter_by(code='default').first()
    if not default_project:
        default_project = Project(
            name='默认项目',
            code='default',
            description='系统默认项目，用于向后兼容',
            status='active'
        )
        session.add(default_project)
        # 刷新以获取自动生成的 id
        session.flush()
    
    # 2. 将所有现有用户添加到默认项目（如果尚未添加）
    all_users = session.query(WebManagerUser).all()
    for user in all_users:
        # 检查用户是否已经在默认项目中
        existing_user_project = session.query(UserProject).filter_by(
            user_id=user.id,
            project_id=default_project.id
        ).first()
        
        if not existing_user_project:
            # 添加用户到默认项目，权限级别为 admin（保持向后兼容）
            user_project = UserProject(
                user_id=user.id,
                project_id=default_project.id,
                permission_level='admin'
            )
            session.add(user_project)

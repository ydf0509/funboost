# -*- coding: utf-8 -*-
"""
角色管理路由模块

包含：
- 角色列表 /roles
- 创建角色 /roles/create
- 编辑角色 /roles/<role_id>/edit
- 删除角色 /roles/<role_id>/delete
"""

from flask import Blueprint, request, jsonify, redirect
from flask_login import login_required, current_user

from funboost.funboost_web_manager.user_models import get_session, Role
from funboost.funboost_web_manager.routes.utils import (
    require_permission,
    role_service,
    permission_service,
)


admin_roles_bp = Blueprint('admin_roles', __name__)


# 注意：/roles 页面由前端静态文件处理，不需要后端路由
# 已移除 GET /roles 路由，避免与前端静态文件冲突导致重定向循环


@admin_roles_bp.route("/api/roles")
@login_required
@require_permission("role:read")
def api_role_list():
    """角色列表 API - 返回 JSON"""
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 100, type=int)
    
    db_session = get_session()
    try:
        # 计算总数
        total = db_session.query(Role).count()
        
        # 分页查询
        offset = (page - 1) * page_size
        roles = db_session.query(Role).order_by(Role.created_at.desc()).offset(offset).limit(page_size).all()
        
        # 转换为字典并添加用户数量
        roles_list = []
        for role in roles:
            role_data = role.to_dict()
            role_data['user_count'] = len(role.users)
            roles_list.append(role_data)
        
        # 计算分页信息
        total_pages = (total + page_size - 1) // page_size
        
        return jsonify({
            "success": True,
            "data": {
                "roles": roles_list,
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages
            }
        })
    finally:
        db_session.close()


@admin_roles_bp.route("/api/roles/<int:role_id>")
@login_required
@require_permission("role:read")
def api_role_detail(role_id):
    """获取单个角色详情 API - 返回 JSON"""
    role_data = role_service.get_role(role_id)
    if not role_data:
        return jsonify({"success": False, "error": "角色不存在"}), 404
    
    return jsonify({
        "success": True,
        "data": role_data
    })


@admin_roles_bp.route("/api/permissions")
@login_required
@require_permission("role:read")
def api_permissions_list():
    """获取所有权限列表 API - 返回 JSON"""
    permissions = permission_service.list_permissions()
    return jsonify({
        "success": True,
        "data": {
            "permissions": permissions
        }
    })


@admin_roles_bp.route("/api/permissions/tree")
@login_required
@require_permission("role:read")
def api_permissions_tree():
    """获取多层级权限树 API
    
    返回按分类分组的多层级权限树，支持 Category > Subcategory > Permission 三级结构。
    分类和权限都按 sort_order 排序。
    支持按项目和操作类型过滤权限。
    
    Query Parameters:
        project: 项目过滤，只返回指定项目的权限和全局权限
        action_type: 操作类型过滤 (create, read, update, delete, execute, export)
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "tree": {
                    "categories": [
                        {
                            "code": "system",
                            "name": "系统管理",
                            "description": "系统级别管理功能",
                            "icon": "⚙️",
                            "sort_order": 1,
                            "subcategories": [
                                {
                                    "code": "user",
                                    "name": "用户管理",
                                    "description": "用户账户相关权限",
                                    "icon": "👤",
                                    "sort_order": 1,
                                    "subcategories": [],
                                    "permissions": [
                                        {
                                            "id": 1,
                                            "code": "user:read",
                                            "name": "查看用户",
                                            "description": "查看用户列表和详情",
                                            "action_type": "read",
                                            "action_type_display": "查看",
                                            "project_scope": null,
                                            "sort_order": 1
                                        },
                                        ...
                                    ]
                                },
                                ...
                            ],
                            "permissions": [...]
                        },
                        ...
                    ]
                }
            }
        }
        
    Requirements:
        - 5.1: 返回多层级 Permission_Tree 结构
        - 5.4: 支持 project 参数过滤
        - 5.5: 支持 action_type 参数过滤
    """
    # 获取查询参数
    project = request.args.get('project')
    action_type = request.args.get('action_type')
    
    # 验证 action_type 参数（如果提供）
    valid_action_types = {'create', 'read', 'update', 'delete', 'execute', 'export'}
    if action_type and action_type not in valid_action_types:
        return jsonify({
            "success": False,
            "error": f"无效的操作类型: {action_type}。有效值: {', '.join(sorted(valid_action_types))}"
        }), 400
    
    # 调用 permission_service 获取权限树
    tree = permission_service.get_permissions_tree(project=project, action_type=action_type)
    
    return jsonify({
        "success": True,
        "data": {
            "tree": tree
        }
    })


@admin_roles_bp.route("/api/permissions/templates")
@login_required
@require_permission("role:read")
def api_permission_templates():
    """获取权限模板列表 API
    
    返回所有权限模板，包含模板自身的权限和继承的所有权限。
    用于在创建或编辑角色时，根据模板预选权限。
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "templates": [
                    {
                        "code": "viewer",
                        "name": "只读用户",
                        "description": "只能查看，不能修改",
                        "permissions": ["user:read", "role:read", ...],
                        "all_permissions": ["user:read", "role:read", ...],
                        "parent_template_code": null,
                        "is_builtin": true
                    },
                    {
                        "code": "operator",
                        "name": "操作员",
                        "description": "可以执行队列操作",
                        "permissions": ["queue:execute", ...],
                        "all_permissions": ["user:read", "queue:execute", ...],
                        "parent_template_code": "viewer",
                        "is_builtin": true
                    },
                    ...
                ]
            }
        }
        
    Requirements:
        - 14.1: THE Permission_System SHALL provide predefined permission templates:
                只读用户, 操作员, 管理员, 项目管理员
    """
    templates = permission_service.get_templates()
    return jsonify({
        "success": True,
        "data": {
            "templates": templates
        }
    })


@admin_roles_bp.route("/api/permissions/categories")
@login_required
@require_permission("role:read")
def api_permission_categories():
    """
    获取权限分类列表 API
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "categories": [
                    {"code": "user", "name": "用户管理", ...},
                    ...
                ]
            }
        }
    """
    categories = permission_service.list_categories()
    return jsonify({
        "success": True,
        "data": {
            "categories": categories
        }
    })


@admin_roles_bp.route("/api/roles", methods=["POST"])
@login_required
@require_permission("role:create")
def api_role_create():
    """创建角色 API - 接收 JSON"""
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    permission_codes = data.get("permissions") or []
    project_ids = data.get("projects") or []  # 项目ID列表
    
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get('User-Agent', '')
    
    # 验证角色名
    if not name or len(name) < 2:
        return jsonify({"success": False, "error": "角色名称至少需要2个字符"}), 400
    
    # 使用 RoleService 创建角色
    result = role_service.create_role(
        name=name,
        description=description if description else None,
        permission_codes=permission_codes,
        project_ids=project_ids,
        admin_user=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if result["success"]:
        return jsonify({
            "success": True,
            "data": {"message": f"角色 {name} 创建成功"}
        })
    else:
        return jsonify({"success": False, "error": result["error"]}), 400


@admin_roles_bp.route("/api/roles/<int:role_id>", methods=["PUT", "PATCH"])
@login_required
@require_permission("role:update")
def api_role_update(role_id):
    """更新角色 API - 接收 JSON"""
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    permission_codes = data.get("permissions") or []
    project_ids = data.get("projects") or []  # 项目ID列表
    
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get('User-Agent', '')
    
    # 获取角色信息检查是否为内置角色
    role_data = role_service.get_role(role_id)
    if not role_data:
        return jsonify({"success": False, "error": "角色不存在"}), 404
    
    # 内置角色不能修改名称
    if role_data.get("is_builtin"):
        name = None  # 不更新名称
    
    # 使用 RoleService 更新角色
    result = role_service.update_role(
        role_id=role_id,
        name=name,
        description=description if description else None,
        permission_codes=permission_codes,
        project_ids=project_ids,
        admin_user=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if result["success"]:
        return jsonify({
            "success": True,
            "data": {"message": "角色更新成功"}
        })
    else:
        return jsonify({"success": False, "error": result["error"]}), 400


@admin_roles_bp.route("/api/roles/<int:role_id>", methods=["DELETE"])
@login_required
@require_permission("role:delete")
def api_role_delete(role_id):
    """删除角色 API"""
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get('User-Agent', '')
    
    # 使用 RoleService 删除角色
    result = role_service.delete_role(
        role_id=role_id,
        admin_user=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if result["success"]:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": result["error"]}), 400


@admin_roles_bp.route("/roles/create", methods=["POST"])
@login_required
@require_permission("role:create")
def role_create():
    """创建角色 API - POST 返回 JSON（GET 由前端静态文件处理）"""
    # POST 请求处理 - 返回 JSON
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    permission_codes = request.form.getlist("permissions")
    
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get('User-Agent', '')
    
    # 验证角色名
    if not name or len(name) < 2:
        return jsonify({"success": False, "error": "角色名称至少需要2个字符"})
    
    # 使用 RoleService 创建角色
    result = role_service.create_role(
        name=name,
        description=description if description else None,
        permission_codes=permission_codes,
        admin_user=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if result["success"]:
        return jsonify({"success": True, "message": f"角色 {name} 创建成功"})
    else:
        return jsonify({"success": False, "error": result["error"]})


@admin_roles_bp.route("/roles/<int:role_id>/edit", methods=["POST"])
@login_required
@require_permission("role:update")
def role_edit(role_id):
    """编辑角色 API - POST 返回 JSON（GET 由前端静态文件处理）"""
    # POST 请求处理 - 返回 JSON
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    permission_codes = request.form.getlist("permissions")
    
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get('User-Agent', '')
    
    # 获取角色信息检查是否为内置角色
    role_data = role_service.get_role(role_id)
    if not role_data:
        return jsonify({"success": False, "error": "角色不存在"})
    
    # 内置角色不能修改名称
    if role_data.get("is_builtin"):
        name = None  # 不更新名称
    
    # 使用 RoleService 更新角色
    result = role_service.update_role(
        role_id=role_id,
        name=name,
        description=description if description else None,
        permission_codes=permission_codes,
        admin_user=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if result["success"]:
        return jsonify({"success": True, "message": "角色更新成功"})
    else:
        return jsonify({"success": False, "error": result["error"]})


@admin_roles_bp.route("/roles/<int:role_id>/delete", methods=["POST"])
@login_required
@require_permission("role:delete")
def role_delete(role_id):
    """删除角色"""
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get('User-Agent', '')
    
    # 使用 RoleService 删除角色
    result = role_service.delete_role(
        role_id=role_id,
        admin_user=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if result["success"]:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": result["error"]})


@admin_roles_bp.route("/api/permissions/discovery")
@login_required
@require_permission("role:read")
def api_permissions_discovery():
    """
    权限发现 API - 扫描所有路由，返回权限保护状态
    
    扫描应用中所有注册的路由，检查每个路由是否有权限保护。
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "routes": [
                    {
                        "endpoint": "admin_users.user_list",
                        "methods": ["GET"],
                        "rule": "/admin/users",
                        "requires_login": true,
                        "required_permission": "user:read",
                        "is_protected": true
                    },
                    ...
                ],
                "summary": {
                    "total_routes": 50,
                    "protected_routes": 45,
                    "unprotected_routes": 5,
                    "login_required_only": 3
                }
            }
        }
    """
    from flask import current_app
    
    routes = []
    protected_count = 0
    unprotected_count = 0
    login_only_count = 0
    
    for rule in current_app.url_map.iter_rules():
        # 跳过静态文件路由
        if rule.endpoint == 'static':
            continue
        
        # 获取视图函数
        view_func = current_app.view_functions.get(rule.endpoint)
        if not view_func:
            continue
        
        # 检查是否需要登录
        requires_login = hasattr(view_func, '__wrapped__') or 'login_required' in str(view_func)
        
        # 检查是否有权限要求
        required_permission = None
        if hasattr(view_func, '_required_permission'):
            required_permission = view_func._required_permission
        
        # 判断保护状态
        is_protected = required_permission is not None
        
        methods = [m for m in rule.methods if m not in ('HEAD', 'OPTIONS')]
        
        route_info = {
            "endpoint": rule.endpoint,
            "methods": methods,
            "rule": str(rule),
            "requires_login": requires_login,
            "required_permission": required_permission,
            "is_protected": is_protected
        }
        routes.append(route_info)
        
        if is_protected:
            protected_count += 1
        elif requires_login:
            login_only_count += 1
        else:
            unprotected_count += 1
    
    # 按端点名称排序
    routes.sort(key=lambda x: x['endpoint'])
    
    return jsonify({
        "success": True,
        "data": {
            "routes": routes,
            "summary": {
                "total_routes": len(routes),
                "protected_routes": protected_count,
                "unprotected_routes": unprotected_count,
                "login_required_only": login_only_count
            }
        }
    })


@admin_roles_bp.route("/api/permissions", methods=["POST"])
@login_required
@require_permission("role:update")
def api_permission_create():
    """
    动态创建权限 API
    
    允许在运行时创建新权限，无需代码修改或数据库迁移。
    
    Request Body:
        {
            "code": "module:action",  // 必填，权限代码
            "name": "权限名称",        // 必填，权限名称
            "description": "描述",     // 可选，权限描述
            "category_code": "module", // 可选，分类代码（不提供则自动推断）
            "sort_order": 0            // 可选，排序顺序
        }
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "permission": {...}
            }
        }
    """
    data = request.get_json() or {}
    code = (data.get("code") or "").strip()
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip() or None
    category_code = (data.get("category_code") or "").strip() or None
    sort_order = data.get("sort_order", 0)
    
    # 验证必填字段
    if not code:
        return jsonify({"success": False, "error": "权限代码不能为空"}), 400
    if not name:
        return jsonify({"success": False, "error": "权限名称不能为空"}), 400
    
    # 验证权限代码格式
    if ':' not in code:
        return jsonify({"success": False, "error": "权限代码格式应为 'module:action'"}), 400
    
    result = permission_service.create_permission_dynamic(
        code=code,
        name=name,
        description=description,
        category_code=category_code,
        sort_order=sort_order
    )
    
    if result["success"]:
        return jsonify({
            "success": True,
            "data": {
                "permission": result["permission"]
            }
        })
    else:
        return jsonify({"success": False, "error": result["error"]}), 400


@admin_roles_bp.route("/api/permissions/categories", methods=["POST"])
@login_required
@require_permission("role:update")
def api_permission_category_create():
    """
    动态创建权限分类 API
    
    允许在运行时创建新权限分类，无需代码修改或数据库迁移。
    
    Request Body:
        {
            "code": "module",      // 必填，分类代码
            "name": "分类名称",     // 必填，分类名称
            "description": "描述", // 可选，分类描述
            "sort_order": 0,       // 可选，排序顺序
            "icon": "📦"           // 可选，图标
        }
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "category": {...}
            }
        }
    """
    data = request.get_json() or {}
    code = (data.get("code") or "").strip()
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip() or None
    sort_order = data.get("sort_order", 0)
    icon = (data.get("icon") or "").strip() or None
    
    # 验证必填字段
    if not code:
        return jsonify({"success": False, "error": "分类代码不能为空"}), 400
    if not name:
        return jsonify({"success": False, "error": "分类名称不能为空"}), 400
    
    result = permission_service.create_category_dynamic(
        code=code,
        name=name,
        description=description,
        sort_order=sort_order,
        icon=icon
    )
    
    if result["success"]:
        return jsonify({
            "success": True,
            "data": {
                "category": result["category"]
            }
        })
    else:
        return jsonify({"success": False, "error": result["error"]}), 400


@admin_roles_bp.route("/api/permissions/audit")
@login_required
@require_permission("role:read")
def api_permissions_audit():
    """
    路由权限审计 API
    
    扫描所有路由，返回权限保护状态和警告信息。
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "routes": [...],
                "warnings": [...],
                "summary": {
                    "total_routes": 50,
                    "protected_routes": 45,
                    "unprotected_routes": 5,
                    "login_required_only": 3
                }
            }
        }
    """
    from flask import current_app
    
    audit_result = permission_service.audit_routes(current_app)
    
    return jsonify({
        "success": True,
        "data": audit_result
    })


@admin_roles_bp.route("/api/action-types")
@login_required
def api_action_types():
    """获取操作类型列表 API
    
    返回标准操作类型列表，包含代码、显示名称和分类信息。
    分类用于区分读操作和写操作，便于前端实现批量选择功能。
    
    此端点只需要登录，不需要特定权限，任何登录用户都可以查看操作类型。
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "action_types": [
                    {"code": "create", "name": "创建", "category": "write"},
                    {"code": "read", "name": "查看", "category": "read"},
                    {"code": "update", "name": "编辑", "category": "write"},
                    {"code": "delete", "name": "删除", "category": "write"},
                    {"code": "execute", "name": "执行", "category": "write"},
                    {"code": "export", "name": "导出", "category": "read"}
                ]
            }
        }
        
    Requirements:
        - 2.1: THE Permission_System SHALL define standard Action_Type values:
               create, read, update, delete, execute, export
        - 2.3: THE Permission_System SHALL provide a mapping from Action_Type to display name:
               create→创建, read→查看, update→编辑, delete→删除, execute→执行, export→导出
    """
    return jsonify({
        "success": True,
        "data": {
            "action_types": [
                {"code": "create", "name": "创建", "category": "write"},
                {"code": "read", "name": "查看", "category": "read"},
                {"code": "update", "name": "编辑", "category": "write"},
                {"code": "delete", "name": "删除", "category": "write"},
                {"code": "execute", "name": "执行", "category": "write"},
                {"code": "export", "name": "导出", "category": "read"}
            ]
        }
    })


@admin_roles_bp.route("/api/permissions/change-history")
@login_required
@require_permission("audit:read")
def api_permission_change_history():
    """查询权限变更历史 API
    
    查询指定角色或用户的权限变更历史记录。
    返回权限变更和用户角色变更的审计日志。
    
    Query Parameters:
        role_name: 角色名称过滤（可选）
        user_name: 用户名过滤（可选，查询该用户的角色变更）
        page: 页码（从1开始，默认1）
        page_size: 每页大小（默认50）
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "logs": [
                    {
                        "id": 1,
                        "event_type": "permission_change",
                        "user_name": "admin",
                        "ip_address": "192.168.1.1",
                        "details": {
                            "role_name": "editor",
                            "added_permissions": ["user:create", "user:update"],
                            "removed_permissions": ["user:delete"],
                            "change_summary": {
                                "added_count": 2,
                                "removed_count": 1
                            }
                        },
                        "created_at": "2024-01-15T10:30:00"
                    },
                    ...
                ],
                "total": 10,
                "page": 1,
                "page_size": 50
            }
        }
        
    Requirements:
        - 13.4: THE Permission_System SHALL provide an API to query permission 
                change history for a specific role or user
    """
    role_name = request.args.get('role_name')
    user_name = request.args.get('user_name')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    
    # 限制 page_size 最大值
    if page_size > 100:
        page_size = 100
    
    result = permission_service.get_permission_change_history(
        role_name=role_name,
        user_name=user_name,
        page=page,
        page_size=page_size
    )
    
    return jsonify({
        "success": True,
        "data": result
    })

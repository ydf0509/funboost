# -*- coding: utf-8 -*-
"""
项目管理路由模块

包含：
- 项目列表 /api/projects
- 创建项目 /api/projects (POST)
- 获取项目详情 /api/projects/:id
- 更新项目 /api/projects/:id (PUT)
- 删除项目 /api/projects/:id (DELETE)
- 项目用户管理 /api/projects/:id/users

Requirements:
    - AC-1: 项目 CRUD
    - US-1.1: 创建、编辑和删除项目
    - US-1.2: 为项目设置名称、描述和状态
    - US-1.3: 查看项目列表和详情
    - US-2.1: 将用户分配到特定项目
    - US-2.2: 为用户设置项目级别的权限
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from funboost.funboost_web_manager.services.project_service import ProjectService
from funboost.funboost_web_manager.routes.utils import (
    require_permission,
    require_project_permission,
    require_permission_and_project,
)


# 创建蓝图
admin_projects_bp = Blueprint('admin_projects', __name__)

# 项目服务实例
project_service = ProjectService()


# ==================== 项目 CRUD API ====================

@admin_projects_bp.route("/api/projects")
@login_required
@require_permission("project:read")
def api_project_list():
    """
    获取项目列表 API
    
    支持分页和搜索。
    
    Query Parameters:
        page: 页码（从1开始，默认1）
        page_size: 每页大小（默认50）
        search: 搜索关键词（可选），匹配项目名称、代码或描述
        status: 状态过滤（可选），'active' 或 'archived'
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "projects": [...],
                "total": 10,
                "page": 1,
                "page_size": 50,
                "total_pages": 1
            }
        }
        
    Requirements:
        - US-1.3: 查看项目列表
        - AC-1: 项目列表支持分页和搜索
    """
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 50, type=int)
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    
    # 限制 page_size 最大值
    if page_size > 100:
        page_size = 100
    
    result = project_service.get_all_projects(
        page=page,
        page_size=page_size,
        search=search if search else None,
        status=status if status else None
    )
    
    return jsonify({
        "success": True,
        "data": result
    })


@admin_projects_bp.route("/api/projects/<int:project_id>")
@login_required
@require_permission("project:read")
def api_project_detail(project_id):
    """
    获取单个项目详情 API
    
    Args:
        project_id: 项目ID
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "project": {...}
            }
        }
        
    Requirements:
        - US-1.3: 查看项目详情
    """
    project = project_service.get_project(project_id)
    
    if not project:
        return jsonify({
            "success": False,
            "error": "项目不存在"
        }), 404
    
    # 获取项目关联的用户数量
    user_count = project_service.get_project_user_count(project_id)
    project['user_count'] = user_count
    
    return jsonify({
        "success": True,
        "data": {
            "project": project
        }
    })


@admin_projects_bp.route("/api/projects", methods=["POST"])
@login_required
@require_permission("project:create")
def api_project_create():
    """
    创建项目 API
    
    Request Body:
        {
            "name": "项目名称",      // 必填，唯一
            "code": "project_code",  // 必填，唯一，小写字母、数字和下划线
            "description": "描述",   // 可选
            "status": "active"       // 可选，默认 'active'
        }
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "project": {...},
                "message": "项目创建成功"
            }
        }
        
    Requirements:
        - US-1.1: 创建项目
        - US-1.2: 设置名称、描述和状态
        - AC-1: 项目名称唯一性校验
    """
    data = request.get_json() or {}
    
    name = (data.get("name") or "").strip()
    code = (data.get("code") or "").strip()
    description = (data.get("description") or "").strip() or None
    status = (data.get("status") or "active").strip()
    
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get('User-Agent', '')
    
    result = project_service.create_project(
        name=name,
        code=code,
        description=description,
        status=status,
        admin_user=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if result["success"]:
        return jsonify({
            "success": True,
            "data": {
                "project": result["project"],
                "message": f"项目 '{name}' 创建成功"
            }
        })
    else:
        return jsonify({
            "success": False,
            "error": result["error"]
        }), 400


@admin_projects_bp.route("/api/projects/<int:project_id>", methods=["PUT", "PATCH"])
@login_required
@require_permission_and_project("project:update", project_level='admin')
def api_project_update(project_id):
    """
    更新项目 API
    
    Args:
        project_id: 项目ID
    
    Request Body:
        {
            "name": "新项目名称",      // 可选
            "code": "new_code",        // 可选
            "description": "新描述",   // 可选
            "status": "archived"       // 可选
        }
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "project": {...},
                "message": "项目更新成功"
            }
        }
        
    Requirements:
        - US-1.1: 编辑项目
        - US-1.2: 设置名称、描述和状态
        - AC-1: 项目名称唯一性校验
    """
    data = request.get_json() or {}
    
    # 只提取提供的字段
    name = data.get("name")
    if name is not None:
        name = name.strip() if name else None
    
    code = data.get("code")
    if code is not None:
        code = code.strip() if code else None
    
    description = data.get("description")
    if description is not None:
        description = description.strip() if description else None
    
    status = data.get("status")
    if status is not None:
        status = status.strip() if status else None
    
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get('User-Agent', '')
    
    result = project_service.update_project(
        project_id=project_id,
        name=name,
        code=code,
        description=description,
        status=status,
        admin_user=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if result["success"]:
        return jsonify({
            "success": True,
            "data": {
                "project": result["project"],
                "message": "项目更新成功"
            }
        })
    else:
        status_code = 404 if result["error"] == "项目不存在" else 400
        return jsonify({
            "success": False,
            "error": result["error"]
        }), status_code


@admin_projects_bp.route("/api/projects/batch-delete", methods=["POST"])
@login_required
@require_permission("project:delete")
def api_projects_batch_delete():
    """
    批量删除项目 API
    
    只能删除空项目（没有活跃队列的项目）。
    默认项目（code='default'）不可删除。
    
    Request Body:
        {
            "project_ids": [1, 2, 3],  // 要删除的项目ID列表
            "force": false             // 是否强制删除（可选）
        }
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "deleted_count": 2,
                "failed_count": 1,
                "failed_projects": [
                    {"id": 3, "name": "xxx", "error": "项目有活跃队列"}
                ]
            }
        }
    """
    data = request.get_json() or {}
    project_ids = data.get("project_ids") or []
    force = data.get("force", False)
    
    if not project_ids:
        return jsonify({"success": False, "error": "请选择要删除的项目"}), 400
    
    # 服务端再次检查 Redis 中的项目列表，确保权限控制到位
    redis_project_names = set()
    try:
        from funboost.core.active_cousumer_info_getter import QueuesConusmerParamsGetter
        redis_project_names = set(QueuesConusmerParamsGetter().get_all_project_names())
    except Exception as e:
        # Redis 连接失败时，如果不是强制删除，则拒绝操作
        if not force:
            return jsonify({
                "success": False, 
                "error": f"无法连接 Redis 验证项目状态：{str(e)}。如需强制删除，请使用强制删除选项。"
            }), 500
    
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get('User-Agent', '')
    
    deleted_count = 0
    failed_projects = []
    
    for project_id in project_ids:
        # 先获取项目信息，检查是否在 Redis 中
        project_info = project_service.get_project(project_id)
        if not project_info:
            failed_projects.append({
                "id": project_id,
                "name": f"项目{project_id}",
                "error": "项目不存在"
            })
            continue
        
        # 服务端检查：如果项目在 Redis 中有队列，且不是强制删除，则拒绝
        if not force and project_info.get("code") in redis_project_names:
            failed_projects.append({
                "id": project_id,
                "name": project_info.get("name", f"项目{project_id}"),
                "error": "项目有活跃队列，无法删除"
            })
            continue
        
        result = project_service.delete_project(
            project_id=project_id,
            force=force,
            admin_user=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if result["success"]:
            deleted_count += 1
        else:
            failed_projects.append({
                "id": project_id,
                "name": project_info.get("name", f"项目{project_id}"),
                "error": result["error"]
            })
    
    return jsonify({
        "success": True,
        "data": {
            "deleted_count": deleted_count,
            "failed_count": len(failed_projects),
            "failed_projects": failed_projects
        }
    })


@admin_projects_bp.route("/api/projects/<int:project_id>", methods=["DELETE"])
@login_required
@require_permission_and_project("project:delete", project_level='admin')
def api_project_delete(project_id):
    """
    删除项目 API
    
    删除规则：
    1. 默认项目（code='default'）不可删除
    2. 如果项目在 Redis 中有活跃队列，需要使用 force=true 参数强制删除
    3. 用户关联会自动清理
    
    Args:
        project_id: 项目ID
    
    Query Parameters:
        force: 是否强制删除（可选，默认 false）
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "message": "项目删除成功",
                "removed_user_count": 0
            }
        }
        
    Requirements:
        - US-1.1: 删除项目
        - AC-1: 可以删除空项目（无队列关联）
    """
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get('User-Agent', '')
    
    # 获取 force 参数
    force = request.args.get("force", "false").lower() in ("true", "1", "yes")
    
    result = project_service.delete_project(
        project_id=project_id,
        force=force,
        admin_user=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if result["success"]:
        return jsonify({
            "success": True,
            "data": {
                "message": "项目删除成功",
                "removed_user_count": result.get("removed_user_count", 0)
            }
        })
    else:
        status_code = 404 if result["error"] == "项目不存在" else 400
        return jsonify({
            "success": False,
            "error": result["error"]
        }), status_code


# ==================== 项目用户管理 API ====================


@admin_projects_bp.route("/api/projects/<int:project_id>/users")
@login_required
@require_permission("project:read")
def api_project_users_list(project_id):
    """
    获取项目用户列表 API
    
    Args:
        project_id: 项目ID
    
    Query Parameters:
        page: 页码（从1开始，默认1）
        page_size: 每页大小（默认50）
        search: 搜索关键词（可选），匹配用户名或邮箱
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "users": [...],
                "total": 10,
                "page": 1,
                "page_size": 50,
                "total_pages": 1,
                "project": {...}
            }
        }
        
    Requirements:
        - US-2.1: 将用户分配到特定项目
        - US-2.2: 为用户设置项目级别的权限
        - AC-2: 项目权限
    """
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 50, type=int)
    search = request.args.get("search", "").strip()
    
    # 限制 page_size 最大值
    if page_size > 100:
        page_size = 100
    
    result = project_service.get_project_users(
        project_id=project_id,
        page=page,
        page_size=page_size,
        search=search if search else None
    )
    
    if result["success"]:
        return jsonify({
            "success": True,
            "data": {
                "users": result["users"],
                "total": result["total"],
                "page": result["page"],
                "page_size": result["page_size"],
                "total_pages": result["total_pages"],
                "project": result["project"]
            }
        })
    else:
        status_code = 404 if "不存在" in result["error"] else 400
        return jsonify({
            "success": False,
            "error": result["error"]
        }), status_code


@admin_projects_bp.route("/api/projects/<int:project_id>/users", methods=["POST"])
@login_required
@require_permission_and_project("project:admin", project_level='admin')
def api_project_add_user(project_id):
    """
    添加用户到项目 API
    
    Args:
        project_id: 项目ID
    
    Request Body:
        {
            "user_id": 1,                    // 必填，用户ID
            "permission_level": "read"       // 可选，默认 'read'，可选 'read', 'write', 'admin'
        }
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "user_project": {...},
                "message": "用户添加成功"
            }
        }
        
    Requirements:
        - US-2.1: 将用户分配到特定项目
        - US-2.2: 为用户设置项目级别的权限
        - AC-2: 可以为用户分配项目访问权限
    """
    data = request.get_json() or {}
    
    user_id = data.get("user_id")
    permission_level = (data.get("permission_level") or "read").strip()
    
    # 验证 user_id
    if user_id is None:
        return jsonify({
            "success": False,
            "error": "用户ID不能为空"
        }), 400
    
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "error": "用户ID必须是整数"
        }), 400
    
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get('User-Agent', '')
    
    result = project_service.add_user_to_project(
        user_id=user_id,
        project_id=project_id,
        permission_level=permission_level,
        admin_user=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if result["success"]:
        return jsonify({
            "success": True,
            "data": {
                "user_project": result["user_project"],
                "message": "用户添加成功"
            }
        })
    else:
        status_code = 404 if "不存在" in result["error"] else 400
        return jsonify({
            "success": False,
            "error": result["error"]
        }), status_code


@admin_projects_bp.route("/api/projects/<int:project_id>/users/<int:user_id>", methods=["PUT", "PATCH"])
@login_required
@require_permission_and_project("project:admin", project_level='admin')
def api_project_update_user_permission(project_id, user_id):
    """
    更新用户项目权限 API
    
    Args:
        project_id: 项目ID
        user_id: 用户ID
    
    Request Body:
        {
            "permission_level": "write"      // 必填，可选 'read', 'write', 'admin'
        }
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "user_project": {...},
                "message": "权限更新成功"
            }
        }
        
    Requirements:
        - US-2.2: 为用户设置项目级别的权限
        - AC-2: 支持项目级别的权限控制（read/write/admin）
    """
    data = request.get_json() or {}
    
    permission_level = data.get("permission_level")
    
    # 验证 permission_level
    if not permission_level:
        return jsonify({
            "success": False,
            "error": "权限级别不能为空"
        }), 400
    
    permission_level = permission_level.strip()
    
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get('User-Agent', '')
    
    result = project_service.update_user_project_permission(
        user_id=user_id,
        project_id=project_id,
        permission_level=permission_level,
        admin_user=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if result["success"]:
        return jsonify({
            "success": True,
            "data": {
                "user_project": result["user_project"],
                "message": "权限更新成功"
            }
        })
    else:
        status_code = 404 if "不存在" in result["error"] else 400
        return jsonify({
            "success": False,
            "error": result["error"]
        }), status_code


@admin_projects_bp.route("/api/projects/<int:project_id>/users/<int:user_id>", methods=["DELETE"])
@login_required
@require_permission_and_project("project:admin", project_level='admin')
def api_project_remove_user(project_id, user_id):
    """
    从项目移除用户 API
    
    Args:
        project_id: 项目ID
        user_id: 用户ID
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "message": "用户已从项目移除"
            }
        }
        
    Requirements:
        - US-2.1: 将用户分配到特定项目（包括移除）
        - AC-2: 可以为用户分配项目访问权限
    """
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get('User-Agent', '')
    
    result = project_service.remove_user_from_project(
        user_id=user_id,
        project_id=project_id,
        admin_user=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if result["success"]:
        return jsonify({
            "success": True,
            "data": {
                "message": "用户已从项目移除"
            }
        })
    else:
        status_code = 404 if "不存在" in result["error"] else 400
        return jsonify({
            "success": False,
            "error": result["error"]
        }), status_code


# ==================== 项目同步 API ====================


@admin_projects_bp.route("/api/projects/sync", methods=["POST"])
@login_required
@require_permission("project:admin")
def api_project_sync_from_redis():
    """
    从 Redis 同步项目 API
    
    从 funboost 框架的 Redis 存储中同步项目名称到数据库。
    项目名称来源于队列任务配置中的 project_name 参数。
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "created_count": 2,
                "existing_count": 3,
                "created_projects": [...],
                "message": "同步完成：新建 2 个项目，已存在 3 个项目"
            }
        }
        
    Requirements:
        - US-1.1: 系统能够自动从 Redis 同步队列任务中配置的项目名称
        - AC-1: 提供手动触发同步的 API 接口
    """
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get('User-Agent', '')
    
    result = project_service.sync_projects_from_redis(
        admin_user=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if result["success"]:
        return jsonify({
            "success": True,
            "data": {
                "created_count": result["created_count"],
                "existing_count": result["existing_count"],
                "created_projects": result["created_projects"],
                "message": result.get("message", "同步完成")
            }
        })
    else:
        return jsonify({
            "success": False,
            "error": result["error"]
        }), 500

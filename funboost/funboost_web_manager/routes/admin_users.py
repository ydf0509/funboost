# -*- coding: utf-8 -*-
"""
用户管理路由模块

包含：
- 用户列表 /users
- 创建用户 /users/create
- 编辑用户 /users/<user_name>/edit
- 切换用户状态 /users/<user_name>/toggle_status
- 解锁用户 /users/<user_name>/unlock
- 重置密码 /users/<user_name>/reset_password
"""

import json
import secrets
import string

from flask import Blueprint, request, jsonify, redirect
from flask_login import login_required, current_user

from funboost.funboost_web_manager.user_models import (
    get_session,
    WebManagerUser,
    Role,
)
from funboost.funboost_web_manager.models.project import UserProject, Project
from funboost.funboost_web_manager.services.password_service import PasswordService
from funboost.funboost_web_manager.services.audit_service import AuditEventType
from funboost.funboost_web_manager.services.project_service import ProjectService
from funboost.funboost_web_manager.routes.utils import (
    require_permission,
    audit_service,
    email_service,
    permission_service,
)


admin_users_bp = Blueprint("admin_users", __name__)


# 注意：/users 页面由前端静态文件处理，不需要后端路由
# 已移除 GET /users 路由，避免与前端静态文件冲突导致重定向循环


@admin_users_bp.route("/api/users")
@login_required
@require_permission("user:read")
def api_user_list():
    """用户列表 API - 返回 JSON

    包含用户的所属项目信息
    """
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "")

    db_session = get_session()
    try:
        query = db_session.query(WebManagerUser)

        # 搜索过滤
        if search:
            query = query.filter(
                (WebManagerUser.user_name.like(f"%{search}%"))
                | (WebManagerUser.email.like(f"%{search}%"))
            )

        # 状态过滤
        if status_filter:
            query = query.filter(WebManagerUser.status == status_filter)

        # 计算总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        users = (
            query.order_by(WebManagerUser.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        # 获取所有用户的 ID
        user_ids = [user.id for user in users]

        # 批量查询用户的项目关联信息
        user_projects_map = {}
        if user_ids:
            user_projects = (
                db_session.query(UserProject)
                .filter(UserProject.user_id.in_(user_ids))
                .all()
            )

            for up in user_projects:
                if up.user_id not in user_projects_map:
                    user_projects_map[up.user_id] = []
                user_projects_map[up.user_id].append(
                    {
                        "project_id": up.project_id,
                        "project_name": up.project.name if up.project else None,
                        "project_code": up.project.code if up.project else None,
                        "permission_level": up.permission_level,
                    }
                )

        # 转换为字典，并添加项目信息
        users_list = []
        for user in users:
            user_dict = user.to_dict()
            user_dict["projects"] = user_projects_map.get(user.id, [])
            users_list.append(user_dict)

        # 计算分页信息
        total_pages = (total + page_size - 1) // page_size

        return jsonify(
            {
                "success": True,
                "data": {
                    "users": users_list,
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": total_pages,
                },
            }
        )
    finally:
        db_session.close()


@admin_users_bp.route("/users/create", methods=["POST"])
@admin_users_bp.route("/api/users/create", methods=["POST"])  # API 别名，供前端使用
@login_required
@require_permission("user:create")
def user_create():
    """创建用户 API - POST 返回 JSON（GET 由前端静态文件处理）"""
    # POST 请求处理 - 返回 JSON
    user_name = request.form.get("user_name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    role_names = request.form.getlist("roles")
    projects_json = request.form.get("projects", "[]")  # 项目授权信息

    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get("User-Agent", "")

    # 解析项目授权信息
    try:
        projects_data = json.loads(projects_json) if projects_json else []
    except json.JSONDecodeError:
        projects_data = []

    # 验证用户名
    if not user_name or len(user_name) < 3:
        return jsonify({"success": False, "error": "用户名至少需要3个字符"})

    # 验证密码强度
    is_valid, errors = PasswordService.validate_strength(password)
    if not is_valid:
        return jsonify({"success": False, "error": "、".join(errors)})

    # 检查用户名是否已存在
    db_session = get_session()
    try:
        existing = (
            db_session.query(WebManagerUser).filter_by(user_name=user_name).first()
        )
        if existing:
            return jsonify({"success": False, "error": "用户名已存在"})

        # 创建用户
        hashed_password = PasswordService.hash_password(password)
        user = WebManagerUser(
            user_name=user_name,
            password=hashed_password,
            email=email if email else None,
            status="active",
            force_password_change=True,  # 新用户首次登录需要修改密码
        )

        # 分配角色
        if role_names:
            roles = db_session.query(Role).filter(Role.name.in_(role_names)).all()
            user.roles = roles
        else:
            # 默认分配 viewer 角色
            viewer_role = db_session.query(Role).filter_by(name="viewer").first()
            if viewer_role:
                user.roles = [viewer_role]

        db_session.add(user)
        db_session.commit()

        # 获取新创建用户的 ID
        new_user_id = user.id

        # 分配项目权限
        project_assignments = []
        if projects_data:
            project_service = ProjectService()
            for project_info in projects_data:
                project_id = project_info.get("projectId")
                permission_level = project_info.get("permissionLevel", "read")

                if project_id:
                    result = project_service.add_user_to_project(
                        user_id=new_user_id,
                        project_id=project_id,
                        permission_level=permission_level,
                        admin_user=current_user.id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                    )
                    if result.get("success"):
                        project_assignments.append(
                            {
                                "project_id": project_id,
                                "permission_level": permission_level,
                            }
                        )

        # 记录审计日志
        audit_service.log(
            AuditEventType.USER_CREATE,
            user_name=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "created_user": user_name,
                "roles": role_names,
                "projects": project_assignments,
            },
        )

        return jsonify({"success": True, "message": f"用户 {user_name} 创建成功"})

    except Exception as e:
        db_session.rollback()
        return jsonify({"success": False, "error": str(e)})
    finally:
        db_session.close()


@admin_users_bp.route("/users/<user_name>/edit", methods=["POST"])
@login_required
@require_permission("user:update")
def user_edit(user_name):
    """编辑用户 API - POST 返回 JSON（GET 由前端静态文件处理）"""
    # POST 请求处理 - 返回 JSON
    email = request.form.get("email", "").strip()
    status = request.form.get("status", "active")
    role_names = request.form.getlist("roles")

    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get("User-Agent", "")

    db_session = get_session()
    try:
        user = db_session.query(WebManagerUser).filter_by(user_name=user_name).first()
        if not user:
            return jsonify({"success": False, "error": "用户不存在"})

        old_data = user.to_dict()

        # 更新用户信息
        user.email = email if email else None
        user.status = status

        # 更新角色
        if role_names:
            roles = db_session.query(Role).filter(Role.name.in_(role_names)).all()
            user.roles = roles

        db_session.commit()

        # 记录审计日志
        audit_service.log(
            AuditEventType.USER_UPDATE,
            user_name=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "target_user": user_name,
                "old_data": old_data,
                "new_status": status,
                "new_roles": role_names,
            },
        )

        return jsonify({"success": True, "message": f"用户 {user_name} 更新成功"})

    except Exception as e:
        db_session.rollback()
        return jsonify({"success": False, "error": str(e)})
    finally:
        db_session.close()


@admin_users_bp.route("/api/users/<user_name>/edit", methods=["POST"])
@login_required
@require_permission("user:update")
def api_user_edit(user_name):
    """编辑用户 API - 返回 JSON"""
    # 支持 JSON 和 FormData 两种格式
    if request.is_json:
        data = request.get_json()
        email = data.get("email", "").strip()
        status = data.get("status", "active")
        role_names = data.get("roles", [])
    else:
        email = request.form.get("email", "").strip()
        status = request.form.get("status", "active")
        role_names = request.form.getlist("roles")

    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get("User-Agent", "")

    db_session = get_session()
    try:
        user = db_session.query(WebManagerUser).filter_by(user_name=user_name).first()
        if not user:
            return jsonify({"success": False, "error": "用户不存在"})

        old_data = user.to_dict()

        # 更新用户信息
        user.email = email if email else None
        user.status = status

        # 更新角色 - 如果提供了角色列表则更新
        if role_names:
            roles = db_session.query(Role).filter(Role.name.in_(role_names)).all()
            user.roles = roles
        else:
            # 如果没有提供角色，清空角色
            user.roles = []

        db_session.commit()

        # 记录审计日志
        audit_service.log(
            AuditEventType.USER_UPDATE,
            user_name=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "target_user": user_name,
                "old_data": old_data,
                "new_status": status,
                "new_roles": role_names,
            },
        )

        return jsonify({"success": True, "message": f"用户 {user_name} 更新成功"})

    except Exception as e:
        db_session.rollback()
        return jsonify({"success": False, "error": str(e)})
    finally:
        db_session.close()


@admin_users_bp.route("/users/<user_name>/toggle_status", methods=["POST"])
@login_required
@require_permission("user:update")
def user_toggle_status(user_name):
    """启用/禁用用户"""
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get("User-Agent", "")

    db_session = get_session()
    try:
        user = db_session.query(WebManagerUser).filter_by(user_name=user_name).first()
        if not user:
            return jsonify({"success": False, "error": "用户不存在"})

        # 不能禁用自己
        if user_name == current_user.id:
            return jsonify({"success": False, "error": "不能禁用自己的账户"})

        old_status = user.status
        new_status = "disabled" if user.status == "active" else "active"
        user.status = new_status

        db_session.commit()

        # 记录审计日志
        audit_service.log(
            AuditEventType.USER_STATUS_CHANGE,
            user_name=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "target_user": user_name,
                "old_status": old_status,
                "new_status": new_status,
            },
        )

        return jsonify({"success": True, "new_status": new_status})

    except Exception as e:
        db_session.rollback()
        return jsonify({"success": False, "error": str(e)})
    finally:
        db_session.close()


@admin_users_bp.route("/users/<user_name>/delete", methods=["DELETE"])
@login_required
@require_permission("user:delete")
def user_delete(user_name):
    """删除用户"""
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get("User-Agent", "")

    # 不能删除自己
    if user_name == current_user.id:
        return jsonify({"success": False, "error": "不能删除自己的账户"})

    db_session = get_session()
    try:
        user = db_session.query(WebManagerUser).filter_by(user_name=user_name).first()
        if not user:
            return jsonify({"success": False, "error": "用户不存在"})

        # 记录审计日志（在删除前记录）
        audit_service.log(
            (
                AuditEventType.USER_DELETE
                if hasattr(AuditEventType, "USER_DELETE")
                else AuditEventType.USER_STATUS_CHANGE
            ),
            user_name=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"deleted_user": user_name, "email": user.email},
        )

        # 删除用户
        db_session.delete(user)
        db_session.commit()

        return jsonify({"success": True})

    except Exception as e:
        db_session.rollback()
        return jsonify({"success": False, "error": str(e)})
    finally:
        db_session.close()


@admin_users_bp.route("/users/<user_name>/unlock", methods=["POST"])
@login_required
@require_permission("user:update")
def user_unlock(user_name):
    """解锁用户"""
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get("User-Agent", "")

    db_session = get_session()
    try:
        user = db_session.query(WebManagerUser).filter_by(user_name=user_name).first()
        if not user:
            return jsonify({"success": False, "error": "用户不存在"})

        # 清除锁定状态
        user.locked_until = None
        user.failed_login_count = 0
        if user.status == "locked":
            user.status = "active"

        db_session.commit()

        # 记录审计日志
        audit_service.log(
            AuditEventType.USER_UNLOCK,
            user_name=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"target_user": user_name},
        )

        return jsonify({"success": True})

    except Exception as e:
        db_session.rollback()
        return jsonify({"success": False, "error": str(e)})
    finally:
        db_session.close()


@admin_users_bp.route("/users/<user_name>/reset_password", methods=["POST"])
@login_required
@require_permission("user:update")
def admin_reset_password(user_name):
    """管理员重置用户密码"""
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get("User-Agent", "")

    db_session = get_session()
    try:
        user = db_session.query(WebManagerUser).filter_by(user_name=user_name).first()
        if not user:
            return jsonify({"success": False, "error": "用户不存在"})

        # 生成随机强密码
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        new_password = "".join(secrets.choice(alphabet) for _ in range(12))

        # 确保密码满足强度要求
        new_password = new_password[:8] + "Aa1!" + new_password[8:]

        # 更新密码
        user.password = PasswordService.hash_password(new_password)
        user.force_password_change = True
        user.locked_until = None
        user.failed_login_count = 0

        db_session.commit()

        # 记录审计日志
        audit_service.log(
            AuditEventType.PASSWORD_RESET_BY_ADMIN,
            user_name=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"target_user": user_name},
        )

        # 尝试发送邮件通知
        email_sent = False
        if user.email:
            success, _ = email_service.send_password_notification(
                user.email, new_password, user_name
            )
            email_sent = success

        return jsonify(
            {"success": True, "new_password": new_password, "email_sent": email_sent}
        )

    except Exception as e:
        db_session.rollback()
        return jsonify({"success": False, "error": str(e)})
    finally:
        db_session.close()


@admin_users_bp.route("/api/user/permissions")
@login_required
def api_current_user_permissions():
    """
    获取当前登录用户的权限列表 API（增强版）

    用于前端菜单权限控制，返回当前用户拥有的所有权限代码、
    权限详情（含 action_type 和 project_scope）以及角色列表。

    Returns:
        JSON: {
            "success": true,
            "data": {
                "user_name": "admin",
                "permissions": ["user:read", "user:create", "user:update", ...],
                "permission_details": [
                    {
                        "code": "user:read",
                        "name": "查看用户",
                        "action_type": "read",
                        "project_scope": null
                    },
                    ...
                ],
                "roles": ["admin"]
            }
        }

    Requirements:
        - 5.3: WHEN the response is generated, THE Permission_Service SHALL include
               action_type information for each Permission_Item
    """
    user_name = current_user.id

    # 获取用户详细权限信息（含 action_type 和 project_scope）
    user_permissions = permission_service.get_user_permissions_detailed(user_name)

    return jsonify(
        {
            "success": True,
            "data": {
                "user_name": user_name,
                "permissions": user_permissions["permissions"],
                "permission_details": user_permissions["details"],
                "roles": user_permissions["roles"],
            },
        }
    )


@admin_users_bp.route("/api/user/permissions/tree")
@login_required
def api_current_user_permissions_tree():
    """
    获取当前登录用户的权限树 API

    返回完整的权限树，并标记用户拥有的权限。

    Returns:
        JSON: {
            "success": true,
            "data": {
                "user_name": "admin",
                "tree": [
                    {
                        "code": "user",
                        "name": "用户管理",
                        "permissions": [
                            {"code": "user:read", "name": "查看用户", "has_permission": true},
                            ...
                        ]
                    },
                    ...
                ]
            }
        }
    """
    user_name = current_user.id

    # 获取用户权限树
    tree = permission_service.get_user_permissions_tree(user_name)

    return jsonify({"success": True, "data": {"user_name": user_name, "tree": tree}})


@admin_users_bp.route("/api/users/export")
@login_required
@require_permission("user:export")
def api_export_users():
    """
    导出用户列表为 CSV 文件

    需要 user:export 权限

    Query Parameters:
        - status: 筛选用户状态 (active/inactive)
        - role: 筛选角色名称

    Returns:
        CSV 文件下载
    """
    import csv
    import io
    from datetime import datetime
    from flask import Response

    try:
        db_session = get_session()

        # 构建查询
        query = db_session.query(WebManagerUser)

        # 状态筛选
        status = request.args.get("status")
        if status:
            query = query.filter(WebManagerUser.status == status)

        # 角色筛选
        role_name = request.args.get("role")
        if role_name:
            query = query.join(WebManagerUser.roles).filter(Role.name == role_name)

        users = query.all()

        # 创建 CSV（添加 UTF-8 BOM 头解决 Excel 中文乱码）
        output = io.StringIO()
        output.write("\ufeff")  # UTF-8 BOM
        writer = csv.writer(output)

        # 写入表头
        writer.writerow(
            ["ID", "用户名", "邮箱", "状态", "角色", "创建时间", "锁定到期时间"]
        )

        # 写入数据
        for user in users:
            roles = ", ".join([r.name for r in user.roles])
            writer.writerow(
                [
                    user.id,
                    user.user_name,
                    user.email or "",
                    user.status,
                    roles,
                    (
                        user.created_at.strftime("%Y-%m-%d %H:%M:%S")
                        if user.created_at
                        else ""
                    ),
                    (
                        user.locked_until.strftime("%Y-%m-%d %H:%M:%S")
                        if user.locked_until
                        else ""
                    ),
                ]
            )

        db_session.close()

        # 记录审计日志
        ip_address = request.remote_addr or "unknown"
        user_agent = request.headers.get("User-Agent", "")
        audit_service.log(
            AuditEventType.USER_UPDATE,  # 使用现有的事件类型
            user_name=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "action": "export_users",
                "count": len(users),
                "filters": {"status": status, "role": role_name},
            },
        )

        # 返回 CSV 文件
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            },
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"导出用户失败: {str(e)}"})

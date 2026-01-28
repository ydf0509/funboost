# -*- coding: utf-8 -*-
"""
用户个人设置路由模块

提供用户自助功能：
- 查看个人信息
- 修改密码
- 修改邮箱
- 获取用户可访问的项目列表
- 设置当前项目

Requirements:
    - US-3.2: 作为用户，我希望在界面上能够切换当前查看的项目
    - AC-4: 项目切换 - 顶部导航栏显示项目选择器
"""

import re
from flask import Blueprint, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from funboost.funboost_web_manager.user_models import (
    get_session, WebManagerUser, LoginAttempt
)
from funboost.funboost_web_manager.services.password_service import PasswordService
from funboost.funboost_web_manager.services.audit_service import AuditService, AuditEventType
from funboost.funboost_web_manager.services.email_service import EmailService
from funboost.funboost_web_manager.services.project_service import ProjectService
from funboost.funboost_web_manager.routes.utils import get_client_ip, get_user_agent

profile_bp = Blueprint('profile', __name__)

# 注意：/profile 的 GET 请求由前端静态文件处理，这里不需要路由
# 只保留 API 路由


@profile_bp.route('/api/profile')
@login_required
def api_profile():
    """API 接口 - 返回 JSON 格式的用户信息"""
    db_session = get_session()
    try:
        # 获取当前用户信息
        user = db_session.query(WebManagerUser).filter_by(
            user_name=current_user.id
        ).first()
        
        if not user:
            return jsonify({"success": False, "error": "用户不存在"}), 404
        
        # 获取最后一次成功登录记录
        last_login = db_session.query(LoginAttempt).filter_by(
            user_name=user.user_name,
            success=True
        ).order_by(LoginAttempt.created_at.desc()).first()
        
        last_login_info = None
        if last_login:
            last_login_info = {
                "time": last_login.created_at.strftime("%Y-%m-%d %H:%M:%S") if last_login.created_at else None,
                "ip": last_login.ip_address
            }
        
        return jsonify({
            "success": True,
            "data": {
                "user_name": user.user_name,
                "email": user.email,
                "status": user.status,
                "roles": [role.name for role in user.roles] if user.roles else [],
                "last_login": last_login_info
            }
        })
    
    finally:
        db_session.close()


@profile_bp.route('/profile/change-password', methods=['POST'])
@login_required
def profile_change_password():
    """修改密码 - POST 返回 JSON（GET 由前端静态文件处理）"""
    # POST 请求处理密码修改 - 返回 JSON
    current_password = request.form.get('current_password', '').strip()
    new_password = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    
    # 基本验证
    if not all([current_password, new_password, confirm_password]):
        return jsonify({"success": False, "error": "所有字段都是必填的"})
    
    if new_password != confirm_password:
        return jsonify({"success": False, "error": "新密码和确认密码不匹配"})
    
    db_session = get_session()
    try:
        # 获取当前用户
        user = db_session.query(WebManagerUser).filter_by(
            user_name=current_user.id
        ).first()
        
        if not user:
            return jsonify({"success": False, "error": "用户不存在"})
        
        # 验证当前密码
        if not PasswordService.verify_password(current_password, user.password):
            return jsonify({"success": False, "error": "当前密码不正确"})
        
        # 验证新密码强度
        is_valid, errors = PasswordService.validate_strength(new_password)
        if not is_valid:
            return jsonify({"success": False, "error": "、".join(errors)})
        
        # 更新密码
        user.password = PasswordService.hash_password(new_password)
        user.force_password_change = False  # 清除强制改密码标记
        user.updated_at = datetime.now()
        
        db_session.commit()
        
        # 记录审计日志
        AuditService().log(
            event_type=AuditEventType.PASSWORD_CHANGE,
            user_name=user.user_name,
            ip_address=get_client_ip(),
            user_agent=get_user_agent(),
            details={'action': 'user_self_change_password'}
        )
        
        return jsonify({"success": True, "message": "密码修改成功"})
    
    except Exception as e:
        db_session.rollback()
        return jsonify({"success": False, "error": f"密码修改失败：{str(e)}"})
    
    finally:
        db_session.close()


@profile_bp.route('/profile/change-email', methods=['POST'])
@login_required
def profile_change_email():
    """修改邮箱 - POST 返回 JSON（GET 由前端静态文件处理）"""
    # POST 请求处理邮箱修改 - 返回 JSON
    new_email = request.form.get('new_email', '').strip()
    
    # 基本验证
    if not new_email:
        return jsonify({"success": False, "error": "邮箱地址不能为空"})
    
    # 简单的邮箱格式验证
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, new_email):
        return jsonify({"success": False, "error": "邮箱格式不正确"})
    
    db_session = get_session()
    try:
        # 获取当前用户
        user = db_session.query(WebManagerUser).filter_by(
            user_name=current_user.id
        ).first()
        
        if not user:
            return jsonify({"success": False, "error": "用户不存在"})
        
        # 检查邮箱是否已被其他用户使用
        existing_user = db_session.query(WebManagerUser).filter(
            WebManagerUser.email == new_email,
            WebManagerUser.id != user.id
        ).first()
        
        if existing_user:
            return jsonify({"success": False, "error": "该邮箱已被其他用户使用"})
        
        # 发送验证邮件
        email_service = EmailService()
        verification_token = email_service.generate_email_verification_token(user.id, new_email)
        
        if verification_token:
            verification_link = request.url_root.rstrip('/') + url_for(
                'profile.verify_email', token=verification_token
            )
            
            success = email_service.send_email_verification(new_email, verification_link)
            
            if success:
                return jsonify({"success": True, "message": "验证邮件已发送到新邮箱，请查收并点击验证链接"})
            else:
                return jsonify({"success": False, "error": "邮件发送失败，请稍后重试"})
        else:
            return jsonify({"success": False, "error": "生成验证令牌失败，请稍后重试"})
    
    except Exception as e:
        return jsonify({"success": False, "error": f"邮箱修改失败：{str(e)}"})
    
    finally:
        db_session.close()


@profile_bp.route('/profile/verify-email/<token>')
def verify_email(token: str):
    """验证邮箱 - 重定向到前端"""
    email_service = EmailService()
    result = email_service.verify_email_token(token)
    
    if result['success']:
        db_session = get_session()
        try:
            user = db_session.query(WebManagerUser).filter_by(
                id=result['user_id']
            ).first()
            
            if user:
                old_email = user.email
                user.email = result['new_email']
                user.updated_at = datetime.now()
                db_session.commit()
                
                # 记录审计日志
                AuditService().log(
                    event_type=AuditEventType.USER_UPDATE,
                    user_name=user.user_name,
                    ip_address=get_client_ip(),
                    user_agent=get_user_agent(),
                    details={
                        'action': 'email_change',
                        'old_email': old_email,
                        'new_email': result['new_email']
                    }
                )
                
                return redirect("/profile/?message=email_verified")
            else:
                return redirect("/profile/?error=user_not_found")
        
        except Exception as e:
            db_session.rollback()
            return redirect("/profile/?error=update_failed")
        
        finally:
            db_session.close()
    else:
        return redirect("/profile/?error=invalid_token")



# ==================== 用户项目 API ====================

@profile_bp.route('/api/user/projects')
@login_required
def api_user_projects():
    """
    获取当前用户可访问的项目列表
    
    只需要登录即可访问，无需特殊权限。
    
    Returns:
        JSON: {
            "success": bool,
            "data": {
                "projects": [
                    {
                        "id": int,
                        "name": str,
                        "code": str,
                        "description": str,
                        "status": str,
                        "permission_level": str,  # 用户在该项目的权限级别
                        "is_global_admin": bool,  # 是否为全局管理员
                        "created_at": str,
                        "updated_at": str
                    },
                    ...
                ]
            },
            "error": str|None
        }
        
    Requirements:
        - US-3.2: 作为用户，我希望在界面上能够切换当前查看的项目
        - AC-4: 项目切换 - 顶部导航栏显示项目选择器
    """
    try:
        project_service = ProjectService()
        
        # 获取当前用户可访问的项目列表
        # current_user.id 是用户名（字符串），ProjectService 支持按用户名查询
        projects = project_service.get_user_projects(current_user.id)
        
        return jsonify({
            "success": True,
            "data": {
                "projects": projects
            },
            "error": None
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "error": f"获取项目列表失败：{str(e)}"
        }), 500


@profile_bp.route('/api/user/current-project', methods=['PUT'])
@login_required
def api_set_current_project():
    """
    设置当前项目（可选，用于服务端记录）
    
    此端点用于记录用户当前选择的项目，可用于：
    1. 服务端记录用户偏好
    2. 审计日志记录
    3. 未来可能的服务端会话管理
    
    注意：前端主要使用 localStorage 存储当前项目，此端点为可选功能。
    
    Request Body:
        {
            "project_id": int  # 项目ID
        }
        
    Returns:
        JSON: {
            "success": bool,
            "message": str|None,
            "error": str|None
        }
        
    Requirements:
        - US-3.2: 作为用户，我希望在界面上能够切换当前查看的项目
        - US-3.3: 作为用户，我希望系统能够记住我上次选择的项目
        - AC-4: 项目切换
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": None,
                "error": "请求数据不能为空"
            }), 400
        
        project_id = data.get('project_id')
        if project_id is None:
            return jsonify({
                "success": False,
                "message": None,
                "error": "project_id 不能为空"
            }), 400
        
        # 验证 project_id 是整数
        try:
            project_id = int(project_id)
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "message": None,
                "error": "project_id 必须是整数"
            }), 400
        
        project_service = ProjectService()
        
        # 验证用户是否有该项目的访问权限
        if not project_service.has_project_access(current_user.id, project_id):
            return jsonify({
                "success": False,
                "message": None,
                "error": "您没有该项目的访问权限"
            }), 403
        
        # 获取项目信息
        project = project_service.get_project(project_id)
        if not project:
            return jsonify({
                "success": False,
                "message": None,
                "error": "项目不存在"
            }), 404
        
        # 记录审计日志（可选）
        AuditService().log(
            event_type=AuditEventType.USER_UPDATE,
            user_name=current_user.id,
            ip_address=get_client_ip(),
            user_agent=get_user_agent(),
            details={
                'action': 'set_current_project',
                'project_id': project_id,
                'project_name': project.get('name'),
                'project_code': project.get('code')
            }
        )
        
        return jsonify({
            "success": True,
            "message": f"已切换到项目：{project.get('name')}",
            "error": None
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": None,
            "error": f"设置当前项目失败：{str(e)}"
        }), 500

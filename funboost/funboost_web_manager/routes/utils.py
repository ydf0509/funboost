# -*- coding: utf-8 -*-
"""
路由公共工具模块

包含：
- 权限检查装饰器
- 公共表单类
- 服务实例获取
"""

from functools import wraps
from flask import flash, redirect, url_for, request, jsonify
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo

from funboost.funboost_web_manager.services.auth_service import AuthService
from funboost.funboost_web_manager.services.password_service import PasswordService
from funboost.funboost_web_manager.services.audit_service import AuditService, AuditEventType
from funboost.funboost_web_manager.services.permission_service import PermissionService
from funboost.funboost_web_manager.services.role_service import RoleService
from funboost.funboost_web_manager.services.password_reset_service import PasswordResetService
from funboost.funboost_web_manager.services.email_service import EmailService
from funboost.funboost_web_manager.services.encryption_service import get_encryption_service, DecryptionError


# ==================== 服务实例 ====================
# 全局服务实例，供所有路由模块使用

auth_service = AuthService()
audit_service = AuditService()
permission_service = PermissionService()
role_service = RoleService()
password_reset_service = PasswordResetService()
email_service = EmailService()

# 加密服务 - 配置密钥持久化存储路径
# 密钥文件存储在项目根目录的 .encryption_keys.json
import os
_key_storage_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    '.encryption_keys.json'
)
encryption_service = get_encryption_service(key_storage_path=_key_storage_path)


# ==================== 辅助函数 ====================

def get_client_ip():
    """获取客户端IP地址"""
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
    elif request.environ.get('HTTP_X_REAL_IP'):
        return request.environ['HTTP_X_REAL_IP']
    else:
        return request.environ.get('REMOTE_ADDR', 'unknown')


def get_user_agent():
    """获取用户代理字符串"""
    return request.headers.get('User-Agent', 'unknown')


def extract_password(password_data):
    """从请求数据中提取密码（支持加密和明文）
    
    Args:
        password_data: 密码数据（可能是加密格式或明文字符串）
        
    Returns:
        明文密码字符串
        
    Raises:
        DecryptionError: 解密失败
        ValueError: 无效的密码格式
    """
    return encryption_service.extract_password(password_data)


# ==================== 权限装饰器 ====================

def require_permission(permission_code):
    """
    权限检查装饰器（角色权限）
    
    用法:
        @require_permission("user:read")
        def user_list():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            is_api_request = (
                '/api/' in request.path or
                request.content_type and 'json' in request.content_type.lower() or
                request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
                request.headers.get('Accept', '').startswith('application/json') or
                request.method in ['POST', 'PUT', 'DELETE', 'PATCH']
            )

            if not current_user.is_authenticated:
                if is_api_request:
                    return jsonify({
                        "success": False,
                        "error": "请先登录",
                        "code": "UNAUTHORIZED"
                    }), 401
                flash("请先登录", category="error")
                return redirect(url_for("auth.login"))
            
            user_name = current_user.id
            if not permission_service.check_permission(user_name, permission_code):
                if is_api_request:
                    return jsonify({
                        "success": False,
                        "error": "您没有权限执行此操作",
                        "code": "FORBIDDEN"
                    }), 403
                flash("您没有权限访问此页面", category="error")
                return redirect(url_for("main.index"))
            
            return f(*args, **kwargs)
        
        # 存储权限代码，用于权限发现 API
        decorated_function._required_permission = permission_code
        return decorated_function
    return decorator


def require_project_permission(required_level: str = 'read', project_id_param: str = 'project_id'):
    """
    项目级别权限检查装饰器
    
    检查用户在特定项目中的权限级别。
    权限级别层次（从高到低）：admin > write > read
    
    用法:
        @require_project_permission('write')
        def update_project_data(project_id):
            ...
            
        # 自定义参数名
        @require_project_permission('admin', project_id_param='pid')
        def admin_action(pid):
            ...
    
    Args:
        required_level: 需要的权限级别，可选 'read', 'write', 'admin'
        project_id_param: URL 参数中项目ID的参数名，默认为 'project_id'
    """
    from flask import jsonify
    from funboost.funboost_web_manager.services.project_service import ProjectService
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"success": False, "error": "请先登录"}), 401
            
            # 从 URL 参数或 kwargs 中获取 project_id
            project_id = kwargs.get(project_id_param)
            if project_id is None:
                # 尝试从请求参数中获取
                project_id = request.args.get(project_id_param) or request.form.get(project_id_param)
                if request.is_json:
                    data = request.get_json() or {}
                    project_id = project_id or data.get(project_id_param)
            
            if project_id is None:
                return jsonify({"success": False, "error": "缺少项目ID参数"}), 400
            
            try:
                project_id = int(project_id)
            except (ValueError, TypeError):
                return jsonify({"success": False, "error": "项目ID必须是整数"}), 400
            
            # 检查项目权限
            project_service = ProjectService()
            user_name = current_user.id
            
            if not project_service.check_project_permission(user_name, project_id, required_level):
                return jsonify({
                    "success": False, 
                    "error": f"您在此项目中没有 {required_level} 权限"
                }), 403
            
            return f(*args, **kwargs)
        
        # 存储权限信息，用于权限发现
        decorated_function._required_project_permission = required_level
        return decorated_function
    return decorator


def require_permission_and_project(permission_code: str, project_level: str = None, project_id_param: str = 'project_id'):
    """
    同时检查角色权限和项目权限的装饰器
    
    用法:
        # 只检查角色权限
        @require_permission_and_project("project:read")
        def view_project(project_id):
            ...
            
        # 同时检查角色权限和项目权限
        @require_permission_and_project("project:update", project_level='write')
        def update_project(project_id):
            ...
    
    Args:
        permission_code: 角色权限代码
        project_level: 项目权限级别，可选 'read', 'write', 'admin'，为 None 时不检查项目权限
        project_id_param: URL 参数中项目ID的参数名
    """
    from flask import jsonify
    from funboost.funboost_web_manager.services.project_service import ProjectService
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"success": False, "error": "请先登录"}), 401
            
            user_name = current_user.id
            
            # 1. 检查角色权限
            if not permission_service.check_permission(user_name, permission_code):
                return jsonify({"success": False, "error": "您没有权限执行此操作"}), 403
            
            # 2. 如果需要，检查项目权限
            if project_level:
                # 从 URL 参数或 kwargs 中获取 project_id
                project_id = kwargs.get(project_id_param)
                if project_id is None:
                    project_id = request.args.get(project_id_param) or request.form.get(project_id_param)
                    if request.is_json:
                        data = request.get_json() or {}
                        project_id = project_id or data.get(project_id_param)
                
                if project_id is not None:
                    try:
                        project_id = int(project_id)
                        project_service = ProjectService()
                        
                        if not project_service.check_project_permission(user_name, project_id, project_level):
                            return jsonify({
                                "success": False, 
                                "error": f"您在此项目中没有 {project_level} 权限"
                            }), 403
                    except (ValueError, TypeError):
                        pass  # 如果 project_id 无效，跳过项目权限检查
            
            return f(*args, **kwargs)
        
        # 存储权限信息
        decorated_function._required_permission = permission_code
        if project_level:
            decorated_function._required_project_permission = project_level
        return decorated_function
    return decorator


# ==================== 表单类 ====================

class LoginForm(FlaskForm):
    """登录表单"""
    user_name = StringField("用户名", validators=[DataRequired(), Length(3, 64)])
    password = PasswordField("密码", validators=[DataRequired(), Length(3, 64)])
    remember_me = BooleanField("记住我")


class ForcePasswordChangeForm(FlaskForm):
    """强制改密码表单"""
    current_password = PasswordField("当前密码", validators=[DataRequired()])
    new_password = PasswordField("新密码", validators=[DataRequired(), Length(8, 64)])
    confirm_password = PasswordField("确认新密码", validators=[
        DataRequired(), 
        EqualTo('new_password', message='两次输入的密码不一致')
    ])
    submit = SubmitField("修改密码")


class ForgotPasswordForm(FlaskForm):
    """忘记密码表单"""
    email = StringField("邮箱", validators=[DataRequired(), Email(message="请输入有效的邮箱地址")])
    submit = SubmitField("发送重置链接")


class ResetPasswordForm(FlaskForm):
    """重置密码表单"""
    new_password = PasswordField("新密码", validators=[DataRequired(), Length(8, 64)])
    confirm_password = PasswordField("确认新密码", validators=[
        DataRequired(), 
        EqualTo('new_password', message='两次输入的密码不一致')
    ])
    submit = SubmitField("重置密码")

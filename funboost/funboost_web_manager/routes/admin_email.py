# -*- coding: utf-8 -*-
"""
邮件配置管理路由模块

提供邮件服务配置的 Web 界面，包括：
- 邮件配置页面
- 测试邮件功能
- 权限控制
"""

from flask import Blueprint, request, redirect, jsonify
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, BooleanField, SubmitField, RadioField
from wtforms.validators import DataRequired, NumberRange, Optional

from .utils import require_permission, get_client_ip, get_user_agent, audit_service, email_service


# 创建 Blueprint
admin_email_bp = Blueprint('admin_email', __name__)


# ==================== 表单类 ====================

class EmailConfigForm(FlaskForm):
    """邮件配置表单"""
    smtp_host = StringField("SMTP服务器", validators=[DataRequired()], 
                           render_kw={"placeholder": "例如: smtp.gmail.com"})
    smtp_port = IntegerField("端口", validators=[DataRequired(), NumberRange(min=1, max=65535)], 
                            default=587)
    smtp_username = StringField("用户名", validators=[Optional()], 
                               render_kw={"placeholder": "SMTP认证用户名（可选）"})
    smtp_password = PasswordField("密码", validators=[Optional()], 
                                 render_kw={"placeholder": "SMTP认证密码（可选）"})
    
    # 加密选项（单选）
    encryption = RadioField("加密方式", 
                           choices=[('tls', 'TLS'), ('ssl', 'SSL'), ('none', '无加密')], 
                           default='tls')
    
    sender_name = StringField("发件人名称", validators=[Optional()], 
                             render_kw={"placeholder": "例如: 系统管理员"})
    sender_email = StringField("发件人邮箱", validators=[DataRequired()], 
                              render_kw={"placeholder": "例如: admin@example.com"})
    
    submit = SubmitField("保存配置")


class TestEmailForm(FlaskForm):
    """测试邮件表单"""
    test_email = StringField("测试邮箱", validators=[DataRequired()], 
                            render_kw={"placeholder": "输入接收测试邮件的邮箱地址"})
    submit = SubmitField("发送测试邮件")


# ==================== 路由处理 ====================

@admin_email_bp.route('/email-config', methods=['POST'])
@login_required
@require_permission("config:read")
def email_config():
    """邮件配置 API - POST 返回 JSON（GET 由前端静态文件处理）"""
    # POST 请求处理 - 返回 JSON
    form = EmailConfigForm()
    
    # 加载现有配置
    config = email_service.load_config()
    
    # 检查写权限
    from .utils import permission_service
    from flask_login import current_user
    
    if not permission_service.check_permission(current_user.id, "config:update"):
        return jsonify({"success": False, "error": "您没有权限修改邮件配置"})
    
    # 保存配置
    new_config = {
        'smtp_host': form.smtp_host.data.strip() if form.smtp_host.data else '',
        'smtp_port': form.smtp_port.data or 587,
        'smtp_username': form.smtp_username.data.strip() if form.smtp_username.data else None,
        'smtp_password': form.smtp_password.data if form.smtp_password.data else None,
        'use_tls': form.encryption.data == 'tls',
        'use_ssl': form.encryption.data == 'ssl',
        'sender_name': form.sender_name.data.strip() if form.sender_name.data else None,
        'sender_email': form.sender_email.data.strip() if form.sender_email.data else ''
    }
    
    # 如果密码为空且已有配置，保留原密码
    if not new_config['smtp_password'] and config and config.get('smtp_password'):
        new_config['smtp_password'] = config['smtp_password']
    
    success = email_service.save_config(new_config)
    
    if success:
        # 记录审计日志
        audit_service.log(
            event_type="email_config_update",
            user_name=current_user.id,
            ip_address=get_client_ip(),
            user_agent=get_user_agent(),
            details={
                "smtp_host": new_config['smtp_host'],
                "smtp_port": new_config['smtp_port'],
                "encryption": form.encryption.data,
                "sender_email": new_config['sender_email']
            }
        )
        return jsonify({"success": True, "message": "邮件配置保存成功"})
    else:
        return jsonify({"success": False, "error": "邮件配置保存失败"})


@admin_email_bp.route('/test-email', methods=['POST'])
@login_required
@require_permission("config:update")
def test_email():
    """发送测试邮件 - 返回 JSON"""
    test_form = TestEmailForm()
    
    if test_form.validate_on_submit():
        test_email_addr = test_form.test_email.data.strip()
        
        # 发送测试邮件
        success, message = email_service.send_test_email(test_email_addr)
        
        # 记录审计日志
        from flask_login import current_user
        audit_service.log(
            event_type="test_email_sent" if success else "test_email_failed",
            user_name=current_user.id,
            ip_address=get_client_ip(),
            user_agent=get_user_agent(),
            details={
                "test_email": test_email_addr,
                "result": "success" if success else "failed",
                "error": message if not success else None
            }
        )
        
        if success:
            return jsonify({"success": True, "message": f"测试邮件已发送到 {test_email_addr}"})
        else:
            return jsonify({"success": False, "error": f"测试邮件发送失败：{message}"})
    else:
        return jsonify({"success": False, "error": "请输入有效的邮箱地址"})


@admin_email_bp.route('/test-email-ajax', methods=['POST'])
@login_required
@require_permission("config:update")
def test_email_ajax():
    """AJAX 发送测试邮件"""
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({"success": False, "message": "缺少邮箱地址"})
    
    test_email_addr = data['email'].strip()
    
    # 简单邮箱验证
    if '@' not in test_email_addr or '.' not in test_email_addr:
        return jsonify({"success": False, "message": "请输入有效的邮箱地址"})
    
    # 发送测试邮件
    success, message = email_service.send_test_email(test_email_addr)
    
    # 记录审计日志
    from flask_login import current_user
    audit_service.log(
        event_type="test_email_sent" if success else "test_email_failed",
        user_name=current_user.id,
        ip_address=get_client_ip(),
        user_agent=get_user_agent(),
        details={
            "test_email": test_email_addr,
            "result": "success" if success else "failed",
            "error": message if not success else None
        }
    )
    
    return jsonify({
        "success": success,
        "message": f"测试邮件已发送到 {test_email_addr}" if success else f"发送失败：{message}"
    })


@admin_email_bp.route('/api/email-config', methods=['GET'])
@login_required
@require_permission("config:read")
def api_email_config_get():
    """获取邮件配置 API - 返回 JSON"""
    config = email_service.load_config()
    
    if config:
        # 不返回密码
        safe_config = {
            'smtp_host': config.get('smtp_host', ''),
            'smtp_port': config.get('smtp_port', 587),
            'smtp_username': config.get('smtp_username', ''),
            'use_tls': config.get('use_tls', True),
            'use_ssl': config.get('use_ssl', False),
            'sender_name': config.get('sender_name', ''),
            'sender_email': config.get('sender_email', ''),
        }
        return jsonify({"success": True, "data": safe_config})
    
    return jsonify({"success": True, "data": None})


@admin_email_bp.route('/api/email-config', methods=['POST', 'PUT'])
@login_required
@require_permission("config:update")
def api_email_config_save():
    """保存邮件配置 API - 接收 JSON"""
    data = request.get_json() or {}
    
    # 加载现有配置（用于保留密码）
    existing_config = email_service.load_config()
    
    # 构建新配置
    new_config = {
        'smtp_host': (data.get('smtp_host') or '').strip(),
        'smtp_port': int(data.get('smtp_port') or 587),
        'smtp_username': (data.get('smtp_username') or '').strip() or None,
        'smtp_password': (data.get('smtp_password') or '').strip() or None,
        'use_tls': data.get('encryption') == 'tls' if 'encryption' in data else data.get('use_tls', True),
        'use_ssl': data.get('encryption') == 'ssl' if 'encryption' in data else data.get('use_ssl', False),
        'sender_name': (data.get('sender_name') or '').strip() or None,
        'sender_email': (data.get('sender_email') or '').strip(),
    }
    
    # 如果密码为空且已有配置，保留原密码
    if not new_config['smtp_password'] and existing_config and existing_config.get('smtp_password'):
        new_config['smtp_password'] = existing_config['smtp_password']
    
    # 验证必填字段
    if not new_config['smtp_host']:
        return jsonify({"success": False, "error": "SMTP服务器地址不能为空"}), 400
    if not new_config['sender_email']:
        return jsonify({"success": False, "error": "发件人邮箱不能为空"}), 400
    
    success = email_service.save_config(new_config)
    
    if success:
        # 记录审计日志
        from flask_login import current_user
        audit_service.log(
            event_type="email_config_update",
            user_name=current_user.id,
            ip_address=get_client_ip(),
            user_agent=get_user_agent(),
            details={
                "smtp_host": new_config['smtp_host'],
                "smtp_port": new_config['smtp_port'],
                "sender_email": new_config['sender_email']
            }
        )
        return jsonify({"success": True, "message": "邮件配置保存成功"})
    else:
        return jsonify({"success": False, "error": "保存失败"}), 500

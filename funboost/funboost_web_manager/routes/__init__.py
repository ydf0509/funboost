# -*- coding: utf-8 -*-
"""
路由模块包

将 app.py 中的路由拆分为多个 Blueprint 模块：
- auth: 认证相关（登录、登出、密码重置、强制改密码）
- admin_users: 用户管理
- admin_roles: 角色权限管理
- admin_projects: 项目管理
- queue: 队列监控
- main: 首页和通用路由
- frontend: 前端静态文件服务
"""

from funboost.funboost_web_manager.routes.auth import auth_bp
from funboost.funboost_web_manager.routes.admin_users import admin_users_bp
from funboost.funboost_web_manager.routes.admin_roles import admin_roles_bp
from funboost.funboost_web_manager.routes.admin_projects import admin_projects_bp
from funboost.funboost_web_manager.routes.admin_email import admin_email_bp
from funboost.funboost_web_manager.routes.admin_audit import admin_audit_bp
from funboost.funboost_web_manager.routes.queue import queue_bp
from funboost.funboost_web_manager.routes.main import main_bp
from funboost.funboost_web_manager.routes.profile import profile_bp
from funboost.funboost_web_manager.routes.frontend import frontend_bp
from funboost.funboost_web_manager.routes.crypto import crypto_bp

__all__ = [
    'auth_bp',
    'admin_users_bp', 
    'admin_roles_bp',
    'admin_projects_bp',
    'admin_email_bp',
    'admin_audit_bp',
    'queue_bp',
    'main_bp',
    'profile_bp',
    'frontend_bp',
    'crypto_bp',
]


def register_blueprints(app, enable_frontend: bool = True):
    """
    注册所有 Blueprint 到 Flask app
    
    Args:
        app: Flask 应用实例
        enable_frontend: 是否启用前端服务，默认 True
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(crypto_bp)  # 加密相关 API（公钥分发）
    app.register_blueprint(admin_users_bp, url_prefix='/admin')
    app.register_blueprint(admin_roles_bp, url_prefix='/admin')
    app.register_blueprint(admin_projects_bp, url_prefix='/admin')  # 项目管理
    app.register_blueprint(admin_email_bp, url_prefix='/admin')
    app.register_blueprint(admin_audit_bp, url_prefix='/admin')
    app.register_blueprint(queue_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(profile_bp)
    
    # 前端路由放在最后，作为 fallback
    if enable_frontend:
        app.register_blueprint(frontend_bp)

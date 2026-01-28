# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/9/18 0018 14:46
import threading
import sys
import typing

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, UserMixin
from flask_cors import CORS

import nb_log
from funboost.core.active_cousumer_info_getter import (
    QueuesConusmerParamsGetter,
    CareProjectNameEnv,
)
from funboost.funboost_web_manager.user_models import (
    init_db,
    init_default_users,
    query_user_by_name,
    query_user_by_id,
)
from funboost.faas import flask_blueprint
from funboost.funboost_web_manager.routes import register_blueprints
from funboost.funboost_web_manager.config import config


class User(UserMixin):
    """Flask-Login 用户类"""
    pass


def create_app():
    """应用工厂函数"""
    import os
    # 获取当前文件所在目录，确保模板路径正确
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_folder = os.path.join(current_dir, 'templates')
    static_folder = os.path.join(current_dir, 'static')
    
    app = Flask(__name__, 
                template_folder=template_folder,
                static_folder=static_folder)
    
    # 应用配置 - 使用环境变量配置
    app.secret_key = config.SECRET_KEY
    app.config["JSON_AS_ASCII"] = False
    
    # 配置 Session Cookie - 支持环境变量配置
    app.config["SESSION_COOKIE_SAMESITE"] = config.SESSION_COOKIE_SAMESITE
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = config.SESSION_COOKIE_SECURE
    
    # 初始化扩展
    bootstrap = Bootstrap(app)
    
    # 初始化 CORS - 支持环境变量配置
    # 使用正则表达式匹配 localhost 和 127.0.0.1
    # 这样可以正确返回请求的 Origin 而不是固定值
    cors_origins = config.CORS_ORIGINS_WITH_DEFAULTS
    # 添加正则表达式支持 localhost 和 127.0.0.1
    import re
    cors_origins_pattern = [
        re.compile(r"^http://(localhost|127\.0\.0\.1)(:\d+)?$"),
    ]
    # 如果有自定义配置，也加入
    if cors_origins:
        cors_origins_pattern.extend(cors_origins)
    
    CORS(app, 
         origins=cors_origins_pattern,
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # 配置 Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.login_message = "Access denied."
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        """Flask-Login 用户加载回调"""
        if query_user_by_id(user_id) is not None:
            curr_user = User()
            curr_user.id = user_id
            return curr_user
    
    @login_manager.unauthorized_handler
    def unauthorized():
        """处理未授权请求 - API 请求返回 401 JSON，页面请求重定向"""
        from flask import request, jsonify, redirect, url_for
        
        # 检查是否是 API/AJAX 请求
        # 条件：请求路径包含 /api/、Content-Type 是 JSON、或 Accept 头优先 JSON
        is_api_request = (
            '/api/' in request.path or
            request.content_type and 'json' in request.content_type.lower() or
            request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
            request.headers.get('Accept', '').startswith('application/json') or
            request.method in ['POST', 'PUT', 'DELETE', 'PATCH']  # 非 GET 请求通常是 API 调用
        )
        
        if is_api_request:
            return jsonify({
                "success": False,
                "error": "未登录或会话已过期，请重新登录",
                "code": "UNAUTHORIZED"
            }), 401
        
        # 页面请求重定向到登录页
        return redirect(url_for('auth.login'))
    
    # 注册蓝图
    app.register_blueprint(flask_blueprint)  # FAAS 蓝图
    register_blueprints(app, enable_frontend=config.FRONTEND_ENABLED)  # 注册所有模块化的蓝图
    
    # 配置日志
    nb_log.get_logger("flask", log_filename="flask.log")
    nb_log.get_logger("werkzeug", log_filename="werkzeug.log")
    
    return app


# 创建应用实例
app = create_app()


def start_funboost_web_manager(
    host: typing.Optional[str] = None,
    port: typing.Optional[int] = None,
    block: bool = False,
    debug: typing.Optional[bool] = None,
    care_project_name: typing.Optional[str] = None,
    init_database: bool = True,
    audit_routes: bool = True,
):
    """启动 funboost web manager
    
    Args:
        host: 监听主机地址，默认从环境变量读取或 0.0.0.0
        port: 监听端口，默认从环境变量读取或 27018
        block: 是否阻塞运行
        debug: 是否开启调试模式，默认从环境变量读取
        care_project_name: 关注的项目名称
        init_database: 是否自动初始化数据库（默认 True，保持向后兼容）
        audit_routes: 是否在启动时审计路由权限（默认 True）
    
    环境变量：
        FUNBOOST_WEB_HOST: 监听地址
        FUNBOOST_WEB_PORT: 监听端口
        FUNBOOST_DEBUG: 调试模式
        FUNBOOST_CORS_ORIGINS: CORS 允许的来源（逗号分隔）
        FUNBOOST_SESSION_SECURE: Session Cookie 是否仅 HTTPS
        FUNBOOST_SESSION_SAMESITE: Session Cookie SameSite 策略
        FUNBOOST_SECRET_KEY: Flask 密钥
        FUNBOOST_FRONTEND_ENABLED: 是否启用前端服务
    """
    # 使用参数或环境变量配置
    actual_host = host if host is not None else config.HOST
    actual_port = port if port is not None else config.PORT
    actual_debug = debug if debug is not None else config.DEBUG
    
    if care_project_name is not None:
       CareProjectNameEnv.set(care_project_name)
    print("start_funboost_web_manager , sys.path :", sys.path)
    print(f"🌐 服务配置: host={actual_host}, port={actual_port}, debug={actual_debug}")
    print(f"🔧 前端服务: {'启用' if config.FRONTEND_ENABLED else '禁用'}")

    # 可选的数据库初始化
    if init_database:
        print("🔄 自动初始化数据库...")
        try:
            # 初始化用户数据库
            init_db()
            init_default_users()
            print("✅ 数据库初始化完成")
        except Exception as e:
            print(f"⚠️  数据库初始化失败: {e}")
            print("💡 建议使用独立的初始化脚本: python init_roles_permissions.py init")
    else:
        print("⏭️  跳过数据库自动初始化")

    # 路由权限审计
    if audit_routes:
        print("🔍 执行路由权限审计...")
        try:
            from funboost.funboost_web_manager.services.permission_service import PermissionService
            permission_service = PermissionService()
            audit_result = permission_service.audit_routes(app)
            permission_service.log_audit_summary(audit_result)
            
            warnings = audit_result.get('warnings', [])
            if warnings:
                print(f"⚠️  发现 {len(warnings)} 个未受保护的端点，请检查日志")
            else:
                print("✅ 所有管理/API 路由已正确保护")
        except Exception as e:
            print(f"⚠️  路由权限审计失败: {e}")

    # 从 Redis 同步项目
    print("🔄 从 Redis 同步项目...")
    try:
        from funboost.funboost_web_manager.services.project_service import ProjectService
        project_service = ProjectService()
        sync_result = project_service.sync_projects_from_redis()
        if sync_result["success"]:
            created = sync_result["created_count"]
            existing = sync_result["existing_count"]
            if created > 0:
                print(f"✅ 项目同步完成：新建 {created} 个项目，已存在 {existing} 个项目")
            else:
                print(f"✅ 项目同步完成：无新项目，已存在 {existing} 个项目")
        else:
            print(f"⚠️  项目同步失败: {sync_result.get('error', '未知错误')}")
    except Exception as e:
        print(f"⚠️  项目同步失败: {e}")

    def _start_funboost_web_manager():
        # 后台线程运行时必须禁用 debug 模式，否则会报错：
        # ValueError: signal only works in main thread of the main interpreter
        # 因为 Flask debug 模式的 reloader 需要在主线程注册信号处理器
        use_debug = actual_debug if block else False
        # 使用 Flask 运行应用
        app.run(debug=use_debug, host=actual_host, port=actual_port)

    QueuesConusmerParamsGetter().cycle_get_queues_params_and_active_consumers_and_report()
    if block is True:
        _start_funboost_web_manager()
    else:
        threading.Thread(target=_start_funboost_web_manager).start()


if __name__ == "__main__":
    start_funboost_web_manager(debug=False)

    """
    funboost web manager 启动方式1：

    web代码在funboost包里面，所以可以直接使用命令行运行起来，不需要用户现亲自下载web代码就可以直接运行。
    
    第一步： 设置 PYTHONPATH 为你的项目根目录
    export PYTHONPATH=你的项目根目录 (这么做是为了这个web可以读取到你项目根目录下的 funboost_config.py里面的配置)
    (怎么设置环境变量应该不需要我来教，环境变量都没听说过太low了)
      例如 export PYTHONPATH=/home/ydf/codes/ydfhome
      或者 export PYTHONPATH=./   (./是相对路径，前提是已近cd到你的项目根目录了，也可以写绝对路径全路径)
      win cmd 设置环境变量语法是 set PYTHONPATH=/home/ydf/codes/ydfhome   
      win powershell 语法是  $env:PYTHONPATH = "/home/ydf/codes/ydfhome"   

    第二步： 启动flask app   
    win上这么做 python3 -m funboost.funboost_web_manager.app 

    linux上可以这么做性能好一些，也可以按win的做。
    gunicorn -w 4 --threads=30 --bind 0.0.0.0:27018 funboost.funboost_web_manager.app:app
    
    环境变量配置示例：
    export FUNBOOST_WEB_HOST=0.0.0.0
    export FUNBOOST_WEB_PORT=27018
    export FUNBOOST_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
    export FUNBOOST_SESSION_SECURE=false
    export FUNBOOST_FRONTEND_ENABLED=true
    """

    """
    funboost web manager 启动方式2：
    在python代码中直接启动：

    ```python
    from  funboost.funboost_web_manager.app import start_funboost_web_manager
    start_funboost_web_manager()
    ```
    
    """

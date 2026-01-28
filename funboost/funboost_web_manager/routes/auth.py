# -*- coding: utf-8 -*-
"""
认证路由模块

包含：
- 登录 /login
- 登出 /logout
- 强制改密码 /force_change_password
- 忘记密码 /forgot_password
- 重置密码 /reset_password/<token>
"""

import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    url_for,
    flash,
    redirect,
    session,
    jsonify,
)
from flask_login import login_user, logout_user, login_required, current_user, UserMixin

from funboost import nb_print
from funboost.funboost_web_manager.user_models import (
    query_user_by_name,
    get_session,
    WebManagerUser,
)
from funboost.funboost_web_manager.services.password_service import PasswordService
from funboost.funboost_web_manager.services.audit_service import AuditEventType
from funboost.funboost_web_manager.routes.utils import (
    auth_service,
    audit_service,
    password_reset_service,
    email_service,
    encryption_service,
    extract_password,
    LoginForm,
    ForcePasswordChangeForm,
    ForgotPasswordForm,
    ResetPasswordForm,
)
from funboost.funboost_web_manager.services.encryption_service import DecryptionError


auth_bp = Blueprint("auth", __name__)


class User(UserMixin):
    """Flask-Login 用户类"""

    pass


@auth_bp.route("/login", methods=["POST"])
def login():
    """登录页面 - POST 处理表单登录（GET 由前端静态文件处理）"""
    # POST 请求 - 处理传统表单登录（保持向后兼容）
    form = LoginForm()
    if form.validate_on_submit():
        user_name = form.user_name.data
        password = form.password.data
        ip_address = request.remote_addr or "unknown"
        user_agent = request.headers.get("User-Agent", "")

        # 使用 AuthService 进行安全认证
        result = auth_service.authenticate(
            user_name, password, ip_address, user_agent
        )

        if result["success"]:
            curr_user = User()
            curr_user.id = user_name

            # 通过Flask-Login的login_user方法登录用户
            nb_print(form.remember_me.data)
            login_user(
                curr_user,
                remember=form.remember_me.data,
                duration=datetime.timedelta(days=7),
            )

            # 检查是否需要强制改密码
            if result.get("force_password_change", False):
                session["force_password_change"] = True
                return redirect("/force-change-password")

            return redirect("/queue-op")
        else:
            # 登录失败，重定向到前端登录页面
            return redirect("/login/?error=1")
    
    # 表单验证失败
    return redirect("/login/?error=1")


@auth_bp.route("/api/login", methods=["POST"])
def api_login():
    """API 登录接口 - 供前端 React 应用使用
    
    支持加密密码和明文密码（向后兼容）。
    加密密码格式: {"encrypted": true, "data": "<base64>", "key_id": "<key_id>"}
    """
    # 从请求中获取数据（支持 form-data 和 JSON）
    if request.is_json:
        data = request.get_json()
        user_name = data.get("user_name", "")
        password_data = data.get("password", "")
        remember_me = data.get("remember_me", False)
    else:
        user_name = request.form.get("user_name", "")
        password_data = request.form.get("password", "")
        remember_me = request.form.get("remember_me", "false").lower() == "true"

    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get("User-Agent", "")

    # 验证必填字段
    if not user_name or not password_data:
        return jsonify({"success": False, "error": "用户名和密码不能为空"}), 400

    # 提取密码（支持加密和明文）
    try:
        password = extract_password(password_data)
    except DecryptionError as e:
        return jsonify({"success": False, "error": "密码解密失败，请刷新页面重试"}), 400
    except ValueError as e:
        return jsonify({"success": False, "error": "密码格式无效"}), 400

    # 使用 AuthService 进行安全认证
    result = auth_service.authenticate(user_name, password, ip_address, user_agent)

    if result["success"]:
        curr_user = User()
        curr_user.id = user_name

        # 通过 Flask-Login 的 login_user 方法登录用户
        login_user(
            curr_user,
            remember=remember_me,
            duration=datetime.timedelta(days=7),
        )

        # 检查是否需要强制改密码
        if result.get("force_password_change", False):
            session["force_password_change"] = True
            return jsonify(
                {
                    "success": True,
                    "force_password_change": True,
                    "message": "您需要修改密码后才能继续使用系统",
                    "redirect": "/force-change-password",
                }
            )

        return jsonify(
            {"success": True, "message": "登录成功", "redirect": "/queue-op"}
        )
    else:
        # 返回具体的错误信息
        error_msg = result.get("error", "用户名或密码错误")
        return jsonify({"success": False, "error": error_msg}), 401


@auth_bp.route("/logout")
@login_required
def logout():
    """登出"""
    user_name = current_user.id if current_user.is_authenticated else "unknown"
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get("User-Agent", "")

    # 记录登出审计日志
    audit_service.log(
        AuditEventType.LOGOUT,
        user_name=user_name,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # 清除会话数据
    session.pop("force_password_change", None)

    logout_user()
    # 重定向到前端登录页面（不带尾部斜杠，与静态文件匹配）
    return redirect("/login")


@auth_bp.route("/force_change_password", methods=["POST"])
@login_required
def force_change_password():
    """强制改密码 API - POST 处理表单（GET 由前端静态文件处理）"""
    # 检查是否需要强制改密码
    if not session.get("force_password_change", False):
        return redirect("/queue-op")

    # POST 请求 - 处理传统表单（保持向后兼容）
    form = ForcePasswordChangeForm()

    if form.validate_on_submit():
        user_name = current_user.id
        current_password = form.current_password.data
        new_password = form.new_password.data
        ip_address = request.remote_addr or "unknown"
        user_agent = request.headers.get("User-Agent", "")

        # 获取用户信息
        user = query_user_by_name(user_name)
        if not user:
            return redirect("/login")

        # 验证当前密码
        if not PasswordService.verify_password(current_password, user["password"]):
            return redirect("/force-change-password/?error=current_password")

        # 验证新密码强度
        is_valid, errors = PasswordService.validate_strength(new_password)
        if not is_valid:
            return redirect("/force-change-password/?error=password_strength")

        # 检查新密码不能与当前密码相同
        if PasswordService.verify_password(new_password, user["password"]):
            return redirect("/force-change-password/?error=same_password")

        # 更新密码
        db_session = get_session()
        try:
            user_obj = (
                db_session.query(WebManagerUser).filter_by(user_name=user_name).first()
            )
            if user_obj:
                user_obj.password = PasswordService.hash_password(new_password)
                user_obj.force_password_change = False
                db_session.commit()

                # 记录审计日志
                audit_service.log(
                    AuditEventType.PASSWORD_CHANGE,
                    user_name=user_name,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details={"reason": "force_password_change"},
                )

                # 清除强制改密码标记
                session.pop("force_password_change", None)

                return redirect("/queue-op")
        except Exception as e:
            db_session.rollback()
        finally:
            db_session.close()

    return redirect("/force-change-password/?error=1")


@auth_bp.route("/api/force_change_password", methods=["POST"])
@login_required
def api_force_change_password():
    """强制改密码 API - 返回 JSON
    
    支持加密密码和明文密码（向后兼容）。
    """
    # 检查是否需要强制改密码
    if not session.get("force_password_change", False):
        return jsonify({"success": False, "error": "无需强制修改密码"})

    # 从请求中获取数据
    if request.is_json:
        data = request.get_json()
        current_password_data = data.get("current_password", "")
        new_password_data = data.get("new_password", "")
        confirm_password_data = data.get("confirm_password", "")
    else:
        current_password_data = request.form.get("current_password", "")
        new_password_data = request.form.get("new_password", "")
        confirm_password_data = request.form.get("confirm_password", "")

    # 验证必填字段
    if not current_password_data or not new_password_data or not confirm_password_data:
        return jsonify({"success": False, "error": "所有字段都是必填的"})

    # 提取密码（支持加密和明文）
    try:
        current_password = extract_password(current_password_data)
        new_password = extract_password(new_password_data)
        confirm_password = extract_password(confirm_password_data)
    except DecryptionError as e:
        return jsonify({"success": False, "error": "密码解密失败，请刷新页面重试"})
    except ValueError as e:
        return jsonify({"success": False, "error": "密码格式无效"})

    # 验证两次密码是否一致
    if new_password != confirm_password:
        return jsonify({"success": False, "error": "两次输入的新密码不一致"})

    user_name = current_user.id
    ip_address = request.remote_addr or "unknown"
    user_agent = request.headers.get("User-Agent", "")

    # 获取用户信息
    user = query_user_by_name(user_name)
    if not user:
        return jsonify({"success": False, "error": "用户不存在"})

    # 验证当前密码
    if not PasswordService.verify_password(current_password, user["password"]):
        return jsonify({"success": False, "error": "当前密码错误"})

    # 验证新密码强度
    is_valid, errors = PasswordService.validate_strength(new_password)
    if not is_valid:
        return jsonify({"success": False, "error": "、".join(errors)})

    # 检查新密码不能与当前密码相同
    if PasswordService.verify_password(new_password, user["password"]):
        return jsonify({"success": False, "error": "新密码不能与当前密码相同"})

    # 更新密码
    db_session = get_session()
    try:
        user_obj = (
            db_session.query(WebManagerUser).filter_by(user_name=user_name).first()
        )
        if user_obj:
            user_obj.password = PasswordService.hash_password(new_password)
            user_obj.force_password_change = False
            db_session.commit()

            # 记录审计日志
            audit_service.log(
                AuditEventType.PASSWORD_CHANGE,
                user_name=user_name,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"reason": "force_password_change"},
            )

            # 清除强制改密码标记
            session.pop("force_password_change", None)

            return jsonify(
                {"success": True, "message": "密码修改成功", "redirect": "/queue-op"}
            )
        else:
            return jsonify({"success": False, "error": "用户不存在"})
    except Exception as e:
        db_session.rollback()
        return jsonify({"success": False, "error": "密码修改失败，请稍后重试"})
    finally:
        db_session.close()


@auth_bp.route("/forgot_password", methods=["POST"])
def forgot_password():
    """忘记密码 API（GET 由前端静态文件处理）"""
    # 检查是否是 API 调用（通过 Content-Type 或 Accept 判断）
    is_api_call = (
        request.content_type and 'application/json' in request.content_type
    ) or (
        request.accept_mimetypes.best_match(['application/json', 'text/html']) == 'application/json'
    ) or (
        # 检查是否是前端 FormData 提交（没有 CSRF token）
        request.method == 'POST' and not request.form.get('csrf_token')
    )
    
    if is_api_call and request.method == "POST":
        # API 调用处理
        try:
            # 支持 JSON 和 FormData
            if request.is_json:
                data = request.get_json()
                email = data.get('email')
            else:
                email = request.form.get('email')
            
            if not email:
                return jsonify({"success": False, "error": "邮箱地址不能为空"}), 400
            
            ip_address = request.remote_addr or "unknown"
            user_agent = request.headers.get("User-Agent", "")

            # 请求密码重置
            token = password_reset_service.request_reset(email, ip_address, user_agent)

            if token:
                # 生成重置链接
                # Next.js 路由格式: /reset-password?token={token}
                # 优先级：配置文件 > Origin 头 > Referer 头 > 环境变量 > request.host_url
                frontend_base = None
                
                # 1. 尝试从配置文件读取
                try:
                    import json
                    import os
                    # 获取项目根目录
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    # 从 auth.py 往上找到项目根目录
                    # auth.py 在 funboost/funboost_web_manager/routes/auth.py
                    # 需要往上找 4 级到项目根目录
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
                    config_path = os.path.join(project_root, 'admin_config.json')
                    
                    nb_print(f"尝试读取配置文件: {config_path}")
                    if os.path.exists(config_path):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            frontend_base = config.get('frontend_url')
                            if frontend_base:
                                nb_print(f"从配置文件读取到 frontend_url: {frontend_base}")
                except Exception as e:
                    nb_print(f"读取配置文件失败: {e}")
                
                # 2. 尝试从请求头获取
                if not frontend_base:
                    origin = request.headers.get('Origin')
                    referer = request.headers.get('Referer')
                    
                    nb_print(f"请求头 - Origin: {origin}, Referer: {referer}")
                    
                    if origin:
                        frontend_base = origin
                        nb_print(f"从 Origin 头获取: {frontend_base}")
                    elif referer:
                        from urllib.parse import urlparse
                        parsed = urlparse(referer)
                        frontend_base = f"{parsed.scheme}://{parsed.netloc}"
                        nb_print(f"从 Referer 头获取: {frontend_base}")
                
                # 3. 尝试从环境变量获取
                if not frontend_base:
                    import os
                    frontend_base = os.environ.get('FRONTEND_URL')
                    if frontend_base:
                        nb_print(f"从环境变量获取: {frontend_base}")
                
                # 4. 使用请求的 host_url（自动检测当前访问地址）
                if not frontend_base:
                    frontend_base = request.host_url.rstrip('/')
                    nb_print(f"从 request.host_url 获取: {frontend_base}")
                
                # 生成前端的重置密码链接（Next.js 路由）
                # 格式: {base}/reset-password?token={token}
                reset_link = f"{frontend_base}/reset-password?token={token}"
                nb_print(f"生成重置链接: {reset_link}")

                # 获取用户信息
                user_info = password_reset_service.get_user_by_token(token)
                user_name = user_info.get("user_name") if user_info else None

                # 发送重置邮件
                success, message = email_service.send_password_reset_email(
                    email, reset_link, user_name
                )

                if success:
                    return jsonify({
                        "success": True,
                        "message": "密码重置链接已发送到您的邮箱，请查收"
                    }), 200
                else:
                    nb_print(f"邮件发送失败: {message}")
                    return jsonify({
                        "success": False,
                        "error": f"邮件发送失败：{message}"
                    }), 500
            else:
                # 为了安全，不透露邮箱是否存在
                return jsonify({
                    "success": True,
                    "message": "如果该邮箱已注册，您将收到密码重置邮件"
                }), 200
                
        except Exception as e:
            nb_print(f"忘记密码处理失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": f"处理失败：{str(e)}"
            }), 500
    
    # 传统表单提交 - 重定向到前端（Next.js 路由）
    return redirect("/forgot-password")


# 处理前端路由格式 /reset-password/{token}（连字符）
# POST 请求转发到后端 API（GET 由前端静态文件处理）
@auth_bp.route("/reset-password/<token>", methods=["POST"])
def reset_password_hyphen(token):
    """重置密码 API - 处理连字符格式的 URL（GET 由前端静态文件处理）"""
    # POST 请求转发到后端 API
    return reset_password(token)


@auth_bp.route("/reset_password/<token>", methods=["POST"])
def reset_password(token):
    """重置密码 API（GET 由前端静态文件处理）"""
    # 检查是否是 API 调用
    is_api_call = (
        request.content_type and 'application/json' in request.content_type
    ) or (
        request.accept_mimetypes.best_match(['application/json', 'text/html']) == 'application/json'
    ) or (
        # 检查是否是前端 FormData 提交（没有 CSRF token）
        request.method == 'POST' and not request.form.get('csrf_token')
    )
    
    if is_api_call and request.method == "POST":
        # API 调用处理
        try:
            # 支持 JSON 和 FormData
            if request.is_json:
                data = request.get_json()
                new_password_data = data.get('new_password')
                confirm_password_data = data.get('confirm_password')
            else:
                new_password_data = request.form.get('new_password')
                confirm_password_data = request.form.get('confirm_password')
            
            if not new_password_data or not confirm_password_data:
                return jsonify({"success": False, "error": "密码不能为空"}), 400
            
            # 提取密码（支持加密和明文）
            try:
                new_password = extract_password(new_password_data)
                confirm_password = extract_password(confirm_password_data)
            except DecryptionError as e:
                return jsonify({"success": False, "error": "密码解密失败，请刷新页面重试"}), 400
            except ValueError as e:
                return jsonify({"success": False, "error": "密码格式无效"}), 400
            
            if new_password != confirm_password:
                return jsonify({"success": False, "error": "两次输入的密码不一致"}), 400
            
            ip_address = request.remote_addr or "unknown"
            user_agent = request.headers.get("User-Agent", "")

            # 重置密码
            success, message = password_reset_service.reset_password(
                token, new_password, ip_address, user_agent
            )

            if success:
                return jsonify({
                    "success": True,
                    "message": "密码重置成功，请使用新密码登录"
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": message
                }), 400
                
        except Exception as e:
            nb_print(f"重置密码处理失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": f"处理失败：{str(e)}"
            }), 500
    
    # 传统表单提交 - 重定向到前端（Next.js 路由）
    return redirect(f"/reset-password?token={token}")

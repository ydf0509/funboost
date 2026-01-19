# -*- coding: utf-8 -*-
"""
审计日志管理路由模块

提供审计日志查询、配置和管理功能。
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, redirect
from flask_login import login_required, current_user

from ..services.audit_service import AuditService, AuditEventType
from ..services.permission_service import PermissionService
from ..routes.utils import require_permission

admin_audit_bp = Blueprint("admin_audit", __name__)


# 注意：/audit/logs 页面由前端静态文件处理，不需要后端路由
# 已移除 GET /audit/logs 路由，避免与前端静态文件冲突导致重定向循环


@admin_audit_bp.route("/api/audit/logs")
@login_required
@require_permission("audit:read")
def api_audit_logs():
    """审计日志 API - 返回 JSON"""
    # 获取查询参数
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 50, type=int)
    event_type = request.args.get("event_type", "").strip()
    user_name = request.args.get("user_name", "").strip()
    ip_address = request.args.get("ip_address", "").strip()
    start_date_str = request.args.get("start_date", "").strip()
    end_date_str = request.args.get("end_date", "").strip()

    # 解析日期
    start_date = None
    end_date = None
    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            end_date = end_date.replace(hour=23, minute=59, second=59)
    except ValueError:
        return (
            jsonify(
                {"success": False, "error": "日期格式错误，请使用 YYYY-MM-DD 格式"}
            ),
            400,
        )

    # 查询审计日志
    audit_service = AuditService()
    result = audit_service.query(
        event_type=event_type if event_type else None,
        user_name=user_name if user_name else None,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )

    # 获取所有事件类型
    event_types = audit_service.get_event_types()

    # 处理IP地址过滤
    if ip_address:
        filtered_logs = []
        for log in result["logs"]:
            if log.get("ip_address") and ip_address in log["ip_address"]:
                filtered_logs.append(log)
        result["logs"] = filtered_logs
        result["total"] = len(filtered_logs)

    total_pages = (result["total"] + page_size - 1) // page_size

    # 事件类型名称映射
    event_type_names = {
        "login_success": "登录成功",
        "login_failed": "登录失败",
        "logout": "登出",
        "password_reset_request": "请求密码重置",
        "password_reset_complete": "密码重置完成",
        "password_reset_by_admin": "管理员重置密码",
        "password_change": "修改密码",
        "user_create": "创建用户",
        "user_update": "更新用户",
        "user_delete": "删除用户",
        "user_status_change": "用户状态变更",
        "user_lock": "用户锁定",
        "user_unlock": "用户解锁",
        "role_create": "创建角色",
        "role_update": "更新角色",
        "role_delete": "删除角色",
        "config_update": "配置更新",
        "email_config_update": "邮件配置更新",
    }

    return jsonify(
        {
            "success": True,
            "data": {
                "logs": result["logs"],
                "page": page,
                "page_size": page_size,
                "total": result["total"],
                "total_pages": total_pages,
                "event_types": [
                    {"value": et, "label": event_type_names.get(et, et)}
                    for et in event_types
                ],
            },
        }
    )


# 注意：/audit/config 页面由前端静态文件处理，不需要后端路由
# 已移除 GET /audit/config 路由，避免与前端静态文件冲突导致重定向循环


@admin_audit_bp.route("/audit/config/update", methods=["POST"])
@login_required
@require_permission("config:update")
def update_audit_config():
    """更新审计日志配置 - 返回 JSON"""
    try:
        retention_days = int(request.form.get("retention_days", 30))
        if retention_days < 1:
            return jsonify({"success": False, "error": "保留天数必须大于0"})

        audit_service = AuditService()
        success = audit_service.set_retention_days(
            retention_days,
            admin_user=current_user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
        )

        if success:
            return jsonify({"success": True, "message": f"审计日志保留天数已更新为 {retention_days} 天"})
        else:
            return jsonify({"success": False, "error": "配置更新失败"})

    except ValueError:
        return jsonify({"success": False, "error": "保留天数必须是有效的数字"})


@admin_audit_bp.route("/audit/cleanup", methods=["POST"])
@login_required
@require_permission("config:update")
def cleanup_audit_logs():
    """手动清理过期审计日志 - 返回 JSON"""
    audit_service = AuditService()
    deleted_count = audit_service.cleanup_old_logs()

    if deleted_count > 0:
        return jsonify({"success": True, "message": f"已清理 {deleted_count} 条过期日志", "deleted_count": deleted_count})
    else:
        return jsonify({"success": True, "message": "没有需要清理的过期日志", "deleted_count": 0})


@admin_audit_bp.route("/api/audit/config")
@login_required
@require_permission("config:update")
def api_audit_config():
    """审计日志配置 API - 返回 JSON"""
    audit_service = AuditService()

    # 获取当前配置
    retention_days = audit_service.get_retention_days()

    # 获取日志统计信息
    from ..user_models import get_session, AuditLog

    session = get_session()
    try:
        total_logs = session.query(AuditLog).count()
        oldest_log = session.query(AuditLog).order_by(AuditLog.created_at.asc()).first()
        oldest_date = oldest_log.created_at.strftime("%Y-%m-%d") if oldest_log else None

        # 计算跨度天数
        if oldest_log:
            span_days = (datetime.now() - oldest_log.created_at).days
        else:
            span_days = 0
    finally:
        session.close()

    return jsonify(
        {
            "success": True,
            "data": {
                "retention_days": retention_days,
                "total_logs": total_logs,
                "oldest_date": oldest_date,
                "span_days": span_days,
            },
        }
    )


@admin_audit_bp.route("/api/audit/config/update", methods=["POST"])
@login_required
@require_permission("config:update")
def api_update_audit_config():
    """更新审计日志配置 API - 返回 JSON"""
    try:
        if request.is_json:
            data = request.get_json()
            retention_days = int(data.get("retention_days", 30))
        else:
            retention_days = int(request.form.get("retention_days", 30))

        if retention_days < 1:
            return jsonify({"success": False, "error": "保留天数必须大于0"})

        audit_service = AuditService()
        success = audit_service.set_retention_days(
            retention_days,
            admin_user=current_user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
        )

        if success:
            return jsonify(
                {
                    "success": True,
                    "message": f"审计日志保留天数已更新为 {retention_days} 天",
                }
            )
        else:
            return jsonify({"success": False, "error": "配置更新失败"})

    except ValueError:
        return jsonify({"success": False, "error": "保留天数必须是有效的数字"})


@admin_audit_bp.route("/api/audit/cleanup", methods=["POST"])
@login_required
@require_permission("config:update")
def api_cleanup_audit_logs():
    """手动清理过期审计日志 API - 返回 JSON"""
    audit_service = AuditService()
    deleted_count = audit_service.cleanup_old_logs()

    if deleted_count > 0:
        return jsonify(
            {
                "success": True,
                "message": f"已清理 {deleted_count} 条过期日志",
                "deleted_count": deleted_count,
            }
        )
    else:
        return jsonify(
            {"success": True, "message": "没有需要清理的过期日志", "deleted_count": 0}
        )


# 注意：/audit/statistics 页面由前端静态文件处理，不需要后端路由
# 已移除 GET /audit/statistics 路由，避免与前端静态文件冲突导致重定向循环


@admin_audit_bp.route("/api/audit/statistics")
@login_required
@require_permission("audit:read")
def api_audit_statistics():
    """审计统计API - 返回JSON数据"""
    try:
        audit_service = AuditService()
        
        # 获取登录统计（最近30天）
        login_stats = audit_service.get_login_statistics(30)
        
        return jsonify({
            "success": True,
            "data": {
                "success_login_count": login_stats.get("success_logins", 0),
                "failed_login_count": login_stats.get("failed_logins", 0),
                "active_user_count": login_stats.get("unique_users", 0),
                "total_attempts": login_stats.get("total_attempts", 0)
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取统计数据失败: {str(e)}"
        }), 500


@admin_audit_bp.route("/api/audit/export")
@login_required
@require_permission("audit:export")
def api_export_audit_logs():
    """
    导出审计日志为 CSV 文件
    
    需要 audit:export 权限
    
    Query Parameters:
        - action: 筛选操作类型
        - start_date: 开始日期 (YYYY-MM-DD)
        - end_date: 结束日期 (YYYY-MM-DD)
    
    Returns:
        CSV 文件下载
    """
    import csv
    import io
    from flask import Response
    from ..user_models import get_session, AuditLog
    
    try:
        db_session = get_session()
        
        # 构建查询
        query = db_session.query(AuditLog)
        
        # 操作类型筛选
        action = request.args.get("action")
        if action:
            query = query.filter(AuditLog.event_type == action)
        
        # 日期范围筛选
        start_date = request.args.get("start_date")
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(AuditLog.created_at >= start_dt)
            except ValueError:
                pass
        
        end_date = request.args.get("end_date")
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                # 包含结束日期当天
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(AuditLog.created_at <= end_dt)
            except ValueError:
                pass
        
        # 按时间倒序
        query = query.order_by(AuditLog.created_at.desc())
        
        # 限制导出数量，防止内存溢出
        logs = query.limit(10000).all()
        
        # 创建 CSV（添加 UTF-8 BOM 头解决 Excel 中文乱码）
        output = io.StringIO()
        output.write('\ufeff')  # UTF-8 BOM
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow([
            "ID", "用户名", "事件类型", "IP地址", 
            "User-Agent", "详情", "时间"
        ])
        
        # 写入数据
        for log in logs:
            details_str = str(log.details) if log.details else ""
            writer.writerow([
                log.id,
                log.user_name or "",
                log.event_type,
                log.ip_address or "",
                log.user_agent or "",
                details_str[:500],  # 限制详情长度
                log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
            ])
        
        db_session.close()
        
        # 记录审计日志
        audit_service = AuditService()
        audit_service.log(
            AuditEventType.CONFIG_UPDATE,  # 使用现有的事件类型
            user_name=current_user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
            details={"action": "export_audit_logs", "count": len(logs), "filters": {
                "action": action,
                "start_date": start_date,
                "end_date": end_date
            }}
        )
        
        # 返回 CSV 文件
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"导出审计日志失败: {str(e)}"})

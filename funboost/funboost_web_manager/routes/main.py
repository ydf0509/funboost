# -*- coding: utf-8 -*-
"""
主路由模块

包含：
- 首页 / - 重定向到前端
- 查询列 /query_cols
- 查询结果 /query_result
- 速度统计 /speed_stats
- 消费速率曲线 /consume_speed_curve

Requirements:
    - US-3.1: 用户只能看到自己有权限的项目数据
    - AC-3: 数据隔离 - 队列数据按项目隔离
"""

from flask import Blueprint, request, jsonify, redirect, url_for, session
from flask_login import login_required, current_user

import nb_log

from funboost import nb_print
from funboost.funboost_web_manager.functions import (
    get_cols,
    query_result,
    get_speed,
    get_consume_speed_curve,
)
from funboost.core.active_cousumer_info_getter import QueuesConusmerParamsGetter
from funboost.funboost_web_manager.services.project_service import ProjectService
from funboost.funboost_web_manager.routes.utils import require_permission

# 获取日志记录器
logger = nb_log.get_logger('main_routes')

# 项目服务实例
project_service = ProjectService()


def _check_project_access(project_id, required_level: str = "read"):
    """
    检查当前用户是否有项目访问权限
    
    Args:
        project_id: 项目ID（可选）
        
    Returns:
        tuple: (has_access: bool, error_response: Response|None)
        - 如果 project_id 为空，返回 (True, None)
        - 如果有权限，返回 (True, None)
        - 如果无权限，返回 (False, error_response)
    """
    if not project_id:
        # project_id 为空时，不进行项目过滤，返回所有数据（向后兼容）
        return True, None
    
    try:
        project_id_int = int(project_id)
    except (ValueError, TypeError):
        return False, (jsonify({
            "success": False,
            "error": "无效的项目ID"
        }), 400)
    
    # 检查用户是否有项目访问权限
    user_name = current_user.id if current_user.is_authenticated else None
    if not user_name:
        return False, (jsonify({
            "success": False,
            "error": "请先登录"
        }), 401)
    
    if not project_service.check_project_permission(user_name, project_id_int, required_level):
        return False, (jsonify({
            "success": False,
            "error": f"您在此项目中没有 {required_level} 权限"
        }), 403)
    
    return True, None


def _get_project_code(project_id) -> str:
    """根据项目 ID 获取项目代码（默认项目返回 None）"""
    if not project_id:
        return None
    try:
        project_id_int = int(project_id)
    except (ValueError, TypeError):
        return None
    return project_service.get_project_code_by_id(project_id_int)


def _normalize_queue_names(queue_names) -> set:
    normalized = set()
    for name in queue_names or []:
        if isinstance(name, bytes):
            normalized.add(name.decode())
        else:
            normalized.add(str(name))
    return normalized


def _get_project_queue_names(project_code: str) -> set:
    if not project_code:
        return set()
    queue_names = QueuesConusmerParamsGetter(care_project_name=project_code).get_all_queue_names()
    return _normalize_queue_names(queue_names)


def _check_queue_in_project(queue_name: str, project_code: str):
    if not project_code:
        return True, None
    allowed = _get_project_queue_names(project_code)
    if queue_name not in allowed:
        return False, (jsonify({
            "success": False,
            "error": "当前项目无此队列权限"
        }), 403)
    return True, None


main_bp = Blueprint('main', __name__)


@main_bp.route("/")
@login_required
def index():
    """首页 - 重定向到前端"""
    # 检查是否需要强制改密码
    if session.get('force_password_change', False):
        return redirect(url_for("auth.force_change_password"))
    
    # 重定向到前端首页（Next.js 路由）
    return redirect("/queue-op")


@main_bp.route("/query_cols")
@login_required
@require_permission("queue:read")
def query_cols_view():
    """
    查询队列列表
    
    参数:
        col_name_search: 队列名称搜索关键字（可选）
        project_id: 项目ID（可选，查询参数）
    
    返回:
        队列列表
        
    Requirements:
        - US-3.1: 用户只能看到自己有权限的项目数据
        - AC-3: 数据隔离 - 队列数据按项目隔离
    """
    # 获取项目ID参数
    project_id = request.args.get("project_id")
    
    # 检查项目访问权限
    has_access, error_response = _check_project_access(project_id, required_level="read")
    if not has_access:
        return error_response

    project_code = _get_project_code(project_id)

    project_code = _get_project_code(project_id)

    project_code = _get_project_code(project_id)

    project_code = _get_project_code(project_id)
    
    # 记录项目过滤信息（用于未来实现）
    if project_id:
        logger.debug(f"查询队列列表，项目ID: {project_id}")
    
    nb_print(request.args)
    cols = get_cols(request.args.get("col_name_search"))
    if project_code:
        allowed = _get_project_queue_names(project_code)
        cols = [col for col in cols if col.get("collection_name") in allowed]
    return jsonify(cols)


@main_bp.route("/query_result")
@login_required
@require_permission("queue:read")
def query_result_view():
    """
    查询函数执行结果
    
    参数:
        project_id: 项目ID（可选，查询参数）
        其他参数: 传递给 query_result 函数
    
    返回:
        函数执行结果
        
    Requirements:
        - US-3.1: 用户只能看到自己有权限的项目数据
        - AC-3: 数据隔离 - 队列数据按项目隔离
    """
    # 获取项目ID参数
    project_id = request.args.get("project_id")
    
    # 检查项目访问权限
    has_access, error_response = _check_project_access(project_id, required_level="read")
    if not has_access:
        return error_response
    
    if project_id:
        logger.debug(f"查询函数执行结果，项目ID: {project_id}")

    # 获取项目代码并校验队列是否属于当前项目
    project_code = _get_project_code(project_id)
    col_name = request.args.get("col_name")
    has_queue_access, queue_error = _check_queue_in_project(col_name, project_code)
    if not has_queue_access:
        return queue_error
    
    # 移除 project_id 参数，因为 query_result 函数不接受它
    params = request.values.to_dict()
    params.pop('project_id', None)
    
    return jsonify(query_result(**params))


@main_bp.route("/speed_stats")
@login_required
@require_permission("queue:read")
def speed_stats():
    """
    获取速度统计
    
    参数:
        project_id: 项目ID（可选，查询参数）
        其他参数: 传递给 get_speed 函数
    
    返回:
        速度统计数据
        
    Requirements:
        - US-3.1: 用户只能看到自己有权限的项目数据
        - AC-3: 数据隔离 - 队列数据按项目隔离
    """
    # 获取项目ID参数
    project_id = request.args.get("project_id")
    
    # 检查项目访问权限
    has_access, error_response = _check_project_access(project_id, required_level="read")
    if not has_access:
        return error_response
    
    if project_id:
        logger.debug(f"获取速度统计，项目ID: {project_id}")

    # 获取项目代码并校验队列是否属于当前项目
    project_code = _get_project_code(project_id)
    col_name = request.args.get("col_name")
    has_queue_access, queue_error = _check_queue_in_project(col_name, project_code)
    if not has_queue_access:
        return queue_error
    
    # 移除 project_id 参数，因为 get_speed 函数不接受它
    params = request.values.to_dict()
    params.pop('project_id', None)
    
    return jsonify(get_speed(**params))


@main_bp.route("/consume_speed_curve")
@login_required
@require_permission("queue:read")
def consume_speed_curve():
    """
    获取消费速率曲线数据
    
    参数:
        col_name: 队列名称（必填）
        start_time: 开始时间（必填）
        end_time: 结束时间（必填）
        granularity: 粒度（可选，默认 "auto"）
        project_id: 项目ID（可选，查询参数）
    
    返回:
        消费速率曲线数据
        
    Requirements:
        - US-3.1: 用户只能看到自己有权限的项目数据
        - AC-3: 数据隔离 - 队列数据按项目隔离
    """
    # 获取项目ID参数
    project_id = request.args.get("project_id")
    
    # 检查项目访问权限
    has_access, error_response = _check_project_access(project_id, required_level="read")
    if not has_access:
        return error_response
    
    col_name = request.args.get("col_name")
    start_time = request.args.get("start_time")
    end_time = request.args.get("end_time")
    granularity = request.args.get("granularity", "auto")
    
    if project_id:
        logger.debug(f"获取消费速率曲线，队列: {col_name}，项目ID: {project_id}")

    # 获取项目代码并校验队列权限
    project_code = _get_project_code(project_id)
    has_queue_access, queue_error = _check_queue_in_project(col_name, project_code)
    if not has_queue_access:
        return queue_error
    
    if not col_name or not start_time or not end_time:
        return jsonify({"error": "缺少必要参数: col_name, start_time, end_time"})
    
    try:
        result = get_consume_speed_curve(col_name, start_time, end_time, granularity)
        return jsonify(result)
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()})

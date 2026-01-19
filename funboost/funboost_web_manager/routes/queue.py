# -*- coding: utf-8 -*-
"""
队列监控路由模块

包含：
- 心跳信息按队列名 /running_consumer/hearbeat_info_by_queue_name
- 心跳信息按IP /running_consumer/hearbeat_info_by_ip
- 心跳信息分区按队列名 /running_consumer/hearbeat_info_partion_by_queue_name
- 心跳信息分区按IP /running_consumer/hearbeat_info_partion_by_ip
- 队列参数和活跃消费者 /queue/params_and_active_consumers
- 所有队列消息数量 /queue/get_msg_num_all_queues
- 时序数据 /queue/get_time_series_data/<queue_name>
- 暂停队列消费 /queue/pause/<queue_name>
- 恢复队列消费 /queue/resume/<queue_name>

Requirements:
    - US-3.1: 用户只能看到自己有权限的项目数据
    - AC-3: 数据隔离 - 队列数据按项目隔离
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from funboost import ActiveCousumerProcessInfoGetter
from funboost.core.active_cousumer_info_getter import (
    QueuesConusmerParamsGetter,
    SingleQueueConusmerParamsGetter,
)
from funboost.utils.redis_manager import RedisMixin
from funboost.constant import RedisKeys
from funboost.funboost_web_manager.services.project_service import ProjectService
from funboost.funboost_web_manager.routes.utils import require_permission

import nb_log

# 获取日志记录器
logger = nb_log.get_logger("queue_routes")

queue_bp = Blueprint("queue", __name__)

# 项目服务实例
project_service = ProjectService()


def _get_project_code(project_id) -> str:
    """
    根据项目 ID 获取项目代码（用于 care_project_name 参数）

    Args:
        project_id: 项目ID（可以是字符串或整数）

    Returns:
        str: 项目代码，如果是默认项目或无效 ID 则返回 None

    Note:
        - 默认项目（code='default'）返回 None，表示不进行项目过滤
        - 这样可以保持向后兼容，默认项目显示所有数据
    """
    if not project_id:
        return None

    try:
        project_id_int = int(project_id)
    except (ValueError, TypeError):
        return None

    return project_service.get_project_code_by_id(project_id_int)


def _check_project_access(project_id, required_level: str = "read"):
    """
    检查当前用户是否有项目访问权限

    Args:
        project_id: 项目ID（可选）
        required_level: 权限级别 ('read', 'write', 'admin')

    Returns:
        tuple: (has_access: bool, error_response: tuple|None)
        - 如果 project_id 为空，返回 (True, None)
        - 如果有权限，返回 (True, None)
        - 如果无权限，返回 (False, (jsonify_response, status_code))
    """
    if not project_id:
        # project_id 为空时，不进行项目过滤，返回所有数据（向后兼容）
        return True, None

    try:
        project_id_int = int(project_id)
    except (ValueError, TypeError):
        return False, (jsonify({"success": False, "error": "无效的项目ID"}), 400)

    # 检查用户是否有项目访问权限
    user_name = current_user.id if current_user.is_authenticated else None
    if not user_name:
        return False, (jsonify({"success": False, "error": "请先登录"}), 401)

    if not project_service.check_project_permission(
        user_name, project_id_int, required_level
    ):
        return False, (
            jsonify(
                {"success": False, "error": f"您在此项目中没有 {required_level} 权限"}
            ),
            403,
        )

    return True, None


def _normalize_queue_names(queue_names) -> set:
    normalized = set()
    for name in queue_names or []:
        if isinstance(name, bytes):
            normalized.add(name.decode())
        else:
            normalized.add(str(name))
    return normalized


def _check_queue_in_project(queue_name: str, project_code: str):
    if not project_code:
        return True, None
    allowed = _normalize_queue_names(
        QueuesConusmerParamsGetter(care_project_name=project_code).get_all_queue_names()
    )
    if queue_name not in allowed:
        return False, (
            jsonify({"success": False, "error": "当前项目无此队列权限"}),
            403,
        )
    return True, None


# ==================== 队列控制路由 ====================


@queue_bp.route("/queue/pause/<queue_name>", methods=["POST"])
@login_required
@require_permission("queue:execute")
def pause_queue(queue_name):
    """
    暂停指定队列的消费

    参数:
        queue_name: 队列名称（URL路径参数）
        project_id: 项目ID（可选，查询参数）

    返回:
        操作结果

    Requirements:
        - US-3.1: 用户只能看到自己有权限的项目数据
        - AC-3: 数据隔离 - 队列数据按项目隔离
    """
    # 获取项目ID参数
    project_id = request.args.get("project_id")

    # 检查项目访问权限
    has_access, error_response = _check_project_access(
        project_id, required_level="write"
    )
    if not has_access:
        return error_response

    project_code = _get_project_code(project_id)
    has_queue_access, queue_error = _check_queue_in_project(queue_name, project_code)
    if not has_queue_access:
        return queue_error

    # 记录项目过滤信息（用于未来实现）
    if project_id:
        logger.info(f"暂停队列 {queue_name}，项目ID: {project_id}")

    try:
        RedisMixin().redis_db_frame.hset(
            RedisKeys.REDIS_KEY_PAUSE_FLAG, queue_name, "1"
        )
        return jsonify({"success": True, "message": f"队列 {queue_name} 已暂停消费"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@queue_bp.route("/queue/resume/<queue_name>", methods=["POST"])
@login_required
@require_permission("queue:execute")
def resume_queue(queue_name):
    """
    恢复指定队列的消费

    参数:
        queue_name: 队列名称（URL路径参数）
        project_id: 项目ID（可选，查询参数）

    返回:
        操作结果

    Requirements:
        - US-3.1: 用户只能看到自己有权限的项目数据
        - AC-3: 数据隔离 - 队列数据按项目隔离
    """
    # 获取项目ID参数
    project_id = request.args.get("project_id")

    # 检查项目访问权限
    has_access, error_response = _check_project_access(
        project_id, required_level="write"
    )
    if not has_access:
        return error_response

    project_code = _get_project_code(project_id)
    has_queue_access, queue_error = _check_queue_in_project(queue_name, project_code)
    if not has_queue_access:
        return queue_error

    # 记录项目过滤信息（用于未来实现）
    if project_id:
        logger.info(f"恢复队列 {queue_name}，项目ID: {project_id}")

    try:
        RedisMixin().redis_db_frame.hset(
            RedisKeys.REDIS_KEY_PAUSE_FLAG, queue_name, "0"
        )
        return jsonify({"success": True, "message": f"队列 {queue_name} 已恢复消费"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==================== 心跳信息路由 ====================


@queue_bp.route("/running_consumer/hearbeat_info_by_queue_name")
@login_required
@require_permission("queue:read")
def hearbeat_info_by_queue_name():
    """
    获取按队列名分组的心跳信息

    参数:
        queue_name: 队列名称，"所有" 或空表示获取所有队列
        project_id: 项目ID（可选，查询参数）

    返回:
        心跳信息列表

    Requirements:
        - US-3.1: 用户只能看到自己有权限的项目数据
        - AC-3: 数据隔离 - 队列数据按项目隔离
    """
    # 获取参数
    project_id = request.args.get("project_id")
    queue_name = request.args.get("queue_name")

    # 检查项目访问权限
    has_access, error_response = _check_project_access(
        project_id, required_level="read"
    )
    if not has_access:
        return error_response

    # 获取项目代码用于过滤
    project_code = _get_project_code(project_id)

    if project_code:
        logger.debug(
            f"获取心跳信息（按队列名），项目代码: {project_code}, 队列名: {queue_name}"
        )

    # 如果指定了队列名，检查队列访问权限
    if queue_name and queue_name not in ("所有", ""):
        has_queue_access, queue_error = _check_queue_in_project(
            queue_name, project_code
        )
        if not has_queue_access:
            return queue_error
    # 使用 care_project_name 参数进行项目过滤
    try:
        getter = ActiveCousumerProcessInfoGetter(care_project_name=project_code)

        if queue_name in ("所有", None, ""):
            info_map = getter.get_all_hearbeat_info_partition_by_queue_name()
            ret_list = []
            for qn, dic in info_map.items():
                ret_list.extend(dic)
            return jsonify(ret_list)
        else:
            return jsonify(getter.get_all_hearbeat_info_by_queue_name(queue_name))
    except Exception as e:
        logger.exception(f"获取心跳信息失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@queue_bp.route("/running_consumer/hearbeat_info_by_ip")
@login_required
@require_permission("queue:read")
def hearbeat_info_by_ip():
    """
    获取按IP分组的心跳信息

    参数:
        ip: IP地址，"所有" 或空表示获取所有IP
        project_id: 项目ID（可选，查询参数）

    返回:
        心跳信息列表

    Requirements:
        - US-3.1: 用户只能看到自己有权限的项目数据
        - AC-3: 数据隔离 - 队列数据按项目隔离
    """
    # 获取项目ID参数
    project_id = request.args.get("project_id")

    # 检查项目访问权限
    has_access, error_response = _check_project_access(
        project_id, required_level="read"
    )
    if not has_access:
        return error_response

    # 获取项目代码用于过滤
    project_code = _get_project_code(project_id)

    if project_code:
        logger.debug(f"获取心跳信息（按IP），项目代码: {project_code}")

    ip = request.args.get("ip")
    # 使用 care_project_name 参数进行项目过滤
    getter = ActiveCousumerProcessInfoGetter(care_project_name=project_code)

    if ip in ("所有", None, ""):
        info_map = getter.get_all_hearbeat_info_partition_by_ip()
        ret_list = []
        for queue_name, dic in info_map.items():
            ret_list.extend(dic)
        return jsonify(ret_list)
    else:
        return jsonify(getter.get_all_hearbeat_info_by_ip(ip))


@queue_bp.route("/running_consumer/hearbeat_info_partion_by_queue_name")
@login_required
@require_permission("queue:read")
def hearbeat_info_partion_by_queue_name():
    """
    获取按队列名分区的心跳信息统计

    参数:
        project_id: 项目ID（可选，查询参数）

    返回:
        包含队列名和消费者数量的列表，第一项为"所有"的汇总

    Requirements:
        - US-3.1: 用户只能看到自己有权限的项目数据
        - AC-3: 数据隔离 - 队列数据按项目隔离
    """
    # 获取项目ID参数
    project_id = request.args.get("project_id")

    # 检查项目访问权限
    has_access, error_response = _check_project_access(
        project_id, required_level="read"
    )
    if not has_access:
        return error_response

    # 获取项目代码用于过滤
    project_code = _get_project_code(project_id)

    if project_code:
        logger.debug(f"获取心跳信息分区（按队列名），项目代码: {project_code}")

    # 使用 care_project_name 参数进行项目过滤
    info_map = ActiveCousumerProcessInfoGetter(
        care_project_name=project_code
    ).get_all_hearbeat_info_partition_by_queue_name()
    ret_list = []
    total_count = 0
    for k, v in info_map.items():
        ret_list.append({"collection_name": k, "count": len(v)})
        total_count += len(v)
    ret_list = sorted(ret_list, key=lambda x: x["collection_name"])
    ret_list.insert(0, {"collection_name": "所有", "count": total_count})
    return jsonify(ret_list)


@queue_bp.route("/running_consumer/hearbeat_info_partion_by_ip")
@login_required
@require_permission("queue:read")
def hearbeat_info_partion_by_ip():
    """
    获取按IP分区的心跳信息统计

    参数:
        project_id: 项目ID（可选，查询参数）

    返回:
        包含IP和消费者数量的列表，第一项为"所有"的汇总

    Requirements:
        - US-3.1: 用户只能看到自己有权限的项目数据
        - AC-3: 数据隔离 - 队列数据按项目隔离
    """
    # 获取项目ID参数
    project_id = request.args.get("project_id")

    # 检查项目访问权限
    has_access, error_response = _check_project_access(
        project_id, required_level="read"
    )
    if not has_access:
        return error_response

    # 获取项目代码用于过滤
    project_code = _get_project_code(project_id)

    if project_code:
        logger.debug(f"获取心跳信息分区（按IP），项目代码: {project_code}")

    # 使用 care_project_name 参数进行项目过滤
    info_map = ActiveCousumerProcessInfoGetter(
        care_project_name=project_code
    ).get_all_hearbeat_info_partition_by_ip()
    ret_list = []
    total_count = 0
    for k, v in info_map.items():
        ret_list.append({"collection_name": k, "count": len(v)})
        total_count += len(v)
    ret_list = sorted(ret_list, key=lambda x: x["collection_name"])
    ret_list.insert(0, {"collection_name": "所有", "count": total_count})
    print(ret_list)
    return jsonify(ret_list)


# ==================== 队列参数和消费者路由 ====================


@queue_bp.route("/queue/params_and_active_consumers")
@login_required
@require_permission("queue:read")
def get_queues_params_and_active_consumers():
    """
    获取所有队列的参数和活跃消费者信息

    参数:
        project_id: 项目ID（可选，查询参数）

    返回:
        队列参数和活跃消费者信息

    Requirements:
        - US-3.1: 用户只能看到自己有权限的项目数据
        - AC-3: 数据隔离 - 队列数据按项目隔离
    """
    # 获取项目ID参数
    project_id = request.args.get("project_id")

    # 检查项目访问权限
    has_access, error_response = _check_project_access(
        project_id, required_level="read"
    )
    if not has_access:
        return error_response

    # 获取项目代码用于过滤
    project_code = _get_project_code(project_id)

    if project_code:
        logger.debug(f"获取队列参数和活跃消费者，项目代码: {project_code}")

    # 使用 care_project_name 参数进行项目过滤
    return jsonify(
        QueuesConusmerParamsGetter(
            care_project_name=project_code
        ).get_queues_params_and_active_consumers()
    )


@queue_bp.route("/queue/get_msg_num_all_queues", methods=["GET"])
@login_required
@require_permission("queue:read")
def get_msg_num_all_queues():
    """
    获取所有队列的消息数量

    这个是通过消费者周期每隔10秒上报到redis的，性能好。
    不需要实时获取每个消息队列，直接从redis读取所有队列的消息数量。

    参数:
        project_id: 项目ID（可选，查询参数）

    返回:
        所有队列的消息数量

    Requirements:
        - US-3.1: 用户只能看到自己有权限的项目数据
        - AC-3: 数据隔离 - 队列数据按项目隔离
    """
    # 获取项目ID参数
    project_id = request.args.get("project_id")

    # 检查项目访问权限
    has_access, error_response = _check_project_access(
        project_id, required_level="read"
    )
    if not has_access:
        return error_response

    # 获取项目代码用于过滤
    project_code = _get_project_code(project_id)

    if project_code:
        logger.debug(f"获取所有队列消息数量，项目代码: {project_code}")

    # 使用 care_project_name 参数进行项目过滤
    return jsonify(
        QueuesConusmerParamsGetter(care_project_name=project_code).get_msg_num(
            ignore_report_ts=True
        )
    )


@queue_bp.route("/queue/get_time_series_data/<queue_name>", methods=["GET"])
@login_required
@require_permission("queue:read")
def get_time_series_data_by_queue_name(queue_name):
    """
    获取指定队列的时序数据

    参数:
        queue_name: 队列名称（URL路径参数）
        start_ts: 开始时间戳（可选）
        end_ts: 结束时间戳（可选）
        curve_samples_count: 采样点数（可选，默认360）
        project_id: 项目ID（可选，查询参数）

    返回:
        时序数据列表，例如:
        [
            {
                'report_data': {
                    'pause_flag': -1,
                    'msg_num_in_broker': 936748,
                    'history_run_count': '150180',
                    'history_run_fail_count': '46511',
                    'all_consumers_last_x_s_execute_count': 7,
                    'all_consumers_last_x_s_execute_count_fail': 0,
                    'all_consumers_last_x_s_avarage_function_spend_time': 3.441,
                    'all_consumers_avarage_function_spend_time_from_start': 4.598,
                    'all_consumers_total_consume_count_from_start': 1296,
                    'all_consumers_total_consume_count_from_start_fail': 314,
                    'report_ts': 1749617360.597841
                },
                'report_ts': 1749617360.597841
            },
            ...
        ]

    Requirements:
        - US-3.1: 用户只能看到自己有权限的项目数据
        - AC-3: 数据隔离 - 队列数据按项目隔离
    """
    # 获取项目ID参数
    project_id = request.args.get("project_id")

    # 检查项目访问权限
    has_access, error_response = _check_project_access(
        project_id, required_level="read"
    )
    if not has_access:
        return error_response

    # 记录项目过滤信息（用于未来实现）
    if project_id:
        logger.debug(f"获取队列 {queue_name} 时序数据，项目ID: {project_id}")

    # 获取前端传递的参数
    start_ts = request.args.get("start_ts")
    end_ts = request.args.get("end_ts")
    curve_samples_count = request.args.get("curve_samples_count")

    # 如果前端指定了采样点数，使用前端的值
    if curve_samples_count:
        try:
            curve_samples_count = int(curve_samples_count)
            # 验证值是否在允许的范围内
            allowed_values = [60, 120, 180, 360, 720, 1440, 8640]
            if curve_samples_count not in allowed_values:
                curve_samples_count = 360  # 默认值
        except (ValueError, TypeError):
            curve_samples_count = 360  # 默认值
    else:
        # 如果前端没有指定，使用默认值
        curve_samples_count = 360

    return jsonify(
        SingleQueueConusmerParamsGetter(queue_name).get_one_queue_time_series_data(
            start_ts, end_ts, curve_samples_count
        )
    )

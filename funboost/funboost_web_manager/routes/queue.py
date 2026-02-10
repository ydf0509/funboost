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
from funboost.constant import RedisKeys, BrokerEnum
from funboost.funboost_web_manager.services.project_service import ProjectService
from funboost.funboost_web_manager.routes.utils import require_permission

import nb_log
import time
import json

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


def _hmget_dict(redis_key: str, fields: list) -> dict:
    """
    Safe hmget -> dict conversion that preserves field/value alignment.
    Redis hmget returns a list aligned with `fields` (may contain None).
    """
    if not fields:
        return {}
    values = RedisMixin().redis_db_frame.hmget(redis_key, fields)
    return {k: v for k, v in zip(fields, values) if v is not None}


def _hmget_int_dict(redis_key: str, fields: list) -> dict:
    raw = _hmget_dict(redis_key, fields)
    ret = {}
    for k, v in raw.items():
        try:
            if isinstance(v, bytes):
                v = v.decode()
            ret[str(k.decode() if isinstance(k, bytes) else k)] = int(v)
        except Exception:
            # Ignore non-int values
            continue
    return ret


def _hmget_msg_num_dict(fields: list, ignore_report_ts: bool = True) -> dict:
    """
    Get msg_num_in_broker for queues from RedisKeys.QUEUE__MSG_COUNT_MAP.
    Values are JSON strings stored by consumers' heartbeat reporter.
    """
    raw = _hmget_dict(RedisKeys.QUEUE__MSG_COUNT_MAP, fields)
    now = time.time()
    ret: dict[str, int] = {}
    for k, v in raw.items():
        try:
            qn = k.decode() if isinstance(k, bytes) else str(k)
            payload = v.decode() if isinstance(v, bytes) else v
            info = json.loads(payload)
            if ignore_report_ts or (
                info.get("report_ts", 0) > now - 15 and info.get("last_get_msg_num_ts", 0) > now - 1200
            ):
                if "msg_num_in_broker" in info:
                    ret[qn] = info["msg_num_in_broker"]
        except Exception:
            continue
    return ret


def _hmget_msg_info_dict(fields: list) -> dict:
    """
    Get msg_count info payloads for queues from RedisKeys.QUEUE__MSG_COUNT_MAP.
    Returns a dict: {queue_name: {"msg_num_in_broker": int, "last_get_msg_num_ts": float, "report_ts": float}}
    """
    raw = _hmget_dict(RedisKeys.QUEUE__MSG_COUNT_MAP, fields)
    ret: dict[str, dict] = {}
    for k, v in raw.items():
        try:
            qn = k.decode() if isinstance(k, bytes) else str(k)
            payload = v.decode() if isinstance(v, bytes) else v
            info = json.loads(payload)
            if isinstance(info, dict):
                ret[qn] = info
        except Exception:
            continue
    return ret


def _save_msg_count_info(queue_name: str, msg_num_in_broker: int):
    """
    Update RedisKeys.QUEUE__MSG_COUNT_MAP using the same structure as consumers' heartbeat reporter.
    This allows WebManager to refresh stale msg_num_in_broker on-demand without changing consumer code.
    """
    now = time.time()
    dic = {
        "msg_num_in_broker": msg_num_in_broker,
        "last_get_msg_num_ts": now,
        "report_ts": now,
    }
    try:
        RedisMixin().redis_db_frame.hset(
            RedisKeys.QUEUE__MSG_COUNT_MAP, queue_name, json.dumps(dic)
        )
    except Exception:
        # Best-effort: do not fail the request if Redis write fails.
        logger.debug("save msg_count info failed", exc_info=True)


def _get_unack_count(queue_name: str) -> int:
    """
    For ack-able redis consumers, unacked tasks are stored in separate zset/list keys.
    Sum those to avoid showing 0 while tasks are executing.
    """
    try:
        registry_key = RedisKeys.gen_funboost_unack_registry_key_by_queue_name(queue_name)
        unack_keys = RedisMixin().redis_db_frame.smembers(registry_key) or []
        total = 0
        for key in unack_keys:
            key_str = key.decode() if isinstance(key, bytes) else str(key)
            key_type = RedisMixin().redis_db_frame.type(key_str)
            if isinstance(key_type, bytes):
                key_type = key_type.decode()
            if key_type == "zset":
                total += RedisMixin().redis_db_frame.zcard(key_str)
            elif key_type == "list":
                total += RedisMixin().redis_db_frame.llen(key_str)
        return total
    except Exception:
        logger.debug("get unack count failed", exc_info=True)
        return 0


def _get_realtime_msg_count(queue_name: str, broker_kind) -> int:
    """
    Get realtime msg count from broker, with ack-able redis unack补偿.
    Returns -1 if broker doesn't support counting and no unack data is available.
    """
    try:
        publisher = SingleQueueConusmerParamsGetter(queue_name).gen_publisher_for_faas()
        count = publisher.get_message_count()
    except Exception as e:
        logger.warning(f"获取队列 {queue_name} 实时消息数失败: {e}")
        return -1
    ackable_kinds = {
        BrokerEnum.REDIS_ACK_ABLE,
        BrokerEnum.REDIS_BRPOP_LPUSH,
        BrokerEnum.REIDS_ACK_USING_TIMEOUT,
        BrokerEnum.REDIS_PRIORITY,
    }
    unack = _get_unack_count(queue_name) if broker_kind in ackable_kinds else 0
    if count == -1:
        return unack if unack > 0 else -1
    return count + unack


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
    # NOTE: funboost.core.active_cousumer_info_getter.hmget_many_by_all_queue_names 会在 hmget 返回 None 时
    #       破坏字段对齐，导致 pause_flag / msg_num 等映射错位。这里在 WebManager 层做一次纠偏，避免 UI 显示异常。
    data = QueuesConusmerParamsGetter(
        care_project_name=project_code
    ).get_queues_params_and_active_consumers()

    queue_names = list(data.keys())
    pause_map = _hmget_int_dict(RedisKeys.REDIS_KEY_PAUSE_FLAG, queue_names)
    msg_info_map = _hmget_msg_info_dict(queue_names)
    msg_num_map = _hmget_msg_num_dict(queue_names, ignore_report_ts=True)
    run_count_map = _hmget_int_dict(RedisKeys.FUNBOOST_QUEUE__RUN_COUNT_MAP, queue_names)
    run_fail_count_map = _hmget_int_dict(RedisKeys.FUNBOOST_QUEUE__RUN_FAIL_COUNT_MAP, queue_names)
    now = time.time()

    for qn in queue_names:
        qn_str = qn.decode() if isinstance(qn, bytes) else str(qn)
        item = data.get(qn)
        if not isinstance(item, dict):
            continue
        item["pause_flag"] = pause_map.get(qn_str, item.get("pause_flag", -1))
        if qn_str in msg_num_map:
            item["msg_num_in_broker"] = msg_num_map[qn_str]
        item["history_run_count"] = run_count_map.get(qn_str, item.get("history_run_count"))
        item["history_run_fail_count"] = run_fail_count_map.get(qn_str, item.get("history_run_fail_count"))

        # Fix "msg_num_in_broker looks wrong while consumers are running":
        # Consumers only refresh msg_num_in_broker periodically (often minutes),
        # so for active queues we opportunistically fetch a real-time count when the report is stale.
        try:
            has_active_consumers = bool(item.get("active_consumers"))
            if not has_active_consumers:
                continue
            info = msg_info_map.get(qn_str, {}) if isinstance(msg_info_map, dict) else {}
            last_get_ts = float(info.get("last_get_msg_num_ts") or 0)
            # If no recent update, query broker directly for this queue.
            if now - last_get_ts > 30:
                broker_kind = None
                if isinstance(item.get("queue_params"), dict):
                    broker_kind = item["queue_params"].get("broker_kind")
                real_count = _get_realtime_msg_count(qn_str, broker_kind)
                item["msg_num_in_broker"] = real_count
                _save_msg_count_info(qn_str, real_count)
        except Exception:
            # Keep the existing value when real-time count fails (network/broker issues).
            logger.debug("refresh real-time msg count failed", exc_info=True)

    return jsonify(data)


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
    # NOTE: 避免 hmget_many_by_all_queue_names 的字段错位问题，改为在路由层用 hmget + zip 保持对齐。
    queue_names = list(
        QueuesConusmerParamsGetter(care_project_name=project_code).get_all_queue_names()
    )
    return jsonify(_hmget_msg_num_dict(queue_names, ignore_report_ts=True))


@queue_bp.route("/queue/get_msg_num_by_queue_names", methods=["POST"])
@login_required
@require_permission("queue:read")
def get_msg_num_by_queue_names():
    """
    Realtime message count for specified queues (best-effort).

    Unlike /queue/get_msg_num_all_queues (fast cache from Redis heartbeat),
    this endpoint queries the broker via publisher.get_message_count() so it can
    be used to "force refresh" stale counts.

    Body JSON:
        {"queue_names": ["q1", "q2", ...]}

    Query:
        project_id: optional
    """
    project_id = request.args.get("project_id")
    has_access, error_response = _check_project_access(project_id, required_level="read")
    if not has_access:
        return error_response

    project_code = _get_project_code(project_id)

    body = request.get_json(silent=True) or {}
    queue_names = body.get("queue_names") or body.get("queues") or []
    if not isinstance(queue_names, list):
        return jsonify({"success": False, "error": "queue_names 必须是列表"}), 400

    # Basic abuse protection.
    if len(queue_names) > 200:
        return jsonify({"success": False, "error": "一次最多查询 200 个队列"}), 400

    # Project isolation: check once.
    allowed = None
    if project_code:
        allowed = _normalize_queue_names(
            QueuesConusmerParamsGetter(care_project_name=project_code).get_all_queue_names()
        )

    ret: dict[str, int] = {}
    for qn in queue_names:
        qn_str = qn.decode() if isinstance(qn, bytes) else str(qn)
        if allowed is not None and qn_str not in allowed:
            # Skip unauthorized queues silently to avoid leaking names.
            continue
        try:
            broker_kind = SingleQueueConusmerParamsGetter(qn_str).get_one_queue_params_use_cache().get("broker_kind")
            count = _get_realtime_msg_count(qn_str, broker_kind)
            ret[qn_str] = count
            _save_msg_count_info(qn_str, count)
        except Exception:
            ret[qn_str] = -1
            logger.debug(f"get_message_count failed for queue={qn_str}", exc_info=True)

    return jsonify(ret)


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

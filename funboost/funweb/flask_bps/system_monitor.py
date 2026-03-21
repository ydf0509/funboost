# -*- coding: utf-8 -*-
import json
import os

import threading
import time
import uuid

from flask import Blueprint, request, jsonify
from flask_login import login_required

from funboost.utils.redis_manager import RedisMixin
from funboost.funweb.flask_bps.web_helper import LOCAL_IP

monitor_bp = Blueprint('monitor', __name__)

_redis = RedisMixin().redis_db_frame

_PSUTIL_OK = False
try:
    import psutil
    _PSUTIL_OK = True
except ImportError:
    raise
    print('[system_monitor] psutil 未安装，资源监控采集功能不可用。pip install psutil 后重启即可。')




_RETENTION_SECS = 30 * 24 * 3600   # 30 天
_TTL_SECS = 40 * 24 * 3600         # 40 天
_COLLECT_INTERVAL = 10              # 每 10 秒聚合一次
_HEARTBEAT_TTL = 35                 # 心跳 TTL


def _zset_key(ip=None):
    return f'monitor:{ip or LOCAL_IP}'


def _heartbeat_key(ip=None):
    return f'monitor:{ip or LOCAL_IP}:heartbeat'


def _get_root_path():
    # if os.name == 'nt':
    #     drive = os.path.splitdrive(os.getcwd())[0]
    #     return drive + os.sep if drive else 'C:\\'
    return '/'


# ======================== 采集线程 ========================

def _collector_loop():
    root_path = _get_root_path()
    zkey = _zset_key()
    hkey = _heartbeat_key()
    collector_uuid = str(uuid.uuid4())

    while True:
        try:
            # 单例检查：近 25 秒内有其他采集器写过心跳则跳过
            last_hb = _redis.get(hkey)
            if last_hb:
                try:
                    hb_data = json.loads(last_hb)
                    if hb_data.get('uuid') != collector_uuid and time.time() - float(hb_data.get('ts', 0)) < 25:
                        time.sleep(_COLLECT_INTERVAL)
                        continue
                except (ValueError, TypeError):
                    pass

            # 采集 10 个样本，每秒 1 次
            cpu_samples = []
            mem_samples = []
            disk_samples = []
            for _ in range(_COLLECT_INTERVAL):
                cpu_samples.append(psutil.cpu_percent(interval=0))
                mem_samples.append(psutil.virtual_memory().percent)
                try:
                    disk_samples.append(psutil.disk_usage(root_path).percent)
                except Exception:
                    disk_samples.append(0.0)
                time.sleep(1)

            avg_cpu = round(sum(cpu_samples) / len(cpu_samples), 1)
            avg_mem = round(sum(mem_samples) / len(mem_samples), 1)
            avg_disk = round(sum(disk_samples) / len(disk_samples), 1) if disk_samples else 0.0

            ts = time.time()
            member = json.dumps({
                'ts': round(ts, 1),
                'cpu': avg_cpu,
                'mem': avg_mem,
                'disk': avg_disk,
            })
            _redis.zadd(zkey, {member: ts})

            # 滑动窗口清理
            _redis.zremrangebyscore(zkey, 0, ts - _RETENTION_SECS)
            _redis.expire(zkey, _TTL_SECS)

            # 刷新心跳
            _redis.set(hkey, json.dumps({'ts': str(ts), 'uuid': collector_uuid}), ex=_HEARTBEAT_TTL)

        except Exception as e:
            print(f'[system_monitor] 采集异常: {e}')
            time.sleep(_COLLECT_INTERVAL)




# ======================== API 路由 ========================

@monitor_bp.route('/monitor/current', methods=['GET'])
@login_required
def monitor_current():
    """返回当前主机最新一条监控数据"""
    ip = request.args.get('ip', LOCAL_IP)
    raw = _redis.zrevrange(_zset_key(ip), 0, 0)
    if not raw:
        return jsonify({'succ': True, 'data': None, 'ip': ip})
    try:
        data = json.loads(raw[0])
    except (json.JSONDecodeError, IndexError):
        data = None
    return jsonify({'succ': True, 'data': data, 'ip': ip})


@monitor_bp.route('/monitor/data', methods=['GET'])
@login_required
def monitor_data():
    """按时间范围查询时序数据，支持降采样"""
    ip = request.args.get('ip', LOCAL_IP)
    now = time.time()
    start_ts = float(request.args.get('start_ts', now - 3600))
    end_ts = float(request.args.get('end_ts', now))
    max_samples = int(request.args.get('samples', 360))

    raw_list = _redis.zrangebyscore(_zset_key(ip), start_ts, end_ts)

    points = []
    for raw in raw_list:
        try:
            points.append(json.loads(raw))
        except json.JSONDecodeError:
            continue

    # 降采样
    if len(points) > max_samples > 0:
        step = len(points) / max_samples
        sampled = []
        for i in range(max_samples):
            idx = int(i * step)
            sampled.append(points[idx])
        if points[-1] not in sampled:
            sampled.append(points[-1])
        points = sampled

    return jsonify({'succ': True, 'data': points, 'ip': ip, 'total': len(points)})


@monitor_bp.route('/monitor/hosts', methods=['GET'])
@login_required
def monitor_hosts():
    """返回所有有监控数据的主机 IP 列表"""
    cursor = 0
    ips = set()
    while True:
        cursor, keys = _redis.scan(cursor, match='monitor:*', count=100)
        for k in keys:
            if ':heartbeat' in k:
                continue
            parts = k.split(':')
            if len(parts) == 2:
                ips.add(parts[1])
        if cursor == 0:
            break
    ip_list = sorted(ips)
    if LOCAL_IP not in ip_list:
        ip_list.insert(0, LOCAL_IP)
    return jsonify({'succ': True, 'data': ip_list, 'current': LOCAL_IP})




_collector_thread = threading.Thread(target=_collector_loop, daemon=True)
_collector_thread.start()
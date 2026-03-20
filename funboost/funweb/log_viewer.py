# -*- coding: utf-8 -*-
import datetime
import json
import os
import re
import socket
import time

from flask import Blueprint, request, jsonify, Response
from flask_login import login_required

from funboost.utils.redis_manager import RedisMixin

log_bp = Blueprint('log_viewer', __name__)

_redis = RedisMixin().redis_db_frame

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')
_LOG_TS_RE = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')
_MAX_SCAN_BYTES = 50 * 1024 * 1024
_LOG_STREAM_MAX_SEC = 300


def _get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = socket.gethostbyname(socket.gethostname())
    return ip


LOCAL_IP = _get_local_ip()


def _folders_key():
    return f'funweb:{LOCAL_IP}:log_folders'


# ======================== 安全校验 ========================

_SENSITIVE_LINUX = {'/etc', '/root', '/proc', '/sys', '/dev', '/boot', '/sbin', '/bin'}
_SENSITIVE_WIN = set()
for _d in ('Windows', 'ProgramData', 'Recovery', 'System Volume Information'):
    for _drive in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        _SENSITIVE_WIN.add(os.path.normcase(f'{_drive}:\\{_d}'))


def _is_sensitive(path):
    norm = os.path.normcase(os.path.realpath(path))
    checks = _SENSITIVE_WIN if os.name == 'nt' else _SENSITIVE_LINUX
    for s in checks:
        ref = os.path.normcase(s)
        if norm == ref or norm.startswith(ref + os.sep):
            return True
    return False


def _is_subpath(child, parent):
    rc = os.path.normcase(os.path.realpath(child))
    rp = os.path.normcase(os.path.realpath(parent))
    return rc == rp or rc.startswith(rp + os.sep)


def _validate_file(filepath):
    folders = _redis.smembers(_folders_key())
    if not folders:
        return False
    for folder in folders:
        if _is_subpath(filepath, folder):
            return True
    return False


def _validate_folder_access(folder_path):
    folders = _redis.smembers(_folders_key())
    if not folders:
        return False
    for folder in folders:
        if _is_subpath(folder_path, folder):
            return True
    return False


# ======================== 工具函数 ========================

def _decode_line(raw):
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('gbk', errors='replace')


def _strip_ansi(text):
    return _ANSI_RE.sub('', text)


def _parse_log_time(line):
    m = _LOG_TS_RE.search(line)
    if m:
        try:
            return datetime.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
    return None


def _parse_dt(s):
    if not s:
        return None
    for fmt in (
        '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d %H', '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M', '%Y-%m-%dT%H',
        '%Y/%m/%d %H:%M:%S', '%Y/%m/%d %H:%M', '%Y/%m/%d',
    ):
        try:
            return datetime.datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    return None


def _bisect_log_offset(filepath, target_dt):
    file_size = os.path.getsize(filepath)
    if file_size == 0:
        return 0
    with open(filepath, 'rb') as f:
        lo, hi = 0, file_size
        while lo < hi:
            mid = (lo + hi) // 2
            f.seek(mid)
            if mid > 0:
                f.readline()
            dt = None
            for _ in range(50):
                raw = f.readline()
                if not raw:
                    break
                dt = _parse_log_time(_decode_line(raw))
                if dt is not None:
                    break
            if dt is None:
                hi = mid
            elif dt < target_dt:
                lo = mid + 1
            else:
                hi = mid
        return max(0, lo - 256)


def _read_log_lines_range(filepath, max_lines, start_offset=0, end_offset=None):
    try:
        with open(filepath, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()
            if file_size == 0:
                return []
            if end_offset is None or end_offset > file_size:
                end_offset = file_size
            if start_offset < 0:
                start_offset = 0
            if start_offset >= end_offset:
                return []
            actual_start = max(start_offset, end_offset - _MAX_SCAN_BYTES)
            lines = []
            chunk_size = 65536
            pos = end_offset
            partial = b''
            while pos > actual_start and len(lines) < max_lines + 1:
                read_size = min(chunk_size, pos - actual_start)
                pos -= read_size
                f.seek(pos)
                chunk = f.read(read_size) + partial
                chunk_lines = chunk.split(b'\n')
                partial = chunk_lines[0]
                lines = chunk_lines[1:] + lines
            if partial:
                lines = [partial] + lines
            result = lines[-max_lines:]
            return [_decode_line(line) for line in result]
    except Exception:
        return []


def _read_log_tail(filepath, max_lines=1000):
    try:
        with open(filepath, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()
            if file_size == 0:
                return []
            lines = []
            chunk_size = 8192
            remaining = file_size
            partial = b''
            while remaining > 0 and len(lines) < max_lines + 1:
                read_size = min(chunk_size, remaining)
                remaining -= read_size
                f.seek(remaining)
                chunk = f.read(read_size) + partial
                chunk_lines = chunk.split(b'\n')
                partial = chunk_lines[0]
                lines = chunk_lines[1:] + lines
            if partial:
                lines = [partial] + lines
            result_lines = lines[-max_lines:]
            return [_decode_line(line) for line in result_lines]
    except Exception:
        return []


def _grep_fast(filepath, keyword, max_lines=200, start_offset=0, end_offset=None):
    """Grep-like fast keyword search via binary scan. Only decodes matching lines."""
    try:
        file_size = os.path.getsize(filepath)
        if end_offset is None or end_offset > file_size:
            end_offset = file_size
        if start_offset < 0:
            start_offset = 0
        if start_offset >= end_offset:
            return []
        actual_start = max(start_offset, end_offset - _MAX_SCAN_BYTES)

        with open(filepath, 'rb') as f:
            f.seek(actual_start)
            data = f.read(end_offset - actual_start)

        kw_lower = keyword.lower()
        kw_variants = set()
        try:
            kw_variants.add(kw_lower.encode('utf-8'))
        except Exception:
            pass
        try:
            gb = kw_lower.encode('gbk')
            kw_variants.add(gb)
        except Exception:
            pass
        if not kw_variants:
            return []

        raw_lines = data.split(b'\n')
        matches = []
        for raw in raw_lines:
            if not raw.strip():
                continue
            low = raw.lower()
            if any(kb in low for kb in kw_variants):
                decoded = _strip_ansi(_decode_line(raw))
                matches.append(decoded)

        return matches[-max_lines:]
    except Exception:
        return []


def _format_size(size):
    if size < 1024:
        return f'{size} B'
    if size < 1024 * 1024:
        return f'{size / 1024:.1f} KB'
    if size < 1024 * 1024 * 1024:
        return f'{size / (1024 * 1024):.1f} MB'
    return f'{size / (1024 * 1024 * 1024):.2f} GB'


# ======================== API 路由 ========================

@log_bp.route('/logview/folders', methods=['GET'])
@login_required
def list_folders():
    folders = _redis.smembers(_folders_key())
    result = []
    for f in sorted(folders):
        exists = os.path.isdir(f)
        result.append({'path': f, 'exists': exists})
    return jsonify({'succ': True, 'data': result})


@log_bp.route('/logview/folders/add', methods=['POST'])
@login_required
def add_folder():
    data = request.get_json(force=True)
    path = data.get('path', '').strip()
    if not path:
        return jsonify({'succ': False, 'msg': '路径不能为空'})
    if not os.path.isabs(path):
        return jsonify({'succ': False, 'msg': '请输入绝对路径'})
    if _is_sensitive(path):
        return jsonify({'succ': False, 'msg': '不允许添加系统敏感目录'})
    if not os.path.isdir(path):
        return jsonify({'succ': False, 'msg': f'目录不存在: {path}'})
    _redis.sadd(_folders_key(), path)
    return jsonify({'succ': True, 'msg': '添加成功'})


@log_bp.route('/logview/folders/remove', methods=['POST'])
@login_required
def remove_folder():
    data = request.get_json(force=True)
    path = data.get('path', '').strip()
    _redis.srem(_folders_key(), path)
    return jsonify({'succ': True, 'msg': '已移除'})


@log_bp.route('/logview/files', methods=['GET'])
@login_required
def list_files():
    folder = request.args.get('folder', '').strip()
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'mtime')
    sort_order = request.args.get('order', 'desc')
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 100))

    if not folder:
        return jsonify({'succ': False, 'msg': '请指定文件夹路径'})
    if not os.path.isabs(folder):
        return jsonify({'succ': False, 'msg': '请使用绝对路径'})

    if not _validate_folder_access(folder):
        return jsonify({'succ': False, 'msg': '无权访问该目录'})

    real_folder = os.path.realpath(folder)
    if not os.path.isdir(real_folder):
        return jsonify({'succ': False, 'msg': '目录不存在'})

    search_lower = search.lower() if search else ''
    entries = []
    try:
        for name in os.listdir(real_folder):
            full_path = os.path.join(real_folder, name)
            if search_lower and search_lower not in name.lower():
                continue
            try:
                stat = os.stat(full_path)
                is_dir = os.path.isdir(full_path)
                ext = os.path.splitext(name)[1].lower() if not is_dir else ''
                entries.append({
                    'name': name,
                    'path': full_path,
                    'is_dir': is_dir,
                    'size': stat.st_size if not is_dir else 0,
                    'size_str': _format_size(stat.st_size) if not is_dir else '-',
                    'mtime': stat.st_mtime,
                    'mtime_str': datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'ctime': stat.st_ctime,
                    'ctime_str': datetime.datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'ext': ext,
                })
            except OSError:
                continue
    except PermissionError:
        return jsonify({'succ': False, 'msg': '无权限读取该目录'})

    reverse = sort_order == 'desc'
    if sort_by == 'size':
        entries.sort(key=lambda e: (not e['is_dir'], e['size']), reverse=reverse)
    elif sort_by == 'mtime':
        entries.sort(key=lambda e: (not e['is_dir'], e['mtime']), reverse=reverse)
    elif sort_by == 'ctime':
        entries.sort(key=lambda e: (not e['is_dir'], e['ctime']), reverse=reverse)
    elif sort_by == 'ext':
        entries.sort(key=lambda e: (not e['is_dir'], e['ext'], e['name'].lower()), reverse=reverse)
    else:
        entries.sort(key=lambda e: (not e['is_dir'], e['name'].lower()), reverse=reverse)

    total = len(entries)
    paginated = entries[offset:offset + limit]

    return jsonify({'succ': True, 'data': paginated, 'folder': real_folder, 'total': total})


@log_bp.route('/logview/content', methods=['GET'])
@login_required
def read_content():
    filepath = request.args.get('file', '').strip()
    keyword = request.args.get('keyword', '').strip()
    time_start = request.args.get('time_start', '').strip()
    time_end = request.args.get('time_end', '').strip()
    max_lines = int(request.args.get('lines', 200))

    if not filepath:
        return jsonify({'succ': False, 'msg': '请指定文件路径'})
    if not _validate_file(filepath):
        return jsonify({'succ': False, 'msg': '无权访问该文件'})
    if not os.path.isfile(filepath):
        return jsonify({'succ': False, 'msg': '文件不存在'})

    try:
        file_stat = os.stat(filepath)
        file_size = file_stat.st_size
        file_mtime = datetime.datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    except OSError:
        return jsonify({'succ': False, 'msg': '无法读取文件信息'})

    dt_start = _parse_dt(time_start)
    dt_end = _parse_dt(time_end)

    start_off = 0
    end_off = file_size

    if dt_start:
        start_off = _bisect_log_offset(filepath, dt_start)
    if dt_end:
        end_off = _bisect_log_offset(filepath, dt_end + datetime.timedelta(seconds=1))

    if start_off >= end_off and (dt_start or dt_end):
        return jsonify({
            'succ': True, 'data': [], 'total': 0,
            'file_size': file_size, 'file_size_str': _format_size(file_size),
            'file_mtime': file_mtime,
        })

    if keyword:
        result_lines = _grep_fast(filepath, keyword, max_lines, start_off, end_off)
        return jsonify({
            'succ': True,
            'data': result_lines,
            'total': len(result_lines),
            'file_size': file_size,
            'file_size_str': _format_size(file_size),
            'file_mtime': file_mtime,
        })

    raw_lines = _read_log_lines_range(filepath, max_lines * 3, start_off, end_off)

    entries = []
    has_any_ts = False
    for line in raw_lines:
        if not line.strip():
            continue
        clean = _strip_ansi(line)
        lt = _parse_log_time(clean)
        if lt:
            has_any_ts = True
            entries.append((lt, [clean]))
        else:
            if entries:
                entries[-1][1].append(clean)
            else:
                entries.append((None, [clean]))

    filtered = []
    for entry_time, entry_lines in entries:
        if dt_start or dt_end:
            if entry_time is not None:
                if dt_start and entry_time < dt_start:
                    continue
                if dt_end and entry_time > dt_end:
                    continue
            elif has_any_ts:
                continue

        filtered.extend(entry_lines)

    result_lines = filtered[-max_lines:]

    return jsonify({
        'succ': True,
        'data': result_lines,
        'total': len(result_lines),
        'file_size': file_size,
        'file_size_str': _format_size(file_size),
        'file_mtime': file_mtime,
    })


@log_bp.route('/logview/stream', methods=['GET'])
@login_required
def log_stream():
    """SSE 端点：实时推送日志新增内容（类似 tail -f）"""
    filepath = request.args.get('file', '').strip()

    if not filepath or not _validate_file(filepath):
        return Response('data: {"error": "无权访问"}\n\n',
                        mimetype='text/event-stream', status=403)
    if not os.path.isfile(filepath):
        return Response('data: {"error": "文件不存在"}\n\n',
                        mimetype='text/event-stream', status=404)

    def generate():
        f = None
        deadline = time.time() + _LOG_STREAM_MAX_SEC
        try:
            f = open(filepath, 'rb')
            f.seek(0, 2)
            last_pos = f.tell()
            idle_ticks = 0

            while time.time() < deadline:
                try:
                    cur_size = os.path.getsize(filepath)
                except OSError:
                    time.sleep(1)
                    continue

                if cur_size < last_pos:
                    last_pos = 0
                    yield f'data: {json.dumps({"event": "truncated"})}\n\n'

                if cur_size > last_pos:
                    f.seek(last_pos)
                    new_data = f.read(cur_size - last_pos)
                    last_pos = cur_size
                    for raw_line in new_data.split(b'\n'):
                        if raw_line.strip():
                            text = _strip_ansi(_decode_line(raw_line))
                            yield f'data: {json.dumps({"line": text})}\n\n'
                    idle_ticks = 0
                else:
                    idle_ticks += 1
                    if idle_ticks >= 30:
                        yield ': heartbeat\n\n'
                        idle_ticks = 0

                time.sleep(0.5)
            yield (
                'data: '
                + json.dumps({
                    'event': 'timeout',
                    'msg': '已持续实时推送 5 分钟，已自动停止。需要请再次开启实时。',
                }, ensure_ascii=False)
                + '\n\n'
            )
        except GeneratorExit:
            pass
        finally:
            if f:
                f.close()

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )


@log_bp.route('/logview/file_info', methods=['GET'])
@login_required
def file_info():
    filepath = request.args.get('file', '').strip()
    if not filepath or not _validate_file(filepath):
        return jsonify({'succ': False, 'msg': '无权访问'})
    if not os.path.isfile(filepath):
        return jsonify({'succ': False, 'msg': '文件不存在'})
    try:
        stat = os.stat(filepath)
        return jsonify({
            'succ': True,
            'data': {
                'path': filepath,
                'name': os.path.basename(filepath),
                'size': stat.st_size,
                'size_str': _format_size(stat.st_size),
                'mtime': stat.st_mtime,
                'mtime_str': datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            }
        })
    except OSError as e:
        return jsonify({'succ': False, 'msg': str(e)})

# -*- coding: utf-8 -*-
import datetime
import json
import os
import re
import signal
import socket
import subprocess
import time
import traceback
import uuid

from flask import Blueprint, request, jsonify
from flask_login import login_required

from funboost.utils.redis_manager import RedisMixin

deploy_bp = Blueprint('deploy', __name__)

_redis = RedisMixin().redis_db_frame


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


def _key_prefix():
    return f'script_deploy:{LOCAL_IP}'


def _config_key(name):
    return f'{_key_prefix()}:{name}:config'


def _runtime_key(name):
    return f'{_key_prefix()}:{name}:runtime'


def _names_key():
    return f'{_key_prefix()}:deploy_names'


def _get_log_path():
    try:
        from nb_log import nb_log_config_default
        return str(nb_log_config_default.LOG_PATH)
    except Exception:
        if os.name == 'nt':
            return os.path.join(os.path.splitdrive(os.getcwd())[0] + os.sep, 'pythonlogs')
        return os.path.join(os.path.expanduser('~'), 'pythonlogs')


def _check_process_alive(pid, deploy_flag):
    """通过 PID 和 deploy_flag 判断进程是否存活"""
    if not pid:
        return False
    pid = int(pid)
    try:
        if os.name == 'nt':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not handle:
                return False
            try:
                exit_code = ctypes.c_ulong()
                if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                    return exit_code.value == STILL_ACTIVE
                return False
            finally:
                kernel32.CloseHandle(handle)
        else:
            os.kill(pid, 0)
            if deploy_flag:
                cmdline_path = f'/proc/{pid}/cmdline'
                if os.path.exists(cmdline_path):
                    with open(cmdline_path, 'r') as f:
                        cmdline = f.read()
                    return deploy_flag in cmdline
            return True
    except (ProcessLookupError, PermissionError, OSError, Exception):
        return False


def _kill_process(pid):
    """跨平台终止进程"""
    pid = int(pid)
    try:
        if os.name == 'nt':
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)],
                           capture_output=True, timeout=10)
        else:
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
            try:
                os.kill(pid, 0)
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        return True
    except Exception:
        return False


def _get_deploy_status(name):
    """获取部署状态信息"""
    runtime_data = _redis.hgetall(_runtime_key(name))
    pid = runtime_data.get('pid', '')
    deploy_flag = runtime_data.get('deploy_flag', '')
    start_time = runtime_data.get('start_time', '')

    alive = False
    if pid:
        alive = _check_process_alive(pid, deploy_flag)
        if not alive:
            _redis.hset(_runtime_key(name), mapping={'pid': '', 'start_time': '', 'deploy_flag': ''})
            pid = ''
            start_time = ''
            deploy_flag = ''

    return {
        'running': alive,
        'pid': pid,
        'start_time': start_time,
        'deploy_flag': deploy_flag,
    }


def _read_log_tail(filepath, max_lines=1000):
    """从文件尾部读取最后 max_lines 行，高效处理大文件"""
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
            decoded = []
            for line in result_lines:
                try:
                    decoded.append(line.decode('utf-8'))
                except UnicodeDecodeError:
                    decoded.append(line.decode('gbk', errors='replace'))
            return decoded
    except Exception:
        return []


def _find_log_files(sys_std_file_name):
    """查找包含 sys_std_file_name 的日志文件，不限制扩展名，因为 nb_log 生成的文件名后缀就是 SYS_STD_FILE_NAME 本身"""
    log_path = _get_log_path()
    if not os.path.isdir(log_path):
        return []

    matched = []
    for fname in os.listdir(log_path):
        if sys_std_file_name in fname:
            full_path = os.path.join(log_path, fname)
            if os.path.isfile(full_path):
                matched.append(full_path)

    matched.sort()
    return matched


_LOG_TIME_PATTERN = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')


def _parse_log_time(line):
    """解析日志行开头的时间戳"""
    m = _LOG_TIME_PATTERN.match(line)
    if m:
        try:
            return datetime.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
    return None


# ======================== 路由 ========================

@deploy_bp.route('/deploy/list', methods=['GET'])
@login_required
def deploy_list():
    names = _redis.smembers(_names_key())
    result = []
    for name in sorted(names):
        config = _redis.hgetall(_config_key(name))
        status = _get_deploy_status(name)
        result.append({
            'name': name,
            'project_dir': config.get('project_dir', ''),
            'start_cmd': config.get('start_cmd', ''),
            'sys_std_file_name': config.get('sys_std_file_name', name),
            **status,
        })
    return jsonify({'succ': True, 'data': result, 'ip': LOCAL_IP})


@deploy_bp.route('/deploy/save', methods=['POST'])
@login_required
def deploy_save():
    data = request.get_json(force=True)
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'succ': False, 'msg': '部署名称不能为空'})

    project_dir = data.get('project_dir', '').strip()
    start_cmd = data.get('start_cmd', '').strip()
    env_vars = data.get('env_vars', '{}')
    sys_std_file_name = data.get('sys_std_file_name', '').strip() or name

    if isinstance(env_vars, dict):
        env_vars = json.dumps(env_vars, ensure_ascii=False)

    _redis.sadd(_names_key(), name)
    _redis.hset(_config_key(name), mapping={
        'name': name,
        'project_dir': project_dir,
        'start_cmd': start_cmd,
        'env_vars': env_vars,
        'sys_std_file_name': sys_std_file_name,
    })
    return jsonify({'succ': True, 'msg': '保存成功'})


@deploy_bp.route('/deploy/<name>/delete', methods=['DELETE'])
@login_required
def deploy_delete(name):
    status = _get_deploy_status(name)
    if status['running']:
        _kill_process(status['pid'])

    _redis.srem(_names_key(), name)
    _redis.delete(_config_key(name))
    _redis.delete(_runtime_key(name))
    return jsonify({'succ': True, 'msg': '删除成功'})


@deploy_bp.route('/deploy/<name>/start', methods=['POST'])
@login_required
def deploy_start(name):
    config = _redis.hgetall(_config_key(name))
    if not config:
        return jsonify({'succ': False, 'msg': '部署配置不存在'})

    status = _get_deploy_status(name)
    if status['running']:
        return jsonify({'succ': False, 'msg': '进程已在运行中'})

    project_dir = config.get('project_dir', '')
    start_cmd = config.get('start_cmd', '')
    sys_std_file_name = config.get('sys_std_file_name', name)

    if not start_cmd:
        return jsonify({'succ': False, 'msg': '启动命令为空'})

    if project_dir and not os.path.isdir(project_dir):
        return jsonify({'succ': False, 'msg': f'项目目录不存在: {project_dir}'})

    deploy_flag = str(uuid.uuid4())
    cmd_with_flag = f'{start_cmd} --deploy_flag={deploy_flag}'

    env = os.environ.copy()
    env['SYS_STD_FILE_NAME'] = sys_std_file_name
    try:
        extra_env = json.loads(config.get('env_vars', '{}'))
        if isinstance(extra_env, dict):
            env.update(extra_env)
    except (json.JSONDecodeError, TypeError):
        pass

    try:
        if os.name == 'nt':
            proc = subprocess.Popen(
                cmd_with_flag, shell=True, cwd=project_dir or None, env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        else:
            proc = subprocess.Popen(
                cmd_with_flag, shell=True, cwd=project_dir or None, env=env,
                start_new_session=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        _redis.hset(_runtime_key(name), mapping={
            'pid': str(proc.pid),
            'start_time': now_str,
            'deploy_flag': deploy_flag,
        })
        return jsonify({'succ': True, 'msg': f'启动成功, PID={proc.pid}', 'pid': proc.pid})
    except Exception as e:
        return jsonify({'succ': False, 'msg': f'启动失败: {e}', 'traceback': traceback.format_exc()})


@deploy_bp.route('/deploy/<name>/stop', methods=['POST'])
@login_required
def deploy_stop(name):
    status = _get_deploy_status(name)
    if not status['running']:
        return jsonify({'succ': False, 'msg': '进程未在运行'})

    ok = _kill_process(status['pid'])
    _redis.hset(_runtime_key(name), mapping={'pid': '', 'start_time': '', 'deploy_flag': ''})
    if ok:
        return jsonify({'succ': True, 'msg': '停止成功'})
    return jsonify({'succ': False, 'msg': '停止进程时出错'})


@deploy_bp.route('/deploy/<name>/restart', methods=['POST'])
@login_required
def deploy_restart(name):
    status = _get_deploy_status(name)
    if status['running']:
        _kill_process(status['pid'])
        _redis.hset(_runtime_key(name), mapping={'pid': '', 'start_time': '', 'deploy_flag': ''})
        time.sleep(1)

    config = _redis.hgetall(_config_key(name))
    if not config:
        return jsonify({'succ': False, 'msg': '部署配置不存在'})

    project_dir = config.get('project_dir', '')
    start_cmd = config.get('start_cmd', '')
    sys_std_file_name = config.get('sys_std_file_name', name)

    if not start_cmd:
        return jsonify({'succ': False, 'msg': '启动命令为空'})

    deploy_flag = str(uuid.uuid4())
    cmd_with_flag = f'{start_cmd} --deploy_flag={deploy_flag}'

    env = os.environ.copy()
    env['SYS_STD_FILE_NAME'] = sys_std_file_name
    try:
        extra_env = json.loads(config.get('env_vars', '{}'))
        if isinstance(extra_env, dict):
            env.update(extra_env)
    except (json.JSONDecodeError, TypeError):
        pass

    try:
        if os.name == 'nt':
            proc = subprocess.Popen(
                cmd_with_flag, shell=True, cwd=project_dir or None, env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        else:
            proc = subprocess.Popen(
                cmd_with_flag, shell=True, cwd=project_dir or None, env=env,
                start_new_session=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        _redis.hset(_runtime_key(name), mapping={
            'pid': str(proc.pid),
            'start_time': now_str,
            'deploy_flag': deploy_flag,
        })
        return jsonify({'succ': True, 'msg': f'重启成功, PID={proc.pid}', 'pid': proc.pid})
    except Exception as e:
        return jsonify({'succ': False, 'msg': f'重启失败: {e}', 'traceback': traceback.format_exc()})


@deploy_bp.route('/deploy/<name>/status', methods=['GET'])
@login_required
def deploy_status(name):
    config = _redis.hgetall(_config_key(name))
    status = _get_deploy_status(name)
    return jsonify({'succ': True, 'data': {**config, **status}})


@deploy_bp.route('/deploy/<name>/git_pull', methods=['POST'])
@login_required
def deploy_git_pull(name):
    config = _redis.hgetall(_config_key(name))
    project_dir = config.get('project_dir', '')
    if not project_dir or not os.path.isdir(project_dir):
        return jsonify({'succ': False, 'msg': f'项目目录不存在: {project_dir}'})

    try:
        result = subprocess.run(
            ['git', '-C', project_dir, 'pull'],
            capture_output=True, text=True, timeout=60
        )
        output = result.stdout + result.stderr
        success = result.returncode == 0
        return jsonify({
            'succ': success,
            'msg': '拉取成功' if success else '拉取失败',
            'output': output,
            'returncode': result.returncode,
        })
    except subprocess.TimeoutExpired:
        return jsonify({'succ': False, 'msg': 'Git pull 超时（60秒）', 'output': ''})
    except Exception as e:
        return jsonify({'succ': False, 'msg': f'Git pull 异常: {e}', 'output': traceback.format_exc()})


@deploy_bp.route('/deploy/<name>/logs', methods=['GET'])
@login_required
def deploy_logs(name):
    config = _redis.hgetall(_config_key(name))
    sys_std_file_name = config.get('sys_std_file_name', name)
    keyword = request.args.get('keyword', '').strip()
    time_start = request.args.get('time_start', '').strip()
    time_end = request.args.get('time_end', '').strip()
    max_lines = int(request.args.get('lines', 1000))

    log_files = _find_log_files(sys_std_file_name)
    if not log_files:
        return jsonify({'succ': True, 'data': [], 'files': [], 'total': 0})

    dt_start = None
    dt_end = None
    if time_start:
        try:
            dt_start = datetime.datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
    if time_end:
        try:
            dt_end = datetime.datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass

    all_lines = []
    for fpath in log_files:
        lines = _read_log_tail(fpath, max_lines=max_lines * 2)
        all_lines.extend(lines)

    filtered = []
    for line in all_lines:
        if not line.strip():
            continue

        if dt_start or dt_end:
            lt = _parse_log_time(line)
            if lt:
                if dt_start and lt < dt_start:
                    continue
                if dt_end and lt > dt_end:
                    continue

        if keyword and keyword.lower() not in line.lower():
            continue

        filtered.append(line)

    result_lines = filtered[-max_lines:]

    return jsonify({
        'succ': True,
        'data': result_lines,
        'files': [os.path.basename(f) for f in log_files],
        'total': len(result_lines),
    })


@deploy_bp.route('/deploy/<name>/config', methods=['GET'])
@login_required
def deploy_get_config(name):
    config = _redis.hgetall(_config_key(name))
    if not config:
        return jsonify({'succ': False, 'msg': '部署配置不存在'})
    status = _get_deploy_status(name)
    return jsonify({'succ': True, 'data': {**config, **status}})

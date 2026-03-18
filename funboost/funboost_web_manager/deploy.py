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

_ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*m')


def _strip_ansi(text):
    return _ANSI_ESCAPE_RE.sub('', text)


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


def _get_nohup_log_path(name):
    log_dir = _get_log_path()
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, f'{name}.nohup.log')


def _get_process_create_time(pid):
    """获取进程的 OS 级创建时间戳，用于防止 PID 复用导致误判/误杀"""
    pid = int(pid)
    try:
        if os.name == 'nt':
            import ctypes

            class FILETIME(ctypes.Structure):
                _fields_ = [("dwLowDateTime", ctypes.c_uint32),
                             ("dwHighDateTime", ctypes.c_uint32)]

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(0x1000, False, pid)
            if not handle:
                return None
            try:
                creation = FILETIME()
                exit_t = FILETIME()
                kernel_t = FILETIME()
                user_t = FILETIME()
                if kernel32.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_t),
                                             ctypes.byref(kernel_t), ctypes.byref(user_t)):
                    ft = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
                    return ft / 10000000.0 - 11644473600.0
                return None
            finally:
                kernel32.CloseHandle(handle)
        else:
            with open(f'/proc/{pid}/stat', 'r') as f:
                stat_content = f.read()
            after_comm = stat_content.rsplit(')', 1)[-1].split()
            starttime_ticks = int(after_comm[19])
            boot_time = None
            with open('/proc/stat', 'r') as f:
                for line in f:
                    if line.startswith('btime'):
                        boot_time = int(line.split()[1])
                        break
            if boot_time is None:
                return None
            clock_ticks = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
            return boot_time + starttime_ticks / clock_ticks
    except Exception:
        return None


def _check_process_alive(pid, deploy_flag, stored_create_time=None):
    """检查进程是否存活，通过进程创建时间二次验证防止 PID 复用误判"""
    if not pid:
        return False
    pid = int(pid)
    try:
        if os.name == 'nt':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(0x1000, False, pid)
            if not handle:
                return False
            try:
                exit_code = ctypes.c_ulong()
                if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                    if exit_code.value != 259:
                        return False
                else:
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
                    if deploy_flag not in cmdline:
                        return False

        if stored_create_time:
            try:
                current_ct = _get_process_create_time(pid)
                if current_ct is not None and abs(current_ct - float(stored_create_time)) > 5.0:
                    return False
            except (ValueError, TypeError):
                pass

        return True
    except (ProcessLookupError, PermissionError, OSError, Exception):
        return False


def _kill_process(pid, stored_create_time=None):
    """停止进程，先验证创建时间防止误杀。返回 (ok, err_msg)"""
    pid = int(pid)
    if stored_create_time:
        try:
            current_ct = _get_process_create_time(pid)
            if current_ct is not None and abs(current_ct - float(stored_create_time)) > 5.0:
                return False, 'PID 已被其他进程占用，拒绝停止（避免误杀）'
        except (ValueError, TypeError):
            pass
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
        return True, ''
    except Exception as e:
        return False, str(e)


def _get_deploy_status(name):
    runtime_data = _redis.hgetall(_runtime_key(name))
    pid = runtime_data.get('pid', '')
    deploy_flag = runtime_data.get('deploy_flag', '')
    start_time = runtime_data.get('start_time', '')
    create_time = runtime_data.get('create_time', '')

    alive = False
    if pid:
        alive = _check_process_alive(pid, deploy_flag, create_time)
        if not alive:
            _redis.hset(_runtime_key(name), mapping={
                'pid': '', 'start_time': '', 'deploy_flag': '', 'create_time': ''
            })
            pid = ''
            start_time = ''
            deploy_flag = ''

    return {
        'running': alive,
        'pid': pid,
        'start_time': start_time,
        'deploy_flag': deploy_flag,
    }


def _build_env(config):
    env = os.environ.copy()
    project_dir = config.get('project_dir', '')

    try:
        extra_env = json.loads(config.get('env_vars', '{}'))
        if isinstance(extra_env, dict):
            env.update(extra_env)
    except (json.JSONDecodeError, TypeError):
        pass

    pythonpath_parts = []
    if project_dir:
        pythonpath_parts.append(project_dir)
    user_pythonpath = env.get('PYTHONPATH', '')
    if user_pythonpath:
        pythonpath_parts.append(user_pythonpath)
    if pythonpath_parts:
        env['PYTHONPATH'] = os.pathsep.join(pythonpath_parts)

    return env


def _format_env_summary(config):
    lines = []
    project_dir = config.get('project_dir', '')
    if project_dir:
        lines.append(f'PYTHONPATH={project_dir}' + (';...' if os.environ.get('PYTHONPATH') else ''))
    try:
        extra_env = json.loads(config.get('env_vars', '{}'))
        if isinstance(extra_env, dict):
            for k, v in extra_env.items():
                lines.append(f'{k}={v}')
    except (json.JSONDecodeError, TypeError):
        pass
    return lines


def _wait_process_alive(proc, deploy_flag, create_time, max_wait=30):
    """启动后轮询进程是否存活，最多等待 max_wait 秒。
    返回 (survived_secs, exit_code):
      survived_secs >= 0  表示存活了这么多秒（成功）
      survived_secs < 0   表示进程在 abs(survived_secs) 秒内死亡（失败）
    """
    create_time_str = str(create_time) if create_time else ''
    pid = proc.pid
    for elapsed in range(1, max_wait + 1):
        time.sleep(1)
        if not _check_process_alive(pid, deploy_flag, create_time_str):
            exit_code = None
            try:
                exit_code = proc.poll()
            except Exception:
                pass
            return -elapsed, exit_code
    return max_wait, None


def _read_log_tail_str(log_file, max_lines=30):
    """读取日志文件末尾若干行，返回字符串，用于启动失败诊断"""
    lines = _read_log_tail(log_file, max_lines)
    return ''.join(lines).strip()


def _start_process(name, config):
    project_dir = config.get('project_dir', '')
    start_cmd = config.get('start_cmd', '')

    if not start_cmd:
        return None, '启动命令为空', {}
    if project_dir and not os.path.isdir(project_dir):
        return None, f'项目目录不存在: {project_dir}', {}

    deploy_flag = str(uuid.uuid4())
    log_file = _get_nohup_log_path(name)
    env = _build_env(config)
    cmd_with_flag = f'{start_cmd} --deploy_flag={deploy_flag}'

    if os.name == 'nt':
        display_cmd = f'{cmd_with_flag}  (stdout/stderr >> "{log_file}")'
    else:
        display_cmd = f'nohup {cmd_with_flag} >> "{log_file}" 2>&1 &'

    cmd_detail = {
        'cwd': project_dir or '(当前目录)',
        'full_cmd': display_cmd,
        'log_file': log_file,
        'env_vars': _format_env_summary(config),
    }

    try:
        log_fh = open(log_file, 'a', encoding='utf-8')
        if os.name == 'nt':
            CREATE_NO_WINDOW = 0x08000000
            proc = subprocess.Popen(
                cmd_with_flag, shell=True, cwd=project_dir or None, env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
                stdout=log_fh, stderr=subprocess.STDOUT,
            )
        else:
            proc = subprocess.Popen(
                cmd_with_flag, shell=True, cwd=project_dir or None, env=env,
                start_new_session=True,
                stdout=log_fh, stderr=subprocess.STDOUT,
            )

        time.sleep(0.3)
        create_time = _get_process_create_time(proc.pid)

        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        _redis.hset(_runtime_key(name), mapping={
            'pid': str(proc.pid),
            'start_time': now_str,
            'deploy_flag': deploy_flag,
            'log_file': log_file,
            'create_time': str(create_time) if create_time else '',
        })
        cmd_detail['start_time'] = now_str
        cmd_detail['pid'] = str(proc.pid)

        # 等待最多 30 秒，确认进程持续存活（防止启动即崩溃）
        survived_secs, exit_code_hint = _wait_process_alive(proc, deploy_flag, create_time, max_wait=30)
        cmd_detail['survived_secs'] = survived_secs
        if survived_secs < 0:
            # 进程已死亡，读取日志尾部辅助诊断
            log_tail = _read_log_tail_str(log_file, 30)
            _redis.hset(_runtime_key(name), mapping={
                'pid': '', 'start_time': '', 'deploy_flag': '', 'create_time': ''
            })
            err_msg = f'进程在启动后 {abs(survived_secs)} 秒内退出'
            if exit_code_hint is not None:
                err_msg += f'（退出码: {exit_code_hint}）'
            if log_tail:
                err_msg += f'\n\n--- 日志尾部 ---\n{log_tail}'
            return proc, err_msg, cmd_detail

        return proc, None, cmd_detail
    except Exception as e:
        return None, f'{e}\n{traceback.format_exc()}', cmd_detail


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
            decoded = []
            for line in result_lines:
                try:
                    decoded.append(line.decode('utf-8'))
                except UnicodeDecodeError:
                    decoded.append(line.decode('gbk', errors='replace'))
            return decoded
    except Exception:
        return []


def _find_log_files(name):
    log_path = _get_log_path()
    if not os.path.isdir(log_path):
        return []

    nohup_file = os.path.join(log_path, f'{name}.nohup.log')
    matched = []
    if os.path.isfile(nohup_file):
        matched.append(nohup_file)

    for fname in os.listdir(log_path):
        full_path = os.path.join(log_path, fname)
        if full_path in matched:
            continue
        if name in fname and os.path.isfile(full_path):
            matched.append(full_path)

    matched.sort()
    return matched


_LOG_TIME_PATTERN = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')


def _parse_log_time(line):
    m = _LOG_TIME_PATTERN.search(line)
    if m:
        try:
            return datetime.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
    return None


def _do_git_pull(project_dir, target_branch=None):
    """执行 git pull，可选切换分支。返回 (success, output, current_branch)"""
    current_result = subprocess.run(
        ['git', '-C', project_dir, 'rev-parse', '--abbrev-ref', 'HEAD'],
        capture_output=True, text=True, timeout=10
    )
    current_branch = current_result.stdout.strip() if current_result.returncode == 0 else ''

    if target_branch and target_branch != current_branch:
        local_branch = target_branch
        if '/' in target_branch:
            local_branch = target_branch.split('/', 1)[-1]

        checkout_result = subprocess.run(
            ['git', '-C', project_dir, 'checkout', local_branch],
            capture_output=True, text=True, timeout=30
        )
        if checkout_result.returncode != 0:
            checkout_result = subprocess.run(
                ['git', '-C', project_dir, 'checkout', '-b', local_branch, target_branch],
                capture_output=True, text=True, timeout=30
            )
            if checkout_result.returncode != 0:
                return False, f'切换分支失败:\n{checkout_result.stdout}{checkout_result.stderr}', current_branch
        current_branch = local_branch

    tracking_result = subprocess.run(
        ['git', '-C', project_dir, 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}'],
        capture_output=True, text=True, timeout=10
    )

    result = None
    if tracking_result.returncode == 0:
        result = subprocess.run(
            ['git', '-C', project_dir, 'pull'],
            capture_output=True, text=True, timeout=60
        )
    else:
        remote_result = subprocess.run(
            ['git', '-C', project_dir, 'remote'],
            capture_output=True, text=True, timeout=10
        )
        remotes = [r.strip() for r in remote_result.stdout.strip().split('\n') if r.strip()]
        remote = remotes[0] if remotes else 'origin'

        branch = current_branch
        if branch:
            ls_result = subprocess.run(
                ['git', '-C', project_dir, 'ls-remote', '--heads', remote, branch],
                capture_output=True, text=True, timeout=15
            )
            if ls_result.stdout.strip():
                result = subprocess.run(
                    ['git', '-C', project_dir, 'pull', remote, branch],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode == 0:
                    subprocess.run(
                        ['git', '-C', project_dir, 'branch', '--set-upstream-to', f'{remote}/{branch}', branch],
                        capture_output=True, text=True, timeout=10
                    )
            else:
                for default_branch in ['main', 'master']:
                    ls_default = subprocess.run(
                        ['git', '-C', project_dir, 'ls-remote', '--heads', remote, default_branch],
                        capture_output=True, text=True, timeout=15
                    )
                    if ls_default.stdout.strip():
                        result = subprocess.run(
                            ['git', '-C', project_dir, 'pull', remote, default_branch],
                            capture_output=True, text=True, timeout=60
                        )
                        break
                else:
                    return False, (
                        f'当前分支 "{branch}" 在远程 "{remote}" 上不存在，'
                        f'且未找到 main/master 分支。\n'
                        f'请手动设置 tracking:\n'
                        f'  git branch --set-upstream-to={remote}/<远程分支名> {branch}'
                    ), current_branch
        else:
            return False, '无法检测当前 Git 分支', current_branch

    output = result.stdout + result.stderr
    return result.returncode == 0, output, current_branch


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

    if isinstance(env_vars, dict):
        env_vars = json.dumps(env_vars, ensure_ascii=False)

    _redis.sadd(_names_key(), name)
    _redis.hset(_config_key(name), mapping={
        'name': name,
        'project_dir': project_dir,
        'start_cmd': start_cmd,
        'env_vars': env_vars,
    })
    return jsonify({'succ': True, 'msg': '保存成功'})


@deploy_bp.route('/deploy/<name>/clone', methods=['POST'])
@login_required
def deploy_clone(name):
    data = request.get_json(force=True)
    new_name = data.get('new_name', '').strip()
    if not new_name:
        return jsonify({'succ': False, 'msg': '新部署名称不能为空'})
    if _redis.sismember(_names_key(), new_name):
        return jsonify({'succ': False, 'msg': f'部署名称 "{new_name}" 已存在'})

    config = _redis.hgetall(_config_key(name))
    if not config:
        return jsonify({'succ': False, 'msg': '源部署配置不存在'})

    _redis.sadd(_names_key(), new_name)
    _redis.hset(_config_key(new_name), mapping={
        'name': new_name,
        'project_dir': config.get('project_dir', ''),
        'start_cmd': config.get('start_cmd', ''),
        'env_vars': config.get('env_vars', '{}'),
    })
    return jsonify({'succ': True, 'msg': f'已复制为 "{new_name}"'})


@deploy_bp.route('/deploy/<name>/delete', methods=['DELETE'])
@login_required
def deploy_delete(name):
    status = _get_deploy_status(name)
    if status['running']:
        return jsonify({'succ': False, 'msg': '进程运行中，请先停止再删除'})

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

    proc, err, cmd_detail = _start_process(name, config)
    if err:
        return jsonify({'succ': False, 'msg': f'启动失败: {err}', 'cmd_detail': cmd_detail})
    return jsonify({
        'succ': True,
        'msg': f'启动成功, PID={proc.pid}',
        'pid': proc.pid,
        'cmd_detail': cmd_detail,
    })


@deploy_bp.route('/deploy/<name>/stop', methods=['POST'])
@login_required
def deploy_stop(name):
    status = _get_deploy_status(name)
    if not status['running']:
        return jsonify({'succ': False, 'msg': '进程未在运行'})

    pid = status['pid']
    runtime_data = _redis.hgetall(_runtime_key(name))
    stored_create_time = runtime_data.get('create_time', '')

    if os.name == 'nt':
        stop_cmd = f'taskkill /F /T /PID {pid}'
    else:
        stop_cmd = f'kill -SIGTERM {pid}'

    old_start_time = status.get('start_time', '')

    ok, err_msg = _kill_process(pid, stored_create_time)
    if ok:
        _redis.hset(_runtime_key(name), mapping={
            'pid': '', 'start_time': '', 'deploy_flag': '', 'create_time': ''
        })
    return jsonify({
        'succ': ok,
        'msg': '停止成功' if ok else (err_msg or '停止进程时出错'),
        'cmd_detail': {'stop_cmd': stop_cmd, 'pid': pid, 'old_start_time': old_start_time},
    })


@deploy_bp.route('/deploy/<name>/restart', methods=['POST'])
@login_required
def deploy_restart(name):
    status = _get_deploy_status(name)
    old_pid = status.get('pid', '')
    old_start_time = status.get('start_time', '')
    stop_cmd = ''
    if status['running']:
        if os.name == 'nt':
            stop_cmd = f'taskkill /F /T /PID {old_pid}'
        else:
            stop_cmd = f'kill -SIGTERM {old_pid}'
        runtime_data = _redis.hgetall(_runtime_key(name))
        stored_create_time = runtime_data.get('create_time', '')
        ok, err_msg = _kill_process(old_pid, stored_create_time)
        if not ok and err_msg:
            return jsonify({'succ': False, 'msg': f'停止旧进程失败: {err_msg}',
                            'cmd_detail': {'stop_cmd': stop_cmd, 'old_pid': old_pid,
                                           'old_start_time': old_start_time}})
        _redis.hset(_runtime_key(name), mapping={
            'pid': '', 'start_time': '', 'deploy_flag': '', 'create_time': ''
        })
        time.sleep(1)

    config = _redis.hgetall(_config_key(name))
    if not config:
        return jsonify({'succ': False, 'msg': '部署配置不存在'})

    proc, err, cmd_detail = _start_process(name, config)
    cmd_detail['stop_cmd'] = stop_cmd
    cmd_detail['old_pid'] = old_pid
    cmd_detail['old_start_time'] = old_start_time
    if err:
        return jsonify({'succ': False, 'msg': f'重启失败: {err}', 'cmd_detail': cmd_detail})
    return jsonify({
        'succ': True,
        'msg': f'重启成功, PID={proc.pid}',
        'pid': proc.pid,
        'cmd_detail': cmd_detail,
    })


@deploy_bp.route('/deploy/<name>/status', methods=['GET'])
@login_required
def deploy_status(name):
    config = _redis.hgetall(_config_key(name))
    status = _get_deploy_status(name)
    return jsonify({'succ': True, 'data': {**config, **status}})


@deploy_bp.route('/deploy/<name>/git_branches', methods=['GET'])
@login_required
def deploy_git_branches(name):
    """获取 git 分支列表（自动 fetch --prune 更新远程信息）"""
    config = _redis.hgetall(_config_key(name))
    project_dir = config.get('project_dir', '')
    if not project_dir or not os.path.isdir(project_dir):
        return jsonify({'succ': False, 'msg': f'项目目录不存在: {project_dir}'})

    try:
        subprocess.run(['git', '-C', project_dir, 'fetch', '--prune'],
                       capture_output=True, text=True, timeout=30)

        current = subprocess.run(
            ['git', '-C', project_dir, 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True, text=True, timeout=10
        )
        current_branch = current.stdout.strip() if current.returncode == 0 else ''

        local = subprocess.run(
            ['git', '-C', project_dir, 'branch', '--format=%(refname:short)'],
            capture_output=True, text=True, timeout=10
        )
        local_branches = [b.strip() for b in local.stdout.strip().split('\n') if b.strip()]

        remote = subprocess.run(
            ['git', '-C', project_dir, 'branch', '-r', '--format=%(refname:short)'],
            capture_output=True, text=True, timeout=10
        )
        remote_branches = [b.strip() for b in remote.stdout.strip().split('\n')
                           if b.strip() and 'HEAD' not in b]

        return jsonify({
            'succ': True,
            'current': current_branch,
            'local': local_branches,
            'remote': remote_branches,
        })
    except subprocess.TimeoutExpired:
        return jsonify({'succ': False, 'msg': 'Git 操作超时'})
    except Exception as e:
        return jsonify({'succ': False, 'msg': str(e)})


@deploy_bp.route('/deploy/<name>/git_pull', methods=['POST'])
@login_required
def deploy_git_pull(name):
    config = _redis.hgetall(_config_key(name))
    project_dir = config.get('project_dir', '')
    if not project_dir or not os.path.isdir(project_dir):
        return jsonify({'succ': False, 'msg': f'项目目录不存在: {project_dir}'})

    data = request.get_json(silent=True) or {}
    target_branch = data.get('branch', '').strip()

    try:
        success, output, current_branch = _do_git_pull(project_dir, target_branch or None)
        return jsonify({
            'succ': success,
            'msg': '拉取成功' if success else '拉取失败',
            'output': output,
            'current_branch': current_branch,
        })
    except subprocess.TimeoutExpired:
        return jsonify({'succ': False, 'msg': 'Git pull 超时（60秒）', 'output': ''})
    except Exception as e:
        return jsonify({'succ': False, 'msg': f'Git pull 异常: {e}', 'output': traceback.format_exc()})


@deploy_bp.route('/deploy/<name>/logs', methods=['GET'])
@login_required
def deploy_logs(name):
    keyword = request.args.get('keyword', '').strip()
    time_start = request.args.get('time_start', '').strip()
    time_end = request.args.get('time_end', '').strip()
    max_lines = int(request.args.get('lines', 200))

    log_files = _find_log_files(name)
    if not log_files:
        return jsonify({'succ': True, 'data': [], 'files': [], 'total': 0})

    def _parse_dt(s):
        for fmt in (
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d %H',
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M',
            '%Y-%m-%dT%H',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d %H:%M',
            '%Y/%m/%d',
        ):
            try:
                return datetime.datetime.strptime(s.strip(), fmt)
            except ValueError:
                continue
        return None

    dt_start = _parse_dt(time_start) if time_start else None
    dt_end = _parse_dt(time_end) if time_end else None

    all_lines = []
    for fpath in log_files:
        lines = _read_log_tail(fpath, max_lines=max_lines * 2)
        all_lines.extend(lines)

    filtered = []
    last_time = None
    for line in all_lines:
        if not line.strip():
            continue

        clean_line = _strip_ansi(line)
        lt = _parse_log_time(clean_line)
        if lt:
            last_time = lt

        if dt_start or dt_end:
            effective_time = lt or last_time
            if effective_time:
                if dt_start and effective_time < dt_start:
                    continue
                if dt_end and effective_time > dt_end:
                    continue
            else:
                continue

        if keyword and keyword.lower() not in clean_line.lower():
            continue

        filtered.append(clean_line)

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

# -*- coding: utf-8 -*-
import datetime
import json
import os
import re
import signal
import socket
import subprocess
import time
import threading

import psutil

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


def _check_pid_alive(pid, stored_ct=None):
    """极速验证 PID 是否存活 + create_time 防 PID 复用。
    仅调用 is_running() 和 create_time()，毫秒级，不读环境变量/命令行。
    """
    try:
        p = psutil.Process(int(pid))
        if not p.is_running():
            return False
        if stored_ct:
            try:
                if abs(p.create_time() - float(stored_ct)) > 3.0:
                    return False
            except (psutil.AccessDenied, ValueError):
                pass
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError, OSError):
        return False


def _find_child_pids(parent_pid, timeout=3.0):
    """找到壳进程（cmd.exe/sh）的所有子进程 PID 和 create_time。
    返回 [(pid, create_time), ...]
    """
    found = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            parent = psutil.Process(parent_pid)
            children = parent.children(recursive=True)
            for c in children:
                try:
                    found.append((c.pid, c.create_time()))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            if found:
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            break
        time.sleep(0.3)
    return found


def _find_deploy_pids(name):
    """从 Redis 读取 PID + create_time 列表，逐一验证存活。
    仅调用 is_running() 和 create_time()，不读环境变量/命令行，毫秒级。
    返回 (alive_pid_list, search_cmd_display)
    """
    if os.name == 'nt':
        display = 'Redis pid_list + psutil.Process(pid).is_running()'
    else:
        display = 'Redis pid_list + psutil / kill -0'

    try:
        raw_pids = _redis.hget(_runtime_key(name), 'pid_list')
        pid_list = json.loads(raw_pids) if raw_pids else []
    except Exception:
        pid_list = []
    try:
        raw_cts = _redis.hget(_runtime_key(name), 'ct_list')
        ct_list = json.loads(raw_cts) if raw_cts else []
    except Exception:
        ct_list = []

    alive = []
    for i, pid_str in enumerate(pid_list):
        if not pid_str:
            continue
        ct = ct_list[i] if i < len(ct_list) else None
        if _check_pid_alive(int(pid_str), ct):
            alive.append(int(pid_str))
    return alive, display


def _kill_pids(pids):
    """杀死一组 PID。返回 [(pid, ok, err_msg, kill_cmd), ...]"""
    results = []
    for pid in pids:
        pid = int(pid)
        if os.name == 'nt':
            kill_cmd = f'taskkill /F /T /PID {pid}'
        else:
            kill_cmd = f'kill -SIGTERM {pid} && sleep 1 && kill -SIGKILL {pid}'
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
            results.append((pid, True, '', kill_cmd))
        except Exception as e:
            results.append((pid, False, str(e), kill_cmd))
    return results


def _get_deploy_status(name):
    """获取部署状态：Redis 读 PID + create_time → psutil 快速验证存活。毫秒级。"""
    alive_pids, search_cmd = _find_deploy_pids(name)
    runtime_data = _redis.hgetall(_runtime_key(name))
    start_time = runtime_data.get('start_time', '')

    return {
        'running': len(alive_pids) > 0,
        'pid': ', '.join(str(p) for p in alive_pids) if alive_pids else '',
        'start_time': start_time,
        'pid_list': [str(p) for p in alive_pids],
        'search_cmd': search_cmd,
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


def _format_env_summary(config, name=''):
    lines = []
    if name:
        lines.append(f'FUNWEB_DEPLOY={name}')
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


def _check_pids_still_alive(pid_list, ct_list):
    """检查一批已知 PID 是否仍存活，返回存活的 PID 列表。"""
    alive = []
    for i, pid in enumerate(pid_list):
        ct = ct_list[i] if i < len(ct_list) else None
        if _check_pid_alive(pid, ct):
            alive.append(pid)
    return alive


def _read_log_tail_str(log_file, max_lines=30):
    """读取日志文件末尾若干行，返回字符串，用于启动失败诊断"""
    lines = _read_log_tail(log_file, max_lines)
    return ''.join(lines).strip()


def _start_process(name, config, num_processes=None):
    """启动一个或多个进程。返回 (procs, err, cmd_detail)"""
    project_dir = config.get('project_dir', '')
    start_cmd = config.get('start_cmd', '')

    if not start_cmd:
        return None, '启动命令为空', {}
    if project_dir and not os.path.isdir(project_dir):
        return None, f'项目目录不存在: {project_dir}', {}

    if num_processes is None:
        num_processes = int(config.get('num_processes', '1') or 1)
    num_processes = max(1, num_processes)

    env = _build_env(config)
    env['FUNWEB_DEPLOY'] = name
    health_secs = int(config.get('health_check_secs', '10') or 10)
    log_file = _get_nohup_log_path(name)

    cmd_detail = {
        'cwd': project_dir or '(当前目录)',
        'env_vars': _format_env_summary(config, name),
        'log_file': log_file,
        'num_processes': num_processes,
    }

    shell_procs = []
    errors = []

    for idx in range(num_processes):
        proc_log = log_file

        if os.name == 'nt':
            display_cmd = f'{start_cmd}  (stdout/stderr >> "{proc_log}")'
        else:
            display_cmd = f'nohup {start_cmd} >> "{proc_log}" 2>&1 &'

        if idx == 0:
            cmd_detail['full_cmd'] = display_cmd

        try:
            log_fh = open(proc_log, 'a', encoding='utf-8')
            if os.name == 'nt':
                CREATE_NO_WINDOW = 0x08000000
                proc = subprocess.Popen(
                    start_cmd, shell=True, cwd=project_dir or None, env=env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
                    stdout=log_fh, stderr=subprocess.STDOUT,
                )
            else:
                proc = subprocess.Popen(
                    start_cmd, shell=True, cwd=project_dir or None, env=env,
                    start_new_session=True,
                    stdout=log_fh, stderr=subprocess.STDOUT,
                )
            shell_procs.append(proc)
        except Exception as e:
            errors.append(f'进程 #{idx}: {e}')

    if not shell_procs:
        return None, '所有进程启动失败: ' + '; '.join(errors), cmd_detail

    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 找真实子进程 PID + create_time（python.exe 而非 cmd.exe 壳进程）
    all_real_pids = []
    all_real_cts = []
    failed_any = False

    for i, proc in enumerate(shell_procs):
        child_info = _find_child_pids(proc.pid, timeout=min(health_secs, 5))
        if child_info:
            for cpid, cct in child_info:
                all_real_pids.append(str(cpid))
                all_real_cts.append(str(cct))
        else:
            exit_code = proc.poll()
            if exit_code is not None and exit_code != 0:
                failed_any = True
                log_tail = _read_log_tail_str(log_file, 20)
                err = f'进程 #{i} 启动后退出（退出码: {exit_code}）'
                if log_tail:
                    err += f'\n--- 日志尾部 ---\n{log_tail}'
                errors.append(err)
            else:
                # 壳进程还活着但子进程找不到，用壳进程 PID 兜底
                try:
                    shell_ct = psutil.Process(proc.pid).create_time()
                except Exception:
                    shell_ct = 0
                all_real_pids.append(str(proc.pid))
                all_real_cts.append(str(shell_ct))

    # PID + create_time 写入 Redis
    _redis.hset(_runtime_key(name), mapping={
        'start_time': now_str,
        'pid_list': json.dumps(all_real_pids),
        'ct_list': json.dumps(all_real_cts),
    })

    cmd_detail['start_time'] = now_str
    cmd_detail['pid'] = ', '.join(all_real_pids)
    cmd_detail['survived_secs'] = health_secs if not failed_any else -1

    if failed_any:
        return shell_procs, '\n'.join(errors), cmd_detail

    return shell_procs, None, cmd_detail


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

    prefix = name + '.'
    matched = []
    for fname in os.listdir(log_path):
        if fname.startswith(prefix) and os.path.isfile(os.path.join(log_path, fname)):
            matched.append(os.path.join(log_path, fname))

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


def _parse_dt(s):
    """解析用户输入的时间字符串，兼容多种格式"""
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


_MAX_SCAN_BYTES = 50 * 1024 * 1024  # 50MB


def _decode_line(raw):
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('gbk', errors='replace')


def _bisect_log_offset(filepath, target_dt):
    """二分查找：在日志文件中找到时间戳 >= target_dt 的近似字节偏移。
    利用日志时间戳单调递增的特性，时间复杂度 O(log(file_size))。
    """
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
    """从日志文件的 [start_offset, end_offset) 字节范围中反向读取最后 max_lines 行。
    支持 10GB 级大文件，读取量 ≈ max_lines × 行均长，不需要全量加载。
    """
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


def _do_git_pull(project_dir, target_branch=None):
    """执行 git pull，可选切换分支。
    返回 dict:
      steps      - list of {cmd, output, ok, summary}  每一步操作
      success    - bool 整体是否成功
      current_branch - 最终所在分支
      summary    - 最终中文总结文本
    """
    steps = []

    def run_step(args, summary_ok='', summary_fail='', **kw):
        cmd_str = 'git ' + ' '.join(args[args.index('-C') + 2:]) if '-C' in args else 'git ' + ' '.join(args[1:])
        r = subprocess.run(args, capture_output=True, text=True, **kw)
        out = (r.stdout + r.stderr).strip()
        ok = r.returncode == 0
        steps.append({'cmd': '$ ' + cmd_str, 'output': out, 'ok': ok,
                      'summary': summary_ok if ok else summary_fail})
        return r, ok, out

    # 获取当前分支（内部查询，不加入 steps）
    cr = subprocess.run(['git', '-C', project_dir, 'rev-parse', '--abbrev-ref', 'HEAD'],
                        capture_output=True, text=True, timeout=10)
    current_branch = cr.stdout.strip() if cr.returncode == 0 else ''

    # 获取 remote 名称（内部查询）
    rr = subprocess.run(['git', '-C', project_dir, 'remote'],
                        capture_output=True, text=True, timeout=10)
    remotes = [r.strip() for r in rr.stdout.strip().split('\n') if r.strip()]
    remote = remotes[0] if remotes else 'origin'

    # 切换分支
    switched = False
    if target_branch and target_branch != current_branch:
        local_branch = target_branch
        if '/' in target_branch:
            local_branch = target_branch.split('/', 1)[-1]

        r, ok, out = run_step(
            ['git', '-C', project_dir, 'checkout', local_branch],
            summary_ok=f'✓ 已切换到分支 "{local_branch}"',
            summary_fail='',
            timeout=30,
        )
        if not ok:
            # 本地不存在，从远程创建
            steps.pop()
            r, ok, out = run_step(
                ['git', '-C', project_dir, 'checkout', '-b', local_branch, target_branch],
                summary_ok=f'✓ 已从 "{target_branch}" 创建并切换到本地分支 "{local_branch}"',
                summary_fail=f'✗ 切换分支失败：无法检出 "{local_branch}"',
                timeout=30,
            )
            if not ok:
                return {'steps': steps, 'success': False, 'current_branch': current_branch,
                        'summary': f'✗ 切换分支失败，已终止。\n{out}'}
        current_branch = local_branch
        switched = True

    # 检查 upstream tracking
    tr = subprocess.run(
        ['git', '-C', project_dir, 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}'],
        capture_output=True, text=True, timeout=10
    )

    if tr.returncode == 0:
        pull_args = ['git', '-C', project_dir, 'pull']
    else:
        if not current_branch:
            return {'steps': steps, 'success': False, 'current_branch': current_branch,
                    'summary': '✗ 无法检测当前 Git 分支，pull 终止。'}
        ls_r = subprocess.run(
            ['git', '-C', project_dir, 'ls-remote', '--heads', remote, current_branch],
            capture_output=True, text=True, timeout=15
        )
        if ls_r.stdout.strip():
            pull_args = ['git', '-C', project_dir, 'pull', remote, current_branch]
        else:
            found_default = None
            for db in ['main', 'master']:
                ls_d = subprocess.run(
                    ['git', '-C', project_dir, 'ls-remote', '--heads', remote, db],
                    capture_output=True, text=True, timeout=15
                )
                if ls_d.stdout.strip():
                    found_default = db
                    break
            if found_default:
                pull_args = ['git', '-C', project_dir, 'pull', remote, found_default]
            else:
                return {'steps': steps, 'success': False, 'current_branch': current_branch,
                        'summary': (f'✗ 分支 "{current_branch}" 在远程 "{remote}" 上不存在，'
                                    f'且未找到 main/master，pull 终止。\n'
                                    f'请手动执行: git branch --set-upstream-to={remote}/<分支名> {current_branch}')}

    r, ok, out = run_step(
        pull_args,
        summary_ok='',  # 下面根据 output 内容精细判断
        summary_fail='',
        timeout=60,
    )

    # 精细判断 pull 结果
    pull_out_lower = out.lower()
    if ok:
        if 'already up to date' in pull_out_lower or 'already up-to-date' in pull_out_lower:
            pull_summary = f'✓ 分支 "{current_branch}" 已是最新，无需更新。'
        elif 'conflict' in pull_out_lower or 'merge conflict' in pull_out_lower:
            pull_summary = '⚠ 拉取时发生合并冲突，请手动解决后再操作。'
            ok = False
        else:
            pull_summary = f'✓ 成功拉取分支 "{current_branch}" 的最新代码。'
        if ok and tr.returncode != 0 and current_branch:
            subprocess.run(
                ['git', '-C', project_dir, 'branch', '--set-upstream-to',
                 f'{remote}/{current_branch}', current_branch],
                capture_output=True, text=True, timeout=10
            )
    else:
        if 'conflict' in pull_out_lower:
            pull_summary = '✗ 拉取失败：存在合并冲突，请手动处理。'
        elif 'rejected' in pull_out_lower:
            pull_summary = '✗ 拉取被拒绝（可能本地有超前提交），建议先检查本地状态。'
        elif 'could not read' in pull_out_lower or 'authentication' in pull_out_lower:
            pull_summary = '✗ 拉取失败：认证或网络问题。'
        else:
            pull_summary = '✗ 拉取失败。'

    steps[-1]['ok'] = ok
    steps[-1]['summary'] = pull_summary

    # 整体总结
    parts = []
    if switched:
        switch_step = next((s for s in steps if 'checkout' in s['cmd']), None)
        if switch_step:
            parts.append(switch_step['summary'])
    parts.append(pull_summary)
    final_summary = '\n'.join(parts)

    return {'steps': steps, 'success': ok, 'current_branch': current_branch,
            'summary': final_summary}


# ======================== 路由 ========================

@deploy_bp.route('/deploy/list', methods=['GET'])
@login_required
def deploy_list():
    names = _redis.smembers(_names_key())
    result = []
    for name in sorted(names):
        config = _redis.hgetall(_config_key(name))
        status = _get_deploy_status(name)  # 从 Redis 读 PID，单进程验证，无全量扫描
        result.append({
            'name': name,
            'description': config.get('description', ''),
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
    description = data.get('description', '').strip()
    env_vars = data.get('env_vars', '{}')

    if isinstance(env_vars, dict):
        env_vars = json.dumps(env_vars, ensure_ascii=False)

    auto_start = '1' if data.get('auto_start') else '0'
    auto_restart = '1' if data.get('auto_restart') else '0'
    max_retry = str(int(data.get('max_retry', 3) or 3))
    health_check_secs = str(int(data.get('health_check_secs', 10) or 10))
    num_processes = str(max(1, int(data.get('num_processes', 1) or 1)))

    _redis.sadd(_names_key(), name)
    _redis.hset(_config_key(name), mapping={
        'name': name,
        'description': description,
        'project_dir': project_dir,
        'start_cmd': start_cmd,
        'env_vars': env_vars,
        'auto_start': auto_start,
        'auto_restart': auto_restart,
        'max_retry': max_retry,
        'health_check_secs': health_check_secs,
        'num_processes': num_processes,
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

    new_config = dict(config)
    new_config['name'] = new_name
    _redis.sadd(_names_key(), new_name)
    _redis.hset(_config_key(new_name), mapping=new_config)
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

    procs, err, cmd_detail = _start_process(name, config)
    if err:
        return jsonify({'succ': False, 'msg': f'启动失败: {err}', 'cmd_detail': cmd_detail})
    _redis.hset(_runtime_key(name), mapping={'manual_stop': '0', 'should_run': '1', 'restart_retry_count': '0'})
    pids = cmd_detail.get('pid', '')
    return jsonify({
        'succ': True,
        'msg': f'启动成功, PID={pids}',
        'pid': pids,
        'cmd_detail': cmd_detail,
    })


@deploy_bp.route('/deploy/<name>/stop', methods=['POST'])
@login_required
def deploy_stop(name):
    alive_pids, search_cmd = _find_deploy_pids(name)
    if not alive_pids:
        return jsonify({'succ': False, 'msg': '进程未在运行'})

    runtime_data = _redis.hgetall(_runtime_key(name))
    old_start_time = runtime_data.get('start_time', '')

    kill_results = _kill_pids(alive_pids)
    all_ok = all(r[1] for r in kill_results)
    last_err = next((r[2] for r in kill_results if not r[1]), '')

    if all_ok:
        _redis.hset(_runtime_key(name), mapping={
            'manual_stop': '1', 'should_run': '0', 'pid_list': '[]', 'ct_list': '[]',
        })
    return jsonify({
        'succ': all_ok,
        'msg': '停止成功' if all_ok else (last_err or '停止进程时出错'),
        'cmd_detail': {
            'search_cmd': search_cmd,
            'found_pids': [str(p) for p in alive_pids],
            'kill_cmds': [r[3] for r in kill_results],
            'stop_cmd': '; '.join(r[3] for r in kill_results),
            'pid': ', '.join(str(p) for p in alive_pids),
            'old_start_time': old_start_time,
        },
    })


@deploy_bp.route('/deploy/<name>/restart', methods=['POST'])
@login_required
def deploy_restart(name):
    alive_pids, search_cmd = _find_deploy_pids(name)
    runtime_data = _redis.hgetall(_runtime_key(name))
    old_pid = ', '.join(str(p) for p in alive_pids) if alive_pids else ''
    old_start_time = runtime_data.get('start_time', '')
    stop_cmds = []
    kill_details = []

    if alive_pids:
        kill_results = _kill_pids(alive_pids)
        for pid, ok, err_msg, kill_cmd in kill_results:
            stop_cmds.append(kill_cmd)
            if not ok and err_msg:
                return jsonify({'succ': False, 'msg': f'停止旧进程失败: {err_msg}',
                                'cmd_detail': {'search_cmd': search_cmd,
                                               'found_pids': [str(p) for p in alive_pids],
                                               'stop_cmd': '; '.join(stop_cmds),
                                               'old_pid': old_pid,
                                               'old_start_time': old_start_time}})
        kill_details = [{'pid': r[0], 'ok': r[1], 'cmd': r[3]} for r in kill_results]
        _redis.hset(_runtime_key(name), mapping={'pid_list': '[]', 'ct_list': '[]'})
        time.sleep(1)

    config = _redis.hgetall(_config_key(name))
    if not config:
        return jsonify({'succ': False, 'msg': '部署配置不存在'})

    procs, err, cmd_detail = _start_process(name, config)
    cmd_detail['search_cmd'] = search_cmd
    cmd_detail['found_pids'] = [str(p) for p in alive_pids]
    cmd_detail['kill_details'] = kill_details
    cmd_detail['stop_cmd'] = '; '.join(stop_cmds)
    cmd_detail['old_pid'] = old_pid
    cmd_detail['old_start_time'] = old_start_time
    if err:
        return jsonify({'succ': False, 'msg': f'重启失败: {err}', 'cmd_detail': cmd_detail})
    _redis.hset(_runtime_key(name), mapping={'manual_stop': '0', 'should_run': '1', 'restart_retry_count': '0'})
    pids = cmd_detail.get('pid', '')
    return jsonify({
        'succ': True,
        'msg': f'重启成功, PID={pids}',
        'pid': pids,
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
        return jsonify({'succ': False, 'is_git_repo': False, 'msg': f'项目目录不存在: {project_dir}'})

    try:
        check = subprocess.run(
            ['git', '-C', project_dir, 'rev-parse', '--is-inside-work-tree'],
            capture_output=True, text=True, timeout=5
        )
        if check.returncode != 0:
            return jsonify({'succ': True, 'is_git_repo': False,
                            'current': '', 'local': [], 'remote': []})

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
            'is_git_repo': True,
            'current': current_branch,
            'local': local_branches,
            'remote': remote_branches,
        })
    except subprocess.TimeoutExpired:
        return jsonify({'succ': False, 'is_git_repo': False, 'msg': 'Git 操作超时'})
    except Exception as e:
        return jsonify({'succ': False, 'is_git_repo': False, 'msg': str(e)})


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
        res = _do_git_pull(project_dir, target_branch or None)
        return jsonify({
            'succ': res['success'],
            'msg': res['summary'],
            'steps': res['steps'],
            'current_branch': res['current_branch'],
        })
    except subprocess.TimeoutExpired:
        return jsonify({'succ': False, 'msg': '✗ Git pull 超时（60秒）', 'steps': [], 'current_branch': ''})
    except Exception as e:
        return jsonify({'succ': False, 'msg': f'✗ Git pull 异常: {e}', 'steps': [], 'current_branch': ''})


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

    dt_start = _parse_dt(time_start)
    dt_end = _parse_dt(time_end)

    all_lines = []
    for fpath in log_files:
        try:
            file_size = os.path.getsize(fpath)
        except OSError:
            continue
        if file_size == 0:
            continue

        start_off = 0
        end_off = file_size

        if dt_start:
            start_off = _bisect_log_offset(fpath, dt_start)
        if dt_end:
            end_off = _bisect_log_offset(fpath, dt_end + datetime.timedelta(seconds=1))

        if start_off >= end_off:
            continue

        lines = _read_log_lines_range(fpath, max_lines * 3, start_off, end_off)
        all_lines.extend(lines)

    # 将行按"日志条目"分组：以时间戳开头的行为新条目起点，
    # 后续无时间戳的行属于同一条目（如 traceback、多行 error 消息）。
    # 若整个文件都没有时间戳（如 make/sphinx 等构建工具输出），则将每行视为独立条目，时间为 None。
    entries = []  # [(entry_time_or_None, [line1, line2, ...])]
    has_any_timestamp = False
    last_time = None
    for line in all_lines:
        if not line.strip():
            continue
        clean_line = _strip_ansi(line)
        lt = _parse_log_time(clean_line)
        if lt:
            has_any_timestamp = True
            last_time = lt
            entries.append((lt, [clean_line]))
        else:
            if entries:
                entries[-1][1].append(clean_line)
            elif last_time:
                entries.append((last_time, [clean_line]))
            else:
                # 无时间戳且尚无任何条目，暂存为 None 时间的独立行
                entries.append((None, [clean_line]))

    keyword_lower = keyword.lower() if keyword else ''
    filtered = []
    for entry_time, entry_lines in entries:
        if dt_start or dt_end:
            if entry_time is not None:
                if dt_start and entry_time < dt_start:
                    continue
                if dt_end and entry_time > dt_end:
                    continue
            elif has_any_timestamp:
                # 文件有时间戳，但此条目没有（附属行），跟随上一条过滤，已在分组时归入上一条，此处理论不会出现
                continue
            # 如果整个文件都没有时间戳，时间过滤不适用，照常显示

        if keyword_lower:
            entry_text = '\n'.join(entry_lines).lower()
            if keyword_lower not in entry_text:
                continue

        filtered.extend(entry_lines)

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


# ======================== 自动启动 & 自动重启守护 ========================

def _auto_restart_daemon():
    """后台守护线程：每 10 秒检查所有配置了 auto_restart 的部署，
    如果进程意外退出（且非人工停止），自动重启，最多连续失败 max_retry 次。
    启动时还负责处理 auto_start 逻辑。
    """
    time.sleep(15)

    try:
        _do_auto_start()
    except Exception:
        pass

    while True:
        try:
            _do_auto_restart_check()
        except Exception:
            pass
        time.sleep(10)


def _do_auto_start():
    """服务启动时执行一次：启动所有配置了 auto_start=1 的部署（如果尚未运行）"""
    try:
        names = _redis.smembers(_names_key())
    except Exception:
        return
    for name in names:
        try:
            config = _redis.hgetall(_config_key(name))
            if not config or config.get('auto_start', '0') != '1':
                continue
            status = _get_deploy_status(name)
            if status['running']:
                continue
            procs, err, _ = _start_process(name, config)
            if not err:
                _redis.hset(_runtime_key(name), mapping={
                    'manual_stop': '0', 'should_run': '1', 'restart_retry_count': '0',
                })
        except Exception:
            pass


def _do_auto_restart_check():
    """守护线程每次循环调用：检查需要自动重启的部署（支持多进程）"""
    try:
        names = _redis.smembers(_names_key())
    except Exception:
        return
    for name in names:
        try:
            config = _redis.hgetall(_config_key(name))
            if not config or config.get('auto_restart', '0') != '1':
                continue

            runtime = _redis.hgetall(_runtime_key(name))
            if runtime.get('manual_stop', '') == '1':
                continue
            if runtime.get('should_run', '') != '1':
                continue

            # 从 Redis 读取 PID 列表，逐一验证，不全量扫描
            alive_pids, _ = _find_deploy_pids(name)
            expected = max(1, int(config.get('num_processes', '1') or 1))

            if len(alive_pids) >= expected:
                _redis.hset(_runtime_key(name), 'restart_retry_count', '0')
                continue

            retry_count = int(runtime.get('restart_retry_count', '0'))
            max_retry = int(config.get('max_retry', '3'))
            if retry_count >= max_retry:
                continue

            _redis.hset(_runtime_key(name), 'restart_retry_count', str(retry_count + 1))

            if alive_pids:
                _kill_pids(alive_pids)
                time.sleep(1)

            procs, err, _ = _start_process(name, config)
            if not err:
                _redis.hset(_runtime_key(name), 'restart_retry_count', '0')
        except Exception:
            pass


_daemon_thread = threading.Thread(target=_auto_restart_daemon, daemon=True)
_daemon_thread.start()

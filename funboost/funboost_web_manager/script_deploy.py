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
    """获取部署状态，支持多进程。返回 running/pids/start_times 等。"""
    runtime_data = _redis.hgetall(_runtime_key(name))

    # 兼容旧版单进程数据：读取 pid_list 或回退到 pid
    try:
        pid_list = json.loads(runtime_data.get('pid_list', '[]'))
    except (json.JSONDecodeError, TypeError):
        pid_list = []
    if not pid_list and runtime_data.get('pid', ''):
        pid_list = [runtime_data['pid']]

    try:
        flag_list = json.loads(runtime_data.get('flag_list', '[]'))
    except (json.JSONDecodeError, TypeError):
        flag_list = []
    if not flag_list and runtime_data.get('deploy_flag', ''):
        flag_list = [runtime_data['deploy_flag']]

    try:
        ct_list = json.loads(runtime_data.get('ct_list', '[]'))
    except (json.JSONDecodeError, TypeError):
        ct_list = []
    if not ct_list and runtime_data.get('create_time', ''):
        ct_list = [runtime_data['create_time']]

    try:
        st_list = json.loads(runtime_data.get('st_list', '[]'))
    except (json.JSONDecodeError, TypeError):
        st_list = []
    if not st_list and runtime_data.get('start_time', ''):
        st_list = [runtime_data['start_time']]

    alive_pids = []
    alive_flags = []
    alive_cts = []
    alive_sts = []
    for i, pid in enumerate(pid_list):
        if not pid:
            continue
        flag = flag_list[i] if i < len(flag_list) else ''
        ct = ct_list[i] if i < len(ct_list) else ''
        st = st_list[i] if i < len(st_list) else ''
        if _check_process_alive(pid, flag, ct):
            alive_pids.append(pid)
            alive_flags.append(flag)
            alive_cts.append(ct)
            alive_sts.append(st)

    any_alive = len(alive_pids) > 0
    if len(alive_pids) != len(pid_list):
        _redis.hset(_runtime_key(name), mapping={
            'pid_list': json.dumps(alive_pids),
            'flag_list': json.dumps(alive_flags),
            'ct_list': json.dumps(alive_cts),
            'st_list': json.dumps(alive_sts),
            'pid': '', 'start_time': '', 'deploy_flag': '', 'create_time': '',
        })

    return {
        'running': any_alive,
        'pid': ', '.join(alive_pids) if alive_pids else '',
        'start_time': alive_sts[0] if alive_sts else '',
        'deploy_flag': ', '.join(alive_flags) if alive_flags else '',
        'pid_list': alive_pids,
        'flag_list': alive_flags,
        'ct_list': alive_cts,
        'st_list': alive_sts,
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
    health_secs = int(config.get('health_check_secs', '10') or 10)
    log_file = _get_nohup_log_path(name)

    cmd_detail = {
        'cwd': project_dir or '(当前目录)',
        'env_vars': _format_env_summary(config),
        'log_file': log_file,
        'num_processes': num_processes,
    }

    all_pids = []
    all_flags = []
    all_cts = []
    all_sts = []
    procs = []
    errors = []

    for idx in range(num_processes):
        deploy_flag = str(uuid.uuid4())
        cmd_with_flag = f'{start_cmd} --deploy_flag={deploy_flag}'
        proc_log = log_file if num_processes == 1 else _get_nohup_log_path(f'{name}.{idx}')

        if os.name == 'nt':
            display_cmd = f'{cmd_with_flag}  (stdout/stderr >> "{proc_log}")'
        else:
            display_cmd = f'nohup {cmd_with_flag} >> "{proc_log}" 2>&1 &'

        if idx == 0:
            cmd_detail['full_cmd'] = display_cmd

        try:
            log_fh = open(proc_log, 'a', encoding='utf-8')
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
            ct = _get_process_create_time(proc.pid)
            now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            all_pids.append(str(proc.pid))
            all_flags.append(deploy_flag)
            all_cts.append(str(ct) if ct else '')
            all_sts.append(now_str)
            procs.append(proc)
        except Exception as e:
            errors.append(f'进程 #{idx}: {e}')

    if not procs:
        return None, '所有进程启动失败: ' + '; '.join(errors), cmd_detail

    # 保存多进程运行时信息
    _redis.hset(_runtime_key(name), mapping={
        'pid_list': json.dumps(all_pids),
        'flag_list': json.dumps(all_flags),
        'ct_list': json.dumps(all_cts),
        'st_list': json.dumps(all_sts),
        'pid': '', 'start_time': '', 'deploy_flag': '', 'create_time': '',
    })

    cmd_detail['start_time'] = all_sts[0]
    cmd_detail['pid'] = ', '.join(all_pids)

    # 健康检查：等待所有进程存活
    failed_any = False
    for i, proc in enumerate(procs):
        survived, exit_code = _wait_process_alive(
            proc, all_flags[i], all_cts[i], max_wait=health_secs
        )
        if survived < 0:
            failed_any = True
            log_f = log_file if num_processes == 1 else _get_nohup_log_path(f'{name}.{i}')
            log_tail = _read_log_tail_str(log_f, 20)
            err = f'进程 #{i} (PID {all_pids[i]}) 启动后 {abs(survived)} 秒内退出'
            if exit_code is not None:
                err += f'（退出码: {exit_code}）'
            if log_tail:
                err += f'\n--- 日志尾部 ---\n{log_tail}'
            errors.append(err)

    cmd_detail['survived_secs'] = health_secs if not failed_any else -1

    if failed_any:
        # 刷新状态，去掉已死进程
        _get_deploy_status(name)
        return procs, '\n'.join(errors), cmd_detail

    return procs, None, cmd_detail


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

    auto_start = '1' if data.get('auto_start') else '0'
    auto_restart = '1' if data.get('auto_restart') else '0'
    max_retry = str(int(data.get('max_retry', 3) or 3))
    health_check_secs = str(int(data.get('health_check_secs', 10) or 10))
    num_processes = str(max(1, int(data.get('num_processes', 1) or 1)))

    _redis.sadd(_names_key(), name)
    _redis.hset(_config_key(name), mapping={
        'name': name,
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
    status = _get_deploy_status(name)
    if not status['running']:
        return jsonify({'succ': False, 'msg': '进程未在运行'})

    pid_list = status.get('pid_list', [])
    ct_list = status.get('ct_list', [])
    old_start_time = status.get('start_time', '')

    stop_cmds = []
    all_ok = True
    last_err = ''
    for i, pid in enumerate(pid_list):
        ct = ct_list[i] if i < len(ct_list) else ''
        if os.name == 'nt':
            stop_cmds.append(f'taskkill /F /T /PID {pid}')
        else:
            stop_cmds.append(f'kill -SIGTERM {pid}')
        ok, err_msg = _kill_process(pid, ct)
        if not ok:
            all_ok = False
            last_err = err_msg

    if all_ok:
        _redis.hset(_runtime_key(name), mapping={
            'pid_list': '[]', 'flag_list': '[]', 'ct_list': '[]', 'st_list': '[]',
            'pid': '', 'start_time': '', 'deploy_flag': '', 'create_time': '',
            'manual_stop': '1', 'should_run': '0',
        })
    return jsonify({
        'succ': all_ok,
        'msg': '停止成功' if all_ok else (last_err or '停止进程时出错'),
        'cmd_detail': {
            'stop_cmd': '; '.join(stop_cmds),
            'pid': ', '.join(pid_list),
            'old_start_time': old_start_time,
        },
    })


@deploy_bp.route('/deploy/<name>/restart', methods=['POST'])
@login_required
def deploy_restart(name):
    status = _get_deploy_status(name)
    old_pid = status.get('pid', '')
    old_start_time = status.get('start_time', '')
    stop_cmds = []
    if status['running']:
        pid_list = status.get('pid_list', [])
        ct_list = status.get('ct_list', [])
        for i, pid in enumerate(pid_list):
            ct = ct_list[i] if i < len(ct_list) else ''
            if os.name == 'nt':
                stop_cmds.append(f'taskkill /F /T /PID {pid}')
            else:
                stop_cmds.append(f'kill -SIGTERM {pid}')
            ok, err_msg = _kill_process(pid, ct)
            if not ok and err_msg:
                return jsonify({'succ': False, 'msg': f'停止旧进程失败: {err_msg}',
                                'cmd_detail': {'stop_cmd': '; '.join(stop_cmds), 'old_pid': old_pid,
                                               'old_start_time': old_start_time}})
        _redis.hset(_runtime_key(name), mapping={
            'pid_list': '[]', 'flag_list': '[]', 'ct_list': '[]', 'st_list': '[]',
            'pid': '', 'start_time': '', 'deploy_flag': '', 'create_time': '',
        })
        time.sleep(1)

    config = _redis.hgetall(_config_key(name))
    if not config:
        return jsonify({'succ': False, 'msg': '部署配置不存在'})

    procs, err, cmd_detail = _start_process(name, config)
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

            status = _get_deploy_status(name)
            expected = max(1, int(config.get('num_processes', '1') or 1))
            alive_count = len(status.get('pid_list', []))

            if alive_count >= expected:
                _redis.hset(_runtime_key(name), 'restart_retry_count', '0')
                continue

            retry_count = int(runtime.get('restart_retry_count', '0'))
            max_retry = int(config.get('max_retry', '3'))
            if retry_count >= max_retry:
                continue

            _redis.hset(_runtime_key(name), 'restart_retry_count', str(retry_count + 1))

            # 先停掉残余进程，再全部重启
            for i, pid in enumerate(status.get('pid_list', [])):
                ct = status['ct_list'][i] if i < len(status.get('ct_list', [])) else ''
                _kill_process(pid, ct)

            _redis.hset(_runtime_key(name), mapping={
                'pid_list': '[]', 'flag_list': '[]', 'ct_list': '[]', 'st_list': '[]',
            })
            time.sleep(1)

            procs, err, _ = _start_process(name, config)
            if not err:
                _redis.hset(_runtime_key(name), 'restart_retry_count', '0')
        except Exception:
            pass


_daemon_thread = threading.Thread(target=_auto_restart_daemon, daemon=True)
_daemon_thread.start()

# -*- coding: utf-8 -*-
import datetime
import json
import os
import re
import signal

import subprocess
import time
import threading

import psutil
from redis5.exceptions import ResponseError

from flask import Blueprint, request, jsonify
from flask_login import login_required

from funboost.utils.redis_manager import RedisMixin
from funboost.funweb.flask_bps.web_helper import LOCAL_IP

deploy_bp = Blueprint('deploy', __name__)

_redis = RedisMixin().redis_db_frame

_ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*m')


def _strip_ansi(text):
    return _ANSI_ESCAPE_RE.sub('', text)




def _key_prefix():
    return f'script_deploy:{LOCAL_IP}'


def _config_key(name):
    return f'{_key_prefix()}:{name}:config'


def _runtime_key(name):
    return f'{_key_prefix()}:{name}:runtime'


def _names_key():
    return f'{_key_prefix()}:deploy_names'


def _coerce_redis_hash_mapping(mapping):
    """保证 HSET 的 field/value 均为 Redis 可编码字符串，避免 None 等触发客户端或服务端错误。"""
    out = {}
    for k, v in mapping.items():
        if v is None:
            out[k] = ''
        elif isinstance(v, bytes):
            out[k] = v.decode('utf-8', errors='replace')
        elif isinstance(v, str):
            out[k] = v
        else:
            out[k] = str(v)
    return out


def _redis_hset_mapping(key, mapping):
    """写入 hash。逐字段 HSET，兼容 Redis 3（不支持 HSET 多 field 形态）；
    若 key 类型错误（WRONGTYPE），删除后重写。"""
    m = _coerce_redis_hash_mapping(mapping)
    if not m:
        return

    def _pipe_hset_all():
        pipe = _redis.pipeline()
        for f, v in m.items():
            pipe.hset(key, f, v)
        pipe.execute()

    try:
        _pipe_hset_all()
    except ResponseError as e:
        err = str(e).upper()
        if 'WRONGTYPE' in err:
            _redis.delete(key)
            _pipe_hset_all()
        else:
            raise


def _redis_hset_field(key, field, value):
    if value is None:
        value = ''
    elif not isinstance(value, (bytes, str)):
        value = str(value)
    elif isinstance(value, bytes):
        value = value.decode('utf-8', errors='replace')
    try:
        _redis.hset(key, field, value)
    except ResponseError as e:
        if 'WRONGTYPE' in str(e).upper():
            _redis.delete(key)
            _redis.hset(key, field, value)
        else:
            raise


def _get_log_path():
    # 不可能不存在，不用考虑兼容的情况。
    from nb_log import nb_log_config_default
    return str(nb_log_config_default.LOG_PATH)
    # try:
    #     from nb_log import nb_log_config_default
    #     return str(nb_log_config_default.LOG_PATH)
    # except Exception:
    #     if os.name == 'nt':
    #         return os.path.join(os.path.splitdrive(os.getcwd())[0] + os.sep, 'pythonlogs')
    #     return os.path.join(os.path.expanduser('~'), 'pythonlogs')


def _get_nohup_log_path(name):
    log_dir = _get_log_path()
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, f'{name}.nohup.log')


# 这些进程会继承 FUNWEB_DEPLOY，但不是业务 Python 进程，不参与合并展示/计数
_DEPLOY_SHELL_PROCESS_NAMES = frozenset({
    'cmd.exe', 'powershell.exe', 'pwsh.exe', 'conhost.exe', 'comhost.exe',
})


def _script_fingerprint_for_config(config):
    """从 start_cmd 解析脚本路径指纹，供 cmdline 匹配与壳子进程过滤。"""
    start_cmd = (config.get('start_cmd') or '').strip() if config else ''
    if not start_cmd:
        return None, None
    sc_norm = start_cmd.replace('/', '\\')
    fingerprint = None
    for tok in sc_norm.split():
        t = tok.strip('"').strip("'")
        if '.py' in t.lower():
            fingerprint = t.lower().replace('/', '\\')
            break
    if not fingerprint:
        parts = sc_norm.split()
        if parts:
            fingerprint = parts[-1].strip('"').strip("'").lower().replace('/', '\\')
    if not fingerprint or len(fingerprint) < 2:
        return None, None
    return fingerprint, os.path.basename(fingerprint)


def _pid_is_ancestor_of(ancestor_pid, desc_pid):
    try:
        ap, dp = int(ancestor_pid), int(desc_pid)
        if ap == dp:
            return False
        for parent in psutil.Process(dp).parents():
            if parent.pid == ap:
                return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError, OSError):
        pass
    return False


def _drop_ancestor_pids(pids):
    """在同一批 PID 内去掉「另一 PID 的祖先」：例如 py.exe → python.exe 只保留后者。"""
    unique = []
    seen = set()
    for p in pids:
        p = int(p)
        if p not in seen:
            seen.add(p)
            unique.append(p)
    drop = set()
    for a in unique:
        for b in unique:
            if a == b:
                continue
            if _pid_is_ancestor_of(a, b):
                drop.add(a)
                break
    return [p for p in unique if p not in drop]



def _filter_shell_children_to_script_leaves(child_info, config):
    """壳进程下可能同时出现 py.exe、python.exe 等多层子进程，只保留真正跑脚本的叶子 Python。"""
    if not child_info or not config:
        return child_info
    fp, base_py = _script_fingerprint_for_config(config)
    project_dir = (config.get('project_dir') or '').strip()
    want_cwd = None
    if project_dir:
        try:
            want_cwd = os.path.normcase(os.path.realpath(project_dir))
        except OSError:
            want_cwd = None

    matched = []
    for pid, ct in child_info:
        try:
            p = psutil.Process(int(pid))
            if 'python' not in (p.name() or '').lower():
                continue
            cmdl = p.cmdline()
        except (psutil.Error, ValueError):
            continue
        if not cmdl:
            continue
        if fp:
            cmd_join = ' '.join(cmdl).lower().replace('/', '\\')
            if fp not in cmd_join and base_py.lower() not in cmd_join:
                continue
        if want_cwd:
            try:
                cw = os.path.normcase(os.path.realpath(p.cwd()))
                if cw != want_cwd:
                    continue
            except psutil.Error:
                continue
        matched.append((int(pid), ct))

    if not matched:
        matched = []
        for pid, ct in child_info:
            try:
                p = psutil.Process(int(pid))
                if 'python' not in (p.name() or '').lower():
                    continue
                matched.append((int(pid), ct))
            except (psutil.Error, ValueError):
                pass
        if not matched:
            return child_info

    leaf_ids = set(_drop_ancestor_pids([m[0] for m in matched]))
    return [(pid, ct) for pid, ct in matched if pid in leaf_ids]


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
    """找到壳进程（cmd.exe/sh）启动的 Python 解释器进程，返回 [(pid, create_time), ...]。
    策略：
      1. 先取壳进程的直接子进程（不递归），过滤出 python 解释器。
      2. 若直接子进程是 py.exe（Windows 启动器），则再向下取其直接子。
      3. 只保留第一层真正的 python 解释器，不继续递归，避免把用户脚本
         spawn 出的孙进程（如多进程 worker）也一并纳入管理。
    """
    _py_launcher = {'py.exe', 'py3.exe'}

    def _get_direct_python_children(pid):
        try:
            p = psutil.Process(pid)
            children = p.children(recursive=False)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []
        result = []
        for c in children:
            try:
                name = (c.name() or '').lower()
                ct = c.create_time()
                if name in _py_launcher:
                    # py.exe 启动器：再向下一层取真正的 python
                    result.extend(_get_direct_python_children(c.pid))
                elif 'python' in name:
                    result.append((c.pid, ct))
                # 其他（conhost 等）忽略
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return result

    found = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        found = _get_direct_python_children(parent_pid)
        if found:
            break
        try:
            psutil.Process(parent_pid)
        except psutil.NoSuchProcess:
            break
        time.sleep(0.3)
    return found


def _find_deploy_pids(name):
    """从 Redis 读取 PID + create_time 列表，逐一验证存活。
    仅调用 is_running() 和 create_time()，不读环境变量/命令行，毫秒级。
    返回 (alive_pid_list, search_cmd_display, alive_ct_list)
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
    alive_cts = []
    for i, pid_str in enumerate(pid_list):
        if not pid_str:
            continue
        ct = ct_list[i] if i < len(ct_list) else None
        if _check_pid_alive(int(pid_str), ct):
            alive.append(int(pid_str))
            alive_cts.append(ct)
    return alive, display, alive_cts


def _verify_pid_belongs_to_deploy(pid, name, stored_ct=None):
    """杀进程前的安全校验：确认 PID 确实属于该部署，防止系统重启后 PID 复用导致误杀。
    校验优先级：
      1. create_time 必须与启动时记录的一致（排除绝大多数 PID 复用）
      2. 环境变量 FUNWEB_DEPLOY == name（最终确认是自己的进程）
    仅在 stop/restart/kill 路径调用，不在轮询路径使用。
    """
    try:
        p = psutil.Process(int(pid))
        if not p.is_running():
            return False, '进程已不存在'
        # 第一层：create_time 校验
        if stored_ct:
            try:
                ct = p.create_time()
                if abs(ct - float(stored_ct)) > 3.0:
                    return False, f'PID 已被复用（create_time 不匹配: 记录={stored_ct}, 实际={ct:.2f}）'
            except (psutil.AccessDenied, ValueError):
                pass
        # 第二层：FUNWEB_DEPLOY 环境变量校验
        try:
            env = p.environ()
            deploy_val = env.get('FUNWEB_DEPLOY', '')
            if deploy_val == name:
                return True, ''
            if deploy_val:
                return False, f'PID 属于其他部署（FUNWEB_DEPLOY={deploy_val}，期望={name}）'
            # 环境变量为空但 create_time 匹配 → 可能是权限问题，允许杀
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            # 无法读取环境变量（权限不足等），回退到仅信任 create_time
            pass
        return True, ''
    except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError, OSError):
        return False, '进程已不存在'


def _kill_pids(pids, name=None, ct_list=None):
    """杀死一组 PID。如果提供 name 和 ct_list，会在杀之前做安全校验防止误杀。
    返回 [(pid, ok, err_msg, kill_cmd), ...]"""
    results = []
    for i, pid in enumerate(pids):
        pid = int(pid)
        if os.name == 'nt':
            kill_cmd = f'taskkill /F /T /PID {pid}'
        else:
            kill_cmd = f'kill -SIGTERM {pid} && sleep 1 && kill -SIGKILL {pid}'

        # 安全校验：确认 PID 属于该部署
        if name:
            ct = ct_list[i] if ct_list and i < len(ct_list) else None
            belongs, reason = _verify_pid_belongs_to_deploy(pid, name, ct)
            if not belongs:
                results.append((pid, True, f'跳过（{reason}）', f'# 跳过 PID {pid}: {reason}'))
                continue

        try:
            if os.name == 'nt':
                r = subprocess.run(
                    ['taskkill', '/F', '/T', '/PID', str(pid)],
                    capture_output=True, timeout=15,
                )
                ok = r.returncode == 0
                err_msg = ''
                if not ok:
                    err_msg = (r.stderr or r.stdout or b'').decode('utf-8', errors='replace').strip() or f'exit {r.returncode}'
                results.append((pid, ok, err_msg, kill_cmd))
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

    # 子进程出现可能较慢：等待上限随「存活检查秒数」放宽，但不超过 60 秒
    child_wait_timeout = min(max(health_secs, 5), 60)
    for i, proc in enumerate(shell_procs):
        child_info = _find_child_pids(proc.pid, timeout=child_wait_timeout)
        if child_info:
            child_info = _filter_shell_children_to_script_leaves(child_info, config)
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

    cmd_detail['start_time'] = now_str
    cmd_detail['pid'] = ', '.join(all_real_pids)

    if failed_any:
        cmd_detail['survived_secs'] = -1
        _redis_hset_mapping(_runtime_key(name), {
            'start_time': now_str,
            'pid_list': json.dumps(all_real_pids),
            'ct_list': json.dumps(all_real_cts),
        })
        return shell_procs, '\n'.join(errors), cmd_detail

    # 存活检查：在 health_secs 秒内每秒确认全部 PID 仍存活（此前仅立即检查，未真正等待）
    pid_ints = [int(p) for p in all_real_pids]
    if not pid_ints:
        cmd_detail['survived_secs'] = -1
        _redis_hset_mapping(_runtime_key(name), {
            'start_time': now_str,
            'pid_list': '[]',
            'ct_list': '[]',
        })
        return shell_procs, '未能记录到任何进程 PID，无法进行存活检查', cmd_detail
    ct_parsed = []
    for s in all_real_cts:
        try:
            ct_parsed.append(float(s))
        except (TypeError, ValueError):
            ct_parsed.append(None)

    for elapsed in range(health_secs):
        time.sleep(1)
        alive = _check_pids_still_alive(pid_ints, ct_parsed)
        if len(alive) < len(pid_ints):
            failed_any = True
            log_tail = _read_log_tail_str(log_file, 30)
            err = (
                f'存活检查失败：启动后约 {elapsed + 1} 秒内进程退出 '
                f'（期望 {len(pid_ints)} 个，剩余 {len(alive)} 个）'
            )
            if log_tail:
                err += f'\n--- 日志尾部 ---\n{log_tail}'
            errors.append(err)
            cmd_detail['survived_secs'] = -1
            cmd_detail['pid'] = ', '.join(str(p) for p in alive) if alive else ''
            _redis_hset_mapping(_runtime_key(name), {
                'start_time': now_str,
                'pid_list': '[]',
                'ct_list': '[]',
            })
            return shell_procs, '\n'.join(errors), cmd_detail

    cmd_detail['survived_secs'] = health_secs
    _redis_hset_mapping(_runtime_key(name), {
        'start_time': now_str,
        'pid_list': json.dumps(all_real_pids),
        'ct_list': json.dumps(all_real_cts),
    })
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
    fpath = _get_nohup_log_path(name)
    if os.path.isfile(fpath):
        return [fpath]
    return []


def _git(project_dir, args, timeout=30):
    """在 project_dir 下执行 git 命令，兼容不支持 -C 的旧版 git（< 1.8.5）。"""
    return subprocess.run(
        ['git'] + args,
        capture_output=True, text=True,
        cwd=project_dir, timeout=timeout,
    )


def _do_git_pull(project_dir, target_branch=None):
    """执行 git pull，可选切换分支。
    返回 dict:
      steps      - list of {cmd, output, ok, summary}  每一步操作
      success    - bool 整体是否成功
      current_branch - 最终所在分支
      summary    - 最终中文总结文本
    """
    steps = []

    def run_step(git_args, summary_ok='', summary_fail='', timeout=30):
        cmd_str = 'git ' + ' '.join(git_args)
        r = _git(project_dir, git_args, timeout=timeout)
        out = (r.stdout + r.stderr).strip()
        ok = r.returncode == 0
        steps.append({'cmd': '$ ' + cmd_str, 'output': out, 'ok': ok,
                      'summary': summary_ok if ok else summary_fail})
        return r, ok, out

    # 获取当前分支（内部查询，不加入 steps）
    cr = _git(project_dir, ['rev-parse', '--abbrev-ref', 'HEAD'], timeout=10)
    current_branch = cr.stdout.strip() if cr.returncode == 0 else ''
    if not current_branch:
        err_detail = (cr.stdout + cr.stderr).strip()
        return {'steps': steps, 'success': False, 'current_branch': '',
                'summary': f'✗ 无法检测当前 Git 分支，pull 终止。\n详情: {err_detail or "(无输出，请确认 git 已安装且项目目录是 git 仓库)"}'}

    # 获取 remote 名称（内部查询）
    rr = _git(project_dir, ['remote'], timeout=10)
    remotes = [r.strip() for r in rr.stdout.strip().split('\n') if r.strip()]
    remote = remotes[0] if remotes else 'origin'

    # 切换分支
    switched = False
    if target_branch and target_branch != current_branch:
        local_branch = target_branch
        if '/' in target_branch:
            local_branch = target_branch.split('/', 1)[-1]

        r, ok, out = run_step(
            ['checkout', local_branch],
            summary_ok=f'✓ 已切换到分支 "{local_branch}"',
            summary_fail='',
            timeout=30,
        )
        if not ok:
            # 本地不存在，从远程创建
            steps.pop()
            r, ok, out = run_step(
                ['checkout', '-b', local_branch, target_branch],
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
    tr = _git(project_dir, ['rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}'], timeout=10)

    if tr.returncode == 0:
        pull_args = ['pull']
    else:
        ls_r = _git(project_dir, ['ls-remote', '--heads', remote, current_branch], timeout=15)
        if ls_r.stdout.strip():
            pull_args = ['pull', remote, current_branch]
        else:
            found_default = None
            for db in ['main', 'master']:
                ls_d = _git(project_dir, ['ls-remote', '--heads', remote, db], timeout=15)
                if ls_d.stdout.strip():
                    found_default = db
                    break
            if found_default:
                pull_args = ['pull', remote, found_default]
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
            _git(project_dir, ['branch', '--set-upstream-to', f'{remote}/{current_branch}', current_branch],
                 timeout=10)
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
    """列表页：仅用 Redis pid_list + is_running()/create_time() 验证，毫秒级返回。"""
    names = _redis.smembers(_names_key())
    result = []
    for name in sorted(names):
        config = _redis.hgetall(_config_key(name))
        alive_pids, search_cmd, _ = _find_deploy_pids(name)
        runtime_data = _redis.hgetall(_runtime_key(name))
        status = {
            'running': len(alive_pids) > 0,
            'pid': ', '.join(str(p) for p in alive_pids) if alive_pids else '',
            'start_time': runtime_data.get('start_time', ''),
            'pid_list': [str(p) for p in alive_pids],
            'search_cmd': search_cmd,
        }
        try:
            hsec = int(config.get('health_check_secs', '10') or 10)
        except (TypeError, ValueError):
            hsec = 10
        result.append({
            'name': name,
            'description': config.get('description', ''),
            'project_dir': config.get('project_dir', ''),
            'start_cmd': config.get('start_cmd', ''),
            'health_check_secs': max(1, hsec),
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
    raw_env = data.get('env_vars', '{}')
    if raw_env is None:
        env_vars = '{}'
    elif isinstance(raw_env, dict):
        env_vars = json.dumps(raw_env, ensure_ascii=False)
    elif isinstance(raw_env, str):
        env_vars = raw_env.strip() or '{}'
    else:
        try:
            env_vars = json.dumps(raw_env, ensure_ascii=False)
        except (TypeError, ValueError):
            env_vars = '{}'

    auto_start = '1' if data.get('auto_start') else '0'
    auto_restart = '1' if data.get('auto_restart') else '0'
    max_retry = str(int(data.get('max_retry', 3) or 3))
    health_check_secs = str(int(data.get('health_check_secs', 10) or 10))
    num_processes = str(max(1, int(data.get('num_processes', 1) or 1)))

    _redis.sadd(_names_key(), name)
    _redis_hset_mapping(_config_key(name), {
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
    _redis_hset_mapping(_config_key(new_name), new_config)
    return jsonify({'succ': True, 'msg': f'已复制为 "{new_name}"'})


@deploy_bp.route('/deploy/<name>/delete', methods=['DELETE'])
@login_required
def deploy_delete(name):
    config = _redis.hgetall(_config_key(name)) or {}
    alive_pids, _, _ = _find_deploy_pids(name)
    if alive_pids:
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

    alive_pids, _, _ = _find_deploy_pids(name)
    if alive_pids:
        return jsonify({'succ': False, 'msg': '进程已在运行中'})

    procs, err, cmd_detail = _start_process(name, config)
    if err:
        return jsonify({'succ': False, 'msg': f'启动失败: {err}', 'cmd_detail': cmd_detail})
    _redis_hset_mapping(_runtime_key(name), {'manual_stop': '0', 'should_run': '1', 'restart_retry_count': '0'})
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
    alive_pids, search_cmd, alive_cts = _find_deploy_pids(name)
    if not alive_pids:
        return jsonify({'succ': False, 'msg': '进程未在运行'})

    runtime_data = _redis.hgetall(_runtime_key(name))
    old_start_time = runtime_data.get('start_time', '')

    kill_results = _kill_pids(alive_pids, name=name, ct_list=alive_cts)
    all_ok = all(r[1] for r in kill_results)
    last_err = next((r[2] for r in kill_results if not r[1]), '')

    if all_ok:
        _redis_hset_mapping(_runtime_key(name), {
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
    config = _redis.hgetall(_config_key(name))
    if not config:
        return jsonify({'succ': False, 'msg': '部署配置不存在'})

    runtime_data = _redis.hgetall(_runtime_key(name))
    old_start_time = runtime_data.get('start_time', '')

    alive_pids, search_cmd, alive_cts = _find_deploy_pids(name)
    old_pid = ', '.join(str(p) for p in alive_pids) if alive_pids else ''
    stop_cmds = []
    kill_details = []

    if alive_pids:
        kill_results = _kill_pids(alive_pids, name=name, ct_list=alive_cts)
        stop_cmds = [r[3] for r in kill_results]
        kill_details = [{'pid': r[0], 'ok': r[1], 'cmd': r[3]} for r in kill_results]
        any_fail = any(not r[1] for r in kill_results)
        if any_fail:
            last_err = next((r[2] for r in kill_results if not r[1]), '')
            return jsonify({
                'succ': False,
                'msg': f'停止旧进程失败: {last_err}',
                'cmd_detail': {
                    'search_cmd': search_cmd,
                    'found_pids': [str(p) for p in alive_pids],
                    'stop_cmd': '; '.join(stop_cmds),
                    'old_pid': old_pid,
                    'old_start_time': old_start_time,
                    'kill_details': kill_details,
                },
            })
        _redis_hset_mapping(_runtime_key(name), {'pid_list': '[]', 'ct_list': '[]'})
        time.sleep(1)

    procs, err, cmd_detail = _start_process(name, config)
    cmd_detail['search_cmd'] = search_cmd
    cmd_detail['found_pids'] = [str(p) for p in alive_pids]
    cmd_detail['kill_details'] = kill_details
    cmd_detail['stop_cmd'] = '; '.join(stop_cmds)
    cmd_detail['old_pid'] = old_pid
    cmd_detail['old_start_time'] = old_start_time
    if err:
        return jsonify({'succ': False, 'msg': f'重启失败: {err}', 'cmd_detail': cmd_detail})
    _redis_hset_mapping(_runtime_key(name), {'manual_stop': '0', 'should_run': '1', 'restart_retry_count': '0'})
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
    """状态轮询：仅用 Redis pid_list + is_running()/create_time() 验证，毫秒级返回。"""
    config = _redis.hgetall(_config_key(name))
    alive_pids, search_cmd, _ = _find_deploy_pids(name)
    runtime_data = _redis.hgetall(_runtime_key(name))
    status = {
        'running': len(alive_pids) > 0,
        'pid': ', '.join(str(p) for p in alive_pids) if alive_pids else '',
        'start_time': runtime_data.get('start_time', ''),
        'pid_list': [str(p) for p in alive_pids],
        'search_cmd': search_cmd,
    }
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
        check = _git(project_dir, ['rev-parse', '--is-inside-work-tree'], timeout=5)
        if check.returncode != 0:
            return jsonify({'succ': True, 'is_git_repo': False,
                            'current': '', 'local': [], 'remote': []})

        _git(project_dir, ['fetch', '--prune'], timeout=30)

        current = _git(project_dir, ['rev-parse', '--abbrev-ref', 'HEAD'], timeout=10)
        current_branch = current.stdout.strip() if current.returncode == 0 else ''

        local = _git(project_dir, ['branch'], timeout=10)
        local_branches = []
        for b in local.stdout.strip().split('\n'):
            b = b.strip().lstrip('* ').strip()
            if b:
                local_branches.append(b)

        remote_r = _git(project_dir, ['branch', '-r'], timeout=10)
        remote_branches = []
        for b in remote_r.stdout.strip().split('\n'):
            b = b.strip()
            if b and 'HEAD' not in b:
                remote_branches.append(b)

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
    """返回部署日志尾部（仅供操作弹框内近期日志使用）。"""
    max_lines = int(request.args.get('lines', 200))
    log_files = _find_log_files(name)
    if not log_files:
        return jsonify({'succ': True, 'data': [], 'files': [], 'total': 0})

    fpath = log_files[0]
    lines = _read_log_tail(fpath, max_lines)
    result = [_strip_ansi(line) for line in lines if line.strip()]
    return jsonify({
        'succ': True,
        'data': result[-max_lines:],
        'files': [os.path.basename(fpath)],
        'total': len(result[-max_lines:]),
    })


@deploy_bp.route('/deploy/<name>/config', methods=['GET'])
@login_required
def deploy_get_config(name):
    config = _redis.hgetall(_config_key(name))
    if not config:
        return jsonify({'succ': False, 'msg': '部署配置不存在'})
    alive_pids, search_cmd, _ = _find_deploy_pids(name)
    runtime_data = _redis.hgetall(_runtime_key(name))
    status = {
        'running': len(alive_pids) > 0,
        'pid': ', '.join(str(p) for p in alive_pids) if alive_pids else '',
        'start_time': runtime_data.get('start_time', ''),
        'pid_list': [str(p) for p in alive_pids],
        'search_cmd': search_cmd,
        'log_file': _get_nohup_log_path(name),
    }
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
            alive_pids, _, _ = _find_deploy_pids(name)
            if alive_pids:
                continue
            procs, err, _ = _start_process(name, config)
            if not err:
                _redis_hset_mapping(_runtime_key(name), {
                    'manual_stop': '0', 'should_run': '1', 'restart_retry_count': '0',
                })
        except Exception:
            pass


def _do_auto_restart_check():
    """守护线程每次循环调用：用 Redis pid_list 快速验证存活，不做全量扫描。"""
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

            alive_pids, _, alive_cts = _find_deploy_pids(name)
            expected = max(1, int(config.get('num_processes', '1') or 1))

            if len(alive_pids) >= expected:
                _redis_hset_field(_runtime_key(name), 'restart_retry_count', '0')
                continue

            retry_count = int(runtime.get('restart_retry_count', '0'))
            max_retry = int(config.get('max_retry', '3'))
            if retry_count >= max_retry:
                continue

            _redis_hset_field(_runtime_key(name), 'restart_retry_count', str(retry_count + 1))

            if alive_pids:
                _kill_pids(alive_pids, name=name, ct_list=alive_cts)
                _redis_hset_mapping(_runtime_key(name), {'pid_list': '[]', 'ct_list': '[]'})
                time.sleep(1)

            procs, err, _ = _start_process(name, config)
            if not err:
                _redis_hset_field(_runtime_key(name), 'restart_retry_count', '0')
        except Exception:
            pass


_daemon_thread = threading.Thread(target=_auto_restart_daemon, daemon=True)
_daemon_thread.start()

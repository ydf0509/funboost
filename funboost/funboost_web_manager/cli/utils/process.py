# -*- coding: utf-8 -*-
"""
进程管理工具

处理进程的启动、停止、查找等操作
"""

import os
import signal
import subprocess
import time
from typing import Optional, List, Dict, Tuple
from pathlib import Path

from .platform import Platform


class ProcessManager:
    """进程管理工具类"""
    
    @classmethod
    def find_process_on_port(cls, port: int) -> Optional[int]:
        """
        查找占用指定端口的进程 PID
        
        Args:
            port: 端口号
        
        Returns:
            进程 PID，未找到返回 None
        """
        try:
            if Platform.is_windows():
                # Windows: netstat -ano | findstr :port
                result = subprocess.run(
                    ['netstat', '-ano'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                for line in result.stdout.split('\n'):
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        if parts:
                            return int(parts[-1])
            else:
                # macOS/Linux: lsof -ti:port
                result = subprocess.run(
                    ['lsof', '-ti', f':{port}'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    # 可能返回多个 PID，取第一个
                    pids = result.stdout.strip().split('\n')
                    return int(pids[0])
        except Exception:
            pass
        return None
    
    @classmethod
    def is_port_in_use(cls, port: int) -> bool:
        """检查端口是否被占用"""
        return cls.find_process_on_port(port) is not None
    
    @classmethod
    def get_process_info(cls, pid: int) -> Optional[Dict[str, str]]:
        """
        获取进程信息
        
        Returns:
            {'pid': ..., 'name': ..., 'cmd': ...}
        """
        try:
            if Platform.is_windows():
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/V'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        # 解析 CSV 格式
                        parts = lines[1].replace('"', '').split(',')
                        return {
                            'pid': str(pid),
                            'name': parts[0] if parts else 'unknown',
                            'cmd': parts[0] if parts else 'unknown'
                        }
            else:
                result = subprocess.run(
                    ['ps', '-p', str(pid), '-o', 'pid,comm,args'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        parts = lines[1].split(None, 2)
                        return {
                            'pid': parts[0] if len(parts) > 0 else str(pid),
                            'name': parts[1] if len(parts) > 1 else 'unknown',
                            'cmd': parts[2] if len(parts) > 2 else parts[1] if len(parts) > 1 else 'unknown'
                        }
        except Exception:
            pass
        return None
    
    @classmethod
    def kill_process(cls, pid: int, force: bool = False) -> bool:
        """
        终止进程
        
        Args:
            pid: 进程 ID
            force: 是否强制终止
        
        Returns:
            是否成功
        """
        try:
            if Platform.is_windows():
                cmd = ['taskkill']
                if force:
                    cmd.append('/F')
                cmd.extend(['/PID', str(pid)])
                result = subprocess.run(cmd, capture_output=True, timeout=10)
                return result.returncode == 0
            else:
                sig = signal.SIGKILL if force else signal.SIGTERM
                os.kill(pid, sig)
                return True
        except (ProcessLookupError, PermissionError, OSError):
            return False
    
    @classmethod
    def kill_process_on_port(cls, port: int, force: bool = False) -> Tuple[bool, Optional[int]]:
        """
        终止占用指定端口的进程
        
        Returns:
            (是否成功, 被终止的 PID)
        """
        pid = cls.find_process_on_port(port)
        if pid is None:
            return True, None  # 端口未被占用
        
        success = cls.kill_process(pid, force)
        return success, pid
    
    @classmethod
    def wait_for_port_free(cls, port: int, timeout: int = 10) -> bool:
        """
        等待端口释放
        
        Args:
            port: 端口号
            timeout: 超时时间（秒）
        
        Returns:
            端口是否已释放
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not cls.is_port_in_use(port):
                return True
            time.sleep(0.5)
        return False
    
    @classmethod
    def wait_for_port_ready(cls, port: int, timeout: int = 30) -> bool:
        """
        等待端口就绪（服务启动）
        
        Args:
            port: 端口号
            timeout: 超时时间（秒）
        
        Returns:
            端口是否已就绪
        """
        import socket
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', port))
                sock.close()
                if result == 0:
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False
    
    @classmethod
    def start_background_process(
        cls,
        cmd: List[str],
        cwd: Path = None,
        env: Dict[str, str] = None,
        log_file: Path = None
    ) -> Optional[int]:
        """
        启动后台进程
        
        Args:
            cmd: 命令列表
            cwd: 工作目录
            env: 环境变量
            log_file: 日志文件路径
        
        Returns:
            进程 PID，失败返回 None
        """
        try:
            # 合并环境变量
            process_env = os.environ.copy()
            if env:
                process_env.update(env)
            
            # 输出重定向
            stdout = stderr = subprocess.DEVNULL
            if log_file:
                log_file.parent.mkdir(parents=True, exist_ok=True)
                stdout = stderr = open(log_file, 'a')
            
            # 启动进程
            if Platform.is_windows():
                # Windows: 使用 CREATE_NEW_PROCESS_GROUP
                process = subprocess.Popen(
                    cmd,
                    cwd=str(cwd) if cwd else None,
                    env=process_env,
                    stdout=stdout,
                    stderr=stderr,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                )
            else:
                # Unix: 使用 nohup 风格
                process = subprocess.Popen(
                    cmd,
                    cwd=str(cwd) if cwd else None,
                    env=process_env,
                    stdout=stdout,
                    stderr=stderr,
                    start_new_session=True
                )
            
            return process.pid
            
        except Exception:
            return None
    
    @classmethod
    def find_python_processes(cls, pattern: str = None) -> List[Dict[str, str]]:
        """
        查找 Python 进程
        
        Args:
            pattern: 命令行匹配模式
        
        Returns:
            进程列表 [{'pid': ..., 'name': ..., 'cmd': ...}, ...]
        """
        processes = []
        
        try:
            if Platform.is_windows():
                result = subprocess.run(
                    ['wmic', 'process', 'where', "name like '%python%'", 'get', 'processid,commandline', '/format:csv'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n')[1:]:
                        if line.strip():
                            parts = line.strip().split(',')
                            if len(parts) >= 3:
                                cmd = parts[1]
                                pid = parts[2]
                                if pattern is None or pattern in cmd:
                                    processes.append({
                                        'pid': pid,
                                        'name': 'python',
                                        'cmd': cmd
                                    })
            else:
                result = subprocess.run(
                    ['ps', 'aux'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n')[1:]:
                        if 'python' in line.lower():
                            parts = line.split(None, 10)
                            if len(parts) >= 11:
                                pid = parts[1]
                                cmd = parts[10]
                                if pattern is None or pattern in cmd:
                                    processes.append({
                                        'pid': pid,
                                        'name': 'python',
                                        'cmd': cmd
                                    })
        except Exception:
            pass
        
        return processes

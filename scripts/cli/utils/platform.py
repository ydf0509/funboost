# -*- coding: utf-8 -*-
"""
跨平台工具

处理不同操作系统的差异
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple


class Platform:
    """跨平台工具类"""
    
    # 项目根目录
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    
    @classmethod
    def is_windows(cls) -> bool:
        """是否是 Windows"""
        return sys.platform == 'win32'
    
    @classmethod
    def is_macos(cls) -> bool:
        """是否是 macOS"""
        return sys.platform == 'darwin'
    
    @classmethod
    def is_linux(cls) -> bool:
        """是否是 Linux"""
        return sys.platform.startswith('linux')
    
    @classmethod
    def get_os_name(cls) -> str:
        """获取操作系统名称"""
        if cls.is_windows():
            return "Windows"
        elif cls.is_macos():
            return "macOS"
        elif cls.is_linux():
            return "Linux"
        return sys.platform
    
    @classmethod
    def get_python_version(cls) -> Tuple[int, int, int]:
        """获取 Python 版本"""
        return sys.version_info[:3]
    
    @classmethod
    def get_python_version_str(cls) -> str:
        """获取 Python 版本字符串"""
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    @classmethod
    def check_python_version(cls, min_version: Tuple[int, int] = (3, 9)) -> Tuple[bool, str]:
        """
        检查 Python 版本
        
        Returns:
            (是否满足, 版本字符串)
        """
        version = cls.get_python_version()
        version_str = cls.get_python_version_str()
        
        if version[:2] >= min_version:
            return True, version_str
        return False, version_str
    
    @classmethod
    def find_python(cls) -> str:
        """
        查找 Python 解释器
        
        优先使用虚拟环境中的 Python
        """
        # 虚拟环境路径
        if cls.is_windows():
            venv_python = cls.PROJECT_ROOT / '.venv' / 'Scripts' / 'python.exe'
        else:
            venv_python = cls.PROJECT_ROOT / '.venv' / 'bin' / 'python'
        
        if venv_python.exists():
            return str(venv_python)
        
        return sys.executable
    
    @classmethod
    def find_pip(cls) -> str:
        """查找 pip"""
        if cls.is_windows():
            venv_pip = cls.PROJECT_ROOT / '.venv' / 'Scripts' / 'pip.exe'
        else:
            venv_pip = cls.PROJECT_ROOT / '.venv' / 'bin' / 'pip'
        
        if venv_pip.exists():
            return str(venv_pip)
        
        return 'pip'
    
    @classmethod
    def find_npm(cls) -> Optional[str]:
        """查找 npm 命令"""
        if cls.is_windows():
            # Windows 上尝试多个可能的命令
            for cmd in ['npm.cmd', 'npm']:
                if shutil.which(cmd):
                    return cmd
        else:
            if shutil.which('npm'):
                return 'npm'
        return None
    
    @classmethod
    def find_node(cls) -> Optional[str]:
        """查找 Node.js"""
        return shutil.which('node')
    
    @classmethod
    def get_node_version(cls) -> Optional[str]:
        """获取 Node.js 版本"""
        node = cls.find_node()
        if not node:
            return None
        
        try:
            result = subprocess.run(
                [node, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    @classmethod
    def get_npm_version(cls) -> Optional[str]:
        """获取 npm 版本"""
        npm = cls.find_npm()
        if not npm:
            return None
        
        try:
            result = subprocess.run(
                [npm, '--version'],
                capture_output=True,
                text=True,
                timeout=10,
                shell=cls.is_windows()
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    @classmethod
    def venv_exists(cls) -> bool:
        """检查虚拟环境是否存在"""
        venv_path = cls.PROJECT_ROOT / '.venv'
        return venv_path.exists() and venv_path.is_dir()
    
    @classmethod
    def create_venv(cls) -> bool:
        """创建虚拟环境"""
        venv_path = cls.PROJECT_ROOT / '.venv'
        
        try:
            subprocess.run(
                [sys.executable, '-m', 'venv', str(venv_path)],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    @classmethod
    def get_venv_activate_command(cls) -> str:
        """获取激活虚拟环境的命令"""
        if cls.is_windows():
            return r".venv\Scripts\activate.bat"
        return "source .venv/bin/activate"
    
    @classmethod
    def run_command(
        cls,
        cmd: list,
        cwd: Path = None,
        capture: bool = False,
        timeout: int = None
    ) -> Tuple[bool, str]:
        """
        运行命令
        
        Args:
            cmd: 命令列表
            cwd: 工作目录
            capture: 是否捕获输出
            timeout: 超时时间（秒）
        
        Returns:
            (是否成功, 输出/错误信息)
        """
        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd) if cwd else None,
                capture_output=capture,
                text=True,
                timeout=timeout,
                shell=cls.is_windows() and cmd[0].endswith('.cmd')
            )
            
            if capture:
                output = result.stdout if result.returncode == 0 else result.stderr
                return result.returncode == 0, output.strip()
            
            return result.returncode == 0, ""
            
        except subprocess.TimeoutExpired:
            return False, "命令执行超时"
        except FileNotFoundError:
            return False, f"命令未找到: {cmd[0]}"
        except Exception as e:
            return False, str(e)
    
    @classmethod
    def get_env_file_path(cls) -> Path:
        """获取 .env 文件路径"""
        return cls.PROJECT_ROOT / '.env'
    
    @classmethod
    def get_env_example_path(cls) -> Path:
        """获取 .env.example 文件路径"""
        return cls.PROJECT_ROOT / '.env.example'
    
    @classmethod
    def get_requirements_path(cls) -> Path:
        """获取 requirements.txt 路径"""
        return cls.PROJECT_ROOT / 'requirements.txt'
    
    @classmethod
    def get_frontend_dir(cls) -> Path:
        """获取前端目录"""
        return cls.PROJECT_ROOT / 'web-manager-frontend'
    
    @classmethod
    def get_database_path(cls) -> Path:
        """获取数据库文件路径"""
        return cls.PROJECT_ROOT / 'web_manager_users.db'
    
    @classmethod
    def get_backup_dir(cls) -> Path:
        """获取备份目录"""
        backup_dir = cls.PROJECT_ROOT / 'backups'
        backup_dir.mkdir(exist_ok=True)
        return backup_dir

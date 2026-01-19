# -*- coding: utf-8 -*-
"""
服务管理命令

启动、停止服务
"""

import sys
import time
from pathlib import Path
from typing import Optional

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scripts.cli.utils import Console, Platform, ProcessManager


class ServiceCommand:
    """服务管理命令"""
    
    # 服务配置
    BACKEND_PORT = 27018
    FRONTEND_PORT = 3000
    
    @classmethod
    def start(cls, backend: bool = True, frontend: bool = True) -> bool:
        """启动服务"""
        Console.title("启动服务")
        
        success = True
        
        if backend:
            if not cls._start_backend():
                success = False
        
        if frontend:
            if not cls._start_frontend():
                success = False
        
        if success:
            Console.newline()
            Console.success("服务启动完成！")
            Console.newline()
            Console.info("访问地址:")
            if backend:
                Console.item(f"后端 API: http://127.0.0.1:{cls.BACKEND_PORT}")
            if frontend:
                Console.item(f"前端界面: http://127.0.0.1:{cls.FRONTEND_PORT}")
        
        return success
    
    @classmethod
    def _start_backend(cls) -> bool:
        """启动后端服务"""
        Console.subtitle("后端服务")
        
        # 检查端口
        if ProcessManager.is_port_in_use(cls.BACKEND_PORT):
            pid = ProcessManager.find_process_on_port(cls.BACKEND_PORT)
            Console.warning(f"端口 {cls.BACKEND_PORT} 已被占用 (PID: {pid})")
            
            if Console.confirm("是否停止现有进程？"):
                ProcessManager.kill_process(pid, force=True)
                time.sleep(1)
            else:
                Console.info("跳过后端启动")
                return True
        
        # 启动后端
        Console.info("启动后端服务...")
        
        python = Platform.find_python()
        project_root = Platform.PROJECT_ROOT
        log_file = project_root / 'logs' / 'backend.log'
        
        pid = ProcessManager.start_background_process(
            cmd=[python, 'start_web_manager.py'],
            cwd=project_root,
            log_file=log_file
        )
        
        if pid is None:
            Console.error("后端服务启动失败")
            return False
        
        Console.item(f"进程 PID: {pid}")
        Console.item(f"日志文件: {log_file}")
        
        # 等待服务就绪
        Console.info("等待服务就绪...")
        if ProcessManager.wait_for_port_ready(cls.BACKEND_PORT, timeout=30):
            Console.success(f"后端服务已启动 (端口 {cls.BACKEND_PORT})")
            return True
        else:
            Console.warning("后端服务启动超时，请检查日志")
            return False
    
    @classmethod
    def _start_frontend(cls) -> bool:
        """启动前端服务"""
        Console.subtitle("前端服务")
        
        frontend_dir = Platform.get_frontend_dir()
        
        if not frontend_dir.exists():
            Console.error("前端目录不存在")
            return False
        
        # 检查 node_modules
        if not (frontend_dir / 'node_modules').exists():
            Console.warning("前端依赖未安装")
            if Console.confirm("是否安装依赖？"):
                cls._install_frontend_deps()
            else:
                return False
        
        # 检查端口
        if ProcessManager.is_port_in_use(cls.FRONTEND_PORT):
            pid = ProcessManager.find_process_on_port(cls.FRONTEND_PORT)
            Console.warning(f"端口 {cls.FRONTEND_PORT} 已被占用 (PID: {pid})")
            
            if Console.confirm("是否停止现有进程？"):
                ProcessManager.kill_process(pid, force=True)
                time.sleep(1)
            else:
                Console.info("跳过前端启动")
                return True
        
        # 启动前端
        Console.info("启动前端服务...")
        
        npm = Platform.find_npm()
        if not npm:
            Console.error("npm 未找到")
            return False
        
        log_file = Platform.PROJECT_ROOT / 'logs' / 'frontend.log'
        
        # 使用 npm run dev
        if Platform.is_windows():
            cmd = ['cmd', '/c', 'npm', 'run', 'dev']
        else:
            cmd = [npm, 'run', 'dev']
        
        pid = ProcessManager.start_background_process(
            cmd=cmd,
            cwd=frontend_dir,
            log_file=log_file
        )
        
        if pid is None:
            Console.error("前端服务启动失败")
            return False
        
        Console.item(f"进程 PID: {pid}")
        Console.item(f"日志文件: {log_file}")
        
        # 等待服务就绪
        Console.info("等待服务就绪...")
        if ProcessManager.wait_for_port_ready(cls.FRONTEND_PORT, timeout=60):
            Console.success(f"前端服务已启动 (端口 {cls.FRONTEND_PORT})")
            return True
        else:
            Console.warning("前端服务启动超时，请检查日志")
            return False
    
    @classmethod
    def _install_frontend_deps(cls) -> bool:
        """安装前端依赖"""
        Console.info("安装前端依赖...")
        
        npm = Platform.find_npm()
        if not npm:
            Console.error("npm 未找到")
            return False
        
        frontend_dir = Platform.get_frontend_dir()
        
        if Platform.is_windows():
            cmd = ['cmd', '/c', 'npm', 'install']
        else:
            cmd = [npm, 'install']
        
        success, output = Platform.run_command(cmd, cwd=frontend_dir, capture=True, timeout=300)
        
        if success:
            Console.success("前端依赖安装完成")
            return True
        else:
            Console.error(f"安装失败: {output}")
            return False
    
    @classmethod
    def stop(cls) -> bool:
        """停止所有服务"""
        Console.title("停止服务")
        
        stopped = False
        
        # 停止后端
        Console.subtitle("后端服务")
        pid = ProcessManager.find_process_on_port(cls.BACKEND_PORT)
        if pid:
            Console.info(f"停止进程 {pid}...")
            if ProcessManager.kill_process(pid, force=True):
                Console.success("后端服务已停止")
                stopped = True
            else:
                Console.error("停止后端服务失败")
        else:
            Console.info("后端服务未运行")
        
        # 停止前端
        Console.subtitle("前端服务")
        pid = ProcessManager.find_process_on_port(cls.FRONTEND_PORT)
        if pid:
            Console.info(f"停止进程 {pid}...")
            if ProcessManager.kill_process(pid, force=True):
                Console.success("前端服务已停止")
                stopped = True
            else:
                Console.error("停止前端服务失败")
        else:
            Console.info("前端服务未运行")
        
        if stopped:
            Console.newline()
            Console.success("服务已停止")
        
        return True
    

# -*- coding: utf-8 -*-
"""
初始化命令

一键初始化整个项目环境
"""

import sys
import shutil
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scripts.cli.utils import Console, Platform
from scripts.cli.commands.db import DbCommand
from scripts.cli.commands.user import UserCommand


class InitCommand:
    """初始化命令"""
    
    @classmethod
    def run(
        cls,
        skip_venv: bool = False,
        skip_deps: bool = False,
        skip_frontend: bool = False,
        skip_db: bool = False,
        skip_user: bool = False
    ) -> bool:
        """
        一键初始化
        
        Args:
            skip_venv: 跳过虚拟环境创建
            skip_deps: 跳过依赖安装
            skip_frontend: 跳过前端初始化
            skip_db: 跳过数据库初始化
            skip_user: 跳过用户创建
        """
        Console.title("Funboost Web Manager 初始化")
        
        total_steps = 6
        current_step = 0
        
        # Step 1: 环境检查
        current_step += 1
        Console.step(current_step, total_steps, "环境检查")
        
        # 检查 Python 版本
        ok, version = Platform.check_python_version((3, 9))
        if not ok:
            Console.error(f"Python 版本过低: {version}")
            Console.suggestion("需要 Python 3.9+", [
                "macOS: brew install python@3.11",
                "Ubuntu: sudo apt install python3.11",
                "Windows: https://www.python.org/downloads/"
            ])
            return False
        Console.success(f"Python {version}")
        
        # Step 2: 虚拟环境
        current_step += 1
        Console.step(current_step, total_steps, "虚拟环境")
        
        if skip_venv:
            Console.info("跳过虚拟环境创建")
        elif Platform.venv_exists():
            Console.success("虚拟环境已存在")
        else:
            Console.info("创建虚拟环境...")
            if Platform.create_venv():
                Console.success("虚拟环境创建完成")
                Console.hint(f"激活命令: {Platform.get_venv_activate_command()}")
            else:
                Console.error("虚拟环境创建失败")
                return False
        
        # Step 3: Python 依赖
        current_step += 1
        Console.step(current_step, total_steps, "Python 依赖")
        
        if skip_deps:
            Console.info("跳过依赖安装")
        else:
            if not cls._install_python_deps():
                Console.warning("依赖安装可能不完整，继续...")
        
        # Step 4: 前端依赖
        current_step += 1
        Console.step(current_step, total_steps, "前端依赖")
        
        if skip_frontend:
            Console.info("跳过前端初始化")
        else:
            if not cls._install_frontend_deps():
                Console.warning("前端依赖安装可能不完整，继续...")
        
        # Step 5: 数据库
        current_step += 1
        Console.step(current_step, total_steps, "数据库初始化")
        
        if skip_db:
            Console.info("跳过数据库初始化")
        else:
            db_path = Platform.get_database_path()
            if db_path.exists():
                Console.success("数据库已存在")
            else:
                if not cls._init_database():
                    Console.warning("数据库初始化可能不完整，继续...")
        
        # Step 6: 创建管理员
        current_step += 1
        Console.step(current_step, total_steps, "创建管理员")
        
        if skip_user:
            Console.info("跳过用户创建")
        else:
            if not cls._create_admin():
                Console.warning("管理员创建可能不完整")
        
        # 完成
        Console.newline()
        Console.title("初始化完成！")
        
        Console.info("下一步:")
        Console.item("启动服务: python manage.py start")
        Console.item(f"访问前端: http://127.0.0.1:3000")
        Console.item(f"访问后端: http://127.0.0.1:27018")
        
        return True
    
    @classmethod
    def _install_python_deps(cls) -> bool:
        """安装 Python 依赖"""
        requirements = Platform.get_requirements_path()
        
        if not requirements.exists():
            Console.warning("requirements.txt 不存在")
            return False
        
        Console.info("安装 Python 依赖...")
        
        pip = Platform.find_pip()
        success, output = Platform.run_command(
            [pip, 'install', '-r', str(requirements)],
            cwd=Platform.PROJECT_ROOT,
            capture=True,
            timeout=600
        )
        
        if success:
            Console.success("Python 依赖安装完成")
            return True
        else:
            Console.error(f"安装失败: {output[:200]}...")
            return False
    
    @classmethod
    def _install_frontend_deps(cls) -> bool:
        """安装前端依赖"""
        frontend_dir = Platform.get_frontend_dir()
        
        if not frontend_dir.exists():
            Console.warning("前端目录不存在")
            return False
        
        node_modules = frontend_dir / 'node_modules'
        if node_modules.exists():
            Console.success("前端依赖已安装")
            return True
        
        npm = Platform.find_npm()
        if not npm:
            Console.error("npm 未找到，请先安装 Node.js")
            return False
        
        Console.info("安装前端依赖...")
        
        if Platform.is_windows():
            cmd = ['cmd', '/c', 'npm', 'install']
        else:
            cmd = [npm, 'install']
        
        success, output = Platform.run_command(
            cmd,
            cwd=frontend_dir,
            capture=True,
            timeout=600
        )
        
        if success:
            Console.success("前端依赖安装完成")
            return True
        else:
            Console.error(f"安装失败: {output[:200]}...")
            return False
    
    @classmethod
    def _init_database(cls) -> bool:
        """初始化数据库"""
        Console.info("初始化数据库...")
        
        try:
            from funboost.funboost_web_manager.user_models import (
                init_db,
                init_default_permissions,
                migrate_database
            )
            
            db_path = Platform.get_database_path()
            db_url = f'sqlite:///{db_path}'
            
            init_db(db_url)
            Console.item("数据库表创建完成")
            
            migrate_database()
            Console.item("数据库迁移完成")
            
            init_default_permissions(db_url)
            Console.item("默认权限初始化完成")
            
            Console.success("数据库初始化完成")
            return True
            
        except Exception as e:
            Console.error(f"数据库初始化失败: {e}")
            return False
    
    @classmethod
    def _create_admin(cls) -> bool:
        """创建管理员用户"""
        try:
            from funboost.funboost_web_manager.user_models import (
                get_session, WebManagerUser, Role, Permission
            )
            
            db_path = Platform.get_database_path()
            db_url = f'sqlite:///{db_path}'
            session = get_session(db_url)
            
            try:
                # 检查是否已有 admin 用户
                admin_user = session.query(WebManagerUser).filter_by(user_name='admin').first()
                
                if admin_user:
                    Console.success("管理员用户已存在")
                    
                    # 确保 admin 角色有所有权限
                    admin_role = session.query(Role).filter_by(name='admin').first()
                    if admin_role:
                        all_permissions = session.query(Permission).all()
                        admin_role.permissions = all_permissions
                        session.commit()
                        Console.item("已更新 admin 角色权限")
                    
                    return True
                
                # 创建 admin 角色（如果不存在）
                admin_role = session.query(Role).filter_by(name='admin').first()
                if not admin_role:
                    admin_role = Role(name='admin', description='管理员')
                    session.add(admin_role)
                    session.flush()
                
                # 给 admin 角色所有权限
                all_permissions = session.query(Permission).all()
                admin_role.permissions = all_permissions
                
                # 创建 admin 用户
                Console.info("创建管理员用户...")
                Console.newline()
                
                password = Console.password("请设置管理员密码")
                if not password:
                    password = 'Admin@123456'
                    Console.warning(f"使用默认密码: {password}")
                
                from funboost.funboost_web_manager.services.password_service import PasswordService
                
                admin_user = WebManagerUser(
                    user_name='admin',
                    password=PasswordService.hash_password(password),
                    email='admin@localhost'
                )
                admin_user.roles.append(admin_role)
                
                session.add(admin_user)
                session.commit()
                
                Console.success("管理员用户创建完成")
                Console.item("用户名: admin")
                
                return True
                
            finally:
                session.close()
                
        except Exception as e:
            Console.error(f"创建管理员失败: {e}")
            return False
    
    @classmethod
    def setup_env(cls) -> bool:
        """设置环境变量文件"""
        env_file = Platform.get_env_file_path()
        env_example = Platform.get_env_example_path()
        
        if env_file.exists():
            Console.success(".env 文件已存在")
            return True
        
        if env_example.exists():
            Console.info("从 .env.example 创建 .env...")
            shutil.copy(env_example, env_file)
            Console.success(".env 文件创建完成")
            Console.hint("请编辑 .env 文件配置环境变量")
            return True
        
        Console.warning(".env.example 不存在，跳过")
        return False

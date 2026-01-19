# -*- coding: utf-8 -*-
"""
用户管理命令

创建、删除、重置密码等用户操作
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scripts.cli.utils import Console, Platform


class UserCommand:
    """用户管理命令"""
    
    @classmethod
    def create(cls, config_file: str = None) -> bool:
        """创建用户"""
        Console.title("创建用户")
        
        db_path = Platform.get_database_path()
        if not db_path.exists():
            Console.error("数据库不存在，请先初始化")
            Console.hint("运行: python manage.py db init")
            return False
        
        if config_file:
            return cls._create_from_config(config_file)
        else:
            return cls._create_interactive()
    
    @classmethod
    def _create_interactive(cls) -> bool:
        """交互式创建用户"""
        try:
            from funboost.funboost_web_manager.user_models import (
                get_session, WebManagerUser, Role
            )
            
            db_url = f'sqlite:///{Platform.get_database_path()}'
            session = get_session(db_url)
            
            try:
                # 获取可用角色
                roles = session.query(Role).all()
                role_names = [r.name for r in roles]
                
                if not role_names:
                    Console.error("没有可用的角色，请先初始化数据库")
                    return False
                
                Console.info("请输入用户信息:")
                Console.newline()
                
                # 用户名
                username = Console.input("用户名")
                if not username:
                    Console.error("用户名不能为空")
                    return False
                
                # 检查用户是否存在
                existing = session.query(WebManagerUser).filter_by(user_name=username).first()
                if existing:
                    Console.error(f"用户 '{username}' 已存在")
                    return False
                
                # 密码
                password = Console.password("密码")
                if not password:
                    Console.error("密码不能为空")
                    return False
                
                confirm_password = Console.password("确认密码")
                if password != confirm_password:
                    Console.error("两次输入的密码不一致")
                    return False
                
                # 邮箱
                email = Console.input("邮箱", f"{username}@localhost")
                
                # 角色
                Console.newline()
                Console.info("可用角色:")
                for i, name in enumerate(role_names):
                    Console.item(f"[{i + 1}] {name}")
                
                role_idx = Console.select("选择角色", role_names, 0)
                role_name = role_names[role_idx]
                role = session.query(Role).filter_by(name=role_name).first()
                
                # 创建用户
                Console.newline()
                Console.info("创建用户...")
                
                from funboost.funboost_web_manager.services.password_service import PasswordService
                
                user = WebManagerUser(
                    user_name=username,
                    password=PasswordService.hash_password(password),
                    email=email
                )
                user.roles.append(role)
                
                session.add(user)
                session.commit()
                
                Console.success(f"用户 '{username}' 创建成功！")
                Console.item(f"角色: {role_name}")
                Console.item(f"邮箱: {email}")
                
                return True
                
            finally:
                session.close()
                
        except Exception as e:
            Console.error(f"创建用户失败: {e}")
            return False
    
    @classmethod
    def _create_from_config(cls, config_file: str) -> bool:
        """从配置文件创建用户"""
        config_path = Path(config_file)
        
        if not config_path.exists():
            Console.error(f"配置文件不存在: {config_file}")
            return False
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            from funboost.funboost_web_manager.user_models import (
                get_session, WebManagerUser, Role
            )
            
            db_url = f'sqlite:///{Platform.get_database_path()}'
            session = get_session(db_url)
            
            try:
                users = config.get('users', [config])  # 支持单用户或用户列表
                
                for user_config in users:
                    username = user_config.get('username') or user_config.get('user_name')
                    password = user_config.get('password')
                    email = user_config.get('email', f"{username}@localhost")
                    role_name = user_config.get('role', 'user')
                    
                    if not username or not password:
                        Console.warning(f"跳过无效配置: {user_config}")
                        continue
                    
                    # 检查用户是否存在
                    existing = session.query(WebManagerUser).filter_by(user_name=username).first()
                    if existing:
                        Console.warning(f"用户 '{username}' 已存在，跳过")
                        continue
                    
                    # 获取角色
                    role = session.query(Role).filter_by(name=role_name).first()
                    if not role:
                        Console.warning(f"角色 '{role_name}' 不存在，使用默认角色")
                        role = session.query(Role).filter_by(name='user').first()
                    
                    # 创建用户
                    from funboost.funboost_web_manager.services.password_service import PasswordService
                    
                    user = WebManagerUser(
                        user_name=username,
                        password=PasswordService.hash_password(password),
                        email=email
                    )
                    if role:
                        user.roles.append(role)
                    
                    session.add(user)
                    Console.success(f"创建用户: {username}")
                
                session.commit()
                Console.success("用户创建完成！")
                return True
                
            finally:
                session.close()
                
        except json.JSONDecodeError as e:
            Console.error(f"配置文件格式错误: {e}")
            return False
        except Exception as e:
            Console.error(f"创建用户失败: {e}")
            return False
    
    @classmethod
    def list(cls) -> bool:
        """列出所有用户"""
        Console.title("用户列表")
        
        db_path = Platform.get_database_path()
        if not db_path.exists():
            Console.error("数据库不存在")
            return False
        
        try:
            from funboost.funboost_web_manager.user_models import get_session, WebManagerUser
            
            db_url = f'sqlite:///{db_path}'
            session = get_session(db_url)
            
            try:
                users = session.query(WebManagerUser).all()
                
                if not users:
                    Console.info("没有用户")
                    return True
                
                headers = ['ID', '用户名', '邮箱', '角色', '状态', '创建时间']
                rows = []
                
                now = datetime.now()
                for user in users:
                    roles = ', '.join([r.name for r in user.roles]) or '-'
                    is_locked = user.status == 'locked' or (
                        user.locked_until and user.locked_until > now
                    )
                    if user.status == 'disabled':
                        status = '禁用'
                    elif is_locked:
                        status = '锁定'
                    else:
                        status = '正常'
                    created = user.created_at.strftime('%Y-%m-%d') if user.created_at else '-'
                    
                    rows.append([
                        str(user.id),
                        user.user_name,
                        user.email or '-',
                        roles,
                        status,
                        created
                    ])
                
                Console.table(headers, rows)
                Console.newline()
                Console.info(f"共 {len(users)} 个用户")
                
                return True
                
            finally:
                session.close()
                
        except Exception as e:
            Console.error(f"获取用户列表失败: {e}")
            return False
    
    @classmethod
    def reset_password(cls, username: str) -> bool:
        """重置用户密码"""
        Console.title(f"重置密码: {username}")
        
        db_path = Platform.get_database_path()
        if not db_path.exists():
            Console.error("数据库不存在")
            return False
        
        try:
            from funboost.funboost_web_manager.user_models import get_session, WebManagerUser
            from funboost.funboost_web_manager.services.password_service import PasswordService
            
            db_url = f'sqlite:///{db_path}'
            session = get_session(db_url)
            
            try:
                user = session.query(WebManagerUser).filter_by(user_name=username).first()
                
                if not user:
                    Console.error(f"用户 '{username}' 不存在")
                    return False
                
                # 输入新密码
                password = Console.password("新密码")
                if not password:
                    Console.error("密码不能为空")
                    return False
                
                confirm_password = Console.password("确认密码")
                if password != confirm_password:
                    Console.error("两次输入的密码不一致")
                    return False
                
                # 重置密码
                user.password = PasswordService.hash_password(password)
                user.force_password_change = False  # 清除强制修改标记
                user.failed_login_count = 0  # 清除登录失败计数
                user.locked_until = None  # 清除锁定状态
                session.commit()
                
                Console.success(f"用户 '{username}' 密码已重置")
                return True
                
            finally:
                session.close()
                
        except Exception as e:
            Console.error(f"重置密码失败: {e}")
            return False
    
    @classmethod
    def unlock(cls, username: str) -> bool:
        """解锁用户"""
        Console.title(f"解锁用户: {username}")
        
        db_path = Platform.get_database_path()
        if not db_path.exists():
            Console.error("数据库不存在")
            return False
        
        try:
            from funboost.funboost_web_manager.user_models import get_session, WebManagerUser
            
            db_url = f'sqlite:///{db_path}'
            session = get_session(db_url)
            
            try:
                user = session.query(WebManagerUser).filter_by(user_name=username).first()
                
                if not user:
                    Console.error(f"用户 '{username}' 不存在")
                    return False
                
                now = datetime.now()
                is_locked = user.status == 'locked' or (
                    user.locked_until and user.locked_until > now
                )
                if not is_locked:
                    Console.info(f"用户 '{username}' 未被锁定")
                    return True

                if user.status == 'locked':
                    user.status = 'active'
                user.failed_login_count = 0
                user.locked_until = None
                session.commit()
                
                Console.success(f"用户 '{username}' 已解锁")
                return True
                
            finally:
                session.close()
                
        except Exception as e:
            Console.error(f"解锁用户失败: {e}")
            return False
    
    @classmethod
    def delete(cls, username: str) -> bool:
        """删除用户"""
        Console.title(f"删除用户: {username}")
        
        db_path = Platform.get_database_path()
        if not db_path.exists():
            Console.error("数据库不存在")
            return False
        
        try:
            from funboost.funboost_web_manager.user_models import get_session, WebManagerUser
            
            db_url = f'sqlite:///{db_path}'
            session = get_session(db_url)
            
            try:
                user = session.query(WebManagerUser).filter_by(user_name=username).first()
                
                if not user:
                    Console.error(f"用户 '{username}' 不存在")
                    return False
                
                Console.warning(f"即将删除用户: {username}")
                if not Console.confirm("确定要删除吗？"):
                    Console.info("已取消")
                    return False
                
                session.delete(user)
                session.commit()
                
                Console.success(f"用户 '{username}' 已删除")
                return True
                
            finally:
                session.close()
                
        except Exception as e:
            Console.error(f"删除用户失败: {e}")
            return False
    
    @classmethod
    def clean_defaults(cls) -> bool:
        """清理默认用户"""
        Console.title("清理默认用户")
        
        db_path = Platform.get_database_path()
        if not db_path.exists():
            Console.error("数据库不存在")
            return False
        
        # 要清理的默认用户
        default_users = ['Tom', 'user']
        
        try:
            from funboost.funboost_web_manager.user_models import get_session, WebManagerUser
            
            db_url = f'sqlite:///{db_path}'
            session = get_session(db_url)
            
            try:
                deleted = []
                
                for username in default_users:
                    user = session.query(WebManagerUser).filter_by(user_name=username).first()
                    if user:
                        session.delete(user)
                        deleted.append(username)
                        Console.item(f"删除: {username}")
                
                if deleted:
                    session.commit()
                    Console.success(f"已清理 {len(deleted)} 个默认用户")
                else:
                    Console.info("没有找到默认用户")
                
                return True
                
            finally:
                session.close()
                
        except Exception as e:
            Console.error(f"清理失败: {e}")
            return False

# -*- coding: utf-8 -*-
"""
数据库管理命令

初始化、迁移、备份、恢复数据库
"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..utils import Console, Platform


class DbCommand:
    """数据库管理命令"""
    
    MAX_PASSWORD_ATTEMPTS = 3  # 密码输入最大尝试次数

    @staticmethod
    def _delete_db_files(db_path: Path) -> None:
        """删除数据库文件及其辅助文件"""
        db_files = [
            db_path,
            db_path.with_name(f"{db_path.name}-wal"),
            db_path.with_name(f"{db_path.name}-shm"),
            db_path.with_name(f"{db_path.name}-journal"),
        ]
        for path in db_files:
            if path.exists():
                path.unlink()
    
    @staticmethod
    def _get_db_url(db_path: Path) -> str:
        """构造数据库 URL"""
        return f'sqlite:///{db_path}'
    
    @staticmethod
    def _prompt_password_with_confirmation() -> Optional[str]:
        """提示用户输入密码并确认
        
        Returns:
            验证通过的密码，失败返回 None
        """
        for attempt in range(DbCommand.MAX_PASSWORD_ATTEMPTS):
            is_last_attempt = (attempt == DbCommand.MAX_PASSWORD_ATTEMPTS - 1)
            
            password = Console.password("密码")
            if not password:
                Console.error("密码不能为空")
                if is_last_attempt:
                    Console.error("已达到最大尝试次数")
                    return None
                Console.hint("请重新输入")
                continue
            
            confirm_password = Console.password("确认密码")
            if password != confirm_password:
                Console.error("两次输入的密码不一致")
                if is_last_attempt:
                    Console.error("已达到最大尝试次数")
                    return None
                Console.hint("请重新输入")
                continue
            
            return password
        
        return None
    
    @classmethod
    def _create_admin_user(cls, db_url: str) -> bool:
        """交互式创建管理员用户"""
        try:
            from funboost.funboost_web_manager.user_models import (
                get_session, WebManagerUser, Role
            )
            from funboost.funboost_web_manager.services.password_service import PasswordService
            
            session = get_session(db_url)
            
            try:
                # 获取 admin 角色
                admin_role = session.query(Role).filter_by(name='admin').first()
                if not admin_role:
                    Console.error("admin 角色不存在")
                    return False
                
                # 用户名（默认 admin）
                username = Console.input("用户名 (默认: admin)", "admin")
                
                # 检查用户是否存在
                existing = session.query(WebManagerUser).filter_by(user_name=username).first()
                if existing:
                    Console.error(f"用户 '{username}' 已存在")
                    return False
                
                # 密码输入（带重试）
                password = cls._prompt_password_with_confirmation()
                if not password:
                    return False
                
                # 邮箱（默认 admin@admin.com）
                email = Console.input("邮箱 (默认: admin@admin.com)", "admin@admin.com")
                
                # 创建管理员用户
                user = WebManagerUser(
                    user_name=username,
                    password=PasswordService.hash_password(password),
                    email=email,
                    force_password_change=False  # 不强制修改密码
                )
                user.roles.append(admin_role)
                
                session.add(user)
                session.commit()
                
                Console.success(f"管理员 '{username}' 创建成功！")
                Console.item(f"邮箱: {email}")
                
                return True
                
            finally:
                session.close()
                
        except Exception as e:
            Console.error(f"创建管理员失败: {e}")
            import traceback
            Console.hint(f"详细错误: {traceback.format_exc()}")
            return False
    
    @classmethod
    def init(cls) -> bool:
        """初始化数据库"""
        Console.title("初始化数据库")
        
        db_path = Platform.get_database_path()
        
        # 检查数据库是否已存在
        if db_path.exists():
            Console.warning(f"数据库已存在: {db_path}")
            if not Console.confirm("是否重新初始化？这将清空所有数据"):
                Console.info("已取消")
                return False
            
            # 备份现有数据库
            Console.info("备份现有数据库...")
            cls.backup()
            try:
                from funboost.funboost_web_manager.user_models import reset_engine
                reset_engine()
            except Exception:
                pass
            cls._delete_db_files(db_path)
        
        try:
            Console.info("创建数据库表...")
            
            # 导入并初始化数据库
            from funboost.funboost_web_manager.user_models import (
                init_db,
                migrate_database
            )
            
            db_url = cls._get_db_url(db_path)
            
            # 初始化数据库
            init_db(db_url)
            Console.item("数据库表创建完成")
            
            # 运行迁移（包含权限、角色、分类等初始化）
            migrate_database(db_url)
            Console.item("数据库迁移完成")
            
            # 创建管理员用户
            Console.newline()
            Console.info("创建管理员账户")
            Console.newline()
            
            if not cls._create_admin_user(db_url):
                Console.error("管理员账户创建失败")
                return False
            
            Console.newline()
            Console.success("数据库初始化完成！")
            return True
            
        except Exception as e:
            Console.error(f"数据库初始化失败: {e}")
            import traceback
            Console.hint(f"详细错误: {traceback.format_exc()}")
            return False
    
    @classmethod
    def migrate(cls) -> bool:
        """运行数据库迁移"""
        Console.title("数据库迁移")
        
        db_path = Platform.get_database_path()
        
        if not db_path.exists():
            Console.error("数据库不存在，请先运行初始化")
            Console.hint("运行: python -m funboost.funboost_web_manager.cli db init")
            return False
        
        try:
            Console.info("运行迁移...")
            
            from funboost.funboost_web_manager.user_models import migrate_database
            
            db_url = cls._get_db_url(db_path)
            migrate_database(db_url)
            
            Console.success("数据库迁移完成！")
            return True
            
        except Exception as e:
            Console.error(f"迁移失败: {e}")
            return False
    
    @classmethod
    def status(cls) -> bool:
        """查看数据库状态"""
        Console.title("数据库状态")
        
        db_path = Platform.get_database_path()
        
        if not db_path.exists():
            Console.error("数据库不存在")
            Console.hint("运行: python -m funboost.funboost_web_manager.cli db init")
            return False
        
        try:
            # 获取文件信息
            stat = db_path.stat()
            size_mb = stat.st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(stat.st_mtime)
            
            Console.info(f"数据库文件: {db_path}")
            Console.item(f"大小: {size_mb:.2f} MB")
            Console.item(f"修改时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 获取统计信息
            from funboost.funboost_web_manager.user_models import (
                get_session, WebManagerUser, Role, Permission
            )
            
            db_url = cls._get_db_url(db_path)
            session = get_session(db_url)
            
            try:
                user_count = session.query(WebManagerUser).count()
                role_count = session.query(Role).count()
                perm_count = session.query(Permission).count()
                
                Console.newline()
                Console.info("统计信息:")
                Console.item(f"用户数: {user_count}")
                Console.item(f"角色数: {role_count}")
                Console.item(f"权限数: {perm_count}", last=True)
                
            finally:
                session.close()
            
            return True
            
        except Exception as e:
            Console.error(f"获取状态失败: {e}")
            return False
    
    @classmethod
    def backup(cls, filename: Optional[str] = None) -> bool:
        """备份数据库"""
        Console.title("备份数据库")
        
        db_path = Platform.get_database_path()
        
        if not db_path.exists():
            Console.error("数据库不存在")
            return False
        
        try:
            backup_dir = Platform.get_backup_dir()
            
            if filename:
                backup_path = backup_dir / filename
            else:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = backup_dir / f"web_manager_users_{timestamp}.db"
            
            Console.info(f"备份到: {backup_path}")
            shutil.copy2(db_path, backup_path)
            
            Console.success("数据库备份完成！")
            return True
            
        except Exception as e:
            Console.error(f"备份失败: {e}")
            return False
    
    @classmethod
    def restore(cls, filename: str) -> bool:
        """恢复数据库"""
        Console.title("恢复数据库")
        
        backup_dir = Platform.get_backup_dir()
        backup_path = backup_dir / filename
        
        if not backup_path.exists():
            # 尝试作为完整路径
            backup_path = Path(filename)
            if not backup_path.exists():
                Console.error(f"备份文件不存在: {filename}")
                cls.list_backups()
                return False
        
        db_path = Platform.get_database_path()
        
        if db_path.exists():
            Console.warning("当前数据库将被覆盖")
            if not Console.confirm("是否继续？"):
                Console.info("已取消")
                return False
            
            # 先备份当前数据库
            Console.info("备份当前数据库...")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            current_backup = backup_dir / f"web_manager_users_before_restore_{timestamp}.db"
            shutil.copy2(db_path, current_backup)
            Console.item(f"已备份到: {current_backup}")
        
        try:
            Console.info(f"从 {backup_path} 恢复...")
            shutil.copy2(backup_path, db_path)
            
            Console.success("数据库恢复完成！")
            return True
            
        except Exception as e:
            Console.error(f"恢复失败: {e}")
            return False
    
    @classmethod
    def reset(cls) -> bool:
        """重置数据库"""
        Console.title("重置数据库")
        
        Console.warning("此操作将删除所有数据！")
        if not Console.confirm("确定要重置数据库吗？"):
            Console.info("已取消")
            return False
        
        db_path = Platform.get_database_path()
        
        if db_path.exists():
            # 备份
            Console.info("备份现有数据库...")
            cls.backup()
            
            # 删除
            Console.info("删除数据库...")
            try:
                from funboost.funboost_web_manager.user_models import reset_engine
                reset_engine()
            except Exception:
                pass
            cls._delete_db_files(db_path)
        
        # 重新初始化
        return cls.init()
    
    @classmethod
    def list_backups(cls) -> None:
        """列出所有备份"""
        backup_dir = Platform.get_backup_dir()
        
        backups = list(backup_dir.glob('*.db'))
        
        if not backups:
            Console.info("没有找到备份文件")
            return
        
        Console.info("可用的备份文件:")
        for backup in sorted(backups, reverse=True):
            stat = backup.stat()
            size_mb = stat.st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(stat.st_mtime)
            Console.item(f"{backup.name} ({size_mb:.2f} MB, {mtime.strftime('%Y-%m-%d %H:%M')})")

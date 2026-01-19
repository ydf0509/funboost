# -*- coding: utf-8 -*-
"""
认证服务模块

提供用户登录验证、账户锁定、状态检查等认证相关功能。
"""

import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from ..user_models import (
    get_session, WebManagerUser, LoginAttempt, AuditLog
)
from .password_service import PasswordService


class AuthService:
    """认证服务，处理登录验证和账户锁定"""
    
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    
    def __init__(self, db_url: Optional[str] = None):
        """
        初始化认证服务
        
        Args:
            db_url: 可选的数据库 URL
        """
        self.db_url = db_url
    
    def authenticate(self, user_name: str, password: str, ip_address: str, 
                    user_agent: str = None) -> Dict[str, Any]:
        """
        验证用户登录
        
        Args:
            user_name: 用户名
            password: 密码
            ip_address: 登录IP地址
            user_agent: 用户代理字符串
            
        Returns:
            Dict: {
                "success": bool,
                "user": dict|None,
                "error": str|None,
                "lockout_remaining": int|None,
                "force_password_change": bool
            }
        """
        session = get_session(self.db_url)
        try:
            # 1. 检查用户是否存在
            user = session.query(WebManagerUser).filter_by(user_name=user_name).first()
            if not user:
                self._record_login_attempt(session, None, user_name, ip_address, 
                                         user_agent, False)
                return {
                    "success": False,
                    "user": None,
                    "error": "用户名或密码错误",
                    "lockout_remaining": None,
                    "force_password_change": False
                }
            
            # 2. 检查账户状态
            if user.status == 'disabled':
                self._record_login_attempt(session, user.id, user_name, ip_address, 
                                         user_agent, False)
                return {
                    "success": False,
                    "user": None,
                    "error": "账户已被禁用",
                    "lockout_remaining": None,
                    "force_password_change": False
                }
            
            # 3. 检查是否被锁定（登录失败次数或手动锁定）
            is_locked, lockout_remaining = self._check_lockout(session, user)
            if is_locked:
                self._record_login_attempt(session, user.id, user_name, ip_address, 
                                         user_agent, False)
                if lockout_remaining:
                    error_msg = f"账户已被锁定，剩余时间：{lockout_remaining // 60}分{lockout_remaining % 60}秒"
                else:
                    error_msg = "账户已被锁定"
                return {
                    "success": False,
                    "user": None,
                    "error": error_msg,
                    "lockout_remaining": lockout_remaining,
                    "force_password_change": False
                }
            
            # 4. 验证密码
            if not PasswordService.verify_password(password, user.password):
                # 密码错误，增加失败计数
                user.failed_login_count += 1
                
                # 检查是否需要锁定
                if user.failed_login_count >= self.MAX_FAILED_ATTEMPTS:
                    user.locked_until = datetime.now() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
                
                session.commit()
                self._record_login_attempt(session, user.id, user_name, ip_address, 
                                         user_agent, False)
                
                remaining_attempts = max(0, self.MAX_FAILED_ATTEMPTS - user.failed_login_count)
                if remaining_attempts > 0:
                    error_msg = f"用户名或密码错误，还有 {remaining_attempts} 次尝试机会"
                else:
                    error_msg = f"密码错误次数过多，账户已被锁定 {self.LOCKOUT_DURATION_MINUTES} 分钟"
                
                return {
                    "success": False,
                    "user": None,
                    "error": error_msg,
                    "lockout_remaining": None,
                    "force_password_change": False
                }
            
            # 5. 密码验证成功，检查是否需要升级密码
            password_upgraded = False
            if not PasswordService.is_hashed(user.password):
                # 明文密码，自动升级为哈希
                user.password = PasswordService.hash_password(password)
                password_upgraded = True
            
            # 6. 清除失败计数和锁定状态
            user.failed_login_count = 0
            user.locked_until = None
            
            session.commit()
            
            # 7. 记录成功登录
            self._record_login_attempt(session, user.id, user_name, ip_address, 
                                     user_agent, True)
            
            # 8. 记录审计日志
            self._log_audit_event(session, "login_success", user_name, ip_address, 
                                 user_agent, {
                                     "password_upgraded": password_upgraded
                                 })
            
            return {
                "success": True,
                "user": user.to_dict(),
                "error": None,
                "lockout_remaining": None,
                "force_password_change": user.force_password_change
            }
            
        except Exception as e:
            session.rollback()
            # 记录系统错误的审计日志
            try:
                self._log_audit_event(session, "login_error", user_name, ip_address, 
                                     user_agent, {"error": str(e)})
            except:
                pass  # 避免审计日志记录失败影响主流程
            raise
        finally:
            session.close()
    
    def _check_lockout(self, session, user: WebManagerUser) -> Tuple[bool, Optional[int]]:
        """
        检查账户是否被锁定
        
        Args:
            session: 数据库会话
            user: 用户对象
            
        Returns:
            Tuple[bool, Optional[int]]: (是否锁定, 剩余秒数)
        """
        # 检查手动锁定状态
        if user.status == 'locked':
            return True, None
        
        # 检查登录失败锁定
        if user.locked_until and user.locked_until > datetime.now():
            remaining_seconds = int((user.locked_until - datetime.now()).total_seconds())
            return True, remaining_seconds
        
        # 如果锁定时间已过，清除锁定状态
        if user.locked_until and user.locked_until <= datetime.now():
            user.locked_until = None
            user.failed_login_count = 0
            session.commit()
        
        return False, None
    
    def _record_login_attempt(self, session, user_id: Optional[int], user_name: str, 
                             ip_address: str, user_agent: Optional[str], success: bool):
        """
        记录登录尝试
        
        Args:
            session: 数据库会话
            user_id: 用户ID（可能为空）
            user_name: 用户名
            ip_address: IP地址
            user_agent: 用户代理
            success: 是否成功
        """
        try:
            attempt = LoginAttempt(
                user_id=user_id,
                user_name=user_name,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success
            )
            session.add(attempt)
            session.commit()
        except Exception:
            # 登录尝试记录失败不应该影响主流程
            session.rollback()
    
    def _log_audit_event(self, session, event_type: str, user_name: str, 
                        ip_address: str, user_agent: Optional[str], 
                        details: Optional[Dict] = None):
        """
        记录审计事件
        
        Args:
            session: 数据库会话
            event_type: 事件类型
            user_name: 用户名
            ip_address: IP地址
            user_agent: 用户代理
            details: 事件详情
        """
        try:
            audit_log = AuditLog(
                event_type=event_type,
                user_name=user_name,
                ip_address=ip_address,
                user_agent=user_agent,
                details=json.dumps(details, ensure_ascii=False) if details else None
            )
            session.add(audit_log)
            session.commit()
        except Exception:
            # 审计日志记录失败不应该影响主流程
            session.rollback()
    
    def clear_failed_attempts(self, user_name: str) -> bool:
        """
        清除失败计数（登录成功或密码重置后调用）
        
        Args:
            user_name: 用户名
            
        Returns:
            bool: 是否成功清除
        """
        session = get_session(self.db_url)
        try:
            user = session.query(WebManagerUser).filter_by(user_name=user_name).first()
            if user:
                user.failed_login_count = 0
                user.locked_until = None
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
    
    def unlock_user(self, user_name: str, admin_user: str, ip_address: str, 
                   user_agent: str = None) -> bool:
        """
        管理员解锁用户
        
        Args:
            user_name: 要解锁的用户名
            admin_user: 管理员用户名
            ip_address: 操作IP
            user_agent: 用户代理
            
        Returns:
            bool: 是否成功解锁
        """
        session = get_session(self.db_url)
        try:
            user = session.query(WebManagerUser).filter_by(user_name=user_name).first()
            if user:
                user.failed_login_count = 0
                user.locked_until = None
                if user.status == 'locked':
                    user.status = 'active'
                
                session.commit()
                
                # 记录审计日志
                self._log_audit_event(session, "user_unlock", admin_user, ip_address, 
                                     user_agent, {"target_user": user_name})
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
    
    def lock_user(self, user_name: str, admin_user: str, ip_address: str, 
                 user_agent: str = None) -> bool:
        """
        管理员锁定用户
        
        Args:
            user_name: 要锁定的用户名
            admin_user: 管理员用户名
            ip_address: 操作IP
            user_agent: 用户代理
            
        Returns:
            bool: 是否成功锁定
        """
        session = get_session(self.db_url)
        try:
            user = session.query(WebManagerUser).filter_by(user_name=user_name).first()
            if user:
                user.status = 'locked'
                session.commit()
                
                # 记录审计日志
                self._log_audit_event(session, "user_lock", admin_user, ip_address, 
                                     user_agent, {"target_user": user_name})
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_login_attempts(self, user_name: str = None, limit: int = 100) -> list:
        """
        获取登录尝试记录
        
        Args:
            user_name: 可选的用户名过滤
            limit: 返回记录数限制
            
        Returns:
            list: 登录尝试记录列表
        """
        session = get_session(self.db_url)
        try:
            query = session.query(LoginAttempt)
            if user_name:
                query = query.filter_by(user_name=user_name)
            
            attempts = query.order_by(LoginAttempt.created_at.desc()).limit(limit).all()
            return [attempt.to_dict() for attempt in attempts]
        finally:
            session.close()
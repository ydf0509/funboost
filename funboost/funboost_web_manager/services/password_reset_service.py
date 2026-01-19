# -*- coding: utf-8 -*-
"""
密码重置服务模块

提供密码重置令牌生成、验证和密码重置功能。
"""

import json
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from ..user_models import (
    get_session, WebManagerUser, PasswordResetToken, AuditLog
)
from .password_service import PasswordService


class PasswordResetService:
    """密码重置服务"""
    
    TOKEN_EXPIRY_MINUTES = 30
    
    def __init__(self, db_url: Optional[str] = None):
        """
        初始化密码重置服务
        
        Args:
            db_url: 可选的数据库 URL
        """
        self.db_url = db_url
    
    def request_reset(self, email: str, ip_address: str, user_agent: str = None) -> Optional[str]:
        """
        请求密码重置
        
        Args:
            email: 用户邮箱
            ip_address: 请求IP地址
            user_agent: 用户代理字符串
            
        Returns:
            Optional[str]: 重置令牌（用于发送邮件）或 None（用户不存在）
        """
        session = get_session(self.db_url)
        try:
            # 1. 查找用户
            user = session.query(WebManagerUser).filter_by(email=email).first()
            if not user:
                # 记录审计日志（不存在的邮箱）
                self._log_audit_event(session, "password_reset_request_failed", None, 
                                     ip_address, user_agent, {"email": email, "reason": "email_not_found"})
                return None
            
            # 2. 生成唯一令牌
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(minutes=self.TOKEN_EXPIRY_MINUTES)
            
            # 3. 使之前的令牌失效（如果存在）
            session.query(PasswordResetToken).filter_by(
                user_id=user.id, used=False
            ).update({"used": True})
            
            # 4. 保存新令牌
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=expires_at
            )
            session.add(reset_token)
            session.commit()
            
            # 5. 记录审计日志
            self._log_audit_event(session, "password_reset_request", user.user_name, 
                                 ip_address, user_agent, {"email": email})
            
            return token
            
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def validate_token(self, token: str) -> Optional[int]:
        """
        验证令牌
        
        Args:
            token: 重置令牌
            
        Returns:
            Optional[int]: 用户ID或None（令牌无效）
        """
        if not token:
            return None
            
        session = get_session(self.db_url)
        try:
            reset_token = session.query(PasswordResetToken).filter_by(
                token=token, used=False
            ).first()
            
            if not reset_token:
                return None
            
            # 检查是否过期
            if reset_token.expires_at < datetime.now():
                return None
            
            return reset_token.user_id
            
        finally:
            session.close()
    
    def reset_password(self, token: str, new_password: str, ip_address: str, 
                      user_agent: str = None) -> Tuple[bool, str]:
        """
        重置密码
        
        Args:
            token: 重置令牌
            new_password: 新密码
            ip_address: 操作IP地址
            user_agent: 用户代理字符串
            
        Returns:
            Tuple[bool, str]: (成功, 消息)
        """
        session = get_session(self.db_url)
        try:
            # 1. 验证令牌
            reset_token = session.query(PasswordResetToken).filter_by(
                token=token, used=False
            ).first()
            
            if not reset_token:
                return False, "重置令牌无效或已过期"
            
            # 检查是否过期
            if reset_token.expires_at < datetime.now():
                return False, "重置令牌已过期"
            
            # 2. 验证密码强度
            is_valid, errors = PasswordService.validate_strength(new_password)
            if not is_valid:
                return False, "密码强度不符合要求：" + "；".join(errors)
            
            # 3. 获取用户
            user = session.query(WebManagerUser).filter_by(id=reset_token.user_id).first()
            if not user:
                return False, "用户不存在"
            
            # 4. 更新密码（哈希）
            user.password = PasswordService.hash_password(new_password)
            
            # 5. 清除登录失败计数和锁定状态
            user.failed_login_count = 0
            user.locked_until = None
            if user.status == 'locked':
                user.status = 'active'
            
            # 6. 使令牌失效
            reset_token.used = True
            
            session.commit()
            
            # 7. 记录审计日志
            self._log_audit_event(session, "password_reset_complete", user.user_name, 
                                 ip_address, user_agent, {"email": user.email})
            
            return True, "密码重置成功"
            
        except Exception as e:
            session.rollback()
            return False, f"密码重置失败：{str(e)}"
        finally:
            session.close()
    
    def cleanup_expired_tokens(self) -> int:
        """
        清理过期的重置令牌
        
        Returns:
            int: 清理的令牌数量
        """
        session = get_session(self.db_url)
        try:
            # 删除过期的令牌
            expired_count = session.query(PasswordResetToken).filter(
                PasswordResetToken.expires_at < datetime.now()
            ).delete()
            
            session.commit()
            return expired_count
            
        except Exception:
            session.rollback()
            return 0
        finally:
            session.close()
    
    def get_user_by_token(self, token: str) -> Optional[dict]:
        """
        根据令牌获取用户信息（用于显示重置页面）
        
        Args:
            token: 重置令牌
            
        Returns:
            Optional[dict]: 用户信息或None
        """
        user_id = self.validate_token(token)
        if not user_id:
            return None
            
        session = get_session(self.db_url)
        try:
            user = session.query(WebManagerUser).filter_by(id=user_id).first()
            if user:
                return {
                    "user_name": user.user_name,
                    "email": user.email
                }
            return None
        finally:
            session.close()
    
    def _log_audit_event(self, session, event_type: str, user_name: Optional[str], 
                        ip_address: str, user_agent: Optional[str], 
                        details: Optional[dict] = None):
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
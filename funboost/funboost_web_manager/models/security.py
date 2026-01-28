# -*- coding: utf-8 -*-
# @Author  : kiro
# @Time    : 2026/1/13
"""
Security models module.

This module contains security-related models for the Web Manager,
including password reset tokens.

Models:
    - PasswordResetToken: Password reset token model for secure password recovery

Dependencies:
    - models.base.Base: SQLAlchemy declarative base
    - Forward reference to WebManagerUser for foreign key relationship
"""

from datetime import datetime
from typing import Dict, Any

from .base import Base, Column, Integer, String, DateTime, Boolean, ForeignKey


class PasswordResetToken(Base):
    """密码重置令牌模型
    
    Attributes:
        id: 自增主键
        user_id: 用户ID（外键）
        token: 重置令牌，唯一且带索引
        expires_at: 过期时间
        used: 是否已使用
        created_at: 创建时间
    """
    __tablename__ = 'password_reset_tokens'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('web_manager_users.id'), nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token': self.token,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'used': self.used,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self) -> str:
        return f"<PasswordResetToken(user_id={self.user_id}, used={self.used}, expires={self.expires_at})>"

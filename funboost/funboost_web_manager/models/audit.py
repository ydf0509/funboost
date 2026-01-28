# -*- coding: utf-8 -*-
# @Author  : kiro
# @Time    : 2026/1/13
"""
Audit models module.

This module contains models for tracking login attempts and system actions.
These models are used for security auditing and compliance purposes.

Models:
    - LoginAttempt: Tracks login attempts (successful and failed)
    - AuditLog: Records system events and user actions

Exports:
    - LoginAttempt: Login attempt tracking model
    - AuditLog: Audit log model
"""

from datetime import datetime
from typing import Dict, Any

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey

from .base import Base


class LoginAttempt(Base):
    """登录尝试记录模型
    
    Attributes:
        id: 自增主键
        user_id: 用户ID（外键，可为空，因为可能是不存在的用户名）
        user_name: 尝试登录的用户名
        ip_address: 登录IP地址
        user_agent: 用户代理字符串
        success: 登录是否成功
        created_at: 创建时间（带索引）
    """
    __tablename__ = 'login_attempts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('web_manager_users.id'), nullable=True)
    user_name = Column(String(64), nullable=False)  # 记录尝试的用户名
    ip_address = Column(String(45), nullable=False)  # 支持 IPv6
    user_agent = Column(String(256), nullable=True)
    success = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'success': self.success,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self) -> str:
        return f"<LoginAttempt(user='{self.user_name}', success={self.success}, ip='{self.ip_address}')>"


class AuditLog(Base):
    """审计日志模型
    
    Attributes:
        id: 自增主键
        event_type: 事件类型（带索引）
        user_name: 用户名（带索引，可为空）
        ip_address: IP地址
        user_agent: 用户代理字符串
        details: 事件详情（JSON格式）
        created_at: 创建时间（带索引）
    """
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(64), nullable=False, index=True)
    user_name = Column(String(64), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(256), nullable=True)
    details = Column(Text, nullable=True)  # JSON 格式
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'event_type': self.event_type,
            'user_name': self.user_name,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self) -> str:
        return f"<AuditLog(event='{self.event_type}', user='{self.user_name}', time={self.created_at})>"

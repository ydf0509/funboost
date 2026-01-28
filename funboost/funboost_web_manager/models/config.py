# -*- coding: utf-8 -*-
# @Author  : kiro
# @Time    : 2026/1/18
"""
Configuration models module.

This module contains system configuration models for the Web Manager,
including email configuration and general system settings.

Models:
    - EmailConfig: Email/SMTP configuration model
    - SystemConfig: General system configuration key-value store

Dependencies:
    - models.base.Base: SQLAlchemy declarative base
"""

from datetime import datetime
from typing import Dict, Any

from .base import Base, Column, Integer, String, DateTime, Boolean


class EmailConfig(Base):
    """邮件配置模型
    
    Attributes:
        id: 自增主键
        smtp_host: SMTP服务器地址
        smtp_port: SMTP端口
        smtp_username: SMTP用户名
        smtp_password: SMTP密码（加密存储）
        use_tls: 是否使用TLS
        use_ssl: 是否使用SSL
        sender_name: 发件人名称
        sender_email: 发件人邮箱
        updated_at: 更新时间
    """
    __tablename__ = 'email_config'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    smtp_host = Column(String(128), nullable=False)
    smtp_port = Column(Integer, default=587)
    smtp_username = Column(String(128), nullable=True)
    smtp_password = Column(String(256), nullable=True)  # 加密存储
    use_tls = Column(Boolean, default=True)
    use_ssl = Column(Boolean, default=False)
    sender_name = Column(String(64), nullable=True)
    sender_email = Column(String(128), nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'smtp_host': self.smtp_host,
            'smtp_port': self.smtp_port,
            'smtp_username': self.smtp_username,
            'smtp_password': '***' if self.smtp_password else None,  # 不暴露密码
            'use_tls': self.use_tls,
            'use_ssl': self.use_ssl,
            'sender_name': self.sender_name,
            'sender_email': self.sender_email,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self) -> str:
        return f"<EmailConfig(host='{self.smtp_host}', port={self.smtp_port})>"


class SystemConfig(Base):
    """系统配置模型
    
    Attributes:
        id: 自增主键
        key: 配置键，唯一
        value: 配置值
        description: 配置描述
        updated_at: 更新时间
    """
    __tablename__ = 'system_config'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(64), unique=True, nullable=False)
    value = Column(String(256), nullable=True)
    description = Column(String(256), nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self) -> str:
        return f"<SystemConfig(key='{self.key}', value='{self.value}')>"

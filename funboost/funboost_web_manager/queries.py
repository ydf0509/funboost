# -*- coding: utf-8 -*-
# @Author  : kiro
# @Time    : 2026/1/18
"""
Query helper functions module.

This module provides common query helper functions for the Web Manager application.

Functions:
    - query_user_by_name(user_name, db_url): Query user by username
    - query_user_by_id(user_id, db_url): Query user by ID (actually username for compatibility)
    - add_user(...): Add new user
    - count_users(db_url): Count total users

Dependencies:
    - database.get_session: For database session management
    - models.WebManagerUser: User model
    - services.password_service.PasswordService: For password hashing
"""

from typing import Optional, Dict, Any
from sqlalchemy.exc import IntegrityError

from .database import get_session
from .models import WebManagerUser


def query_user_by_name(user_name: str, db_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """根据用户名查询用户
    
    Args:
        user_name: 要查询的用户名
        db_url: 可选的数据库 URL，如果不提供则从配置获取
        
    Returns:
        用户字典（包含 id、user_name、password），如果不存在返回 None
    """
    session = get_session(db_url)
    try:
        user = session.query(WebManagerUser).filter_by(user_name=user_name).first()
        return user.to_dict() if user else None
    finally:
        session.close()


def query_user_by_id(user_id: str, db_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """根据用户ID查询用户
    
    注意：为保持与原有 Flask-Login 集成兼容，user_id 实际上是 user_name
    
    Args:
        user_id: 用户ID（即 user_name）
        db_url: 可选的数据库 URL，如果不提供则从配置获取
        
    Returns:
        用户字典（包含 id、user_name、password），如果不存在返回 None
    """
    return query_user_by_name(user_id, db_url)


def add_user(user_name: str, password: str, email: str = None, 
             status: str = 'active', force_password_change: bool = False,
             db_url: Optional[str] = None) -> WebManagerUser:
    """添加新用户
    
    Args:
        user_name: 用户名
        password: 密码（如果不是哈希格式，将自动哈希）
        email: 邮箱地址
        status: 用户状态，默认为 'active'
        force_password_change: 是否强制修改密码，默认为 False
        db_url: 可选的数据库 URL，如果不提供则从配置获取
        
    Returns:
        创建的用户对象
        
    Raises:
        IntegrityError: 如果用户名已存在
    """
    # 导入密码服务
    from funboost.funboost_web_manager.services.password_service import PasswordService
    
    session = get_session(db_url)
    try:
        # 如果密码不是哈希格式，进行哈希
        if not PasswordService.is_hashed(password):
            password = PasswordService.hash_password(password)
        
        user = WebManagerUser(
            user_name=user_name, 
            password=password,
            email=email,
            status=status,
            force_password_change=force_password_change
        )
        session.add(user)
        session.commit()
        # 刷新以获取自动生成的字段
        session.refresh(user)
        return user
    except IntegrityError:
        session.rollback()
        raise
    finally:
        session.close()


def count_users(db_url: Optional[str] = None) -> int:
    """统计用户数量
    
    Args:
        db_url: 可选的数据库 URL，如果不提供则从配置获取
        
    Returns:
        用户总数
    """
    session = get_session(db_url)
    try:
        return session.query(WebManagerUser).count()
    finally:
        session.close()

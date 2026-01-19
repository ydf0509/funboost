# -*- coding: utf-8 -*-
# @Author  : kiro
# @Time    : 2026/1/18
"""
Database connection management module.

This module handles database engine creation, session management,
and connection pooling for the Web Manager application.

Functions:
    - get_db_url(): Get database URL from configuration
    - get_engine(db_url): Get or create SQLAlchemy engine
    - get_session(db_url): Create new database session
    - reset_engine(): Reset engine cache (for testing)
    - init_db(db_url): Create all database tables

Thread Safety:
    All functions are thread-safe using _engine_lock.

Dependencies:
    - models.Base: For table creation
    - funboost_config: For database URL configuration
"""

from threading import Lock
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base


# 数据库引擎和会话工厂（支持多个数据库URL）
_engines = {}  # 存储不同URL对应的引擎
_session_factories = {}  # 存储不同URL对应的会话工厂
_engine_lock = Lock()


def get_db_url() -> str:
    """获取数据库 URL
    
    优先从 funboost_config.py 的 FunboostCommonConfig 读取 WEB_MANAGER_DB_URL，
    如果读取失败则使用默认的 SQLite 数据库路径。
    
    Returns:
        数据库连接 URL 字符串
    """
    try:
        from funboost.funboost_config_deafult import FunboostCommonConfig
        return getattr(FunboostCommonConfig, 'WEB_MANAGER_DB_URL', 
                      'sqlite:///./web_manager_users.db')
    except Exception:
        return 'sqlite:///./web_manager_users.db'


def get_engine(db_url: Optional[str] = None):
    """获取数据库引擎（支持多个数据库URL）
    
    Args:
        db_url: 可选的数据库 URL，如果不提供则从配置获取
        
    Returns:
        SQLAlchemy Engine 实例
    """
    global _engines
    url = db_url or get_db_url()
    
    with _engine_lock:
        if url not in _engines:
            # SQLite 需要特殊的连接参数
            connect_args = {}
            if url.startswith('sqlite'):
                connect_args = {
                    'timeout': 30,  # 等待锁的超时时间（秒）
                    'check_same_thread': False  # 允许多线程访问
                }
            _engines[url] = create_engine(
                url,
                pool_pre_ping=True,  # 连接池健康检查
                echo=False,
                connect_args=connect_args
            )
    return _engines[url]


def get_session(db_url: Optional[str] = None):
    """获取数据库会话
    
    Args:
        db_url: 可选的数据库 URL，如果不提供则从配置获取
        
    Returns:
        SQLAlchemy Session 实例
    """
    global _session_factories
    url = db_url or get_db_url()
    
    # 先获取 engine
    engine = get_engine(url)
    
    with _engine_lock:
        if url not in _session_factories:
            _session_factories[url] = sessionmaker(bind=engine)
    
    return _session_factories[url]()


def reset_engine():
    """重置数据库引擎和会话工厂（主要用于测试）"""
    global _engines, _session_factories
    with _engine_lock:
        for engine in _engines.values():
            engine.dispose()
        _engines.clear()
        _session_factories.clear()


def init_db(db_url: Optional[str] = None) -> None:
    """初始化数据库表
    
    如果表不存在则创建。
    
    Args:
        db_url: 可选的数据库 URL，如果不提供则从配置获取
    """
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)

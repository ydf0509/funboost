# -*- coding: utf-8 -*-
"""
审计服务模块

提供审计事件记录、查询和日志清理功能。
"""

import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List

from ..user_models import get_session, AuditLog, SystemConfig


class AuditEventType(Enum):
    """审计事件类型枚举"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_REQUEST_FAILED = "password_reset_request_failed"
    PASSWORD_RESET_COMPLETE = "password_reset_complete"
    PASSWORD_RESET_BY_ADMIN = "password_reset_by_admin"
    PASSWORD_CHANGE = "password_change"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_STATUS_CHANGE = "user_status_change"
    USER_LOCK = "user_lock"
    USER_UNLOCK = "user_unlock"
    USER_ROLE_ASSIGN = "user_role_assign"
    USER_ROLE_REMOVE = "user_role_remove"
    ROLE_CREATE = "role_create"
    ROLE_UPDATE = "role_update"
    ROLE_DELETE = "role_delete"
    CONFIG_UPDATE = "config_update"
    EMAIL_CONFIG_UPDATE = "email_config_update"
    LOGIN_ERROR = "login_error"
    # 权限变更审计事件类型 (Requirements 13.1, 13.2, 13.3)
    PERMISSION_CHANGE = "permission_change"  # 角色权限变更
    ROLE_PERMISSION_ADD = "role_permission_add"  # 角色添加权限
    ROLE_PERMISSION_REMOVE = "role_permission_remove"  # 角色移除权限


class AuditService:
    """审计日志服务"""
    
    DEFAULT_RETENTION_DAYS = 30
    
    def __init__(self, db_url: Optional[str] = None):
        """
        初始化审计服务
        
        Args:
            db_url: 可选的数据库 URL
        """
        self.db_url = db_url
    
    def log(self, event_type: AuditEventType, user_name: Optional[str] = None, 
            ip_address: Optional[str] = None, user_agent: Optional[str] = None, 
            details: Optional[Dict] = None) -> bool:
        """
        记录审计事件
        
        Args:
            event_type: 事件类型
            user_name: 用户名（可选）
            ip_address: IP地址（可选）
            user_agent: 用户代理（可选）
            details: 事件详情（可选）
            
        Returns:
            bool: 是否记录成功
        """
        session = get_session(self.db_url)
        try:
            audit_log = AuditLog(
                event_type=event_type.value if isinstance(event_type, AuditEventType) else event_type,
                user_name=user_name,
                ip_address=ip_address,
                user_agent=user_agent,
                details=json.dumps(details, ensure_ascii=False) if details else None
            )
            session.add(audit_log)
            session.commit()
            return True
            
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
    
    def query(self, event_type: Optional[str] = None, user_name: Optional[str] = None,
              start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
              page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """
        查询审计日志
        
        Args:
            event_type: 事件类型过滤（可选）
            user_name: 用户名过滤（可选）
            start_date: 开始时间过滤（可选）
            end_date: 结束时间过滤（可选）
            page: 页码（从1开始）
            page_size: 每页大小
            
        Returns:
            Dict: {"logs": List[Dict], "total": int, "page": int, "page_size": int}
        """
        session = get_session(self.db_url)
        try:
            # 构建查询
            query = session.query(AuditLog)
            
            # 应用过滤条件
            if event_type:
                query = query.filter(AuditLog.event_type == event_type)
            
            if user_name:
                query = query.filter(AuditLog.user_name == user_name)
            
            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)
            
            # 计算总数
            total = query.count()
            
            # 分页查询（按时间倒序）
            offset = (page - 1) * page_size
            logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size).all()
            
            # 转换为字典格式
            log_dicts = []
            for log in logs:
                log_dict = log.to_dict()
                # 解析 details JSON
                if log_dict['details']:
                    try:
                        log_dict['details'] = json.loads(log_dict['details'])
                    except (json.JSONDecodeError, TypeError):
                        pass  # 保持原始字符串
                log_dicts.append(log_dict)
            
            return {
                "logs": log_dicts,
                "total": total,
                "page": page,
                "page_size": page_size
            }
            
        finally:
            session.close()
    
    def get_event_types(self) -> List[str]:
        """
        获取所有事件类型
        
        Returns:
            List[str]: 事件类型列表
        """
        session = get_session(self.db_url)
        try:
            # 从数据库获取实际存在的事件类型
            result = session.query(AuditLog.event_type).distinct().all()
            return [row[0] for row in result if row[0]]
        finally:
            session.close()
    
    def get_user_activity(self, user_name: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取用户最近活动
        
        Args:
            user_name: 用户名
            days: 查询天数
            
        Returns:
            List[Dict]: 用户活动列表
        """
        start_date = datetime.now() - timedelta(days=days)
        result = self.query(
            user_name=user_name,
            start_date=start_date,
            page_size=100
        )
        return result["logs"]
    
    def get_login_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        获取登录统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            Dict: 登录统计信息
        """
        session = get_session(self.db_url)
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # 成功登录次数
            success_count = session.query(AuditLog).filter(
                AuditLog.event_type == AuditEventType.LOGIN_SUCCESS.value,
                AuditLog.created_at >= start_date
            ).count()
            
            # 失败登录次数
            failed_count = session.query(AuditLog).filter(
                AuditLog.event_type == AuditEventType.LOGIN_FAILED.value,
                AuditLog.created_at >= start_date
            ).count()
            
            # 独立用户数（成功登录的）
            unique_users = session.query(AuditLog.user_name).filter(
                AuditLog.event_type == AuditEventType.LOGIN_SUCCESS.value,
                AuditLog.created_at >= start_date,
                AuditLog.user_name.isnot(None)
            ).distinct().count()
            
            return {
                "period_days": days,
                "success_logins": success_count,
                "failed_logins": failed_count,
                "unique_users": unique_users,
                "total_attempts": success_count + failed_count
            }
            
        finally:
            session.close()
    
    def cleanup_old_logs(self, retention_days: Optional[int] = None) -> int:
        """
        清理过期日志
        
        Args:
            retention_days: 保留天数，如果不提供则从配置获取
            
        Returns:
            int: 清理的日志条数
        """
        if retention_days is None:
            retention_days = self.get_retention_days()
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        session = get_session(self.db_url)
        try:
            # 删除过期日志
            deleted_count = session.query(AuditLog).filter(
                AuditLog.created_at < cutoff_date
            ).delete()
            
            session.commit()
            
            # 记录清理操作
            if deleted_count > 0:
                self.log(
                    AuditEventType.CONFIG_UPDATE,
                    user_name="system",
                    details={
                        "action": "audit_log_cleanup",
                        "deleted_count": deleted_count,
                        "retention_days": retention_days,
                        "cutoff_date": cutoff_date.isoformat()
                    }
                )
            
            return deleted_count
            
        except Exception:
            session.rollback()
            return 0
        finally:
            session.close()
    
    def get_retention_days(self) -> int:
        """
        获取日志保留天数配置
        
        Returns:
            int: 保留天数
        """
        session = get_session(self.db_url)
        try:
            config = session.query(SystemConfig).filter_by(
                key="audit_retention_days"
            ).first()
            
            if config and config.value:
                try:
                    return int(config.value)
                except (ValueError, TypeError):
                    pass
            
            return self.DEFAULT_RETENTION_DAYS
            
        finally:
            session.close()
    
    def set_retention_days(self, days: int, admin_user: str = None, 
                          ip_address: str = None, user_agent: str = None) -> bool:
        """
        设置日志保留天数
        
        Args:
            days: 保留天数
            admin_user: 操作的管理员用户名
            ip_address: 操作IP
            user_agent: 用户代理
            
        Returns:
            bool: 是否设置成功
        """
        if days < 1:
            return False
        
        session = get_session(self.db_url)
        try:
            config = session.query(SystemConfig).filter_by(
                key="audit_retention_days"
            ).first()
            
            old_value = None
            if config:
                old_value = config.value
                config.value = str(days)
            else:
                config = SystemConfig(
                    key="audit_retention_days",
                    value=str(days),
                    description="审计日志保留天数"
                )
                session.add(config)
            
            session.commit()
            
            # 记录配置变更
            if admin_user:
                self.log(
                    AuditEventType.CONFIG_UPDATE,
                    user_name=admin_user,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details={
                        "config_key": "audit_retention_days",
                        "old_value": old_value,
                        "new_value": str(days)
                    }
                )
            
            return True
            
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_system_activity_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        获取系统活动概览
        
        Args:
            days: 统计天数
            
        Returns:
            Dict: 系统活动概览
        """
        session = get_session(self.db_url)
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # 按事件类型统计
            event_stats = {}
            for event_type in AuditEventType:
                count = session.query(AuditLog).filter(
                    AuditLog.event_type == event_type.value,
                    AuditLog.created_at >= start_date
                ).count()
                if count > 0:
                    event_stats[event_type.value] = count
            
            # 最活跃用户
            active_users = session.query(
                AuditLog.user_name,
                session.query(AuditLog).filter(
                    AuditLog.user_name == AuditLog.user_name,
                    AuditLog.created_at >= start_date
                ).count().label('activity_count')
            ).filter(
                AuditLog.created_at >= start_date,
                AuditLog.user_name.isnot(None)
            ).group_by(AuditLog.user_name).order_by(
                session.text('activity_count DESC')
            ).limit(10).all()
            
            return {
                "period_days": days,
                "event_stats": event_stats,
                "active_users": [
                    {"user_name": user[0], "activity_count": user[1]} 
                    for user in active_users
                ],
                "total_events": sum(event_stats.values())
            }
            
        finally:
            session.close()

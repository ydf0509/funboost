# -*- coding: utf-8 -*-
"""
角色服务模块

提供角色的增删改查和权限分配功能。
"""

import json
from typing import List, Dict, Any, Optional

from ..user_models import (
    get_session, Role, Permission, WebManagerUser, AuditLog, Project
)


class RoleService:
    """角色管理服务"""
    
    def __init__(self, db_url: Optional[str] = None):
        """
        初始化角色服务
        
        Args:
            db_url: 可选的数据库 URL
        """
        self.db_url = db_url
    
    def create_role(self, name: str, description: str = None, 
                   permission_codes: List[str] = None, project_ids: List[int] = None,
                   admin_user: str = None, ip_address: str = None, 
                   user_agent: str = None) -> Dict[str, Any]:
        """
        创建新角色
        
        Args:
            name: 角色名称
            description: 角色描述
            permission_codes: 权限代码列表
            project_ids: 关联的项目ID列表
            admin_user: 操作的管理员用户名
            ip_address: 操作IP
            user_agent: 用户代理
            
        Returns:
            Dict: {"success": bool, "role": dict|None, "error": str|None}
            
        Requirements:
            - 13.1: THE Permission_System SHALL log all permission changes with operator, 
                    timestamp, and change details
            - 13.2: THE Audit_Log SHALL record added and removed permissions for each change
        """
        import logging
        
        logger = logging.getLogger('funboost.permission_audit')
        
        session = get_session(self.db_url)
        try:
            # 检查角色名是否已存在
            existing = session.query(Role).filter_by(name=name).first()
            if existing:
                return {
                    "success": False,
                    "role": None,
                    "error": f"角色名 '{name}' 已存在"
                }
            
            # 创建角色
            role = Role(
                name=name,
                description=description,
                is_builtin=False
            )
            
            # 分配权限
            if permission_codes:
                permissions = session.query(Permission).filter(
                    Permission.code.in_(permission_codes)
                ).all()
                role.permissions = permissions
            
            # 分配项目
            if project_ids:
                projects = session.query(Project).filter(
                    Project.id.in_(project_ids)
                ).all()
                role.projects = projects
            
            session.add(role)
            session.commit()
            session.refresh(role)
            
            # 记录权限变更审计日志 (Requirements 13.1, 13.2)
            if admin_user and permission_codes:
                # 记录到日志系统
                logger.info(
                    f"Permission change: operator={admin_user}, role={name}, "
                    f"added={permission_codes}, removed=[]"
                )
                
                # 记录详细的权限变更审计日志（创建角色时所有权限都是新增的）
                self._log_permission_change_audit(
                    session, admin_user, name, 
                    permission_codes, [],  # 创建时没有移除的权限
                    ip_address, user_agent
                )
            
            # 记录角色创建审计日志
            if admin_user:
                self._log_audit_event(session, "role_create", admin_user, ip_address, 
                                     user_agent, {
                                         "role_name": name,
                                         "permissions": permission_codes or [],
                                         "project_ids": project_ids or []
                                     })
            
            return {
                "success": True,
                "role": role.to_dict(),
                "error": None
            }
            
        except Exception as e:
            session.rollback()
            return {
                "success": False,
                "role": None,
                "error": f"创建角色失败：{str(e)}"
            }
        finally:
            session.close()
    
    def update_role(self, role_id: int, name: str = None, description: str = None,
                   permission_codes: List[str] = None, project_ids: List[int] = None,
                   admin_user: str = None, ip_address: str = None, 
                   user_agent: str = None) -> Dict[str, Any]:
        """
        更新角色
        
        Args:
            role_id: 角色ID
            name: 新角色名称（可选）
            description: 新角色描述（可选）
            permission_codes: 新权限代码列表（可选）
            project_ids: 新关联的项目ID列表（可选）
            admin_user: 操作的管理员用户名
            ip_address: 操作IP
            user_agent: 用户代理
            
        Returns:
            Dict: {"success": bool, "role": dict|None, "error": str|None}
            
        Requirements:
            - 13.1: THE Permission_System SHALL log all permission changes with operator, 
                    timestamp, and change details
            - 13.2: THE Audit_Log SHALL record added and removed permissions for each change
        """
        import logging
        
        logger = logging.getLogger('funboost.permission_audit')
        
        session = get_session(self.db_url)
        try:
            role = session.query(Role).filter_by(id=role_id).first()
            if not role:
                return {
                    "success": False,
                    "role": None,
                    "error": "角色不存在"
                }
            
            old_data = role.to_dict()
            
            # 记录旧权限列表（用于计算变更）
            old_permission_codes = {perm.code for perm in role.permissions}
            old_project_ids = {p.id for p in role.projects} if role.projects else set()
            
            # 更新基本信息
            if name is not None:
                # 检查新名称是否已存在
                existing = session.query(Role).filter(
                    Role.name == name, Role.id != role_id
                ).first()
                if existing:
                    return {
                        "success": False,
                        "role": None,
                        "error": f"角色名 '{name}' 已存在"
                    }
                role.name = name
            
            if description is not None:
                role.description = description
            
            # 更新权限
            added_permissions = []
            removed_permissions = []
            
            if permission_codes is not None:
                new_permission_codes = set(permission_codes)
                
                # 计算添加和移除的权限 (Requirement 13.2)
                added_permissions = list(new_permission_codes - old_permission_codes)
                removed_permissions = list(old_permission_codes - new_permission_codes)
                
                permissions = session.query(Permission).filter(
                    Permission.code.in_(permission_codes)
                ).all()
                role.permissions = permissions
            
            # 更新项目关联
            if project_ids is not None:
                projects = session.query(Project).filter(
                    Project.id.in_(project_ids)
                ).all()
                role.projects = projects
            
            session.commit()
            session.refresh(role)
            
            # 记录权限变更审计日志 (Requirements 13.1, 13.2)
            if admin_user and (added_permissions or removed_permissions):
                # 记录到日志系统
                logger.info(
                    f"Permission change: operator={admin_user}, role={role.name}, "
                    f"added={added_permissions}, removed={removed_permissions}"
                )
                
                # 记录详细的权限变更审计日志
                self._log_permission_change_audit(
                    session, admin_user, role.name, 
                    added_permissions, removed_permissions,
                    ip_address, user_agent
                )
            
            # 记录角色更新审计日志
            if admin_user:
                new_project_ids = {p.id for p in role.projects} if role.projects else set()
                self._log_audit_event(session, "role_update", admin_user, ip_address, 
                                     user_agent, {
                                         "role_id": role_id,
                                         "old_data": old_data,
                                         "new_data": role.to_dict(),
                                         "permission_changes": {
                                             "added": added_permissions,
                                             "removed": removed_permissions
                                         },
                                         "project_changes": {
                                             "added": list(new_project_ids - old_project_ids),
                                             "removed": list(old_project_ids - new_project_ids)
                                         }
                                     })
            
            return {
                "success": True,
                "role": role.to_dict(),
                "error": None
            }
            
        except Exception as e:
            session.rollback()
            return {
                "success": False,
                "role": None,
                "error": f"更新角色失败：{str(e)}"
            }
        finally:
            session.close()
    
    def delete_role(self, role_id: int, admin_user: str = None,
                   ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        删除角色
        
        Args:
            role_id: 角色ID
            admin_user: 操作的管理员用户名
            ip_address: 操作IP
            user_agent: 用户代理
            
        Returns:
            Dict: {"success": bool, "error": str|None}
        """
        session = get_session(self.db_url)
        try:
            role = session.query(Role).filter_by(id=role_id).first()
            if not role:
                return {
                    "success": False,
                    "error": "角色不存在"
                }
            
            # 检查是否为内置角色
            if role.is_builtin:
                return {
                    "success": False,
                    "error": "内置角色不可删除"
                }
            
            # 检查是否有用户使用此角色
            user_count = session.query(WebManagerUser).filter(
                WebManagerUser.roles.contains(role)
            ).count()
            
            if user_count > 0:
                return {
                    "success": False,
                    "error": f"无法删除角色，还有 {user_count} 个用户使用此角色"
                }
            
            role_data = role.to_dict()
            session.delete(role)
            session.commit()
            
            # 记录审计日志
            if admin_user:
                self._log_audit_event(session, "role_delete", admin_user, ip_address, 
                                     user_agent, {"deleted_role": role_data})
            
            return {
                "success": True,
                "error": None
            }
            
        except Exception as e:
            session.rollback()
            return {
                "success": False,
                "error": f"删除角色失败：{str(e)}"
            }
        finally:
            session.close()
    
    def get_role(self, role_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单个角色
        
        Args:
            role_id: 角色ID
            
        Returns:
            Optional[Dict]: 角色信息或None
        """
        session = get_session(self.db_url)
        try:
            role = session.query(Role).filter_by(id=role_id).first()
            return role.to_dict() if role else None
        finally:
            session.close()
    
    def get_role_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        根据名称获取角色
        
        Args:
            name: 角色名称
            
        Returns:
            Optional[Dict]: 角色信息或None
        """
        session = get_session(self.db_url)
        try:
            role = session.query(Role).filter_by(name=name).first()
            return role.to_dict() if role else None
        finally:
            session.close()
    
    def list_roles(self, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """
        获取角色列表
        
        Args:
            page: 页码（从1开始）
            page_size: 每页大小
            
        Returns:
            Dict: {"roles": List[Dict], "total": int, "page": int, "page_size": int}
        """
        session = get_session(self.db_url)
        try:
            # 计算总数
            total = session.query(Role).count()
            
            # 分页查询
            offset = (page - 1) * page_size
            roles = session.query(Role).offset(offset).limit(page_size).all()
            
            return {
                "roles": [role.to_dict() for role in roles],
                "total": total,
                "page": page,
                "page_size": page_size
            }
        finally:
            session.close()
    
    def assign_role_to_user(self, user_name: str, role_name: str, 
                           admin_user: str = None, ip_address: str = None, 
                           user_agent: str = None) -> Dict[str, Any]:
        """
        为用户分配角色
        
        Args:
            user_name: 用户名
            role_name: 角色名
            admin_user: 操作的管理员用户名
            ip_address: 操作IP
            user_agent: 用户代理
            
        Returns:
            Dict: {"success": bool, "error": str|None}
            
        Requirements:
            - 13.3: THE Audit_Log SHALL record user role assignments and removals
        """
        import logging
        
        logger = logging.getLogger('funboost.permission_audit')
        
        session = get_session(self.db_url)
        try:
            user = session.query(WebManagerUser).filter_by(user_name=user_name).first()
            if not user:
                return {"success": False, "error": "用户不存在"}
            
            role = session.query(Role).filter_by(name=role_name).first()
            if not role:
                return {"success": False, "error": "角色不存在"}
            
            # 检查是否已经有此角色
            if role in user.roles:
                return {"success": False, "error": "用户已拥有此角色"}
            
            user.roles.append(role)
            session.commit()
            
            # 记录用户角色分配审计日志 (Requirement 13.3)
            if admin_user:
                # 记录到日志系统
                logger.info(
                    f"User role change: operator={admin_user}, target_user={user_name}, "
                    f"action=分配, role={role_name}"
                )
                
                self._log_audit_event(session, "user_role_assign", admin_user, ip_address, 
                                     user_agent, {
                                         "target_user": user_name,
                                         "role_name": role_name,
                                         "change_type": "assign"
                                     })
            
            return {"success": True, "error": None}
            
        except Exception as e:
            session.rollback()
            return {"success": False, "error": f"分配角色失败：{str(e)}"}
        finally:
            session.close()
    
    def remove_role_from_user(self, user_name: str, role_name: str,
                             admin_user: str = None, ip_address: str = None, 
                             user_agent: str = None) -> Dict[str, Any]:
        """
        移除用户角色
        
        Args:
            user_name: 用户名
            role_name: 角色名
            admin_user: 操作的管理员用户名
            ip_address: 操作IP
            user_agent: 用户代理
            
        Returns:
            Dict: {"success": bool, "error": str|None}
            
        Requirements:
            - 13.3: THE Audit_Log SHALL record user role assignments and removals
        """
        import logging
        
        logger = logging.getLogger('funboost.permission_audit')
        
        session = get_session(self.db_url)
        try:
            user = session.query(WebManagerUser).filter_by(user_name=user_name).first()
            if not user:
                return {"success": False, "error": "用户不存在"}
            
            role = session.query(Role).filter_by(name=role_name).first()
            if not role:
                return {"success": False, "error": "角色不存在"}
            
            # 检查用户是否有此角色
            if role not in user.roles:
                return {"success": False, "error": "用户没有此角色"}
            
            user.roles.remove(role)
            session.commit()
            
            # 记录用户角色移除审计日志 (Requirement 13.3)
            if admin_user:
                # 记录到日志系统
                logger.info(
                    f"User role change: operator={admin_user}, target_user={user_name}, "
                    f"action=移除, role={role_name}"
                )
                
                self._log_audit_event(session, "user_role_remove", admin_user, ip_address, 
                                     user_agent, {
                                         "target_user": user_name,
                                         "role_name": role_name,
                                         "change_type": "remove"
                                     })
            
            return {"success": True, "error": None}
            
        except Exception as e:
            session.rollback()
            return {"success": False, "error": f"移除角色失败：{str(e)}"}
        finally:
            session.close()
    
    def assign_default_role_to_user(self, user_name: str) -> bool:
        """
        为新用户分配默认角色（viewer）
        
        Args:
            user_name: 用户名
            
        Returns:
            bool: 是否成功分配
        """
        result = self.assign_role_to_user(user_name, "viewer")
        return result["success"]
    
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
    
    def _log_permission_change_audit(
        self, 
        session, 
        operator: str, 
        role_name: str,
        added_permissions: List[str],
        removed_permissions: List[str],
        ip_address: str = None,
        user_agent: str = None
    ):
        """记录权限变更审计日志
        
        当角色的权限被修改时，记录详细的审计日志，包括操作者、时间戳、
        以及添加和移除的权限列表。
        
        Args:
            session: 数据库会话
            operator: 执行操作的用户名（操作者）
            role_name: 被修改权限的角色名称
            added_permissions: 新增的权限代码列表
            removed_permissions: 移除的权限代码列表
            ip_address: 操作者的 IP 地址
            user_agent: 操作者的用户代理字符串
            
        Requirements:
            - 13.1: THE Permission_System SHALL log all permission changes with operator, 
                    timestamp, and change details
            - 13.2: THE Audit_Log SHALL record added and removed permissions for each change
        """
        try:
            # 构建审计详情
            details = {
                'role_name': role_name,
                'added_permissions': added_permissions,
                'removed_permissions': removed_permissions,
                'change_summary': {
                    'added_count': len(added_permissions),
                    'removed_count': len(removed_permissions)
                }
            }
            
            audit_log = AuditLog(
                event_type='permission_change',
                user_name=operator,
                ip_address=ip_address,
                user_agent=user_agent,
                details=json.dumps(details, ensure_ascii=False)
            )
            session.add(audit_log)
            session.commit()
        except Exception:
            # 审计日志记录失败不应该影响主流程
            session.rollback()
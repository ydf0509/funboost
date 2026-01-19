# -*- coding: utf-8 -*-
"""
项目服务模块

提供项目的增删改查功能，支持项目名称和代码唯一性校验。
提供项目权限检查功能，支持全局管理员访问所有项目。

Requirements:
    - US-1.1: 作为管理员，我希望能够创建、编辑和删除项目
    - US-1.2: 作为管理员，我希望能够为项目设置名称、描述和状态
    - US-1.3: 作为管理员，我希望能够查看项目列表和详情
    - US-2.1: 作为管理员，我希望能够将用户分配到特定项目
    - US-2.2: 作为管理员，我希望能够为用户设置项目级别的权限
    - US-2.3: 作为管理员，我希望能够设置全局权限，允许某些用户访问所有项目
"""


import json
import re
from typing import List, Dict, Any, Optional

from ..user_models import (
    get_session, Project, UserProject, AuditLog, WebManagerUser, Role, Permission
)


class ProjectService:
    """项目管理服务
    
    提供项目的 CRUD 操作，包括：
    - 创建项目（含名称和代码唯一性校验）
    - 获取项目详情
    - 获取项目列表（支持分页和搜索）
    - 更新项目
    - 删除项目（检查是否有关联数据）
    
    Requirements:
        - US-1.1: 创建、编辑和删除项目
        - US-1.2: 为项目设置名称、描述和状态
        - US-1.3: 查看项目列表和详情
    """
    
    # 项目代码格式：只允许小写字母、数字和下划线，以字母开头
    CODE_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')
    
    # 项目状态枚举
    VALID_STATUSES = ('active', 'archived')
    
    def __init__(self, db_url: Optional[str] = None):
        """
        初始化项目服务
        
        Args:
            db_url: 可选的数据库 URL，如果不提供则从配置获取
        """
        self.db_url = db_url
    
    def create_project(
        self, 
        name: str, 
        code: str, 
        description: str = None,
        status: str = 'active',
        admin_user: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """
        创建新项目
        
        Args:
            name: 项目名称（必填，唯一）
            code: 项目代码（必填，唯一，用于权限标识）
            description: 项目描述（可选）
            status: 项目状态，默认为 'active'，可选 'archived'
            admin_user: 操作的管理员用户名（用于审计日志）
            ip_address: 操作 IP（用于审计日志）
            user_agent: 用户代理（用于审计日志）
            
        Returns:
            Dict: {
                "success": bool,
                "project": dict|None,
                "error": str|None
            }
            
        Requirements:
            - US-1.1: 创建项目
            - US-1.2: 设置名称、描述和状态
            - AC-1: 项目名称唯一性校验
        """
        # 参数验证
        if not name or not name.strip():
            return {
                "success": False,
                "project": None,
                "error": "项目名称不能为空"
            }
        
        if not code or not code.strip():
            return {
                "success": False,
                "project": None,
                "error": "项目代码不能为空"
            }
        
        name = name.strip()
        code = code.strip().lower()
        
        # 验证项目代码格式
        if not self.CODE_PATTERN.match(code):
            return {
                "success": False,
                "project": None,
                "error": "项目代码格式无效，只允许小写字母、数字和下划线，且必须以字母开头"
            }
        
        # 验证项目代码长度
        if len(code) > 32:
            return {
                "success": False,
                "project": None,
                "error": "项目代码长度不能超过32个字符"
            }
        
        # 验证项目名称长度
        if len(name) > 64:
            return {
                "success": False,
                "project": None,
                "error": "项目名称长度不能超过64个字符"
            }
        
        # 验证状态
        if status not in self.VALID_STATUSES:
            return {
                "success": False,
                "project": None,
                "error": f"无效的项目状态，有效值为：{', '.join(self.VALID_STATUSES)}"
            }
        
        session = get_session(self.db_url)
        try:
            # 检查项目名称是否已存在
            existing_name = session.query(Project).filter_by(name=name).first()
            if existing_name:
                return {
                    "success": False,
                    "project": None,
                    "error": f"项目名称 '{name}' 已存在"
                }
            
            # 检查项目代码是否已存在
            existing_code = session.query(Project).filter_by(code=code).first()
            if existing_code:
                return {
                    "success": False,
                    "project": None,
                    "error": f"项目代码 '{code}' 已存在"
                }
            
            # 创建项目
            project = Project(
                name=name,
                code=code,
                description=description,
                status=status
            )
            
            session.add(project)
            session.commit()
            session.refresh(project)
            
            # 记录审计日志
            if admin_user:
                self._log_audit_event(
                    session, 
                    "project_create", 
                    admin_user, 
                    ip_address, 
                    user_agent, 
                    {
                        "project_id": project.id,
                        "project_name": name,
                        "project_code": code,
                        "status": status
                    }
                )
            
            return {
                "success": True,
                "project": project.to_dict(),
                "error": None
            }
            
        except Exception as e:
            session.rollback()
            return {
                "success": False,
                "project": None,
                "error": f"创建项目失败：{str(e)}"
            }
        finally:
            session.close()
    
    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单个项目详情
        
        Args:
            project_id: 项目ID
            
        Returns:
            Optional[Dict]: 项目信息字典，如果不存在返回 None
            
        Requirements:
            - US-1.3: 查看项目详情
        """
        session = get_session(self.db_url)
        try:
            project = session.query(Project).filter_by(id=project_id).first()
            return project.to_dict() if project else None
        finally:
            session.close()
    
    def get_project_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        根据项目代码获取项目
        
        Args:
            code: 项目代码
            
        Returns:
            Optional[Dict]: 项目信息字典，如果不存在返回 None
        """
        session = get_session(self.db_url)
        try:
            project = session.query(Project).filter_by(code=code).first()
            return project.to_dict() if project else None
        finally:
            session.close()
    
    def get_all_projects(
        self, 
        page: int = 1, 
        page_size: int = 50,
        search: str = None,
        status: str = None
    ) -> Dict[str, Any]:
        """
        获取项目列表（支持分页和搜索）
        
        Args:
            page: 页码（从1开始），默认为1
            page_size: 每页大小，默认为50
            search: 搜索关键词（可选），匹配项目名称或代码
            status: 状态过滤（可选），'active' 或 'archived'
            
        Returns:
            Dict: {
                "projects": List[Dict],  # 项目列表
                "total": int,            # 总数
                "page": int,             # 当前页码
                "page_size": int,        # 每页大小
                "total_pages": int       # 总页数
            }
            
        Requirements:
            - US-1.3: 查看项目列表
            - AC-1: 项目列表支持分页和搜索
        """
        session = get_session(self.db_url)
        try:
            # 构建查询
            query = session.query(Project)
            
            # 搜索过滤
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    (Project.name.ilike(search_pattern)) |
                    (Project.code.ilike(search_pattern)) |
                    (Project.description.ilike(search_pattern))
                )
            
            # 状态过滤
            if status and status in self.VALID_STATUSES:
                query = query.filter(Project.status == status)
            
            # 计算总数
            total = query.count()
            
            # 计算总页数
            total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
            
            # 分页查询，按创建时间倒序
            offset = (page - 1) * page_size
            projects = query.order_by(Project.created_at.desc()).offset(offset).limit(page_size).all()
            
            return {
                "projects": [project.to_dict() for project in projects],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        finally:
            session.close()
    
    def update_project(
        self, 
        project_id: int, 
        name: str = None, 
        code: str = None,
        description: str = None,
        status: str = None,
        admin_user: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """
        更新项目
        
        Args:
            project_id: 项目ID
            name: 新项目名称（可选）
            code: 新项目代码（可选）
            description: 新项目描述（可选）
            status: 新项目状态（可选）
            admin_user: 操作的管理员用户名（用于审计日志）
            ip_address: 操作 IP（用于审计日志）
            user_agent: 用户代理（用于审计日志）
            
        Returns:
            Dict: {
                "success": bool,
                "project": dict|None,
                "error": str|None
            }
            
        Requirements:
            - US-1.1: 编辑项目
            - US-1.2: 设置名称、描述和状态
            - AC-1: 项目名称唯一性校验
        """
        session = get_session(self.db_url)
        try:
            project = session.query(Project).filter_by(id=project_id).first()
            if not project:
                return {
                    "success": False,
                    "project": None,
                    "error": "项目不存在"
                }
            
            old_data = project.to_dict()
            
            # 更新名称
            if name is not None:
                name = name.strip()
                if not name:
                    return {
                        "success": False,
                        "project": None,
                        "error": "项目名称不能为空"
                    }
                
                if len(name) > 64:
                    return {
                        "success": False,
                        "project": None,
                        "error": "项目名称长度不能超过64个字符"
                    }
                
                # 检查名称唯一性（排除当前项目）
                existing = session.query(Project).filter(
                    Project.name == name, 
                    Project.id != project_id
                ).first()
                if existing:
                    return {
                        "success": False,
                        "project": None,
                        "error": f"项目名称 '{name}' 已存在"
                    }
                project.name = name
            
            # 更新代码
            if code is not None:
                code = code.strip().lower()
                if not code:
                    return {
                        "success": False,
                        "project": None,
                        "error": "项目代码不能为空"
                    }
                
                # 验证项目代码格式
                if not self.CODE_PATTERN.match(code):
                    return {
                        "success": False,
                        "project": None,
                        "error": "项目代码格式无效，只允许小写字母、数字和下划线，且必须以字母开头"
                    }
                
                if len(code) > 32:
                    return {
                        "success": False,
                        "project": None,
                        "error": "项目代码长度不能超过32个字符"
                    }
                
                # 检查代码唯一性（排除当前项目）
                existing = session.query(Project).filter(
                    Project.code == code, 
                    Project.id != project_id
                ).first()
                if existing:
                    return {
                        "success": False,
                        "project": None,
                        "error": f"项目代码 '{code}' 已存在"
                    }
                project.code = code
            
            # 更新描述
            if description is not None:
                project.description = description
            
            # 更新状态
            if status is not None:
                if status not in self.VALID_STATUSES:
                    return {
                        "success": False,
                        "project": None,
                        "error": f"无效的项目状态，有效值为：{', '.join(self.VALID_STATUSES)}"
                    }
                project.status = status
            
            session.commit()
            session.refresh(project)
            
            # 记录审计日志
            if admin_user:
                self._log_audit_event(
                    session, 
                    "project_update", 
                    admin_user, 
                    ip_address, 
                    user_agent, 
                    {
                        "project_id": project_id,
                        "old_data": old_data,
                        "new_data": project.to_dict()
                    }
                )
            
            return {
                "success": True,
                "project": project.to_dict(),
                "error": None
            }
            
        except Exception as e:
            session.rollback()
            return {
                "success": False,
                "project": None,
                "error": f"更新项目失败：{str(e)}"
            }
        finally:
            session.close()
    
    def delete_project(
        self, 
        project_id: int,
        force: bool = False,
        admin_user: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """
        删除项目
        
        删除规则：
        1. 默认项目（code='default'）不可删除
        2. 如果项目在 Redis 中有活跃队列，不可删除（除非 force=True）
        3. 用户关联会自动清理（级联删除）
        
        Args:
            project_id: 项目ID
            force: 是否强制删除（即使有活跃队列也删除）
            admin_user: 操作的管理员用户名（用于审计日志）
            ip_address: 操作 IP（用于审计日志）
            user_agent: 用户代理（用于审计日志）
            
        Returns:
            Dict: {
                "success": bool,
                "error": str|None
            }
            
        Requirements:
            - US-1.1: 删除项目
            - AC-1: 可以删除空项目（无队列关联）
        """
        session = get_session(self.db_url)
        try:
            project = session.query(Project).filter_by(id=project_id).first()
            if not project:
                return {
                    "success": False,
                    "error": "项目不存在"
                }
            
            # 检查是否为默认项目
            if project.code == 'default':
                return {
                    "success": False,
                    "error": "默认项目不可删除"
                }
            
            project_code = project.code
            
            # 检查 Redis 中是否有该项目的活跃队列
            if not force:
                try:
                    from funboost.core.active_cousumer_info_getter import QueuesConusmerParamsGetter
                    redis_project_names = QueuesConusmerParamsGetter().get_all_project_names()
                    if project_code in redis_project_names:
                        return {
                            "success": False,
                            "error": f"项目 '{project.name}' 在 Redis 中有活跃队列，无法删除。如需强制删除，请使用强制删除选项。"
                        }
                except Exception as e:
                    # Redis 连接失败时，记录日志但允许继续删除
                    logger = __import__('nb_log').get_logger('project_service')
                    logger.warning(f"检查 Redis 项目时出错: {e}")
            
            # 先删除用户关联
            user_count = session.query(UserProject).filter_by(project_id=project_id).count()
            if user_count > 0:
                session.query(UserProject).filter_by(project_id=project_id).delete()
            
            project_data = project.to_dict()
            session.delete(project)
            session.commit()
            
            # 如果是强制删除，同时从 Redis 中删除项目名称
            redis_removed = False
            redis_result = None
            if force:
                try:
                    from funboost.core.active_cousumer_info_getter import QueuesConusmerParamsGetter
                    redis_result = QueuesConusmerParamsGetter().remove_project_name(project_code, force=True)
                    redis_removed = redis_result.get("success", False)
                except Exception as e:
                    logger = __import__('nb_log').get_logger('project_service')
                    logger.warning(f"从 Redis 删除项目名称时出错: {e}")
            
            # 记录审计日志
            if admin_user:
                self._log_audit_event(
                    session, 
                    "project_delete", 
                    admin_user, 
                    ip_address, 
                    user_agent, 
                    {
                        "deleted_project": project_data,
                        "removed_user_count": user_count,
                        "force": force,
                        "redis_removed": redis_removed
                    }
                )
            
            return {
                "success": True,
                "error": None,
                "removed_user_count": user_count,
                "redis_removed": redis_removed
            }
            
        except Exception as e:
            session.rollback()
            return {
                "success": False,
                "error": f"删除项目失败：{str(e)}"
            }
        finally:
            session.close()
    
    def get_project_user_count(self, project_id: int) -> int:
        """
        获取项目关联的用户数量
        
        Args:
            project_id: 项目ID
            
        Returns:
            int: 关联的用户数量
        """
        session = get_session(self.db_url)
        try:
            return session.query(UserProject).filter_by(project_id=project_id).count()
        finally:
            session.close()
    
    def _log_audit_event(
        self, 
        session, 
        event_type: str, 
        user_name: str, 
        ip_address: str, 
        user_agent: Optional[str], 
        details: Optional[Dict] = None
    ):
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
    
    # ==================== 项目权限检查方法 ====================
    
    def _is_global_admin(self, session, user_id: int) -> bool:
        """
        检查用户是否为全局管理员
        
        全局管理员的判断条件：
        1. 用户拥有 'admin' 角色
        2. 或者用户拥有 'project:admin' 权限
        3. 或者用户拥有 '*:*:*' 或 '*:project:*' 等全局权限
        
        Args:
            session: 数据库会话
            user_id: 用户ID（数据库主键）
            
        Returns:
            bool: True 如果用户是全局管理员，否则 False
        """
        # 获取用户
        user = session.query(WebManagerUser).filter_by(id=user_id).first()
        if not user:
            return False
        
        # 检查用户是否有 admin 角色
        for role in user.roles:
            if role.name == 'admin':
                return True
        
        # 检查用户是否有全局项目管理权限
        # 收集用户所有角色的权限
        user_permissions = set()
        for role in user.roles:
            for perm in role.permissions:
                user_permissions.add(perm.code)
        
        # 检查是否有 project:admin 权限或全局权限
        global_admin_permissions = {
            'project:admin',
            '*:*:*',
            '*:project:*',
            '*:*',
        }
        
        if user_permissions & global_admin_permissions:
            return True
        
        return False
    
    def _get_user_by_id_or_name(self, session, user_id) -> Optional[WebManagerUser]:
        """
        根据用户ID或用户名获取用户对象
        
        支持两种查询方式：
        1. 如果 user_id 是整数，按数据库主键查询
        2. 如果 user_id 是字符串，按用户名查询
        
        Args:
            session: 数据库会话
            user_id: 用户ID（整数）或用户名（字符串）
            
        Returns:
            Optional[WebManagerUser]: 用户对象，如果不存在返回 None
        """
        if isinstance(user_id, int):
            return session.query(WebManagerUser).filter_by(id=user_id).first()
        elif isinstance(user_id, str):
            # 尝试转换为整数
            try:
                int_id = int(user_id)
                return session.query(WebManagerUser).filter_by(id=int_id).first()
            except ValueError:
                # 按用户名查询
                return session.query(WebManagerUser).filter_by(user_name=user_id).first()
        return None
    
    def has_project_access(self, user_id, project_id: int) -> bool:
        """
        检查用户是否有项目访问权限
        
        权限检查流程：
        1. 检查用户是否为全局管理员（admin 角色或 project:admin 权限）
        2. 如果不是全局管理员，检查用户是否在 UserProject 表中有该项目的访问权限
        
        Args:
            user_id: 用户ID（整数）或用户名（字符串）
            project_id: 项目ID
            
        Returns:
            bool: True 如果用户有访问权限，否则 False
            
        Requirements:
            - US-2.1: 将用户分配到特定项目
            - US-2.3: 全局管理员可以访问所有项目
        """
        session = get_session(self.db_url)
        try:
            # 获取用户
            user = self._get_user_by_id_or_name(session, user_id)
            if not user:
                return False
            
            # 检查是否为全局管理员
            if self._is_global_admin(session, user.id):
                return True
            
            # 检查用户是否在 UserProject 表中有该项目的访问权限
            user_project = session.query(UserProject).filter_by(
                user_id=user.id,
                project_id=project_id
            ).first()
            
            return user_project is not None
            
        finally:
            session.close()
    
    def get_user_projects(self, user_id) -> List[Dict[str, Any]]:
        """
        获取用户可访问的所有项目
        
        返回规则：
        1. 如果用户是全局管理员，返回所有活跃项目
        2. 否则，返回用户在 UserProject 表中关联的项目
        
        Args:
            user_id: 用户ID（整数）或用户名（字符串）
            
        Returns:
            List[Dict]: 项目列表，每个项目包含项目信息和用户的权限级别
            
        Requirements:
            - US-2.1: 将用户分配到特定项目
            - US-2.3: 全局管理员可以访问所有项目
        """
        session = get_session(self.db_url)
        try:
            # 获取用户
            user = self._get_user_by_id_or_name(session, user_id)
            if not user:
                return []
            
            # 检查是否为全局管理员
            if self._is_global_admin(session, user.id):
                # 全局管理员返回所有活跃项目
                projects = session.query(Project).filter(
                    Project.status == 'active'
                ).order_by(Project.created_at.desc()).all()
                
                return [
                    {
                        **project.to_dict(),
                        'permission_level': 'admin',  # 全局管理员在所有项目中都是 admin
                        'is_global_admin': True
                    }
                    for project in projects
                ]
            
            # 非全局管理员，返回 UserProject 表中关联的项目
            user_projects = session.query(UserProject).filter_by(
                user_id=user.id
            ).all()
            
            result = []
            for up in user_projects:
                if up.project and up.project.status == 'active':
                    result.append({
                        **up.project.to_dict(),
                        'permission_level': up.permission_level,
                        'is_global_admin': False
                    })
            
            # 按创建时间倒序排序
            result.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return result
            
        finally:
            session.close()
    
    def get_project_permission_level(self, user_id, project_id: int) -> Optional[str]:
        """
        获取用户在项目中的权限级别
        
        权限级别：
        - 'admin': 管理权限，可以管理项目和用户
        - 'write': 写入权限，可以修改数据
        - 'read': 只读权限，只能查看数据
        - None: 无权限
        
        返回规则：
        1. 如果用户是全局管理员，返回 'admin'
        2. 否则，返回 UserProject 表中记录的权限级别
        3. 如果用户没有该项目的访问权限，返回 None
        
        Args:
            user_id: 用户ID（整数）或用户名（字符串）
            project_id: 项目ID
            
        Returns:
            Optional[str]: 权限级别 ('admin', 'write', 'read') 或 None
            
        Requirements:
            - US-2.2: 为用户设置项目级别的权限
            - US-2.3: 全局管理员可以访问所有项目
        """
        session = get_session(self.db_url)
        try:
            # 获取用户
            user = self._get_user_by_id_or_name(session, user_id)
            if not user:
                return None
            
            # 检查是否为全局管理员
            if self._is_global_admin(session, user.id):
                # 全局管理员在所有项目中都是 admin 权限
                # 但需要先检查项目是否存在
                project = session.query(Project).filter_by(id=project_id).first()
                if project:
                    return 'admin'
                return None
            
            # 非全局管理员，从 UserProject 表获取权限级别
            user_project = session.query(UserProject).filter_by(
                user_id=user.id,
                project_id=project_id
            ).first()
            
            if user_project:
                return user_project.permission_level
            
            return None
            
        finally:
            session.close()
    
    def check_project_permission(
        self, 
        user_id, 
        project_id: int, 
        required_level: str = 'read'
    ) -> bool:
        """
        检查用户是否有指定级别的项目权限
        
        权限级别层次（从高到低）：
        - 'admin' > 'write' > 'read'
        
        例如：
        - 用户有 'admin' 权限，检查 'read' 权限 -> True
        - 用户有 'read' 权限，检查 'write' 权限 -> False
        
        Args:
            user_id: 用户ID（整数）或用户名（字符串）
            project_id: 项目ID
            required_level: 需要的权限级别，默认为 'read'
            
        Returns:
            bool: True 如果用户有足够的权限，否则 False
            
        Requirements:
            - US-2.2: 为用户设置项目级别的权限
        """
        # 权限级别层次
        permission_hierarchy = {
            'admin': 3,
            'write': 2,
            'read': 1
        }
        
        user_level = self.get_project_permission_level(user_id, project_id)
        if user_level is None:
            return False
        
        user_level_value = permission_hierarchy.get(user_level, 0)
        required_level_value = permission_hierarchy.get(required_level, 0)
        
        return user_level_value >= required_level_value
    
    # ==================== 项目用户管理方法 ====================
    
    # 有效的权限级别
    VALID_PERMISSION_LEVELS = ('read', 'write', 'admin')
    
    def add_user_to_project(
        self,
        user_id: int,
        project_id: int,
        permission_level: str = 'read',
        admin_user: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """
        将用户添加到项目
        
        Args:
            user_id: 用户ID（数据库主键）
            project_id: 项目ID
            permission_level: 权限级别，默认为 'read'，可选 'read', 'write', 'admin'
            admin_user: 操作的管理员用户名（用于审计日志）
            ip_address: 操作 IP（用于审计日志）
            user_agent: 用户代理（用于审计日志）
            
        Returns:
            Dict: {
                "success": bool,
                "user_project": dict|None,  # 用户项目关联信息
                "error": str|None
            }
            
        Requirements:
            - US-2.1: 将用户分配到特定项目
            - US-2.2: 为用户设置项目级别的权限
        """
        # 验证权限级别
        if permission_level not in self.VALID_PERMISSION_LEVELS:
            return {
                "success": False,
                "user_project": None,
                "error": f"无效的权限级别，有效值为：{', '.join(self.VALID_PERMISSION_LEVELS)}"
            }
        
        session = get_session(self.db_url)
        try:
            # 验证用户是否存在
            user = session.query(WebManagerUser).filter_by(id=user_id).first()
            if not user:
                return {
                    "success": False,
                    "user_project": None,
                    "error": f"用户不存在（ID: {user_id}）"
                }
            
            # 验证项目是否存在
            project = session.query(Project).filter_by(id=project_id).first()
            if not project:
                return {
                    "success": False,
                    "user_project": None,
                    "error": f"项目不存在（ID: {project_id}）"
                }
            
            # 检查用户是否已经在项目中
            existing = session.query(UserProject).filter_by(
                user_id=user_id,
                project_id=project_id
            ).first()
            
            if existing:
                return {
                    "success": False,
                    "user_project": None,
                    "error": f"用户 '{user.user_name}' 已经在项目 '{project.name}' 中"
                }
            
            # 创建用户项目关联
            user_project = UserProject(
                user_id=user_id,
                project_id=project_id,
                permission_level=permission_level
            )
            
            session.add(user_project)
            session.commit()
            session.refresh(user_project)
            
            # 记录审计日志
            if admin_user:
                self._log_audit_event(
                    session,
                    "project_add_user",
                    admin_user,
                    ip_address,
                    user_agent,
                    {
                        "project_id": project_id,
                        "project_name": project.name,
                        "user_id": user_id,
                        "user_name": user.user_name,
                        "permission_level": permission_level
                    }
                )
            
            return {
                "success": True,
                "user_project": user_project.to_dict(),
                "error": None
            }
            
        except Exception as e:
            session.rollback()
            return {
                "success": False,
                "user_project": None,
                "error": f"添加用户到项目失败：{str(e)}"
            }
        finally:
            session.close()
    
    def remove_user_from_project(
        self,
        user_id: int,
        project_id: int,
        admin_user: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """
        从项目中移除用户
        
        Args:
            user_id: 用户ID（数据库主键）
            project_id: 项目ID
            admin_user: 操作的管理员用户名（用于审计日志）
            ip_address: 操作 IP（用于审计日志）
            user_agent: 用户代理（用于审计日志）
            
        Returns:
            Dict: {
                "success": bool,
                "error": str|None
            }
            
        Requirements:
            - US-2.1: 将用户分配到特定项目（包括移除）
        """
        session = get_session(self.db_url)
        try:
            # 验证用户是否存在
            user = session.query(WebManagerUser).filter_by(id=user_id).first()
            if not user:
                return {
                    "success": False,
                    "error": f"用户不存在（ID: {user_id}）"
                }
            
            # 验证项目是否存在
            project = session.query(Project).filter_by(id=project_id).first()
            if not project:
                return {
                    "success": False,
                    "error": f"项目不存在（ID: {project_id}）"
                }
            
            # 查找用户项目关联
            user_project = session.query(UserProject).filter_by(
                user_id=user_id,
                project_id=project_id
            ).first()
            
            if not user_project:
                return {
                    "success": False,
                    "error": f"用户 '{user.user_name}' 不在项目 '{project.name}' 中"
                }
            
            # 保存关联信息用于审计日志
            old_permission_level = user_project.permission_level
            
            # 删除关联
            session.delete(user_project)
            session.commit()
            
            # 记录审计日志
            if admin_user:
                self._log_audit_event(
                    session,
                    "project_remove_user",
                    admin_user,
                    ip_address,
                    user_agent,
                    {
                        "project_id": project_id,
                        "project_name": project.name,
                        "user_id": user_id,
                        "user_name": user.user_name,
                        "old_permission_level": old_permission_level
                    }
                )
            
            return {
                "success": True,
                "error": None
            }
            
        except Exception as e:
            session.rollback()
            return {
                "success": False,
                "error": f"从项目移除用户失败：{str(e)}"
            }
        finally:
            session.close()
    
    def update_user_project_permission(
        self,
        user_id: int,
        project_id: int,
        permission_level: str,
        admin_user: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """
        更新用户在项目中的权限级别
        
        Args:
            user_id: 用户ID（数据库主键）
            project_id: 项目ID
            permission_level: 新的权限级别，可选 'read', 'write', 'admin'
            admin_user: 操作的管理员用户名（用于审计日志）
            ip_address: 操作 IP（用于审计日志）
            user_agent: 用户代理（用于审计日志）
            
        Returns:
            Dict: {
                "success": bool,
                "user_project": dict|None,  # 更新后的用户项目关联信息
                "error": str|None
            }
            
        Requirements:
            - US-2.2: 为用户设置项目级别的权限
        """
        # 验证权限级别
        if permission_level not in self.VALID_PERMISSION_LEVELS:
            return {
                "success": False,
                "user_project": None,
                "error": f"无效的权限级别，有效值为：{', '.join(self.VALID_PERMISSION_LEVELS)}"
            }
        
        session = get_session(self.db_url)
        try:
            # 验证用户是否存在
            user = session.query(WebManagerUser).filter_by(id=user_id).first()
            if not user:
                return {
                    "success": False,
                    "user_project": None,
                    "error": f"用户不存在（ID: {user_id}）"
                }
            
            # 验证项目是否存在
            project = session.query(Project).filter_by(id=project_id).first()
            if not project:
                return {
                    "success": False,
                    "user_project": None,
                    "error": f"项目不存在（ID: {project_id}）"
                }
            
            # 查找用户项目关联
            user_project = session.query(UserProject).filter_by(
                user_id=user_id,
                project_id=project_id
            ).first()
            
            if not user_project:
                return {
                    "success": False,
                    "user_project": None,
                    "error": f"用户 '{user.user_name}' 不在项目 '{project.name}' 中"
                }
            
            # 保存旧权限级别用于审计日志
            old_permission_level = user_project.permission_level
            
            # 如果权限级别没有变化，直接返回成功
            if old_permission_level == permission_level:
                return {
                    "success": True,
                    "user_project": user_project.to_dict(),
                    "error": None
                }
            
            # 更新权限级别
            user_project.permission_level = permission_level
            session.commit()
            session.refresh(user_project)
            
            # 记录审计日志
            if admin_user:
                self._log_audit_event(
                    session,
                    "project_update_user_permission",
                    admin_user,
                    ip_address,
                    user_agent,
                    {
                        "project_id": project_id,
                        "project_name": project.name,
                        "user_id": user_id,
                        "user_name": user.user_name,
                        "old_permission_level": old_permission_level,
                        "new_permission_level": permission_level
                    }
                )
            
            return {
                "success": True,
                "user_project": user_project.to_dict(),
                "error": None
            }
            
        except Exception as e:
            session.rollback()
            return {
                "success": False,
                "user_project": None,
                "error": f"更新用户项目权限失败：{str(e)}"
            }
        finally:
            session.close()
    
    def get_project_users(
        self,
        project_id: int,
        page: int = 1,
        page_size: int = 50,
        search: str = None
    ) -> Dict[str, Any]:
        """
        获取项目的所有用户
        
        Args:
            project_id: 项目ID
            page: 页码（从1开始），默认为1
            page_size: 每页大小，默认为50
            search: 搜索关键词（可选），匹配用户名或邮箱
            
        Returns:
            Dict: {
                "success": bool,
                "users": List[Dict],  # 用户列表，包含用户信息和权限级别
                "total": int,         # 总数
                "page": int,          # 当前页码
                "page_size": int,     # 每页大小
                "total_pages": int,   # 总页数
                "project": dict|None, # 项目信息
                "error": str|None
            }
            
        Requirements:
            - US-2.1: 将用户分配到特定项目
            - US-2.2: 为用户设置项目级别的权限
        """
        session = get_session(self.db_url)
        try:
            # 验证项目是否存在
            project = session.query(Project).filter_by(id=project_id).first()
            if not project:
                return {
                    "success": False,
                    "users": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                    "project": None,
                    "error": f"项目不存在（ID: {project_id}）"
                }
            
            # 构建查询：关联 UserProject 和 WebManagerUser
            query = session.query(UserProject, WebManagerUser).join(
                WebManagerUser, UserProject.user_id == WebManagerUser.id
            ).filter(UserProject.project_id == project_id)
            
            # 搜索过滤
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    (WebManagerUser.user_name.ilike(search_pattern)) |
                    (WebManagerUser.email.ilike(search_pattern))
                )
            
            # 计算总数
            total = query.count()
            
            # 计算总页数
            total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
            
            # 分页查询，按创建时间倒序
            offset = (page - 1) * page_size
            results = query.order_by(UserProject.created_at.desc()).offset(offset).limit(page_size).all()
            
            # 构建用户列表
            users = []
            for user_project, user in results:
                user_dict = {
                    'id': user_project.id,  # UserProject 的 ID
                    'user_id': user.id,     # 用户的数据库 ID
                    'username': user.user_name,  # 前端期望的字段名
                    'user_name': user.user_name,  # 保持兼容
                    'email': user.email,
                    'status': user.status,
                    'roles': [role.name for role in user.roles] if user.roles else [],
                    'permission_level': user_project.permission_level,
                    'created_at': user_project.created_at.isoformat() if user_project.created_at else None,
                    'joined_at': user_project.created_at.isoformat() if user_project.created_at else None
                }
                users.append(user_dict)
            
            return {
                "success": True,
                "users": users,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "project": project.to_dict(),
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "users": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "project": None,
                "error": f"获取项目用户失败：{str(e)}"
            }
        finally:
            session.close()

    def sync_projects_from_redis(
        self,
        admin_user: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """
        从 Redis 同步项目名称到数据库
        
        funboost 框架在 Redis 中存储了所有队列任务配置的 project_name，
        此方法从 Redis 读取这些项目名称，并在数据库中创建对应的项目记录。
        
        Args:
            admin_user: 操作的管理员用户名（用于审计日志）
            ip_address: 操作 IP（用于审计日志）
            user_agent: 用户代理（用于审计日志）
            
        Returns:
            Dict: {
                "success": bool,
                "created_count": int,  # 新创建的项目数量
                "existing_count": int,  # 已存在的项目数量
                "created_projects": list,  # 新创建的项目列表
                "error": str|None
            }
            
        Requirements:
            - US-1.1: 系统能够自动从 Redis 同步队列任务中配置的项目名称
            - AC-1: 系统启动时自动从 Redis 同步项目名称到数据库
        """
        try:
            # 从 Redis 获取所有项目名称
            from funboost.core.active_cousumer_info_getter import QueuesConusmerParamsGetter
            
            redis_project_names = QueuesConusmerParamsGetter().get_all_project_names()
            
            if not redis_project_names:
                return {
                    "success": True,
                    "created_count": 0,
                    "existing_count": 0,
                    "created_projects": [],
                    "error": None,
                    "message": "Redis 中没有找到项目名称"
                }
            
            session = get_session(self.db_url)
            created_count = 0
            existing_count = 0
            created_projects = []
            
            try:
                for project_name in redis_project_names:
                    if not project_name or not project_name.strip():
                        continue
                    
                    project_name = project_name.strip()
                    
                    # 检查项目是否已存在（按 code 查找，因为 code 就是 project_name）
                    existing = session.query(Project).filter_by(code=project_name).first()
                    
                    if existing:
                        existing_count += 1
                        continue
                    
                    # 创建新项目
                    # code 和 name 都使用 project_name
                    project = Project(
                        name=project_name,
                        code=project_name,
                        description=f"从队列任务配置自动同步的项目",
                        status='active'
                    )
                    
                    session.add(project)
                    session.flush()  # 获取 ID
                    
                    created_projects.append(project.to_dict())
                    created_count += 1
                
                session.commit()
                
                # 记录审计日志
                if admin_user and created_count > 0:
                    self._log_audit_event(
                        session,
                        "project_sync_from_redis",
                        admin_user,
                        ip_address,
                        user_agent,
                        {
                            "created_count": created_count,
                            "existing_count": existing_count,
                            "created_projects": [p['code'] for p in created_projects]
                        }
                    )
                
                return {
                    "success": True,
                    "created_count": created_count,
                    "existing_count": existing_count,
                    "created_projects": created_projects,
                    "error": None,
                    "message": f"同步完成：新建 {created_count} 个项目，已存在 {existing_count} 个项目"
                }
                
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
                
        except Exception as e:
            return {
                "success": False,
                "created_count": 0,
                "existing_count": 0,
                "created_projects": [],
                "error": f"从 Redis 同步项目失败：{str(e)}"
            }
    
    def get_project_code_by_id(self, project_id: int) -> Optional[str]:
        """
        根据项目 ID 获取项目代码
        
        Args:
            project_id: 项目 ID
            
        Returns:
            项目代码，如果项目不存在或是默认项目则返回 None
            
        Note:
            默认项目（code='default'）返回 None，表示不进行项目过滤
        """
        if not project_id:
            return None
        
        session = get_session(self.db_url)
        try:
            project = session.query(Project).filter_by(id=project_id).first()
            if not project:
                return None
            
            # 默认项目返回 None，表示不过滤
            if project.code == 'default':
                return None
            
            return project.code
        finally:
            session.close()

# -*- coding: utf-8 -*-
"""
权限服务模块

提供权限检查和权限管理功能。
"""

from typing import List, Dict, Any, Optional, Set

from ..user_models import get_session, WebManagerUser, Role, Permission, PermissionCategory


class PermissionService:
    """权限管理服务"""
    
    def __init__(self, db_url: Optional[str] = None):
        """
        初始化权限服务
        
        Args:
            db_url: 可选的数据库 URL
        """
        self.db_url = db_url
    
    def check_permission(self, user_name: str, permission_code: str) -> bool:
        """
        检查用户是否拥有指定权限
        
        Args:
            user_name: 用户名
            permission_code: 权限代码（如 'user:read', 'user:write'）
            
        Returns:
            bool: 是否拥有权限
        """
        # 获取用户的所有权限（通过角色）
        user_permissions = self.get_user_permissions(user_name)
        return self.check_permission_with_wildcard(user_permissions, permission_code)
    
    def check_any_permission(self, user_name: str, permission_codes: List[str]) -> bool:
        """
        检查用户是否拥有任意一个指定权限
        
        Args:
            user_name: 用户名
            permission_codes: 权限代码列表
            
        Returns:
            bool: 是否拥有任意一个权限
        """
        user_permissions = self.get_user_permissions(user_name)
        return any(
            self.check_permission_with_wildcard(user_permissions, code)
            for code in permission_codes
        )
    
    def check_all_permissions(self, user_name: str, permission_codes: List[str]) -> bool:
        """
        检查用户是否拥有所有指定权限
        
        Args:
            user_name: 用户名
            permission_codes: 权限代码列表
            
        Returns:
            bool: 是否拥有所有权限
        """
        user_permissions = self.get_user_permissions(user_name)
        return all(
            self.check_permission_with_wildcard(user_permissions, code)
            for code in permission_codes
        )
    
    def check_permission_with_wildcard(
        self, 
        user_permissions: Set[str], 
        required_permission: str,
        project: str = None
    ) -> bool:
        """检查用户是否拥有指定权限（支持通配符匹配和项目作用域）
        
        支持通配符匹配：
        - user:* 匹配 user:read, user:write 等
        - projectA:queue:* 匹配 projectA:queue:read 等
        
        项目作用域权限检查（Requirements 3.3, 3.5）：
        - 全局权限（无项目前缀）授予所有项目访问权限
        - 项目特定权限（如 projectA:queue:read）只授予该项目访问权限
        - 检查时同时匹配权限代码和项目作用域
        
        检查顺序（满足 Requirement 10.4）：
        1. 精确匹配 - 直接检查 required_permission 是否在 user_permissions 中
           （全局权限在此步骤匹配，满足 Requirement 3.5）
        2. 带项目的精确匹配 - 如果提供了 project，检查 project:required_permission
           （项目特定权限在此步骤匹配，满足 Requirement 3.3）
        3. 通配符匹配 - 使用 _match_wildcard 进行模式匹配
        
        Args:
            user_permissions: 用户拥有的权限代码集合
            required_permission: 需要检查的权限代码（如 'user:read'）
            project: 可选的项目作用域，用于检查项目级别权限
            
        Returns:
            bool: 是否拥有权限
            
        Requirements:
            - 3.3: WHEN checking permissions, THE Permission_System SHALL match both the permission code and project scope
            - 3.5: WHEN a user has a global permission (null project_scope), THE Permission_System SHALL grant access to all projects for that permission
            - 10.1: WHEN a user has `module:*` permission, THE Permission_System SHALL grant all actions under that module
            - 10.2: WHEN a user has `project:module:*` permission, THE Permission_System SHALL grant all actions for that module in that project
            - 10.3: THE Permission_System SHALL support wildcard `*` in permission codes for inheritance
            - 10.4: WHEN checking permissions, THE Permission_System SHALL first check exact match, then wildcard patterns
            
        Examples:
            >>> service = PermissionService()
            >>> # 精确匹配
            >>> service.check_permission_with_wildcard({'user:read'}, 'user:read')
            True
            >>> # 通配符匹配 - module:* 匹配 module:action
            >>> service.check_permission_with_wildcard({'user:*'}, 'user:read')
            True
            >>> # 通配符匹配 - project:module:* 匹配 project:module:action
            >>> service.check_permission_with_wildcard({'projectA:queue:*'}, 'queue:read', 'projectA')
            True
            >>> # 全局权限授予项目访问 (Requirement 3.5)
            >>> service.check_permission_with_wildcard({'queue:read'}, 'queue:read', 'projectA')
            True
            >>> # 项目特定权限匹配 (Requirement 3.3)
            >>> service.check_permission_with_wildcard({'projectA:queue:read'}, 'queue:read', 'projectA')
            True
            >>> # 项目特定权限不匹配其他项目 (Requirement 3.3)
            >>> service.check_permission_with_wildcard({'projectA:queue:read'}, 'queue:read', 'projectB')
            False
        """
        import re
        
        # 1. 精确匹配（优先级最高，满足 Requirement 10.4）
        if required_permission in user_permissions:
            return True
        
        # 2. 带项目的精确匹配
        if project:
            project_perm = f"{project}:{required_permission}"
            if project_perm in user_permissions:
                return True
        
        # 3. 通配符匹配
        return self._match_wildcard(user_permissions, required_permission, project)
    
    def _match_wildcard(
        self, 
        user_permissions: Set[str], 
        required: str,
        project: str = None
    ) -> bool:
        """通配符权限匹配
        
        将用户权限中的通配符 `*` 转换为正则表达式 `.*` 进行匹配。
        
        匹配规则：
        - `module:*` 匹配 `module:read`, `module:write` 等
        - `project:module:*` 匹配 `project:module:read` 等
        - `*:read` 匹配 `user:read`, `role:read` 等
        
        Args:
            user_permissions: 用户拥有的权限代码集合
            required: 需要检查的权限代码
            project: 可选的项目作用域
            
        Returns:
            bool: 是否匹配任意通配符权限
            
        Requirements:
            - 10.1: module:* 匹配该模块下的所有操作
            - 10.2: project:module:* 匹配该项目该模块下的所有操作
            - 10.3: 支持通配符 * 进行权限继承
        """
        import re
        
        for perm in user_permissions:
            # 跳过不包含通配符的权限（已在精确匹配中处理）
            if '*' not in perm:
                continue
            
            # 将通配符转换为正则表达式
            # 需要先转义其他正则特殊字符，然后将 * 替换为 .*
            pattern = re.escape(perm).replace(r'\*', '.*')
            
            # 匹配 required 权限
            if re.match(f'^{pattern}$', required):
                return True
            
            # 如果提供了项目，也尝试匹配 project:required
            if project:
                project_required = f"{project}:{required}"
                if re.match(f'^{pattern}$', project_required):
                    return True
        
        return False
    
    def get_user_permissions(self, user_name: str) -> Set[str]:
        """
        获取用户的所有权限代码
        
        Args:
            user_name: 用户名
            
        Returns:
            Set[str]: 权限代码集合
        """
        session = get_session(self.db_url)
        try:
            user = session.query(WebManagerUser).filter_by(user_name=user_name).first()
            if not user:
                return set()
            
            permissions = set()
            for role in user.roles:
                for permission in role.permissions:
                    permissions.add(permission.code)
            
            return permissions
            
        finally:
            session.close()
    
    def get_user_roles(self, user_name: str) -> List[str]:
        """
        获取用户的所有角色名称
        
        Args:
            user_name: 用户名
            
        Returns:
            List[str]: 角色名称列表
        """
        session = get_session(self.db_url)
        try:
            user = session.query(WebManagerUser).filter_by(user_name=user_name).first()
            if not user:
                return []
            
            return [role.name for role in user.roles]
            
        finally:
            session.close()
    
    def has_role(self, user_name: str, role_name: str) -> bool:
        """
        检查用户是否拥有指定角色
        
        Args:
            user_name: 用户名
            role_name: 角色名称
            
        Returns:
            bool: 是否拥有角色
        """
        user_roles = self.get_user_roles(user_name)
        return role_name in user_roles
    
    def is_admin(self, user_name: str) -> bool:
        """
        检查用户是否为管理员
        
        Args:
            user_name: 用户名
            
        Returns:
            bool: 是否为管理员
        """
        return self.has_role(user_name, 'admin')
    
    def list_permissions(self) -> List[Dict[str, Any]]:
        """
        获取所有权限列表
        
        Returns:
            List[Dict]: 权限列表
        """
        session = get_session(self.db_url)
        try:
            permissions = session.query(Permission).order_by(Permission.code).all()
            return [perm.to_dict() for perm in permissions]
        finally:
            session.close()
    
    def get_permission(self, permission_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单个权限
        
        Args:
            permission_id: 权限ID
            
        Returns:
            Optional[Dict]: 权限信息或None
        """
        session = get_session(self.db_url)
        try:
            permission = session.query(Permission).filter_by(id=permission_id).first()
            return permission.to_dict() if permission else None
        finally:
            session.close()
    
    def get_permission_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        根据代码获取权限
        
        Args:
            code: 权限代码
            
        Returns:
            Optional[Dict]: 权限信息或None
        """
        session = get_session(self.db_url)
        try:
            permission = session.query(Permission).filter_by(code=code).first()
            return permission.to_dict() if permission else None
        finally:
            session.close()
    
    def create_permission(self, code: str, name: str, description: str = None) -> Dict[str, Any]:
        """
        创建新权限
        
        Args:
            code: 权限代码
            name: 权限名称
            description: 权限描述
            
        Returns:
            Dict: {"success": bool, "permission": dict|None, "error": str|None}
        """
        session = get_session(self.db_url)
        try:
            # 检查权限代码是否已存在
            existing = session.query(Permission).filter_by(code=code).first()
            if existing:
                return {
                    "success": False,
                    "permission": None,
                    "error": f"权限代码 '{code}' 已存在"
                }
            
            # 创建权限
            permission = Permission(
                code=code,
                name=name,
                description=description
            )
            
            session.add(permission)
            session.commit()
            session.refresh(permission)
            
            return {
                "success": True,
                "permission": permission.to_dict(),
                "error": None
            }
            
        except Exception as e:
            session.rollback()
            return {
                "success": False,
                "permission": None,
                "error": f"创建权限失败：{str(e)}"
            }
        finally:
            session.close()
    
    def get_role_permissions(self, role_name: str) -> Set[str]:
        """
        获取角色的所有权限代码
        
        Args:
            role_name: 角色名称
            
        Returns:
            Set[str]: 权限代码集合
        """
        session = get_session(self.db_url)
        try:
            role = session.query(Role).filter_by(name=role_name).first()
            if not role:
                return set()
            
            return {perm.code for perm in role.permissions}
            
        finally:
            session.close()
    
    def get_users_with_permission(self, permission_code: str) -> List[str]:
        """
        获取拥有指定权限的所有用户
        
        Args:
            permission_code: 权限代码
            
        Returns:
            List[str]: 用户名列表
        """
        session = get_session(self.db_url)
        try:
            # 查找拥有此权限的所有角色
            permission = session.query(Permission).filter_by(code=permission_code).first()
            if not permission:
                return []
            
            users = set()
            for role in permission.roles:
                for user in role.users:
                    users.add(user.user_name)
            
            return list(users)
            
        finally:
            session.close()
    
    def get_permission_summary(self) -> Dict[str, Any]:
        """
        获取权限系统概览
        
        Returns:
            Dict: 权限系统统计信息
        """
        session = get_session(self.db_url)
        try:
            total_permissions = session.query(Permission).count()
            total_roles = session.query(Role).count()
            total_users = session.query(WebManagerUser).count()
            
            # 统计各角色的用户数
            role_stats = []
            roles = session.query(Role).all()
            for role in roles:
                user_count = len(role.users)
                permission_count = len(role.permissions)
                role_stats.append({
                    "name": role.name,
                    "description": role.description,
                    "is_builtin": role.is_builtin,
                    "user_count": user_count,
                    "permission_count": permission_count
                })
            
            return {
                "total_permissions": total_permissions,
                "total_roles": total_roles,
                "total_users": total_users,
                "role_stats": role_stats
            }
            
        finally:
            session.close()
    
    def get_permissions_tree(
        self, 
        project: str = None, 
        action_type: str = None
    ) -> Dict[str, Any]:
        """获取多层级权限树
        
        按分类分组权限，支持多层级结构（Category > Subcategory > Permission）。
        分类按 sort_order 排序，分类内权限也按 sort_order 排序。
        支持按项目和操作类型过滤权限。
        
        Args:
            project: 项目过滤，只返回指定项目的权限和全局权限
            action_type: 操作类型过滤 (create, read, update, delete, execute, export)
            
        Returns:
            Dict[str, Any]: 多层级权限树结构，格式如下:
            {
                "categories": [
                    {
                        "code": "system",
                        "name": "系统管理",
                        "description": "系统级别管理功能",
                        "icon": "⚙️",
                        "sort_order": 1,
                        "subcategories": [
                            {
                                "code": "user",
                                "name": "用户管理",
                                "description": "用户账户相关权限",
                                "icon": "👤",
                                "sort_order": 1,
                                "subcategories": [],
                                "permissions": [
                                    {
                                        "id": 1,
                                        "code": "user:read",
                                        "name": "查看用户",
                                        "description": "查看用户列表和详情",
                                        "action_type": "read",
                                        "action_type_display": "查看",
                                        "project_scope": null,
                                        "sort_order": 1
                                    },
                                    ...
                                ]
                            },
                            ...
                        ],
                        "permissions": [...]
                    },
                    ...
                ]
            }
            
        Requirements:
            - 5.1: 返回多层级 Permission_Tree 结构
            - 5.2: 包含 categories 及嵌套的 subcategories 和 permission items
            - 5.3: 每个 Permission_Item 包含 action_type 信息
            - 5.4: 支持 project 参数过滤
            - 5.5: 支持 action_type 参数过滤
            - 5.6: 响应格式为 { categories: [...] }
        """
        session = get_session(self.db_url)
        try:
            # 查询顶级分类（parent_code 为 None 的分类）
            query = session.query(PermissionCategory).filter(
                PermissionCategory.parent_code.is_(None)
            ).order_by(PermissionCategory.sort_order)
            
            categories = query.all()
            result = []
            
            for cat in categories:
                cat_dict = self._build_category_tree(
                    session, cat, project, action_type
                )
                # 只添加有权限或有子分类的分类
                if cat_dict['permissions'] or cat_dict['subcategories']:
                    result.append(cat_dict)
            
            # 处理未分类的权限（category_code 为 None 的权限）
            uncategorized_permissions = self._get_filtered_permissions(
                session, None, project, action_type
            )
            
            if uncategorized_permissions:
                result.append({
                    "code": "uncategorized",
                    "name": "未分类",
                    "description": "未分配分类的权限",
                    "icon": "📁",
                    "sort_order": 999,
                    "subcategories": [],
                    "permissions": uncategorized_permissions
                })
            
            return {'categories': result}
            
        finally:
            session.close()
    
    def _build_category_tree(
        self, 
        session, 
        category: PermissionCategory,
        project: str = None,
        action_type: str = None
    ) -> Dict[str, Any]:
        """递归构建分类树
        
        递归遍历分类及其子分类，构建完整的树形结构。
        支持按项目和操作类型过滤权限。
        
        Args:
            session: 数据库会话
            category: 当前分类对象
            project: 项目过滤
            action_type: 操作类型过滤
            
        Returns:
            Dict[str, Any]: 分类树节点，包含子分类和权限列表
        """
        # 查询子分类
        subcategories = session.query(PermissionCategory).filter(
            PermissionCategory.parent_code == category.code
        ).order_by(PermissionCategory.sort_order).all()
        
        # 递归构建子分类树，过滤掉空的子分类
        subcategory_dicts = []
        for sub in subcategories:
            sub_dict = self._build_category_tree(session, sub, project, action_type)
            # 只添加有权限或有子分类的子分类
            if sub_dict['permissions'] or sub_dict['subcategories']:
                subcategory_dicts.append(sub_dict)
        
        # 获取该分类下的权限（应用过滤条件）
        permissions = self._get_filtered_permissions(
            session, category.code, project, action_type
        )
        
        return {
            'code': category.code,
            'name': category.name,
            'description': category.description,
            'icon': category.icon,
            'sort_order': category.sort_order,
            'subcategories': subcategory_dicts,
            'permissions': permissions
        }
    
    def _get_filtered_permissions(
        self,
        session,
        category_code: str,
        project: str = None,
        action_type: str = None
    ) -> List[Dict[str, Any]]:
        """获取过滤后的权限列表
        
        根据分类代码、项目和操作类型过滤权限。
        
        Args:
            session: 数据库会话
            category_code: 分类代码，None 表示未分类权限
            project: 项目过滤，只返回指定项目的权限和全局权限
            action_type: 操作类型过滤
            
        Returns:
            List[Dict[str, Any]]: 权限字典列表
        """
        from sqlalchemy import or_
        from ..user_models import ACTION_TYPE_DISPLAY
        
        # 构建基础查询
        if category_code is None:
            perm_query = session.query(Permission).filter(
                Permission.category_code.is_(None)
            )
        else:
            perm_query = session.query(Permission).filter(
                Permission.category_code == category_code
            )
        
        # 应用项目过滤：返回指定项目的权限和全局权限（project_scope 为 None）
        if project:
            perm_query = perm_query.filter(
                or_(
                    Permission.project_scope == project,
                    Permission.project_scope.is_(None)
                )
            )
        
        # 应用操作类型过滤
        if action_type:
            perm_query = perm_query.filter(Permission.action_type == action_type)
        
        # 按 sort_order 排序
        permissions = perm_query.order_by(Permission.sort_order).all()
        
        # 转换为字典格式，包含 action_type_display
        return [
            {
                'id': p.id,
                'code': p.code,
                'name': p.name,
                'description': p.description,
                'action_type': p.action_type,
                'action_type_display': ACTION_TYPE_DISPLAY.get(p.action_type, p.action_type) if p.action_type else None,
                'project_scope': p.project_scope,
                'sort_order': p.sort_order
            }
            for p in permissions
        ]
    
    def get_permissions_tree_flat(self) -> List[Dict[str, Any]]:
        """获取扁平化的权限树形结构（向后兼容）
        
        按分类分组权限，每个分类包含其下的权限列表。
        分类按 sort_order 排序，分类内权限也按 sort_order 排序。
        
        注意：此方法保留用于向后兼容，新代码应使用 get_permissions_tree()。
        
        Returns:
            List[Dict]: 树形结构的权限列表，格式如下:
            [
                {
                    "code": "user",
                    "name": "用户管理",
                    "description": "用户账户相关权限",
                    "sort_order": 1,
                    "icon": "👤",
                    "permissions": [
                        {"id": 1, "code": "user:read", "name": "查看用户", ...},
                        {"id": 2, "code": "user:write", "name": "管理用户", ...}
                    ]
                },
                ...
            ]
        """
        session = get_session(self.db_url)
        try:
            # 获取所有分类，按 sort_order 排序
            categories = session.query(PermissionCategory).order_by(
                PermissionCategory.sort_order
            ).all()
            
            tree = []
            for category in categories:
                tree.append(category.to_tree_dict())
            
            # 处理未分类的权限（category_code 为 None 的权限）
            uncategorized_permissions = session.query(Permission).filter(
                Permission.category_code.is_(None)
            ).order_by(Permission.sort_order).all()
            
            if uncategorized_permissions:
                tree.append({
                    "code": "uncategorized",
                    "name": "未分类",
                    "description": "未分配分类的权限",
                    "sort_order": 999,
                    "icon": "📁",
                    "permissions": [perm.to_dict() for perm in uncategorized_permissions]
                })
            
            return tree
            
        finally:
            session.close()
    
    def get_user_permissions_tree(self, user_name: str) -> Dict[str, Any]:
        """
        获取用户的权限树形结构
        
        返回完整的权限树，但标记用户拥有的权限。
        支持多层级结构（Category > Subcategory > Permission）。
        
        Args:
            user_name: 用户名
            
        Returns:
            Dict[str, Any]: 带有 has_permission 标记的多层级权限树
        """
        # 获取用户的权限集合
        user_permissions = self.get_user_permissions(user_name)
        
        # 获取完整的权限树
        tree = self.get_permissions_tree()
        
        # 递归标记用户拥有的权限
        def mark_permissions(categories: List[Dict[str, Any]]):
            for category in categories:
                # 标记当前分类下的权限
                for perm in category.get('permissions', []):
                    perm['has_permission'] = perm['code'] in user_permissions
                # 递归处理子分类
                if category.get('subcategories'):
                    mark_permissions(category['subcategories'])
        
        mark_permissions(tree.get('categories', []))
        
        return tree
    
    def list_categories(self) -> List[Dict[str, Any]]:
        """
        获取所有权限分类列表
        
        Returns:
            List[Dict]: 分类列表
        """
        session = get_session(self.db_url)
        try:
            categories = session.query(PermissionCategory).order_by(
                PermissionCategory.sort_order
            ).all()
            return [cat.to_dict() for cat in categories]
        finally:
            session.close()
    
    def get_category(self, category_code: str) -> Optional[Dict[str, Any]]:
        """
        获取单个权限分类
        
        Args:
            category_code: 分类代码
            
        Returns:
            Optional[Dict]: 分类信息或 None
        """
        session = get_session(self.db_url)
        try:
            category = session.query(PermissionCategory).filter_by(
                code=category_code
            ).first()
            return category.to_dict() if category else None
        finally:
            session.close()
    
    def create_category(self, code: str, name: str, description: str = None,
                       sort_order: int = 0, icon: str = None) -> Dict[str, Any]:
        """
        创建新的权限分类
        
        Args:
            code: 分类代码
            name: 分类名称
            description: 分类描述
            sort_order: 排序顺序
            icon: 图标
            
        Returns:
            Dict: {"success": bool, "category": dict|None, "error": str|None}
        """
        session = get_session(self.db_url)
        try:
            # 检查分类代码是否已存在
            existing = session.query(PermissionCategory).filter_by(code=code).first()
            if existing:
                return {
                    "success": False,
                    "category": None,
                    "error": f"分类代码 '{code}' 已存在"
                }
            
            # 创建分类
            category = PermissionCategory(
                code=code,
                name=name,
                description=description,
                sort_order=sort_order,
                icon=icon
            )
            
            session.add(category)
            session.commit()
            session.refresh(category)
            
            return {
                "success": True,
                "category": category.to_dict(),
                "error": None
            }
            
        except Exception as e:
            session.rollback()
            return {
                "success": False,
                "category": None,
                "error": f"创建分类失败：{str(e)}"
            }
        finally:
            session.close()
    
    def auto_assign_category(self, permission_code: str) -> Optional[str]:
        """
        根据权限代码自动分配分类
        
        从权限代码中提取分类代码（冒号前的部分），
        如果对应分类存在，则分配该分类。
        
        Args:
            permission_code: 权限代码（如 'user:read'）
            
        Returns:
            Optional[str]: 分配的分类代码，如果无法分配则返回 None
        """
        if ':' not in permission_code:
            return None
        
        category_code = permission_code.split(':')[0]
        
        session = get_session(self.db_url)
        try:
            # 检查分类是否存在
            category = session.query(PermissionCategory).filter_by(
                code=category_code
            ).first()
            
            if not category:
                return None
            
            # 更新权限的分类
            permission = session.query(Permission).filter_by(
                code=permission_code
            ).first()
            
            if permission and permission.category_code is None:
                permission.category_code = category_code
                session.commit()
                return category_code
            
            return permission.category_code if permission else None
            
        finally:
            session.close()
    
    def init_default_categories(self) -> Dict[str, Any]:
        """
        初始化默认权限分类
        
        创建默认的权限分类（user, role, audit, config, queue）。
        幂等操作，已存在的分类不会重复创建。
        
        Returns:
            Dict: {"success": bool, "created": list, "skipped": list, "error": str|None}
        """
        from ..user_models import DEFAULT_PERMISSION_CATEGORIES
        
        session = get_session(self.db_url)
        created = []
        skipped = []
        
        try:
            for cat_data in DEFAULT_PERMISSION_CATEGORIES:
                existing = session.query(PermissionCategory).filter_by(
                    code=cat_data['code']
                ).first()
                
                if existing:
                    skipped.append(cat_data['code'])
                else:
                    category = PermissionCategory(**cat_data)
                    session.add(category)
                    created.append(cat_data['code'])
            
            session.commit()
            
            return {
                "success": True,
                "created": created,
                "skipped": skipped,
                "error": None
            }
            
        except Exception as e:
            session.rollback()
            return {
                "success": False,
                "created": [],
                "skipped": [],
                "error": f"初始化分类失败：{str(e)}"
            }
        finally:
            session.close()
    
    def get_permissions_by_category(self, category_code: str) -> List[Dict[str, Any]]:
        """
        获取指定分类下的所有权限
        
        Args:
            category_code: 分类代码
            
        Returns:
            List[Dict]: 权限列表
        """
        session = get_session(self.db_url)
        try:
            permissions = session.query(Permission).filter_by(
                category_code=category_code
            ).order_by(Permission.sort_order).all()
            
            return [perm.to_dict() for perm in permissions]
        finally:
            session.close()
    
    def update_permission_category(self, permission_code: str, 
                                   category_code: Optional[str]) -> Dict[str, Any]:
        """
        更新权限的分类
        
        Args:
            permission_code: 权限代码
            category_code: 新的分类代码（None 表示移除分类）
            
        Returns:
            Dict: {"success": bool, "error": str|None}
        """
        session = get_session(self.db_url)
        try:
            permission = session.query(Permission).filter_by(
                code=permission_code
            ).first()
            
            if not permission:
                return {
                    "success": False,
                    "error": f"权限 '{permission_code}' 不存在"
                }
            
            # 如果指定了分类，检查分类是否存在
            if category_code:
                category = session.query(PermissionCategory).filter_by(
                    code=category_code
                ).first()
                if not category:
                    return {
                        "success": False,
                        "error": f"分类 '{category_code}' 不存在"
                    }
            
            permission.category_code = category_code
            session.commit()
            
            return {"success": True, "error": None}
            
        except Exception as e:
            session.rollback()
            return {
                "success": False,
                "error": f"更新权限分类失败：{str(e)}"
            }
        finally:
            session.close()
    
    def audit_routes(self, app) -> Dict[str, Any]:
        """
        审计应用中所有路由的权限保护状态
        
        扫描 Flask 应用中所有注册的路由，检查每个路由是否有权限保护，
        并记录未受保护的端点警告。
        
        Args:
            app: Flask 应用实例
            
        Returns:
            Dict: {
                "routes": List[Dict],  # 所有路由信息
                "warnings": List[str],  # 未受保护路由的警告信息
                "summary": {
                    "total_routes": int,
                    "protected_routes": int,
                    "unprotected_routes": int,
                    "login_required_only": int
                }
            }
        """
        import logging
        logger = logging.getLogger('funboost.permission_audit')
        
        routes = []
        warnings = []
        protected_count = 0
        unprotected_count = 0
        login_only_count = 0
        
        # 需要排除的端点（静态文件、公开接口等）
        excluded_endpoints = {
            'static',
            'auth.login',
            'auth.logout',
            'auth.forgot_password',
            'auth.reset_password',
            'auth.api_login',  # 登录 API
            'auth.api_logout',  # 登出 API
            'main.index',
            'main.health',
            'main.api_health',
            'profile.api_profile',  # 用户自己的资料
            'profile.api_change_password',  # 用户自己改密码
            'admin_users.api_current_user_permissions',  # 用户自己的权限
            'admin_users.api_current_user_permissions_tree',  # 用户自己的权限树
        }
        
        # 需要排除的路由前缀（公开接口）
        excluded_prefixes = [
            '/static/',
            '/faas/',  # FAAS 接口可能有自己的认证机制
        ]
        
        for rule in app.url_map.iter_rules():
            # 跳过静态文件路由
            if rule.endpoint in excluded_endpoints:
                continue
            
            # 跳过排除的前缀
            rule_str = str(rule)
            if any(rule_str.startswith(prefix) for prefix in excluded_prefixes):
                continue
            
            # 获取视图函数
            view_func = app.view_functions.get(rule.endpoint)
            if not view_func:
                continue
            
            # 检查是否需要登录（通过检查装饰器）
            requires_login = self._check_requires_login(view_func)
            
            # 检查是否有权限要求
            required_permission = None
            if hasattr(view_func, '_required_permission'):
                required_permission = view_func._required_permission
            
            # 判断保护状态
            is_protected = required_permission is not None
            
            methods = [m for m in rule.methods if m not in ('HEAD', 'OPTIONS')]
            
            route_info = {
                "endpoint": rule.endpoint,
                "methods": methods,
                "rule": rule_str,
                "requires_login": requires_login,
                "required_permission": required_permission,
                "is_protected": is_protected
            }
            routes.append(route_info)
            
            if is_protected:
                protected_count += 1
            elif requires_login:
                login_only_count += 1
                # 需要登录但没有权限保护的路由，记录警告
                warning_msg = f"WARNING: Route '{rule_str}' ({rule.endpoint}) requires login but lacks permission protection"
                warnings.append(warning_msg)
                logger.warning(warning_msg)
            else:
                unprotected_count += 1
                # 完全没有保护的管理接口，记录警告
                if '/admin/' in rule_str or '/api/' in rule_str:
                    warning_msg = f"WARNING: Admin/API route '{rule_str}' ({rule.endpoint}) lacks permission protection"
                    warnings.append(warning_msg)
                    logger.warning(warning_msg)
        
        # 按端点名称排序
        routes.sort(key=lambda x: x['endpoint'])
        
        return {
            "routes": routes,
            "warnings": warnings,
            "summary": {
                "total_routes": len(routes),
                "protected_routes": protected_count,
                "unprotected_routes": unprotected_count,
                "login_required_only": login_only_count
            }
        }
    
    def _check_requires_login(self, view_func) -> bool:
        """
        检查视图函数是否需要登录
        
        通过检查函数是否被 login_required 装饰器包装来判断。
        
        Args:
            view_func: 视图函数
            
        Returns:
            bool: 是否需要登录
        """
        # 检查是否有 __wrapped__ 属性（被装饰器包装）
        if hasattr(view_func, '__wrapped__'):
            # 检查装饰器链中是否有 login_required
            func = view_func
            while hasattr(func, '__wrapped__'):
                if 'login_required' in str(func):
                    return True
                func = func.__wrapped__
        
        # 检查函数名或模块中是否包含 login_required 相关信息
        func_str = str(view_func)
        if 'login_required' in func_str:
            return True
        
        # 检查函数的 __name__ 属性
        if hasattr(view_func, '__name__'):
            # 如果函数被 login_required 装饰，通常会保留原函数名
            pass
        
        return False
    
    def log_audit_summary(self, audit_result: Dict[str, Any]) -> None:
        """
        记录审计结果摘要到日志
        
        Args:
            audit_result: audit_routes() 返回的结果
        """
        import logging
        logger = logging.getLogger('funboost.permission_audit')
        
        summary = audit_result.get('summary', {})
        warnings = audit_result.get('warnings', [])
        
        logger.info("=" * 60)
        logger.info("Permission Audit Summary")
        logger.info("=" * 60)
        logger.info(f"Total routes: {summary.get('total_routes', 0)}")
        logger.info(f"Protected routes: {summary.get('protected_routes', 0)}")
        logger.info(f"Login required only: {summary.get('login_required_only', 0)}")
        logger.info(f"Unprotected routes: {summary.get('unprotected_routes', 0)}")
        
        if warnings:
            logger.warning(f"Found {len(warnings)} unprotected endpoints:")
            for warning in warnings:
                logger.warning(f"  - {warning}")
        else:
            logger.info("All admin/API routes are properly protected.")
        
        logger.info("=" * 60)
    
    def create_permission_dynamic(self, code: str, name: str, 
                                  description: str = None,
                                  category_code: str = None,
                                  sort_order: int = 0) -> Dict[str, Any]:
        """
        动态创建新权限（运行时创建，无需代码修改或数据库迁移）
        
        支持在运行时创建新权限，自动分配分类（如果未指定）。
        
        Args:
            code: 权限代码（如 'user:read'）
            name: 权限名称
            description: 权限描述
            category_code: 分类代码（可选，如果不提供则自动从 code 推断）
            sort_order: 排序顺序
            
        Returns:
            Dict: {"success": bool, "permission": dict|None, "error": str|None}
        """
        session = get_session(self.db_url)
        try:
            # 检查权限代码是否已存在
            existing = session.query(Permission).filter_by(code=code).first()
            if existing:
                return {
                    "success": False,
                    "permission": existing.to_dict(),
                    "error": f"权限代码 '{code}' 已存在"
                }
            
            # 如果未指定分类，尝试自动分配
            if not category_code and ':' in code:
                inferred_category = code.split(':')[0]
                # 检查推断的分类是否存在
                category = session.query(PermissionCategory).filter_by(
                    code=inferred_category
                ).first()
                if category:
                    category_code = inferred_category
            
            # 如果指定了分类，验证分类是否存在
            if category_code:
                category = session.query(PermissionCategory).filter_by(
                    code=category_code
                ).first()
                if not category:
                    return {
                        "success": False,
                        "permission": None,
                        "error": f"分类 '{category_code}' 不存在"
                    }
            
            # 创建权限
            permission = Permission(
                code=code,
                name=name,
                description=description,
                category_code=category_code,
                sort_order=sort_order
            )
            
            session.add(permission)
            session.commit()
            session.refresh(permission)
            
            return {
                "success": True,
                "permission": permission.to_dict(),
                "error": None
            }
            
        except Exception as e:
            session.rollback()
            return {
                "success": False,
                "permission": None,
                "error": f"创建权限失败：{str(e)}"
            }
        finally:
            session.close()
    
    def create_category_dynamic(self, code: str, name: str,
                                description: str = None,
                                sort_order: int = 0,
                                icon: str = None) -> Dict[str, Any]:
        """
        动态创建新权限分类（运行时创建，无需代码修改或数据库迁移）
        
        Args:
            code: 分类代码
            name: 分类名称
            description: 分类描述
            sort_order: 排序顺序
            icon: 图标
            
        Returns:
            Dict: {"success": bool, "category": dict|None, "error": str|None}
        """
        return self.create_category(code, name, description, sort_order, icon)
    
    def ensure_permission_exists(self, code: str, name: str = None,
                                 description: str = None) -> Dict[str, Any]:
        """
        确保权限存在（如果不存在则创建）
        
        这是一个幂等操作，可以安全地多次调用。
        
        Args:
            code: 权限代码
            name: 权限名称（如果不提供，则从 code 生成）
            description: 权限描述
            
        Returns:
            Dict: {"success": bool, "permission": dict, "created": bool, "error": str|None}
        """
        session = get_session(self.db_url)
        try:
            # 检查权限是否已存在
            existing = session.query(Permission).filter_by(code=code).first()
            if existing:
                return {
                    "success": True,
                    "permission": existing.to_dict(),
                    "created": False,
                    "error": None
                }
            
            # 如果未提供名称，从 code 生成
            if not name:
                # 将 'user:read' 转换为 '用户读取' 或保持原样
                name = code.replace(':', ' - ')
            
            # 创建权限
            result = self.create_permission_dynamic(code, name, description)
            if result['success']:
                result['created'] = True
            else:
                result['created'] = False
            
            return result
            
        finally:
            session.close()
    
    def ensure_category_exists(self, code: str, name: str = None,
                               description: str = None,
                               sort_order: int = 0,
                               icon: str = None) -> Dict[str, Any]:
        """
        确保权限分类存在（如果不存在则创建）
        
        这是一个幂等操作，可以安全地多次调用。
        
        Args:
            code: 分类代码
            name: 分类名称（如果不提供，则使用 code）
            description: 分类描述
            sort_order: 排序顺序
            icon: 图标
            
        Returns:
            Dict: {"success": bool, "category": dict, "created": bool, "error": str|None}
        """
        session = get_session(self.db_url)
        try:
            # 检查分类是否已存在
            existing = session.query(PermissionCategory).filter_by(code=code).first()
            if existing:
                return {
                    "success": True,
                    "category": existing.to_dict(),
                    "created": False,
                    "error": None
                }
            
            # 如果未提供名称，使用 code
            if not name:
                name = code.capitalize()
            
            # 创建分类
            result = self.create_category_dynamic(code, name, description, sort_order, icon)
            if result['success']:
                result['created'] = True
            else:
                result['created'] = False
            
            return result
            
        finally:
            session.close()

    def get_templates(self) -> List[Dict[str, Any]]:
        """获取权限模板列表
        
        返回所有权限模板，包含模板自身的权限和继承的所有权限。
        
        Returns:
            List[Dict[str, Any]]: 权限模板列表，每个模板包含以下字段:
            - code: 模板代码
            - name: 模板名称
            - description: 模板描述
            - permissions: 模板自身的权限列表（不含继承）
            - all_permissions: 包含继承的所有权限列表
            - parent_template_code: 父模板代码（用于继承）
            - is_builtin: 是否为内置模板
            
        Requirements:
            - 14.1: THE Permission_System SHALL provide predefined permission templates: 
                    只读用户, 操作员, 管理员, 项目管理员
            - 14.5: THE Permission_System SHALL support template inheritance 
                    (e.g., 管理员 extends 操作员)
                    
        Example:
            >>> service = PermissionService()
            >>> templates = service.get_templates()
            >>> # 返回格式示例:
            >>> # [
            >>> #     {
            >>> #         'code': 'viewer',
            >>> #         'name': '只读用户',
            >>> #         'description': '只能查看，不能修改',
            >>> #         'permissions': ['user:read', 'role:read', ...],
            >>> #         'all_permissions': ['user:read', 'role:read', ...],
            >>> #         'parent_template_code': None,
            >>> #         'is_builtin': True
            >>> #     },
            >>> #     {
            >>> #         'code': 'operator',
            >>> #         'name': '操作员',
            >>> #         'description': '可以执行队列操作',
            >>> #         'permissions': ['queue:execute', ...],
            >>> #         'all_permissions': ['user:read', 'queue:execute', ...],  # 包含继承自 viewer 的权限
            >>> #         'parent_template_code': 'viewer',
            >>> #         'is_builtin': True
            >>> #     },
            >>> #     ...
            >>> # ]
        """
        from ..user_models import PermissionTemplate
        
        session = get_session(self.db_url)
        try:
            templates = session.query(PermissionTemplate).all()
            return [
                {
                    'code': t.code,
                    'name': t.name,
                    'description': t.description,
                    'permissions': t.get_permissions(),
                    'all_permissions': t.get_all_permissions(session),
                    'parent_template_code': t.parent_template_code,
                    'is_builtin': t.is_builtin
                }
                for t in templates
            ]
        finally:
            session.close()
    
    def apply_template(self, template_code: str) -> Dict[str, Any]:
        """应用权限模板，获取模板的所有权限（包含继承的权限）
        
        用于在创建或编辑角色时，根据模板预选权限。
        返回模板的所有权限列表，包括从父模板继承的权限。
        
        Args:
            template_code: 模板代码（如 'viewer', 'operator', 'admin'）
            
        Returns:
            Dict[str, Any]: 应用结果，包含以下字段:
            - success: 是否成功
            - template: 模板信息（如果成功）
            - permissions: 模板的所有权限列表（包含继承，如果成功）
            - error: 错误信息（如果失败）
            
        Requirements:
            - 14.4: WHEN a template is applied, THE Permission_Tree_Component SHALL 
                    pre-select the template's permissions
            - 14.5: THE Permission_System SHALL support template inheritance 
                    (e.g., 管理员 extends 操作员)
                    
        Example:
            >>> service = PermissionService()
            >>> result = service.apply_template('operator')
            >>> # 成功时返回:
            >>> # {
            >>> #     'success': True,
            >>> #     'template': {
            >>> #         'code': 'operator',
            >>> #         'name': '操作员',
            >>> #         'description': '可以执行队列操作',
            >>> #         'parent_template_code': 'viewer',
            >>> #         'is_builtin': True
            >>> #     },
            >>> #     'permissions': ['user:read', 'role:read', 'queue:execute', ...],
            >>> #     'error': None
            >>> # }
            >>> 
            >>> result = service.apply_template('nonexistent')
            >>> # 失败时返回:
            >>> # {
            >>> #     'success': False,
            >>> #     'template': None,
            >>> #     'permissions': [],
            >>> #     'error': "模板 'nonexistent' 不存在"
            >>> # }
        """
        from ..user_models import PermissionTemplate
        
        session = get_session(self.db_url)
        try:
            template = session.query(PermissionTemplate).filter_by(
                code=template_code
            ).first()
            
            if not template:
                return {
                    'success': False,
                    'template': None,
                    'permissions': [],
                    'error': f"模板 '{template_code}' 不存在"
                }
            
            # 获取模板的所有权限（包含继承的权限）
            all_permissions = template.get_all_permissions(session)
            
            return {
                'success': True,
                'template': {
                    'code': template.code,
                    'name': template.name,
                    'description': template.description,
                    'parent_template_code': template.parent_template_code,
                    'is_builtin': template.is_builtin
                },
                'permissions': all_permissions,
                'error': None
            }
            
        finally:
            session.close()
    
    def get_template(self, template_code: str) -> Optional[Dict[str, Any]]:
        """获取单个权限模板
        
        Args:
            template_code: 模板代码
            
        Returns:
            Optional[Dict[str, Any]]: 模板信息，如果不存在则返回 None
        """
        from ..user_models import PermissionTemplate
        
        session = get_session(self.db_url)
        try:
            template = session.query(PermissionTemplate).filter_by(
                code=template_code
            ).first()
            
            if not template:
                return None
            
            return {
                'code': template.code,
                'name': template.name,
                'description': template.description,
                'permissions': template.get_permissions(),
                'all_permissions': template.get_all_permissions(session),
                'parent_template_code': template.parent_template_code,
                'is_builtin': template.is_builtin
            }
            
        finally:
            session.close()

    def get_user_permissions_detailed(self, user_name: str) -> Dict[str, Any]:
        """获取用户的详细权限信息（增强版）
        
        返回用户的权限列表、权限详情（含 action_type 和 project_scope）以及角色列表。
        用于前端权限上下文，支持细粒度权限控制。
        
        Args:
            user_name: 用户名
            
        Returns:
            Dict[str, Any]: 包含以下字段:
            - permissions: 权限代码列表 (List[str])
            - details: 权限详情列表，每个权限包含 code, name, action_type, project_scope
            - roles: 角色名称列表 (List[str])
            
        Requirements:
            - 5.3: WHEN the response is generated, THE Permission_Service SHALL include 
                   action_type information for each Permission_Item
                   
        Example:
            >>> service = PermissionService()
            >>> result = service.get_user_permissions_detailed('admin')
            >>> # 返回格式:
            >>> # {
            >>> #     'permissions': ['user:read', 'user:write', 'role:*', 'queue:read'],
            >>> #     'details': [
            >>> #         {
            >>> #             'code': 'user:read',
            >>> #             'name': '查看用户',
            >>> #             'action_type': 'read',
            >>> #             'project_scope': None
            >>> #         },
            >>> #         {
            >>> #             'code': 'user:write',
            >>> #             'name': '管理用户',
            >>> #             'action_type': 'update',
            >>> #             'project_scope': None
            >>> #         },
            >>> #         ...
            >>> #     ],
            >>> #     'roles': ['admin']
            >>> # }
        """
        from ..user_models import ACTION_TYPE_DISPLAY
        
        session = get_session(self.db_url)
        try:
            user = session.query(WebManagerUser).filter_by(user_name=user_name).first()
            if not user:
                return {
                    'permissions': [],
                    'details': [],
                    'roles': []
                }
            
            # 收集权限代码和详情
            permissions = set()
            permission_details = []
            seen_codes = set()  # 用于去重
            
            for role in user.roles:
                for permission in role.permissions:
                    permissions.add(permission.code)
                    
                    # 避免重复添加详情
                    if permission.code not in seen_codes:
                        seen_codes.add(permission.code)
                        permission_details.append({
                            'code': permission.code,
                            'name': permission.name,
                            'action_type': permission.action_type,
                            'project_scope': permission.project_scope
                        })
            
            # 获取角色名称列表
            roles = [role.name for role in user.roles]
            
            return {
                'permissions': list(permissions),
                'details': permission_details,
                'roles': roles
            }
            
        finally:
            session.close()


    def log_permission_change(
        self,
        operator: str,
        role_name: str,
        added_permissions: List[str],
        removed_permissions: List[str],
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        """记录权限变更审计日志
        
        当角色的权限被修改时，记录详细的审计日志，包括操作者、时间戳、
        以及添加和移除的权限列表。
        
        Args:
            operator: 执行操作的用户名（操作者）
            role_name: 被修改权限的角色名称
            added_permissions: 新增的权限代码列表
            removed_permissions: 移除的权限代码列表
            ip_address: 操作者的 IP 地址
            user_agent: 操作者的用户代理字符串
            
        Returns:
            bool: 是否记录成功
            
        Requirements:
            - 13.1: THE Permission_System SHALL log all permission changes with operator, 
                    timestamp, and change details
            - 13.2: THE Audit_Log SHALL record added and removed permissions for each change
            
        Example:
            >>> service = PermissionService()
            >>> service.log_permission_change(
            ...     operator='admin',
            ...     role_name='editor',
            ...     added_permissions=['user:create', 'user:update'],
            ...     removed_permissions=['user:delete'],
            ...     ip_address='192.168.1.1'
            ... )
            True
        """
        import json
        import logging
        
        # 使用 nb_log 风格的日志记录
        logger = logging.getLogger('funboost.permission_audit')
        
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
        
        # 记录到日志系统（按设计文档的日志策略）
        logger.info(
            f"Permission change: operator={operator}, role={role_name}, "
            f"added={added_permissions}, removed={removed_permissions}"
        )
        
        # 记录到数据库审计日志
        session = get_session(self.db_url)
        try:
            from ..user_models import AuditLog
            
            audit_log = AuditLog(
                event_type='permission_change',
                user_name=operator,
                ip_address=ip_address,
                user_agent=user_agent,
                details=json.dumps(details, ensure_ascii=False)
            )
            session.add(audit_log)
            session.commit()
            
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log permission change: {e}", exc_info=True)
            return False
        finally:
            session.close()
    
    def log_user_role_change(
        self,
        operator: str,
        target_user: str,
        change_type: str,
        role_name: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        """记录用户角色变更审计日志
        
        当用户的角色被分配或移除时，记录详细的审计日志。
        
        Args:
            operator: 执行操作的用户名（操作者）
            target_user: 被修改角色的用户名
            change_type: 变更类型，'assign' 表示分配角色，'remove' 表示移除角色
            role_name: 被分配或移除的角色名称
            ip_address: 操作者的 IP 地址
            user_agent: 操作者的用户代理字符串
            
        Returns:
            bool: 是否记录成功
            
        Requirements:
            - 13.3: THE Audit_Log SHALL record user role assignments and removals
            
        Example:
            >>> service = PermissionService()
            >>> service.log_user_role_change(
            ...     operator='admin',
            ...     target_user='john',
            ...     change_type='assign',
            ...     role_name='editor',
            ...     ip_address='192.168.1.1'
            ... )
            True
        """
        import json
        import logging
        
        logger = logging.getLogger('funboost.permission_audit')
        
        # 确定事件类型
        event_type = 'user_role_assign' if change_type == 'assign' else 'user_role_remove'
        
        # 构建审计详情
        details = {
            'target_user': target_user,
            'role_name': role_name,
            'change_type': change_type
        }
        
        # 记录到日志系统
        action_desc = '分配' if change_type == 'assign' else '移除'
        logger.info(
            f"User role change: operator={operator}, target_user={target_user}, "
            f"action={action_desc}, role={role_name}"
        )
        
        # 记录到数据库审计日志
        session = get_session(self.db_url)
        try:
            from ..user_models import AuditLog
            
            audit_log = AuditLog(
                event_type=event_type,
                user_name=operator,
                ip_address=ip_address,
                user_agent=user_agent,
                details=json.dumps(details, ensure_ascii=False)
            )
            session.add(audit_log)
            session.commit()
            
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log user role change: {e}", exc_info=True)
            return False
        finally:
            session.close()
    
    def get_permission_change_history(
        self,
        role_name: str = None,
        user_name: str = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """查询权限变更历史
        
        查询指定角色或用户的权限变更历史记录。
        
        Args:
            role_name: 角色名称过滤（可选）
            user_name: 用户名过滤（可选，查询该用户的角色变更）
            page: 页码（从1开始）
            page_size: 每页大小
            
        Returns:
            Dict[str, Any]: 包含以下字段:
            - logs: 审计日志列表
            - total: 总记录数
            - page: 当前页码
            - page_size: 每页大小
            
        Requirements:
            - 13.4: THE Permission_System SHALL provide an API to query permission 
                    change history for a specific role or user
                    
        Example:
            >>> service = PermissionService()
            >>> result = service.get_permission_change_history(role_name='editor')
            >>> # 返回格式:
            >>> # {
            >>> #     'logs': [
            >>> #         {
            >>> #             'id': 1,
            >>> #             'event_type': 'permission_change',
            >>> #             'user_name': 'admin',
            >>> #             'details': {
            >>> #                 'role_name': 'editor',
            >>> #                 'added_permissions': ['user:create'],
            >>> #                 'removed_permissions': []
            >>> #             },
            >>> #             'created_at': '2024-01-15T10:30:00'
            >>> #         },
            >>> #         ...
            >>> #     ],
            >>> #     'total': 10,
            >>> #     'page': 1,
            >>> #     'page_size': 50
            >>> # }
        """
        import json
        from sqlalchemy import or_
        from ..user_models import AuditLog
        
        session = get_session(self.db_url)
        try:
            # 构建查询 - 查询权限变更和用户角色变更事件
            query = session.query(AuditLog).filter(
                AuditLog.event_type.in_([
                    'permission_change',
                    'user_role_assign',
                    'user_role_remove',
                    'role_permission_add',
                    'role_permission_remove'
                ])
            )
            
            # 如果指定了角色名称，过滤包含该角色的记录
            if role_name:
                # 在 details JSON 中搜索角色名称
                query = query.filter(
                    AuditLog.details.like(f'%"role_name": "{role_name}"%') |
                    AuditLog.details.like(f'%"role_name":"{role_name}"%')
                )
            
            # 如果指定了用户名，过滤包含该用户的记录
            if user_name:
                query = query.filter(
                    AuditLog.details.like(f'%"target_user": "{user_name}"%') |
                    AuditLog.details.like(f'%"target_user":"{user_name}"%')
                )
            
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
                'logs': log_dicts,
                'total': total,
                'page': page,
                'page_size': page_size
            }
            
        finally:
            session.close()

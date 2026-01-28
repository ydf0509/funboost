"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";

// 用户权限数据类型
type UserPermissionsData = {
  user_name: string;
  permissions: string[];
  roles: string[];
};

// Hook 返回类型
type UseUserPermissionsReturn = {
  /** 用户权限列表 */
  permissions: string[];
  /** 用户角色列表 */
  roles: string[];
  /** 用户名 */
  userName: string | null;
  /** 是否正在加载 */
  loading: boolean;
  /** 错误信息 */
  error: string | null;
  /** 是否已认证 */
  isAuthenticated: boolean;
  /** 检查是否拥有指定权限 */
  hasPermission: (permissionCode: string) => boolean;
  /** 检查是否拥有任意一个指定权限 */
  hasAnyPermission: (permissionCodes: string[]) => boolean;
  /** 检查是否拥有所有指定权限 */
  hasAllPermissions: (permissionCodes: string[]) => boolean;
  /** 检查是否为管理员 */
  isAdmin: boolean;
  /** 刷新权限数据 */
  refresh: () => Promise<void>;
};

/**
 * 用户权限 Hook
 * 
 * 从 API 获取当前登录用户的权限列表，提供权限检查方法。
 * 用于前端菜单权限控制和页面访问控制。
 * 
 * @example
 * ```tsx
 * const { hasPermission, hasAnyPermission, isAdmin } = useUserPermissions();
 * 
 * if (hasPermission('user:write')) {
 *   // 显示编辑按钮
 * }
 * 
 * if (hasAnyPermission(['user:read', 'user:write'])) {
 *   // 显示用户管理菜单
 * }
 * ```
 */
export function useUserPermissions(): UseUserPermissionsReturn {
  const router = useRouter();
  const [permissions, setPermissions] = useState<string[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [userName, setUserName] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // 权限集合（用于快速查找）
  const permissionSet = useMemo(() => new Set(permissions), [permissions]);

  // 获取用户权限
  const fetchPermissions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch("/admin/api/user/permissions", {
        credentials: "include",
      });

      if (!response.ok) {
        if (response.status === 401) {
          // 未登录，重定向到登录页面
          setPermissions([]);
          setRoles([]);
          setUserName(null);
          setIsAuthenticated(false);
          router.push("/login");
          return;
        }
        throw new Error(`获取权限失败: ${response.status}`);
      }

      const result = await response.json();
      if (result.success && result.data) {
        const data = result.data as UserPermissionsData;
        setPermissions(data.permissions || []);
        setRoles(data.roles || []);
        setUserName(data.user_name || null);
        setIsAuthenticated(true);
      } else {
        throw new Error(result.error || "获取权限失败");
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "获取权限失败";
      setError(message);
      console.error("获取用户权限失败:", err);
    } finally {
      setLoading(false);
    }
  }, [router]);

  // 初始加载
  useEffect(() => {
    fetchPermissions();
  }, [fetchPermissions]);

  // 检查是否拥有指定权限
  const hasPermission = useCallback(
    (permissionCode: string): boolean => {
      return permissionSet.has(permissionCode);
    },
    [permissionSet]
  );

  // 检查是否拥有任意一个指定权限
  const hasAnyPermission = useCallback(
    (permissionCodes: string[]): boolean => {
      return permissionCodes.some((code) => permissionSet.has(code));
    },
    [permissionSet]
  );

  // 检查是否拥有所有指定权限
  const hasAllPermissions = useCallback(
    (permissionCodes: string[]): boolean => {
      return permissionCodes.every((code) => permissionSet.has(code));
    },
    [permissionSet]
  );

  // 检查是否为管理员
  const isAdmin = useMemo(() => roles.includes("admin"), [roles]);

  return {
    permissions,
    roles,
    userName,
    loading,
    error,
    isAuthenticated,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    isAdmin,
    refresh: fetchPermissions,
  };
}

/**
 * 权限上下文类型（用于 Context Provider）
 */
export type PermissionContextType = UseUserPermissionsReturn;

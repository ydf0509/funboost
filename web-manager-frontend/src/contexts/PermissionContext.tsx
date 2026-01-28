"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  useEffect,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";

// ============================================================================
// Types
// ============================================================================

/**
 * 标准操作类型
 */
export type ActionType = "create" | "read" | "update" | "delete" | "execute" | "export";

/**
 * 权限详情
 */
export interface PermissionDetail {
  code: string;
  name: string;
  action_type: string;
  project_scope: string | null;
}

/**
 * 权限状态
 */
interface PermissionState {
  permissions: string[];
  permissionDetails: PermissionDetail[];
  roles: string[];
  userName: string | null;
  loading: boolean;
  error: string | null;
  isAuthenticated: boolean;
}

/**
 * 权限上下文值
 */
export interface PermissionContextValue extends PermissionState {
  // 权限检查方法
  hasPermission: (code: string, project?: string) => boolean;
  hasAnyPermission: (codes: string[], project?: string) => boolean;
  hasAllPermissions: (codes: string[], project?: string) => boolean;

  // 操作类型检查
  hasActionPermission: (module: string, action: ActionType, project?: string) => boolean;

  // 检查是否为管理员
  isAdmin: boolean;

  // 刷新权限
  refresh: () => Promise<void>;

  // 清除缓存（用于登出）
  clearCache: () => void;
}

// ============================================================================
// Constants
// ============================================================================

/** 权限缓存 key */
const CACHE_KEY = "user_permissions_cache";

/** 缓存 TTL: 5 分钟 (Requirement 15.2) */
const CACHE_TTL = 5 * 60 * 1000;

// ============================================================================
// Context
// ============================================================================

const PermissionContext = createContext<PermissionContextValue | null>(null);

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * 通配符匹配
 * 
 * 支持 * 通配符，例如：
 * - user:* 匹配 user:read, user:write 等
 * - projectA:queue:* 匹配 projectA:queue:read 等
 * 
 * @param userPerms 用户权限列表
 * @param required 所需权限
 * @returns 是否匹配
 */
function matchWildcard(userPerms: string[], required: string): boolean {
  for (const perm of userPerms) {
    if (!perm.includes("*")) continue;
    // 将通配符转换为正则表达式
    // 转义特殊字符，然后将 * 替换为 .*
    const escaped = perm.replace(/[.+?^${}()|[\]\\]/g, "\\$&");
    const pattern = new RegExp("^" + escaped.replace(/\*/g, ".*") + "$");
    if (pattern.test(required)) return true;
  }
  return false;
}

/**
 * 从 localStorage 获取缓存的权限数据
 */
function getCachedPermissions(): PermissionState | null {
  if (typeof window === "undefined") return null;

  try {
    const cached = localStorage.getItem(CACHE_KEY);
    if (!cached) return null;

    const { data, timestamp } = JSON.parse(cached);
    // 检查缓存是否过期
    if (Date.now() - timestamp >= CACHE_TTL) {
      localStorage.removeItem(CACHE_KEY);
      return null;
    }

    return data;
  } catch {
    // 缓存解析失败，清除缓存
    localStorage.removeItem(CACHE_KEY);
    return null;
  }
}

/**
 * 将权限数据保存到 localStorage
 */
function setCachedPermissions(data: Omit<PermissionState, "loading" | "error">): void {
  if (typeof window === "undefined") return;

  try {
    localStorage.setItem(
      CACHE_KEY,
      JSON.stringify({
        data,
        timestamp: Date.now(),
      })
    );
  } catch {
    // localStorage 不可用，忽略错误
    console.warn("无法保存权限缓存到 localStorage");
  }
}

/**
 * 清除权限缓存
 */
function clearPermissionCache(): void {
  if (typeof window === "undefined") return;

  try {
    localStorage.removeItem(CACHE_KEY);
  } catch {
    // 忽略错误
  }
}

// ============================================================================
// Provider Component
// ============================================================================

interface PermissionProviderProps {
  children: ReactNode;
}

/**
 * 权限上下文 Provider
 * 
 * 提供权限缓存和检查方法，支持：
 * - 从 API 获取用户权限
 * - localStorage 缓存（5分钟 TTL）
 * - 通配符权限匹配
 * - 项目作用域权限检查
 * 
 * @example
 * ```tsx
 * // 在 app layout 中使用
 * <PermissionProvider>
 *   {children}
 * </PermissionProvider>
 * 
 * // 在组件中使用
 * const { hasPermission, hasActionPermission } = usePermissions();
 * 
 * if (hasPermission('user:read')) {
 *   // 显示用户列表
 * }
 * 
 * if (hasActionPermission('user', 'create')) {
 *   // 显示创建按钮
 * }
 * ```
 */
export function PermissionProvider({ children }: PermissionProviderProps) {
  const router = useRouter();

  const [state, setState] = useState<PermissionState>(() => {
    // 尝试从缓存初始化
    const cached = getCachedPermissions();
    if (cached) {
      return {
        ...cached,
        loading: false,
        error: null,
      };
    }
    return {
      permissions: [],
      permissionDetails: [],
      roles: [],
      userName: null,
      loading: true,
      error: null,
      isAuthenticated: false,
    };
  });

  // 权限集合（用于快速查找）
  const permissionSet = useMemo(() => new Set(state.permissions), [state.permissions]);

  /**
   * 从 API 获取权限
   */
  const fetchPermissions = useCallback(async () => {
    try {
      setState((prev) => ({ ...prev, loading: true, error: null }));

      const response = await fetch("/admin/api/user/permissions", {
        credentials: "include",
      });

      if (!response.ok) {
        if (response.status === 401) {
          // 未登录，清除缓存并重定向
          clearPermissionCache();
          setState({
            permissions: [],
            permissionDetails: [],
            roles: [],
            userName: null,
            loading: false,
            error: null,
            isAuthenticated: false,
          });
          router.push("/login");
          return;
        }
        throw new Error(`获取权限失败: ${response.status}`);
      }

      const result = await response.json();
      if (result.success && result.data) {
        const data = {
          permissions: result.data.permissions || [],
          permissionDetails: result.data.permission_details || [],
          roles: result.data.roles || [],
          userName: result.data.user_name || null,
          isAuthenticated: true,
        };

        // 更新缓存
        setCachedPermissions(data);

        setState((prev) => ({
          ...prev,
          ...data,
          loading: false,
          error: null,
        }));
      } else {
        throw new Error(result.error || "获取权限失败");
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "获取权限失败";
      setState((prev) => ({
        ...prev,
        loading: false,
        error: message,
      }));
      console.error("获取用户权限失败:", err);
    }
  }, [router]);

  /**
   * 清除缓存（用于登出）
   * Requirement 15.6: 用户登出时清除缓存
   */
  const clearCache = useCallback(() => {
    clearPermissionCache();
    setState({
      permissions: [],
      permissionDetails: [],
      roles: [],
      userName: null,
      loading: false,
      error: null,
      isAuthenticated: false,
    });
  }, []);

  /**
   * 检查是否拥有指定权限
   * 
   * 支持：
   * - 精确匹配
   * - 项目作用域匹配
   * - 通配符匹配
   */
  const hasPermission = useCallback(
    (code: string, project?: string): boolean => {
      const { permissions } = state;

      // 精确匹配
      if (permissionSet.has(code)) return true;

      // 带项目的精确匹配
      if (project) {
        const projectPerm = `${project}:${code}`;
        if (permissionSet.has(projectPerm)) return true;
      }

      // 通配符匹配
      if (matchWildcard(permissions, code)) return true;

      // 带项目的通配符匹配
      if (project) {
        const projectPerm = `${project}:${code}`;
        if (matchWildcard(permissions, projectPerm)) return true;
      }

      return false;
    },
    [state.permissions, permissionSet]
  );

  /**
   * 检查是否拥有任意一个指定权限
   */
  const hasAnyPermission = useCallback(
    (codes: string[], project?: string): boolean => {
      return codes.some((code) => hasPermission(code, project));
    },
    [hasPermission]
  );

  /**
   * 检查是否拥有所有指定权限
   */
  const hasAllPermissions = useCallback(
    (codes: string[], project?: string): boolean => {
      return codes.every((code) => hasPermission(code, project));
    },
    [hasPermission]
  );

  /**
   * 检查是否拥有指定模块的操作权限
   * 
   * @example
   * hasActionPermission('user', 'create') // 检查 user:create 权限
   * hasActionPermission('queue', 'read', 'projectA') // 检查 projectA:queue:read 权限
   */
  const hasActionPermission = useCallback(
    (module: string, action: ActionType, project?: string): boolean => {
      const code = `${module}:${action}`;
      return hasPermission(code, project);
    },
    [hasPermission]
  );

  // 检查是否为管理员
  const isAdmin = useMemo(() => state.roles.includes("admin"), [state.roles]);

  // 初始加载（如果没有缓存）
  useEffect(() => {
    // 如果已经从缓存加载了数据，不需要立即请求
    // 但仍然在后台刷新以确保数据最新
    if (state.isAuthenticated && !state.loading) {
      // 后台刷新
      fetchPermissions();
    } else if (!state.isAuthenticated) {
      // 没有缓存，立即请求
      fetchPermissions();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const contextValue = useMemo<PermissionContextValue>(
    () => ({
      ...state,
      hasPermission,
      hasAnyPermission,
      hasAllPermissions,
      hasActionPermission,
      isAdmin,
      refresh: fetchPermissions,
      clearCache,
    }),
    [
      state,
      hasPermission,
      hasAnyPermission,
      hasAllPermissions,
      hasActionPermission,
      isAdmin,
      fetchPermissions,
      clearCache,
    ]
  );

  return (
    <PermissionContext.Provider value={contextValue}>
      {children}
    </PermissionContext.Provider>
  );
}

// ============================================================================
// Hook
// ============================================================================

/**
 * 使用权限上下文
 * 
 * 必须在 PermissionProvider 内部使用
 * 
 * @example
 * ```tsx
 * const { 
 *   hasPermission, 
 *   hasAnyPermission, 
 *   hasAllPermissions,
 *   hasActionPermission,
 *   loading,
 *   isAdmin 
 * } = usePermissions();
 * 
 * // 检查单个权限
 * if (hasPermission('user:read')) { ... }
 * 
 * // 检查带项目的权限
 * if (hasPermission('queue:read', 'projectA')) { ... }
 * 
 * // 检查操作权限
 * if (hasActionPermission('user', 'create')) { ... }
 * 
 * // 检查任意权限
 * if (hasAnyPermission(['user:read', 'user:write'])) { ... }
 * 
 * // 检查所有权限
 * if (hasAllPermissions(['user:read', 'role:read'])) { ... }
 * ```
 */
export function usePermissions(): PermissionContextValue {
  const context = useContext(PermissionContext);
  if (!context) {
    throw new Error("usePermissions must be used within PermissionProvider");
  }
  return context;
}

// ============================================================================
// Exports
// ============================================================================

export { PermissionContext };

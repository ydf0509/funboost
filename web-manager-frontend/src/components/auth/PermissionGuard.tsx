"use client";

import { type ReactNode } from "react";

import { usePermissions } from "@/contexts/PermissionContext";

// ============================================================================
// Types
// ============================================================================

/**
 * PermissionGuard 组件属性
 */
export interface PermissionGuardProps {
  /** 所需权限，可以是单个权限或权限数组 */
  permission: string | string[];
  /** 匹配模式：any=任意一个权限即可，all=需要所有权限 */
  mode?: "any" | "all";
  /** 项目作用域 */
  project?: string;
  /** 无权限时显示的内容 */
  fallback?: ReactNode;
  /** 加载中显示的内容 */
  loading?: ReactNode;
  /** 子组件 */
  children: ReactNode;
}

/**
 * RequireRead 便捷组件属性
 */
export interface RequireReadProps {
  /** 模块名称 */
  module: string;
  /** 项目作用域 */
  project?: string;
  /** 子组件 */
  children: ReactNode;
  /** 无权限时显示的内容 */
  fallback?: ReactNode;
  /** 加载中显示的内容 */
  loading?: ReactNode;
}

/**
 * RequireWrite 便捷组件属性
 */
export interface RequireWriteProps {
  /** 模块名称 */
  module: string;
  /** 操作类型：create, update, delete */
  action?: "create" | "update" | "delete";
  /** 项目作用域 */
  project?: string;
  /** 子组件 */
  children: ReactNode;
  /** 无权限时显示的内容 */
  fallback?: ReactNode;
  /** 加载中显示的内容 */
  loading?: ReactNode;
}

// ============================================================================
// PermissionGuard Component
// ============================================================================

/**
 * 权限守卫组件
 *
 * 用于控制 UI 元素的显示/隐藏，根据用户权限决定是否渲染子组件。
 * 支持 any/all 两种匹配模式，以及项目作用域权限检查。
 *
 * Requirements:
 * - 7.1: 接受所需权限列表
 * - 7.2: 支持 "any" 模式（用户拥有任意一个所需权限）
 * - 7.3: 支持 "all" 模式（用户拥有所有所需权限）
 * - 7.4: 仅当权限检查通过时渲染子组件
 * - 7.5: 权限检查失败时渲染 fallback 内容
 *
 * @example
 * ```tsx
 * // 单个权限检查
 * <PermissionGuard permission="user:read">
 *   <UserList />
 * </PermissionGuard>
 *
 * // 多个权限，任意一个即可
 * <PermissionGuard permission={["user:read", "user:write"]} mode="any">
 *   <UserActions />
 * </PermissionGuard>
 *
 * // 多个权限，需要全部
 * <PermissionGuard permission={["user:read", "role:read"]} mode="all">
 *   <AdminPanel />
 * </PermissionGuard>
 *
 * // 带项目作用域
 * <PermissionGuard permission="queue:read" project="projectA">
 *   <QueueList />
 * </PermissionGuard>
 *
 * // 带 fallback
 * <PermissionGuard
 *   permission="user:delete"
 *   fallback={<span className="text-gray-400">无权限</span>}
 * >
 *   <DeleteButton />
 * </PermissionGuard>
 *
 * // 带 loading
 * <PermissionGuard
 *   permission="user:read"
 *   loading={<Spinner />}
 * >
 *   <UserList />
 * </PermissionGuard>
 * ```
 */
export function PermissionGuard({
  permission,
  mode = "any",
  project,
  fallback = null,
  loading = null,
  children,
}: PermissionGuardProps) {
  const { hasAnyPermission, hasAllPermissions, loading: permLoading } = usePermissions();

  // 加载中状态 (Requirement 7.4)
  if (permLoading) {
    return <>{loading}</>;
  }

  // 将单个权限转换为数组
  const permissions = Array.isArray(permission) ? permission : [permission];

  // 根据模式检查权限 (Requirements 7.2, 7.3)
  const hasAccess =
    mode === "all"
      ? hasAllPermissions(permissions, project)
      : hasAnyPermission(permissions, project);

  // 无权限时显示 fallback (Requirement 7.5)
  if (!hasAccess) {
    return <>{fallback}</>;
  }

  // 有权限时渲染子组件 (Requirement 7.4)
  return <>{children}</>;
}

// ============================================================================
// Convenience Components
// ============================================================================

/**
 * 便捷组件：需要读权限
 *
 * 检查用户是否拥有指定模块的读权限 (module:read)
 *
 * @example
 * ```tsx
 * <RequireRead module="user">
 *   <UserList />
 * </RequireRead>
 *
 * // 带项目作用域
 * <RequireRead module="queue" project="projectA">
 *   <QueueList />
 * </RequireRead>
 * ```
 */
export function RequireRead({
  module,
  project,
  children,
  fallback,
  loading,
}: RequireReadProps) {
  return (
    <PermissionGuard
      permission={`${module}:read`}
      project={project}
      fallback={fallback}
      loading={loading}
    >
      {children}
    </PermissionGuard>
  );
}

/**
 * 便捷组件：需要写权限
 *
 * 检查用户是否拥有指定模块的写权限 (module:create/update/delete)
 *
 * @example
 * ```tsx
 * // 默认检查 update 权限
 * <RequireWrite module="user">
 *   <EditButton />
 * </RequireWrite>
 *
 * // 检查 create 权限
 * <RequireWrite module="user" action="create">
 *   <CreateButton />
 * </RequireWrite>
 *
 * // 检查 delete 权限
 * <RequireWrite module="user" action="delete">
 *   <DeleteButton />
 * </RequireWrite>
 *
 * // 带项目作用域
 * <RequireWrite module="queue" action="create" project="projectA">
 *   <CreateTaskButton />
 * </RequireWrite>
 * ```
 */
export function RequireWrite({
  module,
  action = "update",
  project,
  children,
  fallback,
  loading,
}: RequireWriteProps) {
  return (
    <PermissionGuard
      permission={`${module}:${action}`}
      project={project}
      fallback={fallback}
      loading={loading}
    >
      {children}
    </PermissionGuard>
  );
}

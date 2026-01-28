"use client";

import { ReactNode, useEffect, useState } from "react";

import { usePermissions } from "@/contexts/PermissionContext";
import { useProject } from "@/contexts/ProjectContext";
import { AccessDenied } from "@/components/ui/AccessDenied";
import { navigateTo } from "@/lib/navigation";

type RequirePermissionProps = {
  /** 所需权限（需要拥有任意一个） */
  permissions: string[];
  /** 项目权限级别（可选） */
  projectLevel?: "read" | "write" | "admin";
  /** 指定项目 ID（可选，默认使用当前项目） */
  projectId?: number;
  /** 子组件 */
  children: ReactNode;
  /** 自定义访问拒绝时的标题 */
  deniedTitle?: string;
  /** 自定义访问拒绝时的描述 */
  deniedDescription?: string;
  /** 加载中时显示的内容 */
  loadingFallback?: ReactNode;
};

/**
 * 权限保护包装组件
 * 
 * 用于保护需要特定权限才能访问的页面或组件。
 * 如果用户没有所需权限，将显示访问拒绝页面。
 * 
 * @example
 * ```tsx
 * // 在页面中使用
 * export default function AdminUsersPage() {
 *   return (
 *     <RequirePermission permissions={["user:read"]}>
 *       <div>用户管理内容...</div>
 *     </RequirePermission>
 *   );
 * }
 * 
 * // 需要多个权限之一
 * <RequirePermission permissions={["user:read", "user:write"]}>
 *   <UserList />
 * </RequirePermission>
 * ```
 */
export function RequirePermission({
  permissions,
  projectLevel,
  projectId,
  children,
  deniedTitle,
  deniedDescription,
  loadingFallback,
}: RequirePermissionProps) {
  const { hasAnyPermission, loading, isAuthenticated } = usePermissions();
  const { currentProject, projects, isLoading: projectLoading } = useProject();

  // 解决 Hydration 不匹配问题：服务端和客户端首次渲染都显示 loading
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  const targetProject =
    typeof projectId === "number"
      ? projects.find((project) => project.id === projectId) || null
      : currentProject;

  const hasProjectPermission = (() => {
    if (!projectLevel) return true;
    const levelRank: Record<string, number> = { read: 1, write: 2, admin: 3 };
    const requiredRank = levelRank[projectLevel] ?? 0;

    if (targetProject?.permission_level) {
      const userRank = levelRank[targetProject.permission_level] ?? 0;
      return userRank >= requiredRank;
    }

    if (projects.length > 0) {
      const maxRank = Math.max(
        ...projects.map((project) => levelRank[project.permission_level ?? "read"] ?? 0)
      );
      return maxRank >= requiredRank;
    }

    return false;
  })();

  // 如果未认证且加载完成，重定向到登录页面
  useEffect(() => {
    if (mounted && !loading && !isAuthenticated) {
      navigateTo("/login");
    }
  }, [mounted, loading, isAuthenticated]);

  // 未挂载时（SSR）或加载中状态：显示 loading fallback
  const isLoading = !mounted || loading || (projectLevel && projectLoading);
  if (isLoading) {
    if (loadingFallback) {
      return <>{loadingFallback}</>;
    }
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-[hsl(var(--accent))] border-t-transparent" />
          <p className="text-sm text-[hsl(var(--ink-muted))]">正在验证权限...</p>
        </div>
      </div>
    );
  }

  // 未认证，显示加载状态（等待重定向）
  if (!isAuthenticated) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-[hsl(var(--accent))] border-t-transparent" />
          <p className="text-sm text-[hsl(var(--ink-muted))]">正在跳转到登录页面...</p>
        </div>
      </div>
    );
  }

  // 项目权限检查（如果需要）
  if (projectLevel && !hasProjectPermission) {
    return (
      <AccessDenied
        title={deniedTitle || "无项目权限"}
        description={deniedDescription || "当前项目权限不足，无法访问该页面。"}
        requiredPermission={`项目权限: ${projectLevel}`}
        showBackButton
        showHomeButton
      />
    );
  }

  // 检查功能权限
  if (!hasAnyPermission(permissions)) {
    return (
      <AccessDenied
        title={deniedTitle}
        description={deniedDescription}
        requiredPermission={permissions.join(" 或 ")}
        showBackButton
        showHomeButton
      />
    );
  }

  // 有权限，渲染子组件
  return <>{children}</>;
}

/**
 * 创建带权限检查的页面包装器
 * 
 * 用于快速创建需要特定权限的页面组件。
 * 
 * @example
 * ```tsx
 * const ProtectedPage = withPermission(["user:read"])(MyPageComponent);
 * ```
 */
export function withPermission(permissions: string[]) {
  return function <P extends object>(Component: React.ComponentType<P>) {
    return function ProtectedComponent(props: P) {
      return (
        <RequirePermission permissions={permissions}>
          <Component {...props} />
        </RequirePermission>
      );
    };
  };
}

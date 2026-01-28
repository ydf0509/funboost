"use client";

import { ShieldX, ArrowLeft, Home } from "lucide-react";

import { Button } from "./Button";
import { Card } from "./Card";
import { StaticLink } from "./StaticLink";

type AccessDeniedProps = {
  /** 自定义标题 */
  title?: string;
  /** 自定义描述 */
  description?: string;
  /** 所需权限（用于显示） */
  requiredPermission?: string;
  /** 是否显示返回按钮 */
  showBackButton?: boolean;
  /** 是否显示首页按钮 */
  showHomeButton?: boolean;
};

/**
 * 访问拒绝组件
 * 
 * 当用户尝试访问没有权限的页面时显示此组件。
 * 
 * @example
 * ```tsx
 * <AccessDenied 
 *   requiredPermission="user:write"
 *   showBackButton
 *   showHomeButton
 * />
 * ```
 */
export function AccessDenied({
  title = "访问被拒绝",
  description = "您没有权限访问此页面。请联系管理员获取相应权限。",
  requiredPermission,
  showBackButton = true,
  showHomeButton = true,
}: AccessDeniedProps) {
  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4">
      <Card className="max-w-md text-center">
        <div className="flex flex-col items-center gap-4">
          {/* 图标 */}
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[hsl(var(--danger))]/10">
            <ShieldX className="h-8 w-8 text-[hsl(var(--danger))]" />
          </div>

          {/* 标题 */}
          <h1 className="font-display text-2xl text-[hsl(var(--ink))]">
            {title}
          </h1>

          {/* 描述 */}
          <p className="text-sm text-[hsl(var(--ink-muted))]">
            {description}
          </p>

          {/* 所需权限提示 */}
          {requiredPermission && (
            <div className="mt-2 rounded-lg bg-[hsl(var(--sand-2))] px-4 py-2">
              <p className="text-xs text-[hsl(var(--ink-muted))]">
                所需权限：
                <code className="ml-1 rounded bg-[hsl(var(--sand-3))] px-1.5 py-0.5 font-mono text-[hsl(var(--ink))]">
                  {requiredPermission}
                </code>
              </p>
            </div>
          )}

          {/* 操作按钮 */}
          {(showBackButton || showHomeButton) && (
            <div className="mt-4 flex flex-wrap justify-center gap-3">
              {showBackButton && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.history.back()}
                >
                  <ArrowLeft className="h-4 w-4" />
                  返回上一页
                </Button>
              )}
              {showHomeButton && (
                <StaticLink href="/queue-op">
                  <Button variant="primary" size="sm">
                    <Home className="h-4 w-4" />
                    返回首页
                  </Button>
                </StaticLink>
              )}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

"use client";

import { forwardRef, AnchorHTMLAttributes, ReactNode } from "react";

import { isStaticExportMode } from "@/lib/navigation";

interface StaticLinkProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
  href: string;
  children: ReactNode;
  className?: string;
  prefetch?: boolean; // 兼容 Next.js Link 的 prefetch 属性（在静态模式下忽略）
}

/**
 * 静态导出兼容的 Link 组件
 * 
 * 在静态导出模式下，使用普通的 <a> 标签进行完整页面刷新，
 * 避免 Next.js 客户端路由依赖 RSC payload 文件的问题。
 * 
 * 在开发模式下，也使用普通的 <a> 标签以保持一致性。
 */
export const StaticLink = forwardRef<HTMLAnchorElement, StaticLinkProps>(
  ({ href, children, className, prefetch, ...props }, ref) => {
    // 始终使用普通的 <a> 标签，确保完整页面刷新
    // 这样可以避免静态导出模式下的 RSC payload 问题
    return (
      <a
        ref={ref}
        href={href}
        className={className}
        {...props}
      >
        {children}
      </a>
    );
  }
);

StaticLink.displayName = "StaticLink";

export default StaticLink;

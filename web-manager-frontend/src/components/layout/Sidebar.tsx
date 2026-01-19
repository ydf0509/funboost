"use client";

import clsx from "clsx";
import { usePathname } from "next/navigation";
import { ChevronLeft, LogOut } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { navGroups, filterNavGroupsByPermissions } from "@/lib/nav";
import { usePermissions } from "@/contexts/PermissionContext";
import { StaticLink } from "@/components/ui/StaticLink";

export function Sidebar({ open, onClose }: { open: boolean; onClose?: () => void }) {
  const pathname = usePathname();
  const { permissions, loading } = usePermissions();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // 根据用户权限过滤导航分组
  const filteredNavGroups = useMemo(() => {
    const permissionSet = new Set(permissions);
    return filterNavGroupsByPermissions(navGroups, permissionSet);
  }, [permissions]);

  return (
    <aside
      className={clsx(
        "fixed left-0 top-0 z-40 h-full w-72 border-r border-[hsl(var(--line))] bg-[hsl(var(--card))]/75 backdrop-blur-2xl transition-transform duration-300",
        open ? "translate-x-0" : "-translate-x-full",
        "md:translate-x-0" // 桌面端始终显示
      )}
    >
      <div className="flex h-full flex-col px-6 py-8">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.4em] text-[hsl(var(--accent-2))]">
              Funboost
            </p>
            <h1 className="font-display text-xl text-[hsl(var(--ink))]">管理控制台</h1>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-[hsl(var(--line))] p-2 text-[hsl(var(--ink-muted))] md:hidden"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        </div>

        <nav className="mt-8 flex-1 space-y-6 overflow-y-auto pr-2">
          {loading || !mounted ? (
            // 加载中显示骨架屏
            <div className="space-y-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="space-y-3">
                  <div className="h-3 w-16 animate-pulse rounded bg-[hsl(var(--sand-2))]" />
                  <div className="space-y-2">
                    {[1, 2, 3].map((j) => (
                      <div
                        key={j}
                        className="h-10 animate-pulse rounded-2xl bg-[hsl(var(--sand-2))]"
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            filteredNavGroups.map((group) => (
              <div key={group.title} className="space-y-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-[hsl(var(--ink-muted))]">
                  {group.title}
                </p>
                <div className="space-y-2">
                  {group.items.map((item) => {
                    const isActive = pathname === item.href;
                    const Icon = item.icon;
                    return (
                      <StaticLink
                        key={item.href}
                        href={item.href}
                        className={clsx(
                          "flex items-center gap-3 rounded-2xl px-4 py-2 text-sm font-medium transition",
                          isActive
                            ? "bg-[hsl(var(--accent-2))] text-white"
                            : "text-[hsl(var(--ink))] hover:bg-[hsl(var(--sand-2))]"
                        )}
                      >
                        <Icon className="h-4 w-4" />
                        {item.label}
                      </StaticLink>
                    );
                  })}
                </div>
              </div>
            ))
          )}
        </nav>

        <div className="mt-6 rounded-2xl border border-[hsl(var(--line))] bg-[hsl(var(--card))]/85 px-4 py-3 text-xs text-[hsl(var(--ink-muted))]">
          <p className="font-semibold text-[hsl(var(--ink))]">会话信息</p>
          <p className="mt-1">账号设置请前往个人中心。</p>
          <button
            type="button"
            onClick={() => {
              window.location.href = "/logout";
            }}
            className="mt-3 inline-flex items-center gap-2 rounded-full border border-[hsl(var(--line))] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink))] hover:border-[hsl(var(--accent))] hover:text-[hsl(var(--accent))]"
          >
            <LogOut className="h-3.5 w-3.5" />
            退出登录
          </button>
        </div>
      </div>
    </aside>
  );
}

"use client";

import clsx from "clsx";
import { Menu, RefreshCw, Search, Star } from "lucide-react";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { funboostFetch } from "@/lib/api";
import { ThemeToggle } from "./ThemeToggle";
import { StaticLink } from "@/components/ui/StaticLink";

const titles: Record<string, { title: string; subtitle: string }> = {
  "/queue-op": { title: "队列运维", subtitle: "管理队列、消费者与实时指标。" },
  "/rpc-call": { title: "RPC 控制台", subtitle: "发送请求并追踪任务结果。" },
  "/timing-jobs": { title: "定时任务", subtitle: "创建、暂停并监控任务。" },
  "/care-project": { title: "关注项目", subtitle: "限定监控范围到指定项目。" },
  "/fun-results": { title: "任务结果", subtitle: "查看执行结果与重试情况。" },
  "/consume-speed": { title: "消费速率", subtitle: "分析队列吞吐趋势。" },
  "/running-consumers/ip": { title: "按 IP 查看消费者", subtitle: "按主机分组查看进程。" },
  "/running-consumers/queue": { title: "按队列查看消费者", subtitle: "按队列查看活跃消费端。" },
  "/about": { title: "关于", subtitle: "数据来源说明与注意事项。" },
  "/admin/users": { title: "用户管理", subtitle: "管理用户、锁定与密码。" },
  "/admin/roles": { title: "角色管理", subtitle: "按角色分配权限。" },
  "/admin/projects": { title: "项目管理", subtitle: "管理项目与成员权限。" },
  "/admin/audit/logs": { title: "审计日志", subtitle: "筛选并查看审计事件。" },
  "/admin/audit/config": { title: "审计配置", subtitle: "保留策略与清理设置。" },
  "/admin/audit/statistics": { title: "审计统计", subtitle: "登录与操作概览。" },
  "/admin/email-config": { title: "邮件配置", subtitle: "SMTP 设置与测试邮件。" },
  "/profile": { title: "个人中心", subtitle: "账户概览与安全设置。" },
  "/profile/change-password": { title: "修改密码", subtitle: "安全更新你的密码。" },
  "/profile/change-email": { title: "修改邮箱", subtitle: "验证并更新邮箱地址。" },
};

export function TopBar({ onMenu }: { onMenu: () => void }) {
  const pathname = usePathname();
  const [careProject, setCareProject] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const loadCareProject = async () => {
    setLoading(true);
    try {
      const data = await funboostFetch<{ care_project_name?: string }>("/funboost/get_care_project_name", {
        cache: "no-store",
      });
      setCareProject(data?.care_project_name || "");
    } catch {
      setCareProject("");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCareProject();
    
    // 监听关注项目变更事件
    const handleCareProjectChanged = (event: Event) => {
      const detail = (event as CustomEvent<{ careProjectName?: string }>).detail;
      if (detail && typeof detail.careProjectName === "string") {
        setCareProject(detail.careProjectName || "");
        return;
      }
      loadCareProject();
    };
    window.addEventListener("careProjectChanged", handleCareProjectChanged);
    
    return () => {
      window.removeEventListener("careProjectChanged", handleCareProjectChanged);
    };
  }, []);

  const current = titles[pathname] || {
    title: "Funboost 管理控制台",
    subtitle: "分布式函数的监控与调度中心。",
  };

  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-[hsl(var(--line))] bg-[hsl(var(--card))]/70 px-6 py-4 backdrop-blur-2xl">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenu}
          className="rounded-full border border-[hsl(var(--line))] p-2 text-[hsl(var(--ink))] md:hidden"
        >
          <Menu className="h-4 w-4" />
        </button>
        <div>
          <h2 className="font-display text-xl text-[hsl(var(--ink))]">{current.title}</h2>
          <p className="text-sm text-[hsl(var(--ink-muted))]">{current.subtitle}</p>
        </div>
      </div>
      <div className="flex w-full items-center gap-3 md:w-auto">
        <StaticLink
          href="/care-project"
          className={clsx(
            "flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition",
            careProject
              ? "border-[hsl(var(--accent))] bg-[hsl(var(--accent))]/20 text-[hsl(var(--accent-2))]"
              : "border-[hsl(var(--line))] bg-[hsl(var(--card))]/80 text-[hsl(var(--ink-muted))] hover:border-[hsl(var(--accent))]/50"
          )}
        >
          <Star className={clsx("h-4 w-4", careProject && "fill-current")} />
          <span>{careProject || "全部项目"}</span>
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              loadCareProject();
            }}
            className="rounded-full p-0.5 hover:bg-[hsl(var(--accent))]/20"
          >
            <RefreshCw className={clsx("h-3.5 w-3.5", loading && "animate-spin")} />
          </button>
        </StaticLink>
        <div className="flex flex-1 items-center gap-2 rounded-full border border-[hsl(var(--line))] bg-[hsl(var(--card))]/80 px-4 py-2 text-sm text-[hsl(var(--ink-muted))] md:w-72">
          <Search className="h-4 w-4" />
          <input
            className="w-full bg-transparent text-sm text-[hsl(var(--ink))] outline-none"
            placeholder="搜索队列、任务、用户"
          />
        </div>
        <ThemeToggle />
      </div>
    </header>
  );
}

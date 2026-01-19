"use client";

import { useEffect, useState } from "react";

import { RequirePermission } from "@/components/auth/RequirePermission";
import { Card } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/StatCard";
import { apiFetch } from "@/lib/api";

type StatisticsData = {
  success_login_count: number;
  failed_login_count: number;
  active_user_count: number;
  total_attempts: number;
};

export default function AuditStatisticsPage() {
  const [stats, setStats] = useState<StatisticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const response = await apiFetch<{
          success: boolean;
          data: StatisticsData;
        }>("/admin/api/audit/statistics");
        
        if (response.success && response.data) {
          setStats(response.data);
        } else {
          setNotice("无法加载统计数据");
        }
      } catch (err) {
        setNotice(err instanceof Error ? err.message : "加载统计失败。");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  return (
    <RequirePermission permissions={["audit:read"]}>
    <div className="space-y-6">
      {notice ? (
        <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-top-2 fade-in duration-300">
          <Card className="border-l-4 border-l-red-500 bg-red-50 dark:bg-red-950/20 shadow-lg max-w-md">
            <div className="flex items-start gap-3 p-4">
              <div className="flex-shrink-0 text-red-500">
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800 dark:text-red-200">{notice}</p>
              </div>
              <button 
                onClick={() => setNotice(null)}
                className="flex-shrink-0 text-red-500 hover:text-red-700 transition-colors"
              >
                <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </Card>
        </div>
      ) : null}

      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <StatCard 
          label="成功登录" 
          value={loading ? "-" : (stats?.success_login_count ?? 0)} 
          helper="近 30 天" 
          tone="success"
        />
        <StatCard 
          label="失败登录" 
          value={loading ? "-" : (stats?.failed_login_count ?? 0)} 
          helper="近 30 天" 
          tone="danger"
        />
        <StatCard 
          label="活跃用户" 
          value={loading ? "-" : (stats?.active_user_count ?? 0)} 
          helper="近 30 天" 
          tone="info"
        />
        <StatCard 
          label="总尝试" 
          value={loading ? "-" : (stats?.total_attempts ?? 0)} 
          helper="近 30 天" 
          tone="warning"
        />
      </div>

      <Card>
        <div className="p-6">
          <h3 className="text-sm font-semibold text-[hsl(var(--ink))] mb-2">活动概览</h3>
          <p className="text-sm text-[hsl(var(--ink-muted))]">
            如需完整图表，请使用旧版页面。后端提供更完整的统计表格。若需详细图表，请打开后端的统计页面。
          </p>
        </div>
      </Card>
    </div>
    </RequirePermission>
  );
}

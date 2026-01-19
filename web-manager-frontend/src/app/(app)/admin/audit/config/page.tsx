"use client";

import { useCallback, useEffect, useState } from "react";
import { Trash2, Save, RefreshCw } from "lucide-react";

import { RequirePermission } from "@/components/auth/RequirePermission";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { StatCard } from "@/components/ui/StatCard";
import { apiFetch } from "@/lib/api";

export default function AuditConfigPage() {
  const [retentionDays, setRetentionDays] = useState("30");
  const [stats, setStats] = useState({ total: 0, oldest: "-", span: 0 });
  const [notice, setNotice] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [cleaning, setCleaning] = useState(false);

  const loadConfig = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiFetch<{
        success: boolean;
        data: {
          retention_days: number;
          total_logs: number;
          oldest_date: string | null;
          span_days: number;
        };
      }>("/admin/api/audit/config");

      if (response.success && response.data) {
        setRetentionDays(String(response.data.retention_days));
        setStats({
          total: response.data.total_logs,
          oldest: response.data.oldest_date || "-",
          span: response.data.span_days,
        });
      }
    } catch (err) {
      setNotice({ type: "error", message: err instanceof Error ? err.message : "加载配置失败。" });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  const updateRetention = async () => {
    setNotice(null);
    setSaving(true);
    try {
      const response = await apiFetch<{ success: boolean; error?: string; message?: string }>(
        "/admin/api/audit/config/update",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ retention_days: parseInt(retentionDays, 10) }),
        }
      );

      if (!response.success) {
        throw new Error(response.error || "更新失败");
      }

      setNotice({ type: "success", message: response.message || "保留策略已更新。" });
    } catch (err) {
      setNotice({ type: "error", message: err instanceof Error ? err.message : "更新失败。" });
    } finally {
      setSaving(false);
    }
  };

  const cleanup = async () => {
    if (!confirm("确定要清理过期日志吗？此操作不可撤销！")) return;
    
    setNotice(null);
    setCleaning(true);
    try {
      const response = await apiFetch<{ success: boolean; error?: string; message?: string; deleted_count?: number }>(
        "/admin/api/audit/cleanup",
        { method: "POST" }
      );

      if (!response.success) {
        throw new Error(response.error || "清理失败");
      }

      setNotice({ type: "success", message: response.message || "清理完成。" });
      loadConfig(); // 刷新统计数据
    } catch (err) {
      setNotice({ type: "error", message: err instanceof Error ? err.message : "清理失败。" });
    } finally {
      setCleaning(false);
    }
  };

  return (
    <RequirePermission permissions={["config:update"]}>
    <div className="space-y-6">
      {notice ? (
        <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-top-2 fade-in duration-300">
          <Card className={`shadow-lg max-w-md border-l-4 ${
            notice.type === "success"
              ? "border-l-green-500 bg-green-50 dark:bg-green-950/20"
              : "border-l-red-500 bg-red-50 dark:bg-red-950/20"
          }`}>
            <div className="flex items-start gap-3 p-4">
              <div className={`flex-shrink-0 ${notice.type === "success" ? "text-green-500" : "text-red-500"}`}>
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  {notice.type === "success" ? (
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  ) : (
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  )}
                </svg>
              </div>
              <div className="flex-1">
                <p className={`text-sm font-medium ${notice.type === "success" ? "text-green-800 dark:text-green-200" : "text-red-800 dark:text-red-200"}`}>
                  {notice.message}
                </p>
              </div>
              <button 
                onClick={() => setNotice(null)}
                className={`flex-shrink-0 transition-colors ${notice.type === "success" ? "text-green-500 hover:text-green-700" : "text-red-500 hover:text-red-700"}`}
              >
                <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </Card>
        </div>
      ) : null}

      {/* 统计卡片 */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-3">
        <StatCard label="总日志数" value={stats.total} helper="条" tone="info" />
        <StatCard label="最早日期" value={stats.oldest} helper="记录" tone="neutral" />
        <StatCard label="时间跨度" value={stats.span} helper="天" tone="warning" />
      </div>

      {/* 配置和操作区域 */}
      <Card>
        <div className="flex flex-col gap-6">
          {/* 标题和刷新按钮 */}
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[hsl(var(--ink))]">审计配置</h3>
            <Button variant="outline" size="sm" onClick={loadConfig} className="cursor-pointer">
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              刷新
            </Button>
          </div>

          {/* 保留策略 */}
          <div className="space-y-3">
            <div>
              <h4 className="text-sm font-medium text-[hsl(var(--ink))] mb-1">保留策略</h4>
              <p className="text-xs text-[hsl(var(--ink-muted))]">设置日志保留时长</p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <Input 
                type="number"
                value={retentionDays} 
                onChange={(e) => setRetentionDays(e.target.value)} 
                className="w-32"
                min={1}
                placeholder="天数"
              />
              <span className="text-sm text-[hsl(var(--ink-muted))]">天</span>
              <Button onClick={updateRetention} disabled={saving} className="cursor-pointer">
                <Save className="h-4 w-4" />
                {saving ? "保存中..." : "保存"}
              </Button>
            </div>
          </div>

          {/* 分隔线 */}
          <div className="border-t border-[hsl(var(--line))]" />

          {/* 清理操作 */}
          <div className="space-y-3">
            <div>
              <h4 className="text-sm font-medium text-[hsl(var(--ink))] mb-1">清理过期日志</h4>
              <p className="text-xs text-[hsl(var(--ink-muted))]">清理超过保留期限的日志，此操作不可撤销</p>
            </div>
            <Button variant="danger" onClick={cleanup} disabled={cleaning} className="cursor-pointer">
              <Trash2 className="h-4 w-4" />
              {cleaning ? "清理中..." : "清理过期日志"}
            </Button>
          </div>
        </div>
      </Card>
    </div>
    </RequirePermission>
  );
}

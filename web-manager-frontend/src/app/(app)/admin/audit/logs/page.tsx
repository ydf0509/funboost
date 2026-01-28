"use client";

import { useCallback, useEffect, useState } from "react";
import { ClipboardList, RefreshCw, Settings, BarChart3, Download } from "lucide-react";

import { RequirePermission } from "@/components/auth/RequirePermission";
import { useActionPermissions } from "@/hooks/useActionPermissions";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Select } from "@/components/ui/Select";
import { StatCard } from "@/components/ui/StatCard";
import { StaticLink } from "@/components/ui/StaticLink";
import { apiFetch } from "@/lib/api";


type AuditLog = {
  time: string;
  eventType: string;
  user: string;
  ip: string;
  details: string;
};

type EventTypeOption = {
  value: string;
  label: string;
};

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [eventTypes, setEventTypes] = useState<EventTypeOption[]>([]);
  const [eventType, setEventType] = useState("");
  const [userName, setUserName] = useState("");
  const [ipAddress, setIpAddress] = useState("");
  const [dateRange, setDateRange] = useState("all");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [pageSize, setPageSize] = useState("50");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [notice, setNotice] = useState<string | null>(null);

  // 使用 useActionPermissions hook 获取操作权限
  const { canExport } = useActionPermissions("audit");

  // 根据快捷日期范围计算实际的开始和结束日期
  const getDateRange = useCallback(() => {
    const now = new Date();
    const today = now.toISOString().split('T')[0];
    
    switch (dateRange) {
      case "all":
        return { start: "", end: "" };
      case "today":
        return { start: today, end: today };
      case "yesterday":
        const yesterday = new Date(now);
        yesterday.setDate(yesterday.getDate() - 1);
        const yesterdayStr = yesterday.toISOString().split('T')[0];
        return { start: yesterdayStr, end: yesterdayStr };
      case "last7days":
        const last7 = new Date(now);
        last7.setDate(last7.getDate() - 7);
        return { start: last7.toISOString().split('T')[0], end: today };
      case "last30days":
        const last30 = new Date(now);
        last30.setDate(last30.getDate() - 30);
        return { start: last30.toISOString().split('T')[0], end: today };
      case "custom":
        return { start: startDate, end: endDate };
      default:
        return { start: "", end: "" };
    }
  }, [dateRange, startDate, endDate]);

  const loadLogs = useCallback(async () => {
    setNotice(null);
    try {
      const { start, end } = getDateRange();
      
      const query = new URLSearchParams();
      if (eventType) query.set("event_type", eventType);
      if (userName) query.set("user_name", userName);
      if (ipAddress) query.set("ip_address", ipAddress);
      if (start) query.set("start_date", start);
      if (end) query.set("end_date", end);
      query.set("page", String(page));
      query.set("page_size", pageSize);

      const response = await apiFetch<{
        success: boolean;
        data: {
          logs: Array<{
            created_at: string;
            event_type: string;
            user_name: string;
            ip_address: string;
            details: Record<string, unknown>;
          }>;
          page: number;
          total: number;
          total_pages: number;
          event_types: EventTypeOption[];
        };
      }>(`/admin/api/audit/logs?${query.toString()}`);

      if (response.success && response.data) {
        setLogs(response.data.logs.map((log) => ({
          time: log.created_at,
          eventType: log.event_type,
          user: log.user_name,
          ip: log.ip_address,
          details: JSON.stringify(log.details || {}),
        })));
        setTotal(response.data.total);
        setTotalPages(response.data.total_pages);
        // 只在首次加载时设置事件类型选项
        if (eventTypes.length === 0 && response.data.event_types) {
          setEventTypes([{ value: "", label: "全部事件" }, ...response.data.event_types]);
        }
      }
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "加载日志失败。");
    }
  }, [eventType, userName, ipAddress, page, pageSize, getDateRange, eventTypes.length]);

  // 初始加载和依赖变化时加载数据
  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

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

      {/* 统计卡片 */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <StatCard label="总记录数" value={total} helper="条" tone="info" />
        <StatCard label="当前页" value={page} helper={`/ ${totalPages}`} tone="success" />
        <StatCard label="总页数" value={totalPages} helper="页" tone="warning" />
        <StatCard label="每页显示" value={pageSize} helper="条" tone="neutral" />
      </div>

      {/* 筛选和操作区域 */}
      <Card>
        <div className="flex flex-col gap-4">
          {/* 第一行：快捷操作按钮 */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-[hsl(var(--ink))]">审计日志</h3>
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="outline" size="sm" onClick={loadLogs} className="cursor-pointer">
                <RefreshCw className="h-4 w-4" />
                刷新
              </Button>
              {canExport && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => {
                    const params = new URLSearchParams();
                    if (eventType) params.append("action", eventType);
                    if (startDate) params.append("start_date", startDate);
                    if (endDate) params.append("end_date", endDate);
                    window.open(`/admin/api/audit/export?${params.toString()}`, "_blank");
                  }}
                  className="cursor-pointer"
                >
                  <Download className="h-4 w-4" />
                  导出
                </Button>
              )}
              <StaticLink href="/admin/audit/config" className="inline-flex">
                <Button variant="outline" size="sm" className="cursor-pointer">
                  <Settings className="h-4 w-4" />
                  配置
                </Button>
              </StaticLink>
              <StaticLink href="/admin/audit/statistics" className="inline-flex">
                <Button variant="outline" size="sm" className="cursor-pointer">
                  <BarChart3 className="h-4 w-4" />
                  统计
                </Button>
              </StaticLink>
            </div>
          </div>

          {/* 第二行：筛选条件 */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Select value={eventType} onChange={(event) => setEventType(event.target.value)}>
              {eventTypes.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
            <Input placeholder="用户名" value={userName} onChange={(event) => setUserName(event.target.value)} />
            <Input placeholder="IP 地址" value={ipAddress} onChange={(event) => setIpAddress(event.target.value)} />
            <Select value={pageSize} onChange={(event) => setPageSize(event.target.value)}>
              <option value="25">25 条/页</option>
              <option value="50">50 条/页</option>
              <option value="100">100 条/页</option>
              <option value="200">200 条/页</option>
            </Select>
          </div>

          {/* 第三行：时间范围 */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Select value={dateRange} onChange={(event) => setDateRange(event.target.value)}>
              <option value="all">全部时间</option>
              <option value="today">今天</option>
              <option value="yesterday">昨天</option>
              <option value="last7days">最近7天</option>
              <option value="last30days">最近30天</option>
              <option value="custom">自定义范围</option>
            </Select>
            {dateRange === "custom" && (
              <>
                <Input 
                  type="date" 
                  value={startDate} 
                  onChange={(event) => setStartDate(event.target.value)}
                  placeholder="开始日期"
                />
                <Input 
                  type="date" 
                  value={endDate} 
                  onChange={(event) => setEndDate(event.target.value)}
                  placeholder="结束日期"
                />
              </>
            )}
            <Button variant="primary" size="sm" onClick={loadLogs} className="cursor-pointer">
              <ClipboardList className="h-4 w-4" />
              查询
            </Button>
          </div>
        </div>
      </Card>

      <Card>
        <div className="mt-6">
          {logs.length === 0 ? (
            <EmptyState title="暂无日志" subtitle="暂无审计数据。" />
          ) : (
            <div className="overflow-x-auto -mx-6 px-6">
              <table className="min-w-full text-sm">
                <thead className="text-left text-xs uppercase tracking-wider text-[hsl(var(--ink-muted))] border-b border-[hsl(var(--line))]">
                  <tr>
                    <th className="pb-3 pr-4 font-semibold">时间</th>
                    <th className="pb-3 px-4 font-semibold">事件类型</th>
                    <th className="pb-3 px-4 font-semibold">用户</th>
                    <th className="pb-3 px-4 font-semibold">IP地址</th>
                    <th className="pb-3 pl-4 font-semibold">详情</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[hsl(var(--line))]">
                  {logs.map((log, index) => (
                    <tr key={`${log.time}-${index}`} className="hover:bg-[hsl(var(--sand-2))]/50 transition-colors">
                      <td className="py-4 pr-4 text-xs text-[hsl(var(--ink-muted))] whitespace-nowrap">{log.time}</td>
                      <td className="py-4 px-4 text-[hsl(var(--ink))] font-medium">{log.eventType}</td>
                      <td className="py-4 px-4 text-[hsl(var(--ink-muted))]">{log.user}</td>
                      <td className="py-4 px-4 text-[hsl(var(--ink-muted))] font-mono text-xs">{log.ip}</td>
                      <td className="py-4 pl-4">
                        <details className="group cursor-pointer">
                          <summary className="text-xs text-[hsl(var(--accent))] hover:text-[hsl(var(--accent-2))] transition-colors list-none flex items-center gap-1">
                            <span className="inline-block transition-transform group-open:rotate-90">▶</span>
                            查看详情
                          </summary>
                          <pre className="mt-2 p-3 bg-[hsl(var(--sand-2))] rounded-lg text-xs overflow-x-auto border border-[hsl(var(--line))] max-w-2xl">
                            <code className="text-[hsl(var(--ink-muted))]">{JSON.stringify(JSON.parse(log.details || "{}"), null, 2)}</code>
                          </pre>
                        </details>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        <div className="mt-6 pt-4 border-t border-[hsl(var(--line))] flex flex-col sm:flex-row items-center justify-between gap-4">
          <span className="text-sm text-[hsl(var(--ink-muted))]">
            第 <span className="font-semibold text-[hsl(var(--ink))]">{page}</span> / <span className="font-semibold text-[hsl(var(--ink))]">{totalPages}</span> 页
          </span>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
              disabled={page === 1}
            >
              上一页
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setPage((prev) => Math.min(prev + 1, totalPages))}
              disabled={page === totalPages}
            >
              下一页
            </Button>
          </div>
        </div>
      </Card>
    </div>
    </RequirePermission>
  );
}

"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Check, Clock, Copy, Eye, RefreshCw } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Pagination } from "@/components/ui/Pagination";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Select } from "@/components/ui/Select";
import { StatCard } from "@/components/ui/StatCard";

import { apiFetch, buildQuery, funboostFetch } from "@/lib/api";
import { formatDateTimeSeconds, formatNumber, toBackendDateTime, toDateTimeInputValue } from "@/lib/format";
import { useAutoRefresh } from "@/hooks/useAutoRefresh";

import { refreshIntervals, resultQuickRanges } from "../constants";
import type { QueryResultResponse, ResultRow, SpeedStats } from "../types";

type ResultsTabProps = {
  queueName: string;
  projectId?: string;
  canOperateQueue: boolean;
  onOpenJson: (title: string, content: string) => void;
};

export function ResultsTab({ queueName, projectId, canOperateQueue, onOpenJson }: ResultsTabProps) {
  const [results, setResults] = useState<ResultRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [status, setStatus] = useState("all");
  const [functionParams, setFunctionParams] = useState("");
  const [taskId, setTaskId] = useState("");
  const [minCost, setMinCost] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [stats, setStats] = useState<SpeedStats | null>(null);
  const [msgCount, setMsgCount] = useState<number | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [totalCount, setTotalCount] = useState(0);
  const [copiedTaskId, setCopiedTaskId] = useState<string | null>(null);
  const suppressNextAutoLoadRef = useRef(false);

  const loadResults = useCallback(async (options?: { endTimeOverride?: string }) => {
    const effectiveEndTime = options?.endTimeOverride ?? endTime;
    if (!queueName || !startTime || !effectiveEndTime) return;
    setLoading(true);
    setNotice(null);
    try {
      const query = buildQuery({
        col_name: queueName,
        start_time: toBackendDateTime(startTime),
        end_time: toBackendDateTime(effectiveEndTime),
        is_success: status === "all" ? "" : status,
        function_params: functionParams,
        task_id: taskId,
        page: currentPage,
        page_size: pageSize,
        project_id: projectId || "",
      });
      const response = await apiFetch<QueryResultResponse>(`/query_result?${query}`);
      setResults(response.data);
      setTotalCount(response.total_count);

      const statQuery = buildQuery({
        col_name: queueName,
        start_time: toBackendDateTime(startTime),
        end_time: toBackendDateTime(effectiveEndTime),
        project_id: projectId || "",
      });
      const statData = await apiFetch<SpeedStats>(`/speed_stats?${statQuery}`);
      setStats(statData);

      const msgData = await funboostFetch<{ count: number }>(
        `/funboost/get_msg_count?queue_name=${encodeURIComponent(queueName)}${projectId ? `&project_id=${projectId}` : ""}`
      );
      setMsgCount(msgData.count);
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "加载结果失败。");
    } finally {
      setLoading(false);
    }
  }, [queueName, startTime, endTime, status, functionParams, taskId, currentPage, pageSize, projectId]);

  const runAutoRefresh = useCallback(() => {
    const now = toDateTimeInputValue(new Date());
    // Auto refresh updates endTime, which would otherwise trigger the auto-load effect again.
    suppressNextAutoLoadRef.current = true;
    setEndTime(now);
    loadResults({ endTimeOverride: now });
    // If endTime doesn't change (minute precision), the effect won't run to clear this flag.
    setTimeout(() => {
      suppressNextAutoLoadRef.current = false;
    }, 0);
  }, [loadResults]);

  const { enabled: autoRefresh, toggle: toggleAutoRefresh, intervalMs, setIntervalMs } = useAutoRefresh(
    runAutoRefresh,
    false,
    30000
  );

  const refreshInterval = intervalMs / 1000;

  const handleToggleAutoRefresh = () => {
    if (!autoRefresh) {
      runAutoRefresh();
    }
    toggleAutoRefresh();
  };

  useEffect(() => {
    if (!queueName) return;
    const now = new Date();
    // Use local midnight to avoid timezone-shift showing 1969 in some environments.
    setStartTime(toDateTimeInputValue(new Date(1970, 0, 1, 0, 0, 0)));
    setEndTime(toDateTimeInputValue(now));
    setCurrentPage(0);
    setStatus("all");
    setFunctionParams("");
    setTaskId("");
    setMinCost("");
  }, [queueName]);

  useEffect(() => {
    if (suppressNextAutoLoadRef.current) {
      suppressNextAutoLoadRef.current = false;
      return;
    }
    if (queueName && startTime && endTime) {
      loadResults();
    }
  }, [queueName, startTime, endTime, loadResults]);

  const handleSearch = () => {
    if (currentPage === 0) {
      loadResults();
      return;
    }
    setCurrentPage(0);
  };

  const handleCopyTaskId = async (id: string) => {
    await navigator.clipboard.writeText(id);
    setCopiedTaskId(id);
    setTimeout(() => setCopiedTaskId(null), 1500);
  };

  const handleRetry = async (row: ResultRow) => {
    if (!canOperateQueue) return;
    let msgBody: unknown;
    try {
      msgBody = JSON.parse(row.params_str || "{}");
    } catch (err) {
      setNotice("重试失败：参数不是合法 JSON。");
      return;
    }
    if (!msgBody || typeof msgBody !== "object" || Array.isArray(msgBody)) {
      setNotice("重试失败：msg_body 必须是 JSON 对象。");
      return;
    }
    try {
      const response = await apiFetch<{
        success: boolean;
        data?: { task_id?: string };
        error?: string;
        message?: string;
      }>("/queue/publish", {
        method: "POST",
        json: {
          queue_name: queueName,
          msg_body: msgBody,
          task_id: row.task_id,
          project_id: projectId,
        },
      });
      if (!response.success) {
        throw new Error(response.error || response.message || "重试失败。");
      }
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "重试失败。");
    }
  };

  const filteredResults = useMemo(() => {
    if (!minCost) return results;
    const min = Number(minCost);
    if (Number.isNaN(min)) return results;
    return results.filter((row) => row.time_cost >= min);
  }, [results, minCost]);

  const truncateText = (text: unknown, maxLength: number = 40): string => {
    if (text === null || text === undefined) return "-";
    const str = typeof text === "string" ? text : JSON.stringify(text);
    if (!str) return "-";
    if (str.length <= maxLength) return str;
    return `${str.slice(0, maxLength)}...`;
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-end gap-2">
        <Button variant="outline" size="sm" onClick={() => loadResults()} disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          数据刷新
        </Button>
        <div className="flex items-center gap-1 rounded-full border border-[hsl(var(--line))] p-0.5">
          <span className="px-2 text-xs text-[hsl(var(--ink-muted))]">刷新间隔:</span>
          {refreshIntervals.map((interval) => (
            <button
              key={interval.value}
              onClick={() => setIntervalMs(interval.value * 1000)}
              className={`px-2 py-1 text-xs rounded-full transition ${refreshInterval === interval.value
                ? "bg-[hsl(var(--accent))] text-white"
                : "text-[hsl(var(--ink-muted))] hover:text-[hsl(var(--ink))]"
              }`}
            >
              {interval.label}
            </button>
          ))}
        </div>
        <Button variant={autoRefresh ? "primary" : "outline"} size="sm" onClick={handleToggleAutoRefresh}>
          <Clock className="h-4 w-4" />
          {autoRefresh ? "刷新中..." : "已暂停"}
        </Button>
      </div>

      {notice ? (
        <Card className="border border-[hsl(var(--accent))]/30 bg-[hsl(var(--accent))]/10 text-sm text-[hsl(var(--accent-2))]">
          {notice}
        </Card>
      ) : null}

      <Card>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="space-y-1">
            <label className="text-xs font-medium text-[hsl(var(--ink-muted))]">起始时间</label>
            <Input type="datetime-local" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-[hsl(var(--ink-muted))]">截止时间</label>
            <Input type="datetime-local" value={endTime} onChange={(e) => setEndTime(e.target.value)} />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-[hsl(var(--ink-muted))]">运行状态</label>
            <Select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="all">全部</option>
              <option value="2">成功</option>
              <option value="3">失败</option>
            </Select>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-[hsl(var(--ink-muted))]">Task ID</label>
            <Input placeholder="输入 task_id..." value={taskId} onChange={(e) => setTaskId(e.target.value)} />
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-xs text-[hsl(var(--ink-muted))]">快捷时间:</span>
          {resultQuickRanges.map((range) => (
            <button
              key={range.minutes}
              onClick={() => {
                const end = new Date();
                const start = new Date(end.getTime() - range.minutes * 60 * 1000);
                setStartTime(toDateTimeInputValue(start));
                setEndTime(toDateTimeInputValue(end));
              }}
              className="px-3 py-1.5 text-xs rounded-full border border-[hsl(var(--line))] text-[hsl(var(--ink-muted))] hover:border-[hsl(var(--accent))] hover:text-[hsl(var(--accent))]"
            >
              近{range.label}
            </button>
          ))}
          <div className="flex-1" />
          <div className="flex items-center gap-2">
            <label className="text-xs text-[hsl(var(--ink-muted))]">函数参数</label>
            <Input className="w-40" placeholder="参数关键字" value={functionParams} onChange={(e) => setFunctionParams(e.target.value)} />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-[hsl(var(--ink-muted))]">最小耗时(秒)</label>
            <Input className="w-20" placeholder="如 1" value={minCost} onChange={(e) => setMinCost(e.target.value)} />
          </div>
          <Button variant="primary" onClick={handleSearch}>
            <RefreshCw className="h-4 w-4" />
            查询
          </Button>
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="当前队列" value={queueName} helper="已选范围" />
        <StatCard
          label="查询统计"
          value={stats ? (
            <span>
              <span className="text-[hsl(var(--success))]">成功: {formatNumber(stats.success_num)}</span>
              {" / "}
              <span className="text-[hsl(var(--danger))]">失败: {formatNumber(stats.fail_num)}</span>
            </span>
          ) : "-"}
          helper="时间范围内"
        />
        <StatCard label="队列剩余" value={msgCount !== null ? formatNumber(msgCount) : "-"} helper="当前消息" />
        <StatCard label="失败率" value={stats ? `${((stats.fail_num / Math.max(stats.success_num + stats.fail_num, 1)) * 100).toFixed(1)}%` : "-"} helper="时间范围" tone="danger" />
      </div>

      <Card>
        <div className="flex items-center justify-between mb-3">
          <SectionHeader title="执行记录列表" subtitle="" />
        </div>
        <div className="overflow-x-auto">
          {loading ? (
            <div className="py-8 text-center text-sm text-[hsl(var(--ink-muted))]">
              <RefreshCw className="h-8 w-8 mx-auto mb-2 animate-spin text-[hsl(var(--accent))]" />
              正在加载结果...
            </div>
          ) : filteredResults.length === 0 ? (
            <div className="py-8 text-center text-sm text-[hsl(var(--ink-muted))]">暂无结果</div>
          ) : (
            <table className="w-full text-sm min-w-[980px] md:min-w-[1120px] xl:min-w-[1280px]">
              <thead className="text-left text-xs uppercase tracking-wider text-[hsl(var(--ink-muted))] bg-[hsl(var(--sand-2))]">
                <tr>
                  <th className="px-3 py-3 font-medium whitespace-nowrap hidden lg:table-cell">函数</th>
                  <th className="px-3 py-3 font-medium whitespace-nowrap">Task ID</th>
                  <th className="px-3 py-3 font-medium whitespace-nowrap">参数</th>
                  <th className="px-3 py-3 font-medium whitespace-nowrap">结果/异常</th>
                  <th className="px-3 py-3 font-medium whitespace-nowrap">发布时间</th>
                  <th className="px-3 py-3 font-medium whitespace-nowrap">开始时间</th>
                  <th className="px-3 py-3 font-medium whitespace-nowrap">耗时</th>
                  <th className="px-3 py-3 font-medium whitespace-nowrap">状态</th>
                  <th className="px-3 py-3 font-medium whitespace-nowrap">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[hsl(var(--line))]">
                {filteredResults.map((row, index) => {
                  const failed = !row.success;
                  const running = row.run_status === "running";
                  return (
                    <tr key={`${row.task_id}-${index}`} className="hover:bg-[hsl(var(--sand-2))]/50 transition-colors">
                      <td className="px-3 py-3 font-medium text-[hsl(var(--ink))] whitespace-nowrap max-w-[220px] hidden lg:table-cell">
                        <span className="truncate block" title={row.function}>{row.function}</span>
                      </td>
                      <td className="px-3 py-3 text-xs text-[hsl(var(--ink-muted))] max-w-[240px]">
                        <div className="flex items-center gap-1">
                          <span className="truncate block" title={row.task_id}>{truncateText(row.task_id, 28)}</span>
                          <button
                            onClick={() => handleCopyTaskId(row.task_id)}
                            className="p-1 rounded hover:bg-[hsl(var(--sand-2))] text-[hsl(var(--ink-muted))] hover:text-[hsl(var(--accent))]"
                            title="复制 Task ID"
                          >
                            {copiedTaskId === row.task_id ? (
                              <Check className="h-3 w-3 text-[hsl(var(--success))]" />
                            ) : (
                              <Copy className="h-3 w-3" />
                            )}
                          </button>
                        </div>
                      </td>
                      <td className="px-3 py-3 max-w-[260px]">
                        <div className="flex items-center gap-1">
                          <span className="text-xs text-[hsl(var(--ink-muted))] truncate block max-w-[180px]">
                            {truncateText(row.params_str, 32)}
                          </span>
                          {row.params_str && row.params_str !== "-" && (
                            <Button variant="ghost" size="sm" className="p-1 h-auto" onClick={() => onOpenJson("函数入参", row.params_str)}>
                              <Eye className="h-3 w-3" />
                            </Button>
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-3 max-w-[260px]">
                        <div className="flex items-center gap-1">
                          <span className="text-xs text-[hsl(var(--ink-muted))] truncate block max-w-[200px]">
                            {truncateText(row.result || row.exception, 32)}
                          </span>
                          {(row.result || row.exception) && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="p-1 h-auto"
                              onClick={() => onOpenJson(failed ? "异常信息" : "函数结果", row.result || row.exception)}
                            >
                              <Eye className="h-3 w-3" />
                            </Button>
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-3 text-xs text-[hsl(var(--ink-muted))] whitespace-nowrap">
                        {formatDateTimeSeconds(row.publish_time_format)}
                      </td>
                      <td className="px-3 py-3 text-xs text-[hsl(var(--ink-muted))] whitespace-nowrap">
                        {formatDateTimeSeconds(row.time_start)}
                      </td>
                      <td className="px-3 py-3 text-[hsl(var(--ink))] whitespace-nowrap">
                        {row.time_cost?.toFixed(3) || "-"}s
                      </td>
                      <td className="px-3 py-3 whitespace-nowrap">
                        {running ? (
                          <Badge tone="info">运行中</Badge>
                        ) : failed ? (
                          <Badge tone="danger">失败</Badge>
                        ) : (
                          <Badge tone="success">成功</Badge>
                        )}
                      </td>
                      <td className="px-3 py-3 whitespace-nowrap">
                        {failed ? (
                          <Button variant="outline" size="sm" className="h-7 px-2" onClick={() => handleRetry(row)} disabled={!canOperateQueue}>
                            重试
                          </Button>
                        ) : (
                          <span className="text-xs text-[hsl(var(--ink-muted))]">-</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
        <Pagination
          currentPage={currentPage}
          pageSize={pageSize}
          totalCount={totalCount}
          onPageChange={setCurrentPage}
          onPageSizeChange={(size) => { setPageSize(size); setCurrentPage(0); }}
          loading={loading}
        />
      </Card>
    </div>
  );
}

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { RefreshCw, Repeat, Search, Eye, Copy, Check, Clock } from "lucide-react";

import { RequirePermission } from "@/components/auth/RequirePermission";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Pagination } from "@/components/ui/Pagination";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Select } from "@/components/ui/Select";
import { StatCard } from "@/components/ui/StatCard";
import { JsonViewerModal } from "@/components/ui/JsonViewerModal";
import { apiFetch, buildQuery, funboostFetch } from "@/lib/api";
import { formatDateTime, formatNumber, toBackendDateTime, toDateTimeInputValue } from "@/lib/format";
import { useAutoRefresh } from "@/hooks/useAutoRefresh";
import { useActionPermissions } from "@/hooks/useActionPermissions";
import { useProject } from "@/contexts/ProjectContext";

const quickRanges = [
  { minutes: 1, label: "1分钟" },
  { minutes: 10, label: "10分钟" },
  { minutes: 60, label: "1小时" },
  { minutes: 360, label: "6小时" },
  { minutes: 1440, label: "1天" },
  { minutes: 2880, label: "2天" },
  { minutes: 10080, label: "7天" },
  { minutes: 43200, label: "30天" },
];

const refreshIntervals = [
  { value: 5, label: "5秒" },
  { value: 10, label: "10秒" },
  { value: 30, label: "30秒" },
  { value: 60, label: "60秒" },
];

type QueueOption = {
  collection_name: string;
  count: number;
};

type ResultRow = {
  function: string;
  task_id: string;
  params_str: string;
  result: string;
  publish_time_format: string;
  time_start: number;
  time_cost: number;
  run_times: number;
  run_status: string;
  success: boolean;
  exception: string;
  host_process: string;
  script_name?: string;
  total_thread?: number;
};

type SpeedStats = {
  success_num: number;
  fail_num: number;
  qps: number;
};

// API 响应类型（新的分页格式）
type QueryResultResponse = {
  data: ResultRow[];
  total_count: number;
  page: number;
  page_size: number;
};

export default function FunResultsPage() {
  const [queues, setQueues] = useState<QueueOption[]>([]);
  const [queue, setQueue] = useState("");
  const [status, setStatus] = useState("all");
  const [functionParams, setFunctionParams] = useState("");
  const [taskId, setTaskId] = useState("");
  const [minCost, setMinCost] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [results, setResults] = useState<ResultRow[]>([]);
  const [stats, setStats] = useState<SpeedStats | null>(null);
  const [msgCount, setMsgCount] = useState<number | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [copiedTaskId, setCopiedTaskId] = useState<string | null>(null);

  // 分页状态
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);  // 默认20条
  const [totalCount, setTotalCount] = useState(0);

  // JSON viewer modal state
  const [jsonModalOpen, setJsonModalOpen] = useState(false);
  const [jsonModalTitle, setJsonModalTitle] = useState("");
  const [jsonModalContent, setJsonModalContent] = useState("");

  // 获取当前项目
  const { currentProject, careProjectName } = useProject();
  const { canExecute } = useActionPermissions("queue");
  // 当未选择具体项目时默认有写权限（全部项目模式）
  const projectLevel = currentProject?.permission_level ?? "admin";
  const canWriteProject = !currentProject || projectLevel === "write" || projectLevel === "admin";
  const canOperateQueue = canExecute && canWriteProject;

  const { enabled: autoRefresh, toggle: toggleAutoRefresh, intervalMs, setIntervalMs } = useAutoRefresh(
    () => loadResults(),
    false,
    30000  // 默认 30 秒
  );

  // 当前间隔（秒）
  const refreshInterval = intervalMs / 1000;

  useEffect(() => {
    const now = new Date();
    const start = new Date(now.getTime() - 2880 * 60 * 1000);
    setStartTime(toDateTimeInputValue(start));
    setEndTime(toDateTimeInputValue(now));
  }, []);

  const loadQueues = useCallback(async () => {
    try {
      // 构建 API URL，添加 project_id 参数
      let url = "/query_cols";
      if (currentProject?.id) {
        url += `?project_id=${currentProject.id}`;
      }
      const data = await apiFetch<QueueOption[]>(url);
      setQueues(data);
      if (!queue && data.length > 0) {
        setQueue(data[0].collection_name);
      }
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "加载队列失败。");
    }
  }, [queue, currentProject?.id, careProjectName]);

  const loadResults = useCallback(async () => {
    if (!queue || !startTime || !endTime) return;
    setLoading(true);
    setNotice(null);
    try {
      const effectiveEnd = autoRefresh ? toDateTimeInputValue(new Date()) : endTime;
      if (autoRefresh) {
        setEndTime(effectiveEnd);
      }
      const query = buildQuery({
        col_name: queue,
        start_time: toBackendDateTime(startTime),
        end_time: toBackendDateTime(effectiveEnd),
        is_success: status === "all" ? "" : status,
        function_params: functionParams,
        task_id: taskId,
        page: currentPage,
        page_size: pageSize,
        project_id: currentProject?.id || "",
      });

      const response = await apiFetch<QueryResultResponse>(`/query_result?${query}`);
      setResults(response.data);
      setTotalCount(response.total_count);

      const statQuery = buildQuery({
        col_name: queue,
        start_time: toBackendDateTime(startTime),
        end_time: toBackendDateTime(effectiveEnd),
        project_id: currentProject?.id || "",
      });
      const statData = await apiFetch<SpeedStats>(`/speed_stats?${statQuery}`);
      setStats(statData);

      const msgData = await funboostFetch<{ count: number }>(
        `/funboost/get_msg_count?queue_name=${encodeURIComponent(queue)}${currentProject?.id ? `&project_id=${currentProject.id}` : ""}`
      );
      setMsgCount(msgData.count);
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "加载结果失败。");
    } finally {
      setLoading(false);
    }
  }, [queue, startTime, endTime, status, functionParams, taskId, autoRefresh, currentPage, pageSize, currentProject?.id, careProjectName]);

  useEffect(() => {
    loadQueues();
  }, [loadQueues]);

  useEffect(() => {
    if (queue) {
      loadResults();
    }
  }, [queue, loadResults]);

  const filteredResults = useMemo(() => {
    if (!minCost) return results;
    const min = Number(minCost);
    if (Number.isNaN(min)) return results;
    return results.filter((row) => row.time_cost >= min);
  }, [results, minCost]);

  // 检测当前选中的快捷时间范围
  const activeQuickRange = useMemo(() => {
    if (!startTime || !endTime) return null;

    const start = new Date(startTime);
    const end = new Date(endTime);
    const diffMinutes = Math.round((end.getTime() - start.getTime()) / (60 * 1000));

    // 允许5分钟的误差
    const tolerance = 5;
    for (const range of quickRanges) {
      if (Math.abs(diffMinutes - range.minutes) <= tolerance) {
        return range.minutes;
      }
    }
    return null;
  }, [startTime, endTime]);

  const handleRetry = async (row: ResultRow) => {
    try {
      if (!canOperateQueue) {
        setNotice("当前项目无写权限，无法重试任务。");
        return;
      }
      const msgBody = JSON.parse(row.params_str || "{}");
      await funboostFetch("/funboost/publish", {
        method: "POST",
        json: {
          queue_name: queue,
          msg_body: msgBody,
          task_id: row.task_id,
          project_id: currentProject?.id,
        },
      });
      setNotice("已发送重试。");
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "重试失败。");
    }
  };

  const handleViewJson = (title: string, content: string) => {
    setJsonModalTitle(title);
    setJsonModalContent(content);
    setJsonModalOpen(true);
  };

  // 分页处理函数
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handlePageSizeChange = (size: number) => {
    setPageSize(size);
    setCurrentPage(0); // 切换每页数量时重置到第一页
  };

  // 搜索时重置页码
  const handleSearch = () => {
    setCurrentPage(0);
    loadResults();
  };

  const handleCopyTaskId = async (taskId: string) => {
    try {
      await navigator.clipboard.writeText(taskId);
      setCopiedTaskId(taskId);
      setTimeout(() => setCopiedTaskId(null), 2000);
    } catch {
      // Fallback
    }
  };

  // Truncate text for display
  const truncateText = (text: unknown, maxLength: number = 50): string => {
    if (text === null || text === undefined) return "-";
    // Convert non-string values to string (handles objects, numbers, etc.)
    const str = typeof text === "string" ? text : JSON.stringify(text);
    if (!str) return "-";
    if (str.length <= maxLength) return str;
    return str.substring(0, maxLength) + "...";
  };

  return (
    <RequirePermission permissions={["queue:read"]} projectLevel="read">
      <div className="space-y-6">
        {/* Action Bar */}
        <div className="flex flex-wrap items-center justify-end gap-2">
          <Button variant="outline" size="sm" onClick={loadResults}>
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
          <Button
            variant={autoRefresh ? "primary" : "outline"}
            size="sm"
            onClick={toggleAutoRefresh}
          >
            <Clock className="h-4 w-4" />
            {autoRefresh ? "刷新中..." : "已暂停"}
          </Button>
        </div>

        {notice ? (
          <Card className="border border-[hsl(var(--accent))]/30 bg-[hsl(var(--accent))]/10 text-sm text-[hsl(var(--accent-2))]">
            {notice}
          </Card>
        ) : null}

        {/* Filter Section */}
        <Card>
          <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
            <div className="space-y-1">
              <label className="text-xs font-medium text-[hsl(var(--ink-muted))]">队列名称</label>
              <Select value={queue} onChange={(e) => setQueue(e.target.value)}>
                {queues.map((item) => (
                  <option key={item.collection_name} value={item.collection_name}>
                    {item.collection_name} (记录数: {formatNumber(item.count)})
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-[hsl(var(--ink-muted))]">起始时间</label>
              <Input
                type="datetime-local"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-[hsl(var(--ink-muted))]">截止时间</label>
              <Input
                type="datetime-local"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
              />
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
              <label className="text-xs font-medium text-[hsl(var(--ink-muted))]">函数参数</label>
              <Input
                placeholder="输入参数搜索关键..."
                value={functionParams}
                onChange={(e) => setFunctionParams(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-[hsl(var(--ink-muted))]">Task ID</label>
              <Input
                placeholder="输入task_id..."
                value={taskId}
                onChange={(e) => setTaskId(e.target.value)}
              />
            </div>
          </div>

          {/* Quick Range + Min Cost + Search */}
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-xs text-[hsl(var(--ink-muted))]">快捷时间:</span>
            {quickRanges.map((range) => {
              const isActive = activeQuickRange === range.minutes;
              return (
                <button
                  key={range.minutes}
                  onClick={() => {
                    const end = new Date();
                    const start = new Date(end.getTime() - range.minutes * 60 * 1000);
                    setStartTime(toDateTimeInputValue(start));
                    setEndTime(toDateTimeInputValue(end));
                  }}
                  className={`px-3 py-1.5 text-xs rounded-full border transition ${isActive
                    ? "border-[hsl(var(--accent))] bg-[hsl(var(--accent))] text-white"
                    : "border-[hsl(var(--line))] text-[hsl(var(--ink-muted))] hover:border-[hsl(var(--accent))] hover:text-[hsl(var(--accent))]"
                    }`}
                >
                  近{range.label}
                </button>
              );
            })}
            <div className="flex-1" />
            <div className="flex items-center gap-2">
              <label className="text-xs text-[hsl(var(--ink-muted))]">最小耗时(秒)</label>
              <Input
                className="w-20"
                placeholder="如: 1"
                value={minCost}
                onChange={(e) => setMinCost(e.target.value)}
              />
            </div>
            <Button variant="primary" onClick={handleSearch}>
              <Search className="h-4 w-4" />
              查询
            </Button>
          </div>
        </Card>

        {/* Statistics Cards */}
        <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="当前队列"
            value={queue ? truncateText(queue, 20) : "-"}
            helper="已选范围"
          />
          <StatCard
            label="查询范围统计"
            value={
              stats ? (
                <span>
                  <span className="text-[hsl(var(--success))]">成功: {formatNumber(stats.success_num)}</span>
                  {" / "}
                  <span className="text-[hsl(var(--danger))]">失败: {formatNumber(stats.fail_num)}</span>
                </span>
              ) : (
                "-"
              )
            }
            helper="时间范围内"
          />
          <StatCard
            label="最近1分钟"
            value={
              <span>
                <span className="text-[hsl(var(--success))]">成功: 0</span>
                {" / "}
                <span className="text-[hsl(var(--danger))]">失败: 0</span>
              </span>
            }
            helper="10秒/刷新"
          />
          <StatCard
            label="队列剩余消息"
            value={msgCount !== null ? formatNumber(msgCount) : "-"}
            helper="10秒/刷新"
          />
        </div>

        {/* Results Table */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <SectionHeader title="执行记录列表" subtitle="" />
          </div>

          <div className="overflow-x-auto">
            {loading ? (
              <div className="py-8 text-center text-sm text-[hsl(var(--ink-muted))]">
                <RefreshCw className="h-8 w-8 mx-auto mb-2 animate-spin text-[hsl(var(--accent))]" />
                正在加载结果...
              </div>
            ) : filteredResults.length === 0 ? (
              <EmptyState title="暂无结果" subtitle="尝试调整时间范围或队列。" />
            ) : (
              <table className="w-full text-sm">
                <thead className="text-left text-xs uppercase tracking-wider text-[hsl(var(--ink-muted))] bg-[hsl(var(--sand-2))]">
                  <tr>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">函数名称</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">Task ID</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">函数入参</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">函数结果</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">发布时间</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">开始时间</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">耗时(秒)</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">执行次数</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">运行状态</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">是否成功</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">健康策略</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">执行机器</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">线程数</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[hsl(var(--line))]">
                  {filteredResults.map((row, index) => {
                    const failed = !row.success;
                    const running = row.run_status === "running";
                    return (
                      <tr
                        key={`${row.task_id}-${index}`}
                        className="hover:bg-[hsl(var(--sand-2))]/50 transition-colors"
                      >
                        {/* 函数名称 */}
                        <td className="px-3 py-3 font-medium text-[hsl(var(--ink))] whitespace-nowrap max-w-[120px]">
                          <span className="truncate block" title={row.function}>
                            {row.function}
                          </span>
                        </td>

                        {/* Task ID */}
                        <td className="px-3 py-3 text-xs text-[hsl(var(--ink-muted))] max-w-[180px]">
                          <div className="flex items-center gap-1">
                            <span className="truncate block" title={row.task_id}>
                              {truncateText(row.task_id, 20)}
                            </span>
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

                        {/* 函数入参 */}
                        <td className="px-3 py-3 max-w-[150px]">
                          <div className="flex items-center gap-1">
                            <span className="text-xs text-[hsl(var(--ink-muted))] truncate block max-w-[80px]">
                              {truncateText(row.params_str, 20)}
                            </span>
                            {row.params_str && row.params_str !== "-" && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="p-1 h-auto"
                                onClick={() => handleViewJson("函数入参", row.params_str)}
                              >
                                <Eye className="h-3 w-3" />
                              </Button>
                            )}
                          </div>
                        </td>

                        {/* 函数结果 */}
                        <td className="px-3 py-3 max-w-[150px]">
                          <div className="flex items-center gap-1">
                            <span className="text-xs text-[hsl(var(--ink-muted))] truncate block max-w-[80px]">
                              {truncateText(row.result || row.exception, 20)}
                            </span>
                            {(row.result || row.exception) && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="p-1 h-auto"
                                onClick={() =>
                                  handleViewJson(
                                    failed ? "异常信息" : "函数结果",
                                    row.result || row.exception
                                  )
                                }
                              >
                                <Eye className="h-3 w-3" />
                              </Button>
                            )}
                          </div>
                        </td>

                        {/* 发布时间 */}
                        <td className="px-3 py-3 text-xs text-[hsl(var(--ink-muted))] whitespace-nowrap">
                          {row.publish_time_format || "-"}
                        </td>

                        {/* 开始时间 */}
                        <td className="px-3 py-3 text-xs text-[hsl(var(--ink-muted))] whitespace-nowrap">
                          {row.time_start ? formatDateTime(row.time_start) : "-"}
                        </td>

                        {/* 耗时(秒) */}
                        <td className="px-3 py-3 text-[hsl(var(--ink))] whitespace-nowrap">
                          {row.time_cost?.toFixed(3) || "-"}
                        </td>

                        {/* 执行次数 */}
                        <td className="px-3 py-3 text-center text-[hsl(var(--ink))]">
                          {row.run_times || 1}
                        </td>

                        {/* 运行状态 */}
                        <td className="px-3 py-3 whitespace-nowrap">
                          <Badge tone={running ? "info" : "neutral"}>
                            {row.run_status || "finish"}
                          </Badge>
                        </td>

                        {/* 是否成功 */}
                        <td className="px-3 py-3 whitespace-nowrap">
                          {running ? (
                            <span className="text-[hsl(var(--info))]">-</span>
                          ) : failed ? (
                            <Badge tone="danger">失败</Badge>
                          ) : (
                            <Badge tone="success">成功</Badge>
                          )}
                        </td>

                        {/* 健康策略 */}
                        <td className="px-3 py-3 text-center">
                          {failed && row.params_str ? (
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-7 px-2"
                              onClick={() => handleRetry(row)}
                              disabled={!canOperateQueue}
                            >
                              <Repeat className="h-3 w-3" />
                              重试
                            </Button>
                          ) : (
                            <span className="text-[hsl(var(--ink-muted))]">-</span>
                          )}
                        </td>

                        {/* 执行机器 */}
                        <td className="px-3 py-3 text-xs text-[hsl(var(--ink-muted))] whitespace-nowrap max-w-[120px]">
                          <span className="truncate block" title={row.host_process}>
                            {truncateText(row.host_process, 15) || "-"}
                          </span>
                        </td>

                        {/* 场景数 */}
                        <td className="px-3 py-3 text-center text-[hsl(var(--ink))]">
                          {row.total_thread || "-"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>

          {/* 分页控件 */}
          <Pagination
            currentPage={currentPage}
            pageSize={pageSize}
            totalCount={totalCount}
            onPageChange={handlePageChange}
            onPageSizeChange={handlePageSizeChange}
            loading={loading}
          />
        </Card>

        {/* JSON Viewer Modal */}
        <JsonViewerModal
          open={jsonModalOpen}
          title={jsonModalTitle}
          content={jsonModalContent}
          onClose={() => setJsonModalOpen(false)}
        />
      </div>
    </RequirePermission>
  );
}

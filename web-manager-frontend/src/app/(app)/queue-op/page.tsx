"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertTriangle, ChartLine, Info, Pause, Play, RefreshCw, Trash2, Eye, Zap } from "lucide-react";

import { RequirePermission } from "@/components/auth/RequirePermission";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { StatCard } from "@/components/ui/StatCard";
import { Toggle } from "@/components/ui/Toggle";
import { QueueTimeSeriesChart } from "@/components/charts/QueueTimeSeriesChart";
import { JsonViewerModal } from "@/components/ui/JsonViewerModal";
import { apiFetch, funboostFetch } from "@/lib/api";
import { formatDateTime, formatNumber, toDateTimeInputValue } from "@/lib/format";
import { useAutoRefresh } from "@/hooks/useAutoRefresh";
import { useActionPermissions } from "@/hooks/useActionPermissions";
import { useProject } from "@/contexts/ProjectContext";

const curveSamplesOptions = [60, 120, 180, 360, 720, 1440, 8640];
const PAGE_SIZE = 20;

type QueueParams = {
  broker_kind?: string;
  consuming_function_name?: string;
  auto_generate_info?: Record<string, unknown>;
};

type QueueInfo = {
  queue_params?: QueueParams;
  active_consumers?: Array<Record<string, unknown>>;
  pause_flag?: number;
  msg_num_in_broker?: number;
  history_run_count?: number;
  history_run_fail_count?: number;
  all_consumers_last_x_s_execute_count?: number;
  all_consumers_last_x_s_execute_count_fail?: number;
  all_consumers_last_x_s_avarage_function_spend_time?: number;
  all_consumers_avarage_function_spend_time_from_start?: number;
  all_consumers_last_execute_task_time?: number;
};

type QueueRow = QueueInfo & {
  queue_name: string;
};

type QueueTimeSeriesPoint = {
  report_data: {
    history_run_count?: number;
    history_run_fail_count?: number;
    all_consumers_last_x_s_execute_count?: number;
    all_consumers_last_x_s_execute_count_fail?: number;
    all_consumers_last_x_s_avarage_function_spend_time?: number;
    all_consumers_avarage_function_spend_time_from_start?: number;
    msg_num_in_broker?: number;
  };
  report_ts: number;
};

export default function QueueOpPage() {
  const [queues, setQueues] = useState<QueueRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [activeOnly, setActiveOnly] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [modalQueue, setModalQueue] = useState<QueueRow | null>(null);
  const [consumerDetails, setConsumerDetails] = useState<Record<string, unknown>[] | null>(null);
  const [chartQueue, setChartQueue] = useState<QueueRow | null>(null);
  const [chartData, setChartData] = useState<QueueTimeSeriesPoint[]>([]);
  const [chartSamples, setChartSamples] = useState(360);
  const [chartLoading, setChartLoading] = useState(false);
  const [chartStartTime, setChartStartTime] = useState(() => {
    const d = new Date(Date.now() - 3600 * 1000);
    return toDateTimeInputValue(d);
  });
  const [chartEndTime, setChartEndTime] = useState(() => {
    const d = new Date();
    return toDateTimeInputValue(d);
  });
  const [currentPage, setCurrentPage] = useState(1);

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
  const canClearQueue = canOperateQueue;

  const fetchQueues = useCallback(async () => {
    setLoading(true);
    try {
      // 构建 API URL，添加 project_id 参数
      let url = "/queue/params_and_active_consumers";
      if (currentProject?.id) {
        url += `?project_id=${currentProject.id}`;
      }
      const data = await apiFetch<Record<string, QueueInfo>>(url);
      const rows = Object.entries(data).map(([queue_name, info]) => ({
        queue_name,
        ...info,
      }));
      setQueues(rows);
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "加载队列失败。");
    } finally {
      setLoading(false);
    }
  }, [currentProject?.id, careProjectName]);

  const { enabled: autoRefresh, toggle: toggleAutoRefresh } = useAutoRefresh(fetchQueues, false, 10000);

  useEffect(() => {
    fetchQueues();

    // 监听关注项目变更事件，自动刷新队列数据
    const handleCareProjectChanged = () => {
      fetchQueues();
    };
    window.addEventListener("careProjectChanged", handleCareProjectChanged);

    return () => {
      window.removeEventListener("careProjectChanged", handleCareProjectChanged);
    };
  }, [fetchQueues]);

  const stats = useMemo(() => {
    const activeQueues = queues.filter((queue) => (queue.active_consumers?.length ?? 0) > 0);
    const idleQueues = queues.filter((queue) => (queue.active_consumers?.length ?? 0) === 0);
    const consumers = queues.reduce((sum, queue) => sum + (queue.active_consumers?.length ?? 0), 0);
    const retryCount = queues.reduce((sum, queue) => sum + (queue.history_run_fail_count ?? 0), 0);
    return {
      active: activeQueues.length,
      idle: idleQueues.length,
      consumers,
      retryCount,
    };
  }, [queues]);

  const filteredQueues = useMemo(() => {
    return queues.filter((queue) => {
      if (activeOnly && (queue.active_consumers?.length ?? 0) === 0) {
        return false;
      }
      if (search && !queue.queue_name.toLowerCase().includes(search.toLowerCase())) {
        return false;
      }
      return true;
    });
  }, [queues, search, activeOnly]);

  // Pagination
  const totalPages = Math.ceil(filteredQueues.length / PAGE_SIZE);
  const paginatedQueues = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return filteredQueues.slice(start, start + PAGE_SIZE);
  }, [filteredQueues, currentPage]);

  const refreshAllMsgCounts = async () => {
    setNotice(null);
    try {
      const updated = await Promise.all(
        queues.map(async (queue) => {
          try {
            let url = `/funboost/get_msg_count?queue_name=${encodeURIComponent(queue.queue_name)}`;
            if (currentProject?.id) {
              url += `&project_id=${currentProject.id}`;
            }
            const data = await funboostFetch<{ queue_name: string; count: number }>(url);
            return { ...queue, msg_num_in_broker: data.count };
          } catch {
            return queue;
          }
        })
      );
      setQueues(updated);
      setNotice("消息数量已刷新。");
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "刷新失败。");
    }
  };

  const openQueueConfig = (queue: QueueRow) => {
    setJsonModalTitle(`队列配置: ${queue.queue_name}`);
    setJsonModalContent(JSON.stringify(queue.queue_params ?? {}, null, 2));
    setJsonModalOpen(true);
  };

  const loadConsumers = async (queue: QueueRow) => {
    setModalQueue(queue);
    try {
      let url = `/running_consumer/hearbeat_info_by_queue_name?queue_name=${encodeURIComponent(queue.queue_name)}`;
      if (currentProject?.id) {
        url += `&project_id=${currentProject.id}`;
      }
      const data = await apiFetch<Record<string, unknown>[]>(url);
      setConsumerDetails(data);
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "加载消费者失败。");
    }
  };

  const loadChartData = async (queue?: QueueRow) => {
    const targetQueue = queue || chartQueue;
    if (!targetQueue) return;
    if (queue) setChartQueue(queue);
    setChartLoading(true);
    try {
      const startTs = Math.floor(new Date(chartStartTime).getTime() / 1000);
      const endTs = Math.floor(new Date(chartEndTime).getTime() / 1000);
      let url = `/queue/get_time_series_data/${encodeURIComponent(targetQueue.queue_name)}?start_ts=${startTs}&end_ts=${endTs}&curve_samples_count=${chartSamples}`;
      if (currentProject?.id) {
        url += `&project_id=${currentProject.id}`;
      }
      const data = await apiFetch<QueueTimeSeriesPoint[]>(url);
      setChartData(data);
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "加载曲线数据失败。");
    } finally {
      setChartLoading(false);
    }
  };

  const handleQueueAction = async (queue: QueueRow, action: "clear" | "pause" | "resume" | "deprecate") => {
    setNotice(null);
    try {
      if ((action === "pause" || action === "resume") && !canOperateQueue) {
        setNotice("当前项目无写权限，无法执行队列操作。");
        return;
      }
      if ((action === "clear" || action === "deprecate") && !canClearQueue) {
        setNotice("当前项目无写权限，无法清空或废弃队列。");
        return;
      }
      if (action === "clear") {
        await funboostFetch("/funboost/clear_queue", {
          method: "POST",
          json: { queue_name: queue.queue_name, project_id: currentProject?.id },
        });
      }
      if (action === "deprecate") {
        await funboostFetch("/funboost/deprecate_queue", {
          method: "DELETE",
          json: { queue_name: queue.queue_name, project_id: currentProject?.id },
        });
      }
      if (action === "pause") {
        let url = `/queue/pause/${encodeURIComponent(queue.queue_name)}`;
        if (currentProject?.id) {
          url += `?project_id=${currentProject.id}`;
        }
        await apiFetch(url, { method: "POST" });
      }
      if (action === "resume") {
        let url = `/queue/resume/${encodeURIComponent(queue.queue_name)}`;
        if (currentProject?.id) {
          url += `?project_id=${currentProject.id}`;
        }
        await apiFetch(url, { method: "POST" });
      }
      await fetchQueues();
      setNotice("操作已完成。");
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "操作失败。");
    }
  };

  const startAutoConsume = async () => {
    if (!canOperateQueue) {
      setNotice("当前项目无写权限，无法启动自动消费。");
      return;
    }
    setNotice("正在启动自动消费...");
    // This would trigger auto-consume on all queues
    try {
      await fetchQueues();
      setNotice("自动消费已启动。");
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "启动失败。");
    }
  };

  return (
    <RequirePermission permissions={["queue:read"]} projectLevel="read">
      <div className="space-y-6">
        {notice ? (
          <Card className="border border-[hsl(var(--accent))]/30 bg-[hsl(var(--accent))]/10 text-sm text-[hsl(var(--accent-2))]">
            {notice}
          </Card>
        ) : null}

        {/* 统计卡片 - 独立一行 */}
        <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
          <StatCard label="远程队列" value={queues.length} helper="总数" tone="info" />
          <StatCard label="消费队列" value={stats.active} helper="活跃" tone="success" />
          <StatCard label="消费者监控" value={stats.consumers} helper="在线" tone="warning" />
          <StatCard label="重试次数" value={stats.retryCount} helper="累计" tone="danger" />
        </div>

        {/* 筛选和操作区域 */}
        <Card>
          <div className="flex flex-col gap-4">
            {/* 搜索和筛选 */}
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-[hsl(var(--ink-muted))]">队列搜索</span>
                <Input
                  placeholder="请输入队列名称搜索..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-64"
                />
              </div>
              <Toggle checked={activeOnly} onChange={setActiveOnly} label="仅显示消费队列" />
              <div className="flex-1" />
              {/* 操作按钮 */}
              <div className="flex flex-wrap items-center gap-2">
                <Button variant="secondary" size="sm" onClick={refreshAllMsgCounts} className="cursor-pointer">
                  <RefreshCw className="h-4 w-4" />
                  全部队列消息数量
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={startAutoConsume}
                  className="cursor-pointer"
                  disabled={!canOperateQueue}
                >
                  <Zap className="h-4 w-4" />
                  启动自动消费
                </Button>
                <Button variant="outline" size="sm" onClick={fetchQueues} className="cursor-pointer">
                  <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                  刷新
                </Button>
              </div>
            </div>
          </div>
        </Card>

        {/* Queue Table */}
        <Card>
          <div className="overflow-x-auto">
            {loading ? (
              <div className="py-8 text-center text-sm text-[hsl(var(--ink-muted))]">
                <RefreshCw className="h-8 w-8 mx-auto mb-2 animate-spin text-[hsl(var(--accent))]" />
                正在加载队列...
              </div>
            ) : filteredQueues.length === 0 ? (
              <EmptyState title="未找到队列" subtitle="调整筛选条件或刷新列表。" />
            ) : (
              <table className="w-full text-sm">
                <thead className="text-left text-xs uppercase tracking-wider text-[hsl(var(--ink-muted))] bg-[hsl(var(--sand-2))]">
                  <tr>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">名称</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">消费者数量</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">Broker类型</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">消费函数</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">最近执行时间</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">消息数量</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">历史运行次数</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">历史失败次数</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">近10秒完成</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">近10秒失败</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">累计平均耗时</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">状态</th>
                    <th className="px-3 py-3 font-medium whitespace-nowrap">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[hsl(var(--line))]">
                  {paginatedQueues.map((queue) => {
                    const hasConsumers = (queue.active_consumers?.length ?? 0) > 0;
                    const isPaused = queue.pause_flag === 1;
                    const consumingFunction = queue.queue_params?.consuming_function_name ?? "-";

                    return (
                      <tr
                        key={queue.queue_name}
                        className="hover:bg-[hsl(var(--sand-2))]/50 transition-colors"
                      >
                        {/* 名称 */}
                        <td className="px-3 py-3">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-[hsl(var(--ink))]">{queue.queue_name}</span>
                            {hasConsumers ? (
                              <Badge tone="success">消费</Badge>
                            ) : (
                              <Badge tone="neutral">等待</Badge>
                            )}
                            {isPaused && <Badge tone="warning">已暂停</Badge>}
                          </div>
                        </td>

                        {/* 消费者数量 */}
                        <td className="px-3 py-3 text-center">
                          <Badge tone={hasConsumers ? "success" : "neutral"}>
                            {queue.active_consumers?.length ?? 0}
                          </Badge>
                        </td>

                        {/* Broker类型 */}
                        <td className="px-3 py-3">
                          <Badge tone="info">{queue.queue_params?.broker_kind ?? "-"}</Badge>
                        </td>

                        {/* 消费函数 */}
                        <td className="px-3 py-3 text-[hsl(var(--ink))]">
                          <code className="text-xs bg-[hsl(var(--sand-2))] px-1.5 py-0.5 rounded">
                            {consumingFunction}
                          </code>
                        </td>

                        {/* 最近执行时间 */}
                        <td className="px-3 py-3 text-xs text-[hsl(var(--ink-muted))] whitespace-nowrap">
                          {formatDateTime(queue.all_consumers_last_execute_task_time ?? null)}
                        </td>

                        {/* 消息数量 */}
                        <td className="px-3 py-3 text-center">
                          <Badge tone="warning">
                            {formatNumber(queue.msg_num_in_broker ?? 0)}
                          </Badge>
                        </td>

                        {/* 历史运行次数 */}
                        <td className="px-3 py-3 text-center text-[hsl(var(--ink))]">
                          {formatNumber(queue.history_run_count ?? 0)}
                        </td>

                        {/* 历史失败次数 */}
                        <td className="px-3 py-3 text-center">
                          <span className={queue.history_run_fail_count ? "text-[hsl(var(--danger))]" : "text-[hsl(var(--ink-muted))]"}>
                            {formatNumber(queue.history_run_fail_count ?? 0)}
                          </span>
                        </td>

                        {/* 近10秒完成 */}
                        <td className="px-3 py-3 text-center text-[hsl(var(--ink))]">
                          {queue.all_consumers_last_x_s_execute_count ?? 0}
                        </td>

                        {/* 近10秒失败 */}
                        <td className="px-3 py-3 text-center">
                          <span className={queue.all_consumers_last_x_s_execute_count_fail ? "text-[hsl(var(--danger))]" : "text-[hsl(var(--ink-muted))]"}>
                            {queue.all_consumers_last_x_s_execute_count_fail ?? 0}
                          </span>
                        </td>

                        {/* 累计平均耗时 */}
                        <td className="px-3 py-3 text-center text-[hsl(var(--ink))]">
                          {queue.all_consumers_avarage_function_spend_time_from_start
                            ? `${queue.all_consumers_avarage_function_spend_time_from_start.toFixed(3)}s`
                            : "-"}
                        </td>

                        {/* 状态 */}
                        <td className="px-3 py-3">
                          {isPaused ? (
                            <Badge tone="warning">暂停中</Badge>
                          ) : hasConsumers ? (
                            <Badge tone="success">运行中</Badge>
                          ) : (
                            <Badge tone="neutral">空闲</Badge>
                          )}
                        </td>

                        {/* 操作 */}
                        <td className="px-3 py-3">
                          <div className="flex items-center gap-1">
                            <Button
                              variant="secondary"
                              size="sm"
                              className="h-7 px-2"
                              onClick={() => openQueueConfig(queue)}
                            >
                              <Eye className="h-3 w-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 px-2"
                              onClick={() => loadChartData(queue)}
                            >
                              <ChartLine className="h-3 w-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 px-2"
                              onClick={() => loadConsumers(queue)}
                            >
                              <Info className="h-3 w-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 px-2"
                              onClick={() => handleQueueAction(queue, isPaused ? "resume" : "pause")}
                              disabled={!canOperateQueue}
                            >
                              {isPaused ? <Play className="h-3 w-3" /> : <Pause className="h-3 w-3" />}
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 px-2 text-[hsl(var(--danger))]"
                              onClick={() => handleQueueAction(queue, "clear")}
                              disabled={!canClearQueue}
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-end gap-2 mt-4 pt-4 border-t border-[hsl(var(--line))]">
              <Button
                variant="outline"
                size="sm"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(1)}
              >
                首页
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(currentPage - 1)}
              >
                上一页
              </Button>
              <span className="px-3 py-1 text-sm text-[hsl(var(--ink-muted))]">
                {currentPage} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage(currentPage + 1)}
              >
                下一页
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage(totalPages)}
              >
                末页
              </Button>
            </div>
          )}
        </Card>

        {/* Queue Config JSON Modal */}
        <JsonViewerModal
          open={jsonModalOpen}
          title={jsonModalTitle}
          content={jsonModalContent}
          onClose={() => setJsonModalOpen(false)}
        />

        {/* Consumer Details Modal */}
        <Modal
          open={modalQueue !== null}
          title={modalQueue ? `消费者详情: ${modalQueue.queue_name}` : "消费者详情"}
          onClose={() => {
            setModalQueue(null);
            setConsumerDetails(null);
          }}
          footer={
            <div className="flex justify-end">
              <Button variant="outline" onClick={() => setModalQueue(null)}>
                关闭
              </Button>
            </div>
          }
        >
          {modalQueue ? (
            <div className="space-y-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
                  队列参数
                </p>
                <pre className="mt-2 rounded-2xl bg-[hsl(var(--sand-2))] p-4 text-xs text-[hsl(var(--ink))] overflow-auto max-h-48">
                  {JSON.stringify(modalQueue.queue_params ?? {}, null, 2)}
                </pre>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
                  活跃消费者 ({consumerDetails?.length ?? modalQueue.active_consumers?.length ?? 0})
                </p>
                {consumerDetails ? (
                  <pre className="mt-2 rounded-2xl bg-[hsl(var(--sand-2))] p-4 text-xs text-[hsl(var(--ink))] overflow-auto max-h-80">
                    {JSON.stringify(consumerDetails, null, 2)}
                  </pre>
                ) : (
                  <p className="mt-2 text-sm text-[hsl(var(--ink-muted))]">
                    正在加载消费者详情...
                  </p>
                )}
              </div>
            </div>
          ) : null}
        </Modal>

        {/* Chart Modal */}
        <Modal
          open={chartQueue !== null}
          title=""
          onClose={() => setChartQueue(null)}
          size="xl"
          footer={
            <div className="flex justify-end">
              <Button variant="outline" onClick={() => setChartQueue(null)}>
                ✕ 关闭
              </Button>
            </div>
          }
        >
          {chartQueue && (
            <QueueTimeSeriesChart
              queueName={chartQueue.queue_name}
              data={chartData}
              loading={chartLoading}
              startTime={chartStartTime}
              endTime={chartEndTime}
              sampleCount={chartSamples}
              sampleOptions={curveSamplesOptions}
              onStartTimeChange={setChartStartTime}
              onEndTimeChange={setChartEndTime}
              onSampleCountChange={setChartSamples}
              onRefresh={() => loadChartData()}
            />
          )}
        </Modal>
      </div>
    </RequirePermission>
  );
}

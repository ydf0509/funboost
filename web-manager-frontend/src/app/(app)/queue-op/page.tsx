"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { RequirePermission } from "@/components/auth/RequirePermission";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { StatCard } from "@/components/ui/StatCard";
import { QueueTimeSeriesChart } from "@/components/charts/QueueTimeSeriesChart";
import { JsonViewerModal } from "@/components/ui/JsonViewerModal";
import { ToastContainer } from "@/components/ui/Toast";
import { apiFetch, funboostFetch } from "@/lib/api";
import { toDateTimeInputValue } from "@/lib/format";
import { useAutoRefresh } from "@/hooks/useAutoRefresh";
import { useActionPermissions } from "@/hooks/useActionPermissions";
import { useProject } from "@/contexts/ProjectContext";
import { useToast } from "@/hooks/useToast";

import {
  QueueFilters,
  QueueTable,
  curveSamplesOptions,
} from "@/components/queue-op";
import type {
  QueueInfo,
  QueueRow,
  QueueTimeSeriesPoint,
  SortField,
  SortDirection,
} from "@/components/queue-op";

export default function QueueOpPage() {
  const [queues, setQueues] = useState<QueueRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [activeOnly, setActiveOnly] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [sortField, setSortField] = useState<SortField>("queue_name");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  // Modal states
  const [modalQueue, setModalQueue] = useState<QueueRow | null>(null);
  const [consumerDetails, setConsumerDetails] = useState<Record<string, unknown>[] | null>(null);
  const [chartQueue, setChartQueue] = useState<QueueRow | null>(null);
  const [chartData, setChartData] = useState<QueueTimeSeriesPoint[]>([]);
  const [chartSamples, setChartSamples] = useState(360);
  const [chartLoading, setChartLoading] = useState(false);
  const [chartStartTime, setChartStartTime] = useState(() => toDateTimeInputValue(new Date(Date.now() - 3600 * 1000)));
  const [chartEndTime, setChartEndTime] = useState(() => toDateTimeInputValue(new Date()));
  const [jsonModalOpen, setJsonModalOpen] = useState(false);
  const [jsonModalTitle, setJsonModalTitle] = useState("");
  const [jsonModalContent, setJsonModalContent] = useState("");

  const { currentProject, careProjectName } = useProject();
  const { canExecute } = useActionPermissions("queue");
  const projectLevel = currentProject?.permission_level ?? "admin";
  const canWriteProject = !currentProject || projectLevel === "write" || projectLevel === "admin";
  const canOperateQueue = canExecute && canWriteProject;
  const canClearQueue = canOperateQueue;

  const toast = useToast();
  const toastRef = useRef(toast);
  toastRef.current = toast;

  const fetchQueues = useCallback(async () => {
    setLoading(true);
    try {
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
      toastRef.current.error(err instanceof Error ? err.message : "加载队列失败。");
    } finally {
      setLoading(false);
    }
  }, [currentProject?.id, careProjectName]);

  const { enabled: autoRefresh, toggle: toggleAutoRefresh, intervalMs, setIntervalMs } = useAutoRefresh(fetchQueues, false, 30000);
  const refreshInterval = intervalMs / 1000;

  useEffect(() => {
    fetchQueues();
  }, [fetchQueues]);

  // Stats
  const stats = useMemo(() => {
    const activeQueues = queues.filter((q) => (q.active_consumers?.length ?? 0) > 0);
    const consumers = queues.reduce((sum, q) => sum + (q.active_consumers?.length ?? 0), 0);
    const retryCount = queues.reduce((sum, q) => sum + (q.history_run_fail_count ?? 0), 0);
    return { active: activeQueues.length, idle: queues.length - activeQueues.length, consumers, retryCount };
  }, [queues]);

  // Filter & Sort
  const filteredQueues = useMemo(() => {
    return queues.filter((q) => {
      if (activeOnly && (q.active_consumers?.length ?? 0) === 0) return false;
      if (search && !q.queue_name.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [queues, search, activeOnly]);

  const sortedQueues = useMemo(() => {
    return [...filteredQueues].sort((a, b) => {
      let aVal: number | string = 0;
      let bVal: number | string = 0;
      switch (sortField) {
        case "queue_name": aVal = a.queue_name; bVal = b.queue_name; break;
        case "active_consumers": aVal = a.active_consumers?.length ?? 0; bVal = b.active_consumers?.length ?? 0; break;
        case "msg_num_in_broker": aVal = a.msg_num_in_broker ?? 0; bVal = b.msg_num_in_broker ?? 0; break;
        case "history_run_count": aVal = a.history_run_count ?? 0; bVal = b.history_run_count ?? 0; break;
        case "history_run_fail_count": aVal = a.history_run_fail_count ?? 0; bVal = b.history_run_fail_count ?? 0; break;
        case "all_consumers_last_x_s_execute_count": aVal = a.all_consumers_last_x_s_execute_count ?? 0; bVal = b.all_consumers_last_x_s_execute_count ?? 0; break;
        case "all_consumers_last_execute_task_time": aVal = a.all_consumers_last_execute_task_time ?? 0; bVal = b.all_consumers_last_execute_task_time ?? 0; break;
      }
      if (typeof aVal === "string" && typeof bVal === "string") {
        return sortDirection === "asc" ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }
      return sortDirection === "asc" ? (aVal as number) - (bVal as number) : (bVal as number) - (aVal as number);
    });
  }, [filteredQueues, sortField, sortDirection]);

  const totalCount = sortedQueues.length;
  const paginatedQueues = useMemo(() => {
    const start = currentPage * pageSize;
    return sortedQueues.slice(start, start + pageSize);
  }, [sortedQueues, currentPage, pageSize]);

  // Handlers
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  };

  const refreshAllMsgCounts = async () => {
    try {
      const updated = await Promise.all(
        queues.map(async (queue) => {
          try {
            let url = `/funboost/get_msg_count?queue_name=${encodeURIComponent(queue.queue_name)}`;
            if (currentProject?.id) url += `&project_id=${currentProject.id}`;
            const data = await funboostFetch<{ count: number }>(url);
            return { ...queue, msg_num_in_broker: data.count };
          } catch { return queue; }
        })
      );
      setQueues(updated);
      toast.success("消息数量已刷新。");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "刷新失败。");
    }
  };

  const startAutoConsume = async () => {
    if (!canOperateQueue) {
      toast.warning("当前项目无写权限。");
      return;
    }
    toast.info("正在启动自动消费...");
    try {
      await fetchQueues();
      toast.success("自动消费已启动。");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "启动失败。");
    }
  };

  const handleQueueAction = async (queue: QueueRow, action: "clear" | "pause" | "resume") => {
    try {
      if ((action === "pause" || action === "resume") && !canOperateQueue) {
        toast.warning("当前项目无写权限。");
        return;
      }
      if (action === "clear" && !canClearQueue) {
        toast.warning("当前项目无写权限。");
        return;
      }
      if (action === "clear") {
        await funboostFetch("/funboost/clear_queue", { method: "POST", json: { queue_name: queue.queue_name, project_id: currentProject?.id } });
      }
      if (action === "pause") {
        let url = `/queue/pause/${encodeURIComponent(queue.queue_name)}`;
        if (currentProject?.id) url += `?project_id=${currentProject.id}`;
        await apiFetch(url, { method: "POST" });
      }
      if (action === "resume") {
        let url = `/queue/resume/${encodeURIComponent(queue.queue_name)}`;
        if (currentProject?.id) url += `?project_id=${currentProject.id}`;
        await apiFetch(url, { method: "POST" });
      }
      await fetchQueues();
      toast.success("操作已完成。");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "操作失败。");
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
      if (currentProject?.id) url += `&project_id=${currentProject.id}`;
      const data = await apiFetch<Record<string, unknown>[]>(url);
      setConsumerDetails(data);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "加载消费者失败。");
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
      if (currentProject?.id) url += `&project_id=${currentProject.id}`;
      const data = await apiFetch<QueueTimeSeriesPoint[]>(url);
      setChartData(data);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "加载曲线数据失败。");
    } finally {
      setChartLoading(false);
    }
  };

  return (
    <RequirePermission permissions={["queue:read"]} projectLevel="read">
      <div className="space-y-6">
        <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
          <StatCard label="远程队列" value={queues.length} helper="总数" tone="info" />
          <StatCard label="消费队列" value={stats.active} helper="活跃" tone="success" />
          <StatCard label="消费者监控" value={stats.consumers} helper="在线" tone="warning" />
          <StatCard label="重试次数" value={stats.retryCount} helper="累计" tone="danger" />
        </div>

        <QueueFilters
          search={search}
          activeOnly={activeOnly}
          onSearchChange={setSearch}
          onActiveOnlyChange={setActiveOnly}
          loading={loading}
          autoRefresh={autoRefresh}
          refreshInterval={refreshInterval}
          canOperateQueue={canOperateQueue}
          onRefresh={fetchQueues}
          onRefreshAllMsgCounts={refreshAllMsgCounts}
          onStartAutoConsume={startAutoConsume}
          onToggleAutoRefresh={toggleAutoRefresh}
          onIntervalChange={(v) => setIntervalMs(v * 1000)}
        />

        <QueueTable
          queues={paginatedQueues}
          loading={loading}
          currentPage={currentPage}
          pageSize={pageSize}
          totalCount={totalCount}
          sortField={sortField}
          sortDirection={sortDirection}
          canOperateQueue={canOperateQueue}
          canClearQueue={canClearQueue}
          onPageChange={setCurrentPage}
          onPageSizeChange={(size) => { setPageSize(size); setCurrentPage(0); }}
          onSort={handleSort}
          onViewConfig={openQueueConfig}
          onViewChart={loadChartData}
          onViewConsumers={loadConsumers}
          onQueueAction={handleQueueAction}
        />

        <JsonViewerModal open={jsonModalOpen} title={jsonModalTitle} content={jsonModalContent} onClose={() => setJsonModalOpen(false)} />

        <Modal
          open={modalQueue !== null}
          title={modalQueue ? `消费者详情: ${modalQueue.queue_name}` : ""}
          onClose={() => { setModalQueue(null); setConsumerDetails(null); }}
          footer={<Button variant="outline" onClick={() => setModalQueue(null)}>关闭</Button>}
        >
          {modalQueue && (
            <div className="space-y-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">队列参数</p>
                <pre className="mt-2 rounded-2xl bg-[hsl(var(--sand-2))] p-4 text-xs overflow-auto max-h-48">
                  {JSON.stringify(modalQueue.queue_params ?? {}, null, 2)}
                </pre>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
                  活跃消费者 ({consumerDetails?.length ?? modalQueue.active_consumers?.length ?? 0})
                </p>
                {consumerDetails ? (
                  <pre className="mt-2 rounded-2xl bg-[hsl(var(--sand-2))] p-4 text-xs overflow-auto max-h-80">
                    {JSON.stringify(consumerDetails, null, 2)}
                  </pre>
                ) : (
                  <p className="mt-2 text-sm text-[hsl(var(--ink-muted))]">正在加载...</p>
                )}
              </div>
            </div>
          )}
        </Modal>

        <Modal
          open={chartQueue !== null}
          title=""
          onClose={() => setChartQueue(null)}
          size="xl"
          footer={<Button variant="outline" onClick={() => setChartQueue(null)}>关闭</Button>}
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

        <ToastContainer toasts={toast.toasts} onRemove={toast.removeToast} />
      </div>
    </RequirePermission>
  );
}

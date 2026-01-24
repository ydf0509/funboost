"use client";

import { ChartLine, ChevronDown, ChevronUp, Eye, Gauge, Info, Pause, Play, RefreshCw, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Pagination } from "@/components/ui/Pagination";
import { formatDateTime, formatNumber } from "@/lib/format";
import type { QueueRow, SortField, SortDirection } from "./types";

type QueueTableProps = {
  queues: QueueRow[];
  loading: boolean;
  currentPage: number;
  pageSize: number;
  totalCount: number;
  sortField: SortField;
  sortDirection: SortDirection;
  canOperateQueue: boolean;
  canClearQueue: boolean;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onSort: (field: SortField) => void;
  onViewConfig: (queue: QueueRow) => void;
  onViewChart: (queue: QueueRow) => void;
  onViewConsumers: (queue: QueueRow) => void;
  onOpenInsight: (queue: QueueRow) => void;
  onQueueAction: (queue: QueueRow, action: "clear" | "pause" | "resume") => void;
};

export function QueueTable({
  queues,
  loading,
  currentPage,
  pageSize,
  totalCount,
  sortField,
  sortDirection,
  canOperateQueue,
  canClearQueue,
  onPageChange,
  onPageSizeChange,
  onSort,
  onViewConfig,
  onViewChart,
  onViewConsumers,
  onOpenInsight,
  onQueueAction,
}: QueueTableProps) {
  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <ChevronDown className="h-3 w-3 opacity-30" />;
    return sortDirection === "asc" ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />;
  };

  const SortableHeader = ({ field, children }: { field: SortField; children: React.ReactNode }) => (
    <th
      className="px-3 py-3 font-medium whitespace-nowrap cursor-pointer hover:text-[hsl(var(--ink))]"
      onClick={() => onSort(field)}
    >
      <div className="flex items-center gap-1">
        {children}
        <SortIcon field={field} />
      </div>
    </th>
  );

  return (
    <Card>
      <div className="overflow-x-auto">
        {loading ? (
          <div className="py-8 text-center text-sm text-[hsl(var(--ink-muted))]">
            <RefreshCw className="h-8 w-8 mx-auto mb-2 animate-spin text-[hsl(var(--accent))]" />
            正在加载队列...
          </div>
        ) : queues.length === 0 ? (
          <EmptyState title="未找到队列" subtitle="调整筛选条件或刷新列表。" />
        ) : (
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase tracking-wider text-[hsl(var(--ink-muted))] bg-[hsl(var(--sand-2))]">
              <tr>
                <th className="px-3 py-3 font-medium whitespace-nowrap">洞察</th>
                <SortableHeader field="queue_name">名称</SortableHeader>
                <SortableHeader field="active_consumers">消费者数量</SortableHeader>
                <th className="px-3 py-3 font-medium whitespace-nowrap">Broker类型</th>
                <th className="px-3 py-3 font-medium whitespace-nowrap">消费函数</th>
                <SortableHeader field="all_consumers_last_execute_task_time">最近执行时间</SortableHeader>
                <SortableHeader field="msg_num_in_broker">消息数量</SortableHeader>
                <SortableHeader field="history_run_count">历史运行次数</SortableHeader>
                <SortableHeader field="history_run_fail_count">历史失败次数</SortableHeader>
                <SortableHeader field="all_consumers_last_x_s_execute_count">近10秒完成</SortableHeader>
                <th className="px-3 py-3 font-medium whitespace-nowrap">近10秒失败</th>
                <th className="px-3 py-3 font-medium whitespace-nowrap">累计平均耗时</th>
                <th className="px-3 py-3 font-medium whitespace-nowrap">状态</th>
                <th className="px-3 py-3 font-medium whitespace-nowrap">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[hsl(var(--line))]">
              {queues.map((queue) => {
                const hasConsumers = (queue.active_consumers?.length ?? 0) > 0;
                const isPaused = queue.pause_flag === 1;
                const consumingFunction = queue.queue_params?.consuming_function_name ?? "-";

                return (
                  <tr key={queue.queue_name} className="hover:bg-[hsl(var(--sand-2))]/50 transition-colors">
                    <td className="px-3 py-3">
                      <Button
                        variant="secondary"
                        size="sm"
                        className="h-7 px-2"
                        onClick={() => onOpenInsight(queue)}
                      >
                        <Gauge className="h-3 w-3" />
                        洞察
                      </Button>
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-[hsl(var(--ink))]">{queue.queue_name}</span>
                        {hasConsumers ? <Badge tone="success">消费</Badge> : <Badge tone="neutral">等待</Badge>}
                        {isPaused && <Badge tone="warning">已暂停</Badge>}
                      </div>
                    </td>
                    <td className="px-3 py-3 text-center">
                      <Badge tone={hasConsumers ? "success" : "neutral"}>{queue.active_consumers?.length ?? 0}</Badge>
                    </td>
                    <td className="px-3 py-3">
                      <Badge tone="info">{queue.queue_params?.broker_kind ?? "-"}</Badge>
                    </td>
                    <td className="px-3 py-3 text-[hsl(var(--ink))]">
                      <code className="text-xs bg-[hsl(var(--sand-2))] px-1.5 py-0.5 rounded">{consumingFunction}</code>
                    </td>
                    <td className="px-3 py-3 text-xs text-[hsl(var(--ink-muted))] whitespace-nowrap">
                      {formatDateTime(queue.all_consumers_last_execute_task_time ?? null)}
                    </td>
                    <td className="px-3 py-3 text-center">
                      <Badge tone="warning">{formatNumber(queue.msg_num_in_broker ?? 0)}</Badge>
                    </td>
                    <td className="px-3 py-3 text-center text-[hsl(var(--ink))]">
                      {formatNumber(queue.history_run_count ?? 0)}
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span className={queue.history_run_fail_count ? "text-[hsl(var(--danger))]" : "text-[hsl(var(--ink-muted))]"}>
                        {formatNumber(queue.history_run_fail_count ?? 0)}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-center text-[hsl(var(--ink))]">
                      {queue.all_consumers_last_x_s_execute_count ?? 0}
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span className={queue.all_consumers_last_x_s_execute_count_fail ? "text-[hsl(var(--danger))]" : "text-[hsl(var(--ink-muted))]"}>
                        {queue.all_consumers_last_x_s_execute_count_fail ?? 0}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-center text-[hsl(var(--ink))]">
                      {queue.all_consumers_avarage_function_spend_time_from_start
                        ? `${queue.all_consumers_avarage_function_spend_time_from_start.toFixed(3)}s`
                        : "-"}
                    </td>
                    <td className="px-3 py-3">
                      {isPaused ? (
                        <Badge tone="warning">暂停中</Badge>
                      ) : hasConsumers ? (
                        <Badge tone="success">运行中</Badge>
                      ) : (
                        <Badge tone="neutral">空闲</Badge>
                      )}
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex items-center gap-1">
                        <Button variant="secondary" size="sm" className="h-7 px-2" onClick={() => onViewConfig(queue)}>
                          <Eye className="h-3 w-3" />
                        </Button>
                        <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => onViewChart(queue)}>
                          <ChartLine className="h-3 w-3" />
                        </Button>
                        <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => onViewConsumers(queue)}>
                          <Info className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 px-2"
                          onClick={() => onQueueAction(queue, isPaused ? "resume" : "pause")}
                          disabled={!canOperateQueue}
                        >
                          {isPaused ? <Play className="h-3 w-3" /> : <Pause className="h-3 w-3" />}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 px-2 text-[hsl(var(--danger))]"
                          onClick={() => onQueueAction(queue, "clear")}
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

      <Pagination
        currentPage={currentPage}
        pageSize={pageSize}
        totalCount={totalCount}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
        loading={loading}
      />
    </Card>
  );
}

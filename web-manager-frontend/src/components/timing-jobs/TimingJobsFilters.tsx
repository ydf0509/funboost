"use client";

import { Clock, Info, Pause, Play, Plus, RefreshCw, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";

const refreshIntervals = [
  { value: 5, label: "5秒" },
  { value: 10, label: "10秒" },
  { value: 30, label: "30秒" },
  { value: 60, label: "60秒" },
];

type QueueOption = {
  name: string;
  count: number;
};

type TimingJobsFiltersProps = {
  queueOptions: QueueOption[];
  queueFilter: string;
  statusFilter: string;
  search: string;
  loading: boolean;
  autoRefresh: boolean;
  refreshInterval: number;  // 刷新间隔（秒）
  canOperate?: boolean;
  allRunning?: boolean;
  batchLoading?: boolean;
  onQueueChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onSearchChange: (value: string) => void;
  onAdd: () => void;
  onRefresh: () => void;
  onToggleAutoRefresh: () => void;
  onRefreshIntervalChange: (value: number) => void;  // 修改刷新间隔
  onDeleteAll: () => void;
  onShowHelp: () => void;
  onBatchToggle?: () => void;
};

export function TimingJobsFilters({
  queueOptions,
  queueFilter,
  statusFilter,
  search,
  loading,
  autoRefresh,
  refreshInterval,
  canOperate = true,
  allRunning = false,
  batchLoading = false,
  onQueueChange,
  onStatusChange,
  onSearchChange,
  onAdd,
  onRefresh,
  onToggleAutoRefresh,
  onRefreshIntervalChange,
  onDeleteAll,
  onShowHelp,
  onBatchToggle,
}: TimingJobsFiltersProps) {
  return (
    <div className="flex flex-row flex-wrap items-center justify-between gap-3 rounded-3xl border border-[hsl(var(--line))] bg-[hsl(var(--card))]/75 p-4 backdrop-blur-2xl">
      <div className="flex flex-row items-center gap-2">
        <Select
          value={queueFilter}
          onChange={(event) => onQueueChange(event.target.value)}
          className="h-10 w-48 text-sm"
        >
          <option value="">所有队列</option>
          {queueOptions.map((option) => (
            <option key={option.name} value={option.name}>
              {option.name} ({option.count}个)
            </option>
          ))}
        </Select>
        <Select
          value={statusFilter}
          onChange={(event) => onStatusChange(event.target.value)}
          className="h-10 w-32 text-sm"
        >
          <option value="all">所有状态</option>
          <option value="running">运行中</option>
          <option value="paused">已暂停</option>
        </Select>
        <Input
          placeholder="搜索任务ID或队列名..."
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          className="h-10 w-56 text-sm"
        />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant="primary"
          size="sm"
          onClick={onAdd}
          className="h-10 px-4"
          disabled={!canOperate}
        >
          <Plus className="h-4 w-4" />
          添加任务
        </Button>
        {onBatchToggle && queueOptions.length > 0 && (
          <Button
            variant={allRunning ? "danger" : "primary"}
            size="sm"
            onClick={onBatchToggle}
            className={`h-10 px-4 ${allRunning ? "bg-[hsl(var(--warning))] hover:bg-[hsl(var(--warning))]/90" : "bg-[hsl(var(--success))] hover:bg-[hsl(var(--success))]/90"}`}
            disabled={!canOperate || batchLoading}
          >
            {batchLoading ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : allRunning ? (
              <Pause className="h-4 w-4" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            {allRunning ? "暂停全部" : "启动全部"}
          </Button>
        )}
        <Button variant="outline" size="sm" onClick={onRefresh} className="h-10 px-4" disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          数据刷新
        </Button>
        <div className="flex items-center gap-1 rounded-full border border-[hsl(var(--line))] p-0.5">
          <span className="px-2 text-xs text-[hsl(var(--ink-muted))]">刷新间隔:</span>
          {refreshIntervals.map((interval) => (
            <button
              key={interval.value}
              onClick={() => onRefreshIntervalChange(interval.value)}
              className={`px-2 py-1 text-xs rounded-full transition cursor-pointer ${refreshInterval === interval.value
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
          onClick={onToggleAutoRefresh}
          className="h-10 px-4"
        >
          <Clock className="h-4 w-4" />
          {autoRefresh ? "刷新中..." : "已暂停"}
        </Button>
        <Button
          variant="danger"
          size="sm"
          onClick={onDeleteAll}
          className="h-10 px-4"
          disabled={!canOperate}
        >
          <Trash2 className="h-4 w-4" />
          删除全部
        </Button>
        <Button variant="outline" size="sm" onClick={onShowHelp} className="h-10 px-4">
          <Info className="h-4 w-4" />
          说明
        </Button>
      </div>
    </div>
  );
}

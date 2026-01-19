"use client";

import { Info, Plus, RefreshCw, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";

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
  canOperate?: boolean;
  onQueueChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onSearchChange: (value: string) => void;
  onAdd: () => void;
  onRefresh: () => void;
  onToggleAutoRefresh: () => void;
  onDeleteAll: () => void;
  onShowHelp: () => void;
};

export function TimingJobsFilters({
  queueOptions,
  queueFilter,
  statusFilter,
  search,
  loading,
  autoRefresh,
  canOperate = true,
  onQueueChange,
  onStatusChange,
  onSearchChange,
  onAdd,
  onRefresh,
  onToggleAutoRefresh,
  onDeleteAll,
  onShowHelp,
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
        <Button variant="outline" size="sm" onClick={onRefresh} className="h-10 px-4" disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          刷新
        </Button>
        <Button
          variant={autoRefresh ? "secondary" : "outline"}
          size="sm"
          onClick={onToggleAutoRefresh}
          className="h-10 px-4"
        >
          <RefreshCw className={`h-4 w-4 ${autoRefresh ? "animate-spin" : ""}`} />
          {autoRefresh ? "暂停刷新" : "自动刷新"}
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
        <div className="hidden items-center gap-2 text-xs text-[hsl(var(--ink-muted))] lg:flex">
          <span
            className={`h-2 w-2 rounded-full ${autoRefresh ? "bg-[hsl(var(--accent))] animate-pulse" : "bg-[hsl(var(--line))]"
              }`}
          />
          <span>每 10 秒自动刷新</span>
        </div>
      </div>
    </div>
  );
}

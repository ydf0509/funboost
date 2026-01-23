"use client";

import { Clock, RefreshCw, Zap } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Toggle } from "@/components/ui/Toggle";
import { refreshIntervals } from "./constants";

type QueueFiltersProps = {
  search: string;
  activeOnly: boolean;
  onSearchChange: (value: string) => void;
  onActiveOnlyChange: (value: boolean) => void;
  loading: boolean;
  autoRefresh: boolean;
  refreshInterval: number;
  canOperateQueue: boolean;
  onRefresh: () => void;
  onRefreshAllMsgCounts: () => void;
  onStartAutoConsume: () => void;
  onToggleAutoRefresh: () => void;
  onIntervalChange: (value: number) => void;
};

export function QueueFilters({
  search,
  activeOnly,
  onSearchChange,
  onActiveOnlyChange,
  loading,
  autoRefresh,
  refreshInterval,
  canOperateQueue,
  onRefresh,
  onRefreshAllMsgCounts,
  onStartAutoConsume,
  onToggleAutoRefresh,
  onIntervalChange,
}: QueueFiltersProps) {
  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-[hsl(var(--ink-muted))]">队列搜索</span>
            <Input
              placeholder="请输入队列名称搜索..."
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-64"
            />
          </div>
          <Toggle checked={activeOnly} onChange={onActiveOnlyChange} label="仅显示消费队列" />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="secondary" size="sm" onClick={onRefreshAllMsgCounts} className="cursor-pointer">
            <RefreshCw className="h-4 w-4" />
            刷新消息数量
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={onStartAutoConsume}
            className="cursor-pointer"
            disabled={!canOperateQueue}
          >
            <Zap className="h-4 w-4" />
            启动自动消费
          </Button>
          <Button variant="outline" size="sm" onClick={onRefresh} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            数据刷新
          </Button>
          <div className="flex items-center gap-1 rounded-full border border-[hsl(var(--line))] p-0.5">
            <span className="px-2 text-xs text-[hsl(var(--ink-muted))]">刷新间隔:</span>
            {refreshIntervals.map((interval) => (
              <button
                key={interval.value}
                onClick={() => onIntervalChange(interval.value)}
                className={`px-2 py-1 text-xs rounded-full transition cursor-pointer ${
                  refreshInterval === interval.value
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
          >
            <Clock className="h-4 w-4" />
            {autoRefresh ? "刷新中..." : "已暂停"}
          </Button>
        </div>
      </div>
    </Card>
  );
}

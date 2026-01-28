"use client";

import { StatCard } from "@/components/ui/StatCard";

type TimingJobsHeaderProps = {
  stats: {
    queues: number;
    total: number;
    running: number;
  };
};

export function TimingJobsHeader({ stats }: TimingJobsHeaderProps) {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
      <StatCard label="队列数" value={stats.queues} helper="总数" tone="info" />
      <StatCard label="定时计划总数" value={stats.total} helper="任务" tone="warning" />
      <StatCard label="运行中" value={stats.running} helper="活跃" tone="success" />
    </div>
  );
}

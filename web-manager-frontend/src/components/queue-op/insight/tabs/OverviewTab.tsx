"use client";

import { useMemo } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { StatCard } from "@/components/ui/StatCard";

import { formatDateTime, formatNumber } from "@/lib/format";

import type { QueueRow } from "@/components/queue-op/types";

type OverviewTabProps = {
  queue: QueueRow;
  onOpenJson: (title: string, content: string) => void;
};

export function OverviewTab({ queue, onOpenJson }: OverviewTabProps) {
  const overviewStats = useMemo(() => {
    const last10 = queue.all_consumers_last_x_s_execute_count ?? 0;
    const last10Fail = queue.all_consumers_last_x_s_execute_count_fail ?? 0;
    const qps = last10 / 10;
    const failRate = last10 ? (last10Fail / last10) * 100 : 0;
    const backlog = queue.msg_num_in_broker ?? 0;
    const avgTime = queue.all_consumers_avarage_function_spend_time_from_start ?? 0;
    return { qps, failRate, backlog, avgTime };
  }, [queue]);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="QPS" value={overviewStats.qps.toFixed(2)} helper="近10秒均值" tone="info" />
        <StatCard label="失败率" value={`${overviewStats.failRate.toFixed(1)}%`} helper="近10秒" tone="danger" />
        <StatCard label="积压" value={formatNumber(overviewStats.backlog)} helper="消息数" tone="warning" />
        <StatCard label="平均耗时" value={`${overviewStats.avgTime.toFixed(3)}s`} helper="累计" tone="success" />
      </div>

      <Card>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <SectionHeader title="基础信息" subtitle="队列核心参数概览" />
            <div className="mt-3 grid gap-3 text-sm text-[hsl(var(--ink))]">
              <div className="flex flex-wrap gap-3">
                <Badge tone="info">Broker: {queue.queue_params?.broker_kind ?? "-"}</Badge>
                <Badge tone="neutral">函数: {queue.queue_params?.consuming_function_name ?? "-"}</Badge>
                {queue.pause_flag === 1 && <Badge tone="warning">暂停中</Badge>}
              </div>
              <div className="text-xs text-[hsl(var(--ink-muted))]">
                最近执行: {formatDateTime(queue.all_consumers_last_execute_task_time ?? null)}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onOpenJson("队列配置", JSON.stringify(queue.queue_params ?? {}, null, 2))}
            >
              查看配置
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { StatCard } from "@/components/ui/StatCard";

import { apiFetch } from "@/lib/api";

import type { ConsumerInfo } from "../types";

type ConsumersTabProps = {
  queueName: string;
  projectId?: string;
  onOpenJson: (title: string, content: string) => void;
};

export function ConsumersTab({ queueName, projectId, onOpenJson }: ConsumersTabProps) {
  const [consumerDetails, setConsumerDetails] = useState<ConsumerInfo[]>([]);
  const [consumersLoading, setConsumersLoading] = useState(false);

  const loadConsumers = useCallback(async () => {
    if (!queueName) return;
    setConsumersLoading(true);
    try {
      let url = `/running_consumer/hearbeat_info_by_queue_name?queue_name=${encodeURIComponent(queueName)}`;
      if (projectId) url += `&project_id=${projectId}`;
      const data = await apiFetch<ConsumerInfo[]>(url);
      setConsumerDetails(data);
    } finally {
      setConsumersLoading(false);
    }
  }, [queueName, projectId]);

  useEffect(() => {
    if (!queueName) return;
    loadConsumers();
  }, [queueName, loadConsumers]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-end">
        <Button variant="outline" size="sm" onClick={loadConsumers} disabled={consumersLoading}>
          <RefreshCw className={`h-4 w-4 ${consumersLoading ? "animate-spin" : ""}`} />
          刷新消费者
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="当前队列" value={queueName} helper="洞察范围" />
        <StatCard label="消费者" value={consumerDetails.length} helper="当前运行" />
        <StatCard label="当前心跳" value={consumerDetails[0]?.hearbeat_datetime_str ?? "-"} helper="最近记录" />
      </div>

      <Card>
        <SectionHeader title="消费者列表" subtitle="心跳与吞吐详情。" />
        <div className="mt-4 overflow-x-auto">
          {consumersLoading ? (
            <div className="text-sm text-[hsl(var(--ink-muted))]">正在加载消费者...</div>
          ) : consumerDetails.length === 0 ? (
            <div className="text-sm text-[hsl(var(--ink-muted))]">暂无心跳数据。</div>
          ) : (
            <table className="min-w-full text-sm">
              <thead className="text-left text-xs uppercase tracking-[0.18em] text-[hsl(var(--ink-muted))]">
                <tr>
                  <th className="pb-3">队列</th>
                  <th className="pb-3">函数</th>
                  <th className="pb-3">主机</th>
                  <th className="pb-3">心跳</th>
                  <th className="pb-3">近 10 秒</th>
                  <th className="pb-3">累计</th>
                  <th className="pb-3">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[hsl(var(--line))]">
                {consumerDetails.map((row, index) => (
                  <tr
                    key={`${row.queue_name}-${row.process_id}-${index}`}
                    className="hover:bg-[hsl(var(--sand-2))]/50 transition-colors"
                  >
                    <td className="py-4 font-semibold text-[hsl(var(--ink))]">{row.queue_name ?? "-"}</td>
                    <td className="py-4 text-[hsl(var(--ink-muted))]">{row.consuming_function ?? "-"}</td>
                    <td className="py-4 text-[hsl(var(--ink-muted))]">
                      <div>{row.computer_ip ?? "-"}</div>
                      <div className="text-xs text-[hsl(var(--ink-muted))]">{row.computer_name ?? "-"}</div>
                    </td>
                    <td className="py-4 text-xs text-[hsl(var(--ink-muted))]">
                      <div>启动 {row.start_datetime_str ?? "-"}</div>
                      <div>心跳 {row.hearbeat_datetime_str ?? "-"}</div>
                    </td>
                    <td className="py-4 text-xs text-[hsl(var(--ink-muted))]">
                      <div>成功 {row.last_x_s_execute_count ?? 0}</div>
                      <div>失败 {row.last_x_s_execute_count_fail ?? 0}</div>
                    </td>
                    <td className="py-4 text-xs text-[hsl(var(--ink-muted))]">
                      <div>累计 {row.total_consume_count_from_start ?? 0}</div>
                      <div>失败 {row.total_consume_count_from_start_fail ?? 0}</div>
                    </td>
                    <td className="py-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onOpenJson("消费者详情", JSON.stringify(row ?? {}, null, 2))}
                      >
                        详情
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>
    </div>
  );
}

"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw, Server } from "lucide-react";

import { RequirePermission } from "@/components/auth/RequirePermission";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Select } from "@/components/ui/Select";
import { StatCard } from "@/components/ui/StatCard";
import { apiFetch } from "@/lib/api";
import { useProject } from "@/contexts/ProjectContext";

const ALL_LABEL = "全部";

type PartitionItem = {
  collection_name: string;
  count: number;
};

type ConsumerInfo = {
  queue_name: string;
  consuming_function: string;
  computer_name: string;
  computer_ip: string;
  process_id: number;
  start_datetime_str: string;
  hearbeat_datetime_str: string;
  last_x_s_execute_count: number;
  last_x_s_execute_count_fail: number;
  last_x_s_avarage_function_spend_time: number;
  total_consume_count_from_start: number;
  total_consume_count_from_start_fail: number;
  avarage_function_spend_time_from_start: number;
};

export default function ConsumersByIpPage() {
  const [partitions, setPartitions] = useState<PartitionItem[]>([]);
  const [selected, setSelected] = useState(ALL_LABEL);
  const [consumers, setConsumers] = useState<ConsumerInfo[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // 获取当前项目
  const { currentProject, careProjectName } = useProject();

  const loadPartitions = useCallback(async () => {
    try {
      // 构建 API URL，添加 project_id 参数
      let url = "/running_consumer/hearbeat_info_partion_by_ip";
      if (currentProject?.id) {
        url += `?project_id=${currentProject.id}`;
      }
      const data = await apiFetch<PartitionItem[]>(url);
      setPartitions(data);
      if (!selected && data.length > 0) {
        setSelected(data[0].collection_name);
      }
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "加载 IP 列表失败。");
    }
  }, [selected, currentProject?.id, careProjectName]);

  const loadConsumers = useCallback(async () => {
    setLoading(true);
    setNotice(null);
    try {
      const queryValue = selected === ALL_LABEL ? "" : selected;
      // 构建 API URL，添加 project_id 参数
      let url = `/running_consumer/hearbeat_info_by_ip?ip=${encodeURIComponent(queryValue)}`;
      if (currentProject?.id) {
        url += `&project_id=${currentProject.id}`;
      }
      const data = await apiFetch<ConsumerInfo[]>(url);
      setConsumers(data);
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "加载消费者失败。");
    } finally {
      setLoading(false);
    }
  }, [selected, currentProject?.id, careProjectName]);

  useEffect(() => {
    loadPartitions();
  }, [loadPartitions]);

  useEffect(() => {
    loadConsumers();
  }, [loadConsumers]);

  return (
    <RequirePermission permissions={["queue:read"]} projectLevel="read">
      <div className="space-y-8">
      {/* Action Bar */}
      <div className="flex items-center justify-end">
        <Button variant="outline" size="sm" onClick={loadConsumers}>
          <RefreshCw className="h-4 w-4" />
          刷新
        </Button>
      </div>

      {notice ? (
        <Card className="border border-[hsl(var(--accent))]/30 bg-[hsl(var(--accent))]/10 text-sm text-[hsl(var(--accent-2))]">
          {notice}
        </Card>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="活跃 IP" value={partitions.length} helper="有消费者" />
        <StatCard label="消费者" value={consumers.length} helper="当前运行" />
        <StatCard label="范围" value={selected} helper="已选 IP" />
      </div>

      <Card>
        <SectionHeader title="筛选" subtitle="选择 IP 进行聚焦。" />
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <Select value={selected} onChange={(event) => setSelected(event.target.value)}>
            {[ALL_LABEL, ...partitions.map((item) => item.collection_name)].map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </Select>
        </div>
      </Card>

      <Card>
        <SectionHeader title="消费者列表" subtitle="心跳与吞吐详情。" />
        <div className="mt-6 overflow-x-auto">
          {loading ? (
            <div className="text-sm text-[hsl(var(--ink-muted))]">正在加载消费者...</div>
          ) : consumers.length === 0 ? (
            <EmptyState title="暂无消费者" subtitle="暂无心跳数据。" />
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
                </tr>
              </thead>
              <tbody className="divide-y divide-[hsl(var(--line))]">
                {consumers.map((row, index) => (
                  <tr key={`${row.queue_name}-${row.process_id}-${index}`}>
                    <td className="py-4 font-semibold text-[hsl(var(--ink))]">{row.queue_name}</td>
                    <td className="py-4 text-[hsl(var(--ink-muted))]">{row.consuming_function}</td>
                    <td className="py-4 text-[hsl(var(--ink-muted))]">
                      <div className="flex items-center gap-2">
                        <Server className="h-4 w-4 text-[hsl(var(--accent-2))]" />
                        {row.computer_ip}
                      </div>
                      <div className="text-xs text-[hsl(var(--ink-muted))]">{row.computer_name}</div>
                    </td>
                    <td className="py-4 text-xs text-[hsl(var(--ink-muted))]">
                      <div>启动 {row.start_datetime_str}</div>
                      <div>心跳 {row.hearbeat_datetime_str}</div>
                    </td>
                    <td className="py-4 text-xs text-[hsl(var(--ink-muted))]">
                      <div>成功 {row.last_x_s_execute_count}</div>
                      <div>失败 {row.last_x_s_execute_count_fail}</div>
                    </td>
                    <td className="py-4 text-xs text-[hsl(var(--ink-muted))]">
                      <div>累计 {row.total_consume_count_from_start}</div>
                      <div>失败 {row.total_consume_count_from_start_fail}</div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>
      </div>
    </RequirePermission>
  );
}

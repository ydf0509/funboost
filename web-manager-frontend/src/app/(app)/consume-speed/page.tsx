"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";

import { RequirePermission } from "@/components/auth/RequirePermission";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Select } from "@/components/ui/Select";
import { StatCard } from "@/components/ui/StatCard";
import { QueueTimeSeriesChart } from "@/components/charts/QueueTimeSeriesChart";
import { apiFetch } from "@/lib/api";
import { formatNumber, toDateTimeInputValue } from "@/lib/format";
import { useProject } from "@/contexts/ProjectContext";

type QueueOption = {
  collection_name: string;
  count: number;
};

// Reuse the type from QueueTimeSeriesChart
export type QueueTimeSeriesPoint = {
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

export default function ConsumeSpeedPage() {
  const [queues, setQueues] = useState<QueueOption[]>([]);
  const [queue, setQueue] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [chartData, setChartData] = useState<QueueTimeSeriesPoint[]>([]);
  const [chartLoading, setChartLoading] = useState(false);
  const [chartSamples, setChartSamples] = useState(360);
  const [notice, setNotice] = useState<string | null>(null);

  // 获取当前项目
  const { currentProject, careProjectName } = useProject();

  // Initialize default time range (last hour)
  useEffect(() => {
    const now = new Date();
    const start = new Date(now.getTime() - 60 * 60 * 1000);
    setStartTime(toDateTimeInputValue(start));
    setEndTime(toDateTimeInputValue(now));
  }, []);

  // 加载队列列表
  const loadQueues = useCallback(async () => {
    try {
      // 构建 API URL，添加 project_id 参数
      let url = "/query_cols";
      if (currentProject?.id) {
        url += `?project_id=${currentProject.id}`;
      }
      const data = await apiFetch<QueueOption[]>(url);
      setQueues(data);
      if (!queue && data.length > 0) {
        setQueue(data[0].collection_name);
      }
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "加载队列失败。");
    }
  }, [queue, currentProject?.id, careProjectName]);

  // 加载图表数据 - 接受可选参数以支持从子组件调用
  const loadChartData = useCallback(async (
    overrideStartTime?: string,
    overrideEndTime?: string,
    overrideSamples?: number
  ) => {
    const st = overrideStartTime ?? startTime;
    const et = overrideEndTime ?? endTime;
    const samples = overrideSamples ?? chartSamples;

    if (!queue || !st || !et) return;
    setChartLoading(true);
    setNotice(null);
    try {
      // 将本地时间转换为时间戳
      const startTs = Math.floor(new Date(st).getTime() / 1000);
      const endTs = Math.floor(new Date(et).getTime() / 1000);
      // 构建 API URL，添加 project_id 参数
      let url = `/queue/get_time_series_data/${encodeURIComponent(queue)}?start_ts=${startTs}&end_ts=${endTs}&curve_samples_count=${samples}`;
      if (currentProject?.id) {
        url += `&project_id=${currentProject.id}`;
      }
      const data = await apiFetch<QueueTimeSeriesPoint[]>(url);
      setChartData(data);
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "加载曲线失败。");
    } finally {
      setChartLoading(false);
    }
  }, [queue, startTime, endTime, chartSamples, currentProject?.id, careProjectName]);

  // 初始加载队列
  useEffect(() => {
    loadQueues();
  }, [loadQueues]);

  // 队列变更时自动加载数据
  useEffect(() => {
    if (queue && startTime && endTime) {
      loadChartData();
    }
  }, [queue, careProjectName]); // 只在队列或关注项目变更时自动加载

  // 处理刷新 - 从 QueueTimeSeriesChart 触发
  const handleRefresh = useCallback(() => {
    loadChartData(startTime, endTime, chartSamples);
  }, [loadChartData, startTime, endTime, chartSamples]);

  // 计算统计数据
  const qps = useMemo(() => {
    if (chartData.length === 0) return 0;
    const totalSuccess = chartData.reduce((sum, p) => sum + (p.report_data.history_run_count ?? 0), 0);
    const totalFail = chartData.reduce((sum, p) => sum + (p.report_data.history_run_fail_count ?? 0), 0);
    const start = chartData[0].report_ts * 1000;
    const end = chartData[chartData.length - 1].report_ts * 1000;
    const seconds = Math.max((end - start) / 1000, 1);
    return (totalSuccess + totalFail) / seconds;
  }, [chartData]);

  const totalSuccess = chartData.reduce((sum, p) => sum + (p.report_data.history_run_count ?? 0), 0);
  const totalFail = chartData.reduce((sum, p) => sum + (p.report_data.history_run_fail_count ?? 0), 0);

  return (
    <RequirePermission permissions={["queue:read"]} projectLevel="read">
      <div className="space-y-6">
      {/* 通知消息 */}
      {notice && (
        <Card className="border border-[hsl(var(--accent))]/30 bg-[hsl(var(--accent))]/10 text-sm text-[hsl(var(--accent-2))]">
          {notice}
        </Card>
      )}

      {/* 统计卡片 */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="成功" value={formatNumber(totalSuccess)} helper="累计" tone="success" />
        <StatCard label="失败" value={formatNumber(totalFail)} helper="累计" tone="danger" />
        <StatCard label="总计" value={formatNumber(totalSuccess + totalFail)} helper="事件" tone="info" />
        <StatCard label="QPS" value={qps.toFixed(2)} helper="平均速率" tone="warning" />
      </div>

      {/* 图表区域 - 包含队列选择 */}
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <SectionHeader title="吞吐曲线" subtitle="成功与失败趋势。" />
          <div className="flex items-center gap-3">
            <label className="text-xs font-medium text-[hsl(var(--ink-muted))]">队列</label>
            <Select
              value={queue}
              onChange={e => setQueue(e.target.value)}
              className="w-64 cursor-pointer"
            >
              {queues.map(item => (
                <option key={item.collection_name} value={item.collection_name}>
                  {item.collection_name} ({item.count})
                </option>
              ))}
            </Select>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={chartLoading}
              className="cursor-pointer"
            >
              <RefreshCw className={`h-4 w-4 ${chartLoading ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </div>

        {/* 图表组件 */}
        <QueueTimeSeriesChart
          queueName={queue}
          data={chartData}
          loading={chartLoading}
          startTime={startTime}
          endTime={endTime}
          sampleCount={chartSamples}
          sampleOptions={[60, 120, 180, 360, 720, 1440, 8640]}
          onStartTimeChange={setStartTime}
          onEndTimeChange={setEndTime}
          onSampleCountChange={setChartSamples}
          onRefresh={handleRefresh}
        />
      </Card>
      </div>
    </RequirePermission>
  );
}

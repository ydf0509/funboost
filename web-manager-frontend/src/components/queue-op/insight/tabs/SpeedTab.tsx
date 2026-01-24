"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Clock, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { StatCard } from "@/components/ui/StatCard";
import { QueueTimeSeriesChart } from "@/components/charts/QueueTimeSeriesChart";

import { apiFetch } from "@/lib/api";
import { formatNumber, toDateTimeInputValue } from "@/lib/format";
import { useAutoRefresh } from "@/hooks/useAutoRefresh";

import { curveSamplesOptions } from "@/components/queue-op/constants";
import { refreshIntervals } from "../constants";
import type { QueueTimeSeriesPoint } from "@/components/queue-op/types";

type SpeedTabProps = {
  queueName: string;
  projectId?: string;
};

export function SpeedTab({ queueName, projectId }: SpeedTabProps) {
  const [chartData, setChartData] = useState<QueueTimeSeriesPoint[]>([]);
  const [chartLoading, setChartLoading] = useState(false);
  const [chartSamples, setChartSamples] = useState(360);
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");

  const loadChartData = useCallback(async () => {
    if (!queueName || !startTime || !endTime) return;
    setChartLoading(true);
    try {
      const startTs = Math.floor(new Date(startTime).getTime() / 1000);
      const endTs = Math.floor(new Date(endTime).getTime() / 1000);
      let url = `/queue/get_time_series_data/${encodeURIComponent(queueName)}?start_ts=${startTs}&end_ts=${endTs}&curve_samples_count=${chartSamples}`;
      if (projectId) url += `&project_id=${projectId}`;
      const data = await apiFetch<QueueTimeSeriesPoint[]>(url);
      setChartData(data);
    } finally {
      setChartLoading(false);
    }
  }, [queueName, startTime, endTime, chartSamples, projectId]);

  const { enabled: autoRefresh, toggle: toggleAutoRefresh, intervalMs, setIntervalMs } = useAutoRefresh(
    loadChartData,
    false,
    30000
  );

  const refreshInterval = intervalMs / 1000;

  useEffect(() => {
    if (!queueName) return;
    const now = new Date();
    const start = new Date(now.getTime() - 60 * 60 * 1000);
    setStartTime(toDateTimeInputValue(start));
    setEndTime(toDateTimeInputValue(now));
  }, [queueName]);

  useEffect(() => {
    if (queueName && startTime && endTime) {
      loadChartData();
    }
  }, [queueName, startTime, endTime, loadChartData]);

  const stats = useMemo(() => {
    if (chartData.length === 0) {
      return { totalSuccess: 0, totalFail: 0, qps: 0 };
    }
    const first = chartData[0];
    const last = chartData[chartData.length - 1];
    const totalSuccess = Math.max(0, (last.report_data.history_run_count ?? 0) - (first.report_data.history_run_count ?? 0));
    const totalFail = Math.max(0, (last.report_data.history_run_fail_count ?? 0) - (first.report_data.history_run_fail_count ?? 0));
    const seconds = Math.max(last.report_ts - first.report_ts, 1);
    const qps = (totalSuccess + totalFail) / seconds;
    return { totalSuccess, totalFail, qps };
  }, [chartData]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-end gap-2">
        <Button variant="outline" size="sm" onClick={loadChartData} disabled={chartLoading}>
          <RefreshCw className={`h-4 w-4 ${chartLoading ? "animate-spin" : ""}`} />
          数据刷新
        </Button>
        <div className="flex items-center gap-1 rounded-full border border-[hsl(var(--line))] p-0.5">
          <span className="px-2 text-xs text-[hsl(var(--ink-muted))]">刷新间隔:</span>
          {refreshIntervals.map((interval) => (
            <button
              key={interval.value}
              onClick={() => setIntervalMs(interval.value * 1000)}
              className={`px-2 py-1 text-xs rounded-full transition ${refreshInterval === interval.value
                ? "bg-[hsl(var(--accent))] text-white"
                : "text-[hsl(var(--ink-muted))] hover:text-[hsl(var(--ink))]"
              }`}
            >
              {interval.label}
            </button>
          ))}
        </div>
        <Button variant={autoRefresh ? "primary" : "outline"} size="sm" onClick={toggleAutoRefresh}>
          <Clock className="h-4 w-4" />
          {autoRefresh ? "刷新中..." : "已暂停"}
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="成功" value={formatNumber(stats.totalSuccess)} helper="累计" tone="success" />
        <StatCard label="失败" value={formatNumber(stats.totalFail)} helper="累计" tone="danger" />
        <StatCard label="总计" value={formatNumber(stats.totalSuccess + stats.totalFail)} helper="事件" tone="info" />
        <StatCard label="QPS" value={stats.qps.toFixed(2)} helper="平均速率" tone="warning" />
      </div>

      <QueueTimeSeriesChart
        queueName={queueName}
        data={chartData}
        loading={chartLoading}
        startTime={startTime}
        endTime={endTime}
        sampleCount={chartSamples}
        sampleOptions={curveSamplesOptions}
        onStartTimeChange={setStartTime}
        onEndTimeChange={setEndTime}
        onSampleCountChange={setChartSamples}
        onRefresh={loadChartData}
      />
    </div>
  );
}

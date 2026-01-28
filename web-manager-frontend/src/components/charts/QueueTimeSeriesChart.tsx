"use client";

import ReactECharts from "echarts-for-react";
import { Calendar, Clock, RefreshCw, Search, Settings, TrendingUp } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useTheme } from "@/hooks/useTheme";

type QueueTimeSeriesPoint = {
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

type QueueTimeSeriesChartProps = {
  queueName: string;
  data: QueueTimeSeriesPoint[];
  loading?: boolean;
  startTime: string;
  endTime: string;
  sampleCount: number;
  sampleOptions: number[];
  onStartTimeChange: (value: string) => void;
  onEndTimeChange: (value: string) => void;
  onSampleCountChange: (value: number) => void;
  onRefresh: () => void;
};

// 指标分组配置
// group: "cumulative" = 累计指标（左Y轴），"rate" = 速率指标（右Y轴）
// 使用项目设计规范中的语义化颜色
const SERIES_CONFIG = [
  { key: "history_run_count", name: "历史运行次数", color: "#3b82f6", group: "cumulative" },      // accent blue
  { key: "history_run_fail_count", name: "历史失败次数", color: "#ef4444", group: "cumulative" }, // danger red
  { key: "all_consumers_last_x_s_execute_count", name: "近10秒完成", color: "#22c55e", group: "rate" },  // success green
  { key: "all_consumers_last_x_s_execute_count_fail", name: "近10秒失败", color: "#f59e0b", group: "rate" }, // warning orange
  { key: "all_consumers_last_x_s_avarage_function_spend_time", name: "近10秒平均耗时(s)", color: "#06b6d4", group: "rate" }, // cyan
  { key: "all_consumers_avarage_function_spend_time_from_start", name: "累计平均耗时(s)", color: "#6b7280", group: "rate" }, // gray
  { key: "msg_num_in_broker", name: "消息数量", color: "#8b5cf6", group: "rate" }, // purple
] as const;

// Quick time range options in minutes
const QUICK_TIME_OPTIONS = [
  { label: "近10分钟", minutes: 10 },
  { label: "近30分钟", minutes: 30 },
  { label: "近1小时", minutes: 60 },
  { label: "近3小时", minutes: 180 },
  { label: "近6小时", minutes: 360 },
  { label: "近12小时", minutes: 720 },
  { label: "近24小时", minutes: 1440 },
  { label: "近3天", minutes: 4320 },
  { label: "近7天", minutes: 10080 },
] as const;

export function QueueTimeSeriesChart({
  queueName,
  data,
  loading,
  startTime,
  endTime,
  sampleCount,
  sampleOptions,
  onStartTimeChange,
  onEndTimeChange,
  onSampleCountChange,
  onRefresh,
}: QueueTimeSeriesChartProps) {
  const { isDark } = useTheme();

  const [selectedSeries, setSelectedSeries] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    SERIES_CONFIG.forEach((s) => {
      initial[s.key] = true;
    });
    return initial;
  });

  const [activeQuickTime, setActiveQuickTime] = useState<number | null>(60); // Default to 1 hour

  const handleQuickTimeSelect = (minutes: number) => {
    setActiveQuickTime(minutes);
    const now = new Date();
    const start = new Date(now.getTime() - minutes * 60 * 1000);
    // 使用本地时间格式化，避免 toISOString() 返回 UTC 时间
    const pad = (num: number) => String(num).padStart(2, "0");
    const formatLocal = (d: Date) =>
      `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
    onStartTimeChange(formatLocal(start));
    onEndTimeChange(formatLocal(now));
  };

  const chartOption = useMemo(() => {
    if (data.length === 0) {
      return null;
    }

    const xAxisData = data.map((point) => {
      const date = new Date(point.report_ts * 1000);
      return date.toLocaleString("zh-CN", {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    });

    // 根据分组和选中状态生成 series，并指定 yAxisIndex
    const series = SERIES_CONFIG.filter((config) => selectedSeries[config.key]).map((config) => ({
      name: config.name,
      type: "line" as const,
      smooth: true,
      symbol: "circle",
      symbolSize: 4,
      lineStyle: { width: 2, color: config.color },
      itemStyle: { color: config.color },
      yAxisIndex: config.group === "cumulative" ? 0 : 1,
      data: data.map((point) => {
        const value = point.report_data[config.key as keyof typeof point.report_data];
        return value ?? 0;
      }),
    }));

    // 检查是否有累计指标和速率指标被选中
    const hasCumulative = SERIES_CONFIG.some(c => c.group === "cumulative" && selectedSeries[c.key]);
    const hasRate = SERIES_CONFIG.some(c => c.group === "rate" && selectedSeries[c.key]);

    // 根据主题动态设置颜色
    const textColor = isDark ? "rgba(255,255,255,0.6)" : "rgba(0,0,0,0.6)";
    const lineColor = isDark ? "rgba(255,255,255,0.2)" : "rgba(0,0,0,0.15)";
    const splitLineColor = isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.08)";
    const tooltipBg = isDark ? "rgba(30, 30, 30, 0.95)" : "rgba(255, 255, 255, 0.95)";
    const tooltipBorder = isDark ? "rgba(100, 100, 100, 0.3)" : "rgba(200, 200, 200, 0.5)";
    const tooltipTextColor = isDark ? "#fff" : "#333";
    const crossLineColor = isDark ? "rgba(255,255,255,0.3)" : "rgba(0,0,0,0.2)";

    return {
      backgroundColor: "transparent",
      tooltip: {
        trigger: "axis" as const,
        backgroundColor: tooltipBg,
        borderColor: tooltipBorder,
        textStyle: { color: tooltipTextColor, fontSize: 12 },
        axisPointer: {
          type: "cross" as const,
          lineStyle: { color: crossLineColor },
        },
      },
      legend: {
        show: false,
      },
      grid: {
        left: hasCumulative ? 80 : 60,
        right: hasRate ? 80 : 20,
        top: 20,
        bottom: 60,
      },
      xAxis: {
        type: "category" as const,
        data: xAxisData,
        axisLine: { lineStyle: { color: lineColor } },
        axisLabel: {
          color: textColor,
          fontSize: 10,
          rotate: 0,
          interval: Math.floor(data.length / 8),
        },
        splitLine: { show: false },
        name: "时间",
        nameLocation: "center" as const,
        nameGap: 40,
        nameTextStyle: { color: textColor, fontSize: 12 },
      },
      yAxis: [
        // 左 Y 轴 - 累计指标
        {
          type: "value" as const,
          name: hasCumulative ? "累计次数" : "",
          position: "left" as const,
          axisLine: {
            show: hasCumulative,
            lineStyle: { color: textColor }
          },
          axisLabel: {
            show: hasCumulative,
            color: textColor,
            fontSize: 10,
            formatter: (value: number) => {
              if (value >= 1000000) return (value / 1000000).toFixed(1) + "M";
              if (value >= 1000) return (value / 1000).toFixed(1) + "K";
              return value.toString();
            }
          },
          splitLine: {
            show: hasCumulative && !hasRate,
            lineStyle: { color: splitLineColor }
          },
          nameTextStyle: { color: textColor, fontSize: 11 },
        },
        // 右 Y 轴 - 速率指标
        {
          type: "value" as const,
          name: hasRate ? "速率/数量" : "",
          position: "right" as const,
          axisLine: {
            show: hasRate,
            lineStyle: { color: textColor }
          },
          axisLabel: {
            show: hasRate,
            color: textColor,
            fontSize: 10
          },
          splitLine: {
            show: hasRate,
            lineStyle: { color: splitLineColor }
          },
          nameTextStyle: { color: textColor, fontSize: 11 },
        },
      ],
      series,
    };
  }, [data, selectedSeries, isDark]);

  const toggleSeries = (key: string) => {
    setSelectedSeries((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="space-y-4">
      {/* Title */}
      <div className="flex items-center gap-3">
        <TrendingUp className="h-5 w-5 text-[hsl(var(--accent))]" />
        <h3 className="text-lg font-semibold text-[hsl(var(--ink))]">
          队列数据曲线图: {queueName}
        </h3>
      </div>

      {/* Quick Time Options */}
      <div className="flex flex-wrap items-center gap-2 rounded-xl border border-[hsl(var(--line))] bg-[hsl(var(--sand-2))]/30 p-3">
        <Clock className="h-4 w-4 text-[hsl(var(--ink-muted))]" />
        <span className="text-xs font-medium text-[hsl(var(--ink-muted))]">快捷选择</span>
        <div className="mx-2 h-4 w-px bg-[hsl(var(--line))]" />
        {QUICK_TIME_OPTIONS.map((option) => (
          <button
            key={option.minutes}
            type="button"
            onClick={() => handleQuickTimeSelect(option.minutes)}
            className={`cursor-pointer rounded-lg px-3 py-1.5 text-xs font-medium transition-colors duration-200 ${activeQuickTime === option.minutes
                ? "bg-[hsl(var(--accent))] text-white"
                : "bg-[hsl(var(--card))] text-[hsl(var(--ink))] hover:bg-[hsl(var(--accent))]/20"
              }`}
          >
            {option.label}
          </button>
        ))}
      </div>

      {/* Custom Time Filters */}
      <div className="flex flex-wrap items-center gap-4 rounded-xl border border-[hsl(var(--line))] bg-[hsl(var(--sand-2))]/50 p-4">
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-[hsl(var(--ink-muted))]" />
          <span className="text-sm text-[hsl(var(--ink-muted))]">起始时间</span>
          <Input
            type="datetime-local"
            value={startTime}
            onChange={(e) => {
              setActiveQuickTime(null);
              onStartTimeChange(e.target.value);
            }}
            className="w-48 cursor-pointer"
          />
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-[hsl(var(--ink-muted))]" />
          <span className="text-sm text-[hsl(var(--ink-muted))]">结束时间</span>
          <Input
            type="datetime-local"
            value={endTime}
            onChange={(e) => {
              setActiveQuickTime(null);
              onEndTimeChange(e.target.value);
            }}
            className="w-48 cursor-pointer"
          />
        </div>
        <div className="flex items-center gap-2">
          <Settings className="h-4 w-4 text-[hsl(var(--ink-muted))]" />
          <span className="text-sm text-[hsl(var(--ink-muted))]">采样点数</span>
          <select
            value={sampleCount}
            onChange={(e) => onSampleCountChange(Number(e.target.value))}
            className="h-10 cursor-pointer rounded-xl border border-[hsl(var(--line))] bg-[hsl(var(--card))] px-3 text-sm text-[hsl(var(--ink))] transition-colors duration-200 hover:border-[hsl(var(--accent))]"
          >
            {sampleOptions.map((count) => (
              <option key={count} value={count}>
                {count} (推荐)
              </option>
            ))}
          </select>
        </div>
        <Button variant="primary" size="sm" onClick={onRefresh} disabled={loading} className="cursor-pointer">
          <Search className="h-4 w-4" />
          查询
        </Button>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-[hsl(var(--line))] bg-[hsl(var(--card))]/50 p-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--ink-muted))]">
          队列 [{queueName}] 各项指标变化趋势 ({data.length}个数据点)
        </span>
        <div className="flex-1" />
        {SERIES_CONFIG.map((config) => (
          <button
            key={config.key}
            type="button"
            onClick={() => toggleSeries(config.key)}
            className={`flex cursor-pointer items-center gap-1.5 rounded-lg px-2 py-1 text-xs transition-all duration-200 ${selectedSeries[config.key]
                ? "bg-[hsl(var(--sand-2))] hover:bg-[hsl(var(--sand-2))]/80"
                : "opacity-40 hover:opacity-60"
              }`}
          >
            <span
              className="h-3 w-3 rounded-sm"
              style={{ backgroundColor: config.color }}
            />
            <span className="text-[hsl(var(--ink))]">{config.name}</span>
          </button>
        ))}
      </div>

      {/* Chart */}
      <div className="rounded-xl border border-[hsl(var(--line))] bg-[hsl(var(--card))] p-4">
        {loading ? (
          <div className="flex h-80 items-center justify-center text-[hsl(var(--ink))]">
            <RefreshCw className="mr-2 h-5 w-5 animate-spin" />
            加载中...
          </div>
        ) : chartOption ? (
          <ReactECharts
            option={chartOption}
            style={{ height: 400 }}
            notMerge
          />
        ) : (
          <div className="flex h-80 items-center justify-center text-[hsl(var(--ink-muted))]">
            暂无曲线数据。请调整时间范围后重新查询。
          </div>
        )}
      </div>
    </div>
  );
}

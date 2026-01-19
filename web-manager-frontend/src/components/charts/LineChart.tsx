import clsx from "clsx";
import { useId } from "react";

type LineChartProps = {
  data: number[];
  labels?: string[];
  height?: number;
  stroke?: string;
  fill?: string;
  className?: string;
};

export function LineChart({
  data,
  labels,
  height = 180,
  stroke = "hsl(var(--accent-2))",
  fill = "hsl(var(--accent-2))",
  className,
}: LineChartProps) {
  const gradientId = useId();
  if (data.length === 0) {
    return <div className="text-sm text-[hsl(var(--ink-muted))]">暂无数据</div>;
  }

  const width = 600;
  const padding = 20;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data.map((value, index) => {
    const x = padding + (index / (data.length - 1 || 1)) * (width - padding * 2);
    const y = padding + ((max - value) / range) * (height - padding * 2);
    return `${x},${y}`;
  });

  const areaPoints = [`${padding},${height - padding}`, ...points, `${width - padding},${height - padding}`].join(
    " "
  );

  return (
    <div className={clsx("w-full", className)}>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full">
        <defs>
          <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor={fill} stopOpacity="0.35" />
            <stop offset="100%" stopColor={fill} stopOpacity="0" />
          </linearGradient>
        </defs>
        <polyline points={points.join(" ")} fill="none" stroke={stroke} strokeWidth="3" />
        <polygon points={areaPoints} fill={`url(#${gradientId})`} />
      </svg>
      {labels ? (
        <div className="mt-2 flex justify-between text-[10px] uppercase tracking-[0.18em] text-[hsl(var(--ink-muted))]">
          <span>{labels[0]}</span>
          <span>{labels[labels.length - 1]}</span>
        </div>
      ) : null}
    </div>
  );
}

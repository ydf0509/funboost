import clsx from "clsx";
import { Card } from "./Card";

type StatCardProps = {
  label: string;
  value: React.ReactNode;
  helper?: string;
  /** 颜色主题: success(绿), danger(红), warning(橙), info(蓝), neutral(默认) */
  tone?: "success" | "danger" | "warning" | "info" | "neutral";
};

const toneStyles = {
  success: {
    border: "border-l-4 border-l-[hsl(var(--success))]",
    value: "text-[hsl(var(--success))]",
    bg: "bg-[hsl(var(--success)/0.05)]",
  },
  danger: {
    border: "border-l-4 border-l-[hsl(var(--danger))]",
    value: "text-[hsl(var(--danger))]",
    bg: "bg-[hsl(var(--danger)/0.05)]",
  },
  warning: {
    border: "border-l-4 border-l-[hsl(var(--warning))]",
    value: "text-[hsl(var(--warning))]",
    bg: "bg-[hsl(var(--warning)/0.05)]",
  },
  info: {
    border: "border-l-4 border-l-[hsl(var(--info))]",
    value: "text-[hsl(var(--info))]",
    bg: "bg-[hsl(var(--info)/0.05)]",
  },
  neutral: {
    border: "",
    value: "text-[hsl(var(--ink))]",
    bg: "",
  },
};

export function StatCard({ label, value, helper, tone = "neutral" }: StatCardProps) {
  const styles = toneStyles[tone];

  return (
    <Card
      className={clsx(
        "flex flex-col gap-2 transition-all duration-200 hover:shadow-lg cursor-default",
        styles.border,
        styles.bg
      )}
    >
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[hsl(var(--ink-muted))]">
        {label}
      </p>
      <div className={clsx("font-display text-2xl", styles.value)}>{value}</div>
      {helper ? <p className="text-xs text-[hsl(var(--ink-muted))]">{helper}</p> : null}
    </Card>
  );
}

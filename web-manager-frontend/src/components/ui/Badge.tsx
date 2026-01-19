import clsx from "clsx";
import type { HTMLAttributes } from "react";

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: "neutral" | "success" | "warning" | "danger" | "info";
};

const tones = {
  neutral: "bg-[hsl(var(--sand-2))] text-[hsl(var(--ink))]",
  success: "bg-[hsl(var(--success))]/15 text-[hsl(var(--success))]",
  warning: "bg-[hsl(var(--warning))]/15 text-[hsl(var(--warning))]",
  danger: "bg-[hsl(var(--danger))]/15 text-[hsl(var(--danger))]",
  info: "bg-[hsl(var(--info))]/15 text-[hsl(var(--info))]",
};

export function Badge({ tone = "neutral", className, ...props }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em]",
        tones[tone],
        className
      )}
      {...props}
    />
  );
}

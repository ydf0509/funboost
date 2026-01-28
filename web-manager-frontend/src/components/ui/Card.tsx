import clsx from "clsx";
import type { HTMLAttributes } from "react";

type CardProps = HTMLAttributes<HTMLDivElement> & {
  glass?: boolean;
};

export function Card({ glass = true, className, ...props }: CardProps) {
  return (
    <div
      className={clsx(
        "rounded-3xl p-6",
        glass ? "glass-card" : "bg-[hsl(var(--card))] border border-[hsl(var(--line))]",
        className
      )}
      {...props}
    />
  );
}

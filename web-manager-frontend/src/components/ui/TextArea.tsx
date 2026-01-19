import clsx from "clsx";
import type { TextareaHTMLAttributes } from "react";

type TextAreaProps = TextareaHTMLAttributes<HTMLTextAreaElement>;

export function TextArea({ className, ...props }: TextAreaProps) {
  return (
    <textarea
      className={clsx(
        "w-full rounded-2xl border border-[hsl(var(--line))] bg-[hsl(var(--card))]/80 px-4 py-3 text-sm text-[hsl(var(--ink))] shadow-sm outline-none transition placeholder:text-[hsl(var(--ink-muted))] focus:border-[hsl(var(--accent))] focus:ring-2 focus:ring-[hsl(var(--accent))]/20",
        className
      )}
      {...props}
    />
  );
}

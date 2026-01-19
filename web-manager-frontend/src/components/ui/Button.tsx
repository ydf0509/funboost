import clsx from "clsx";
import type { ButtonHTMLAttributes } from "react";

const variants = {
  primary: "bg-[hsl(var(--accent))] text-white hover:bg-[hsl(var(--accent-2))]",
  secondary: "bg-[hsl(var(--accent-2))] text-white hover:bg-[hsl(var(--accent))]",
  outline:
    "border border-[hsl(var(--line))] text-[hsl(var(--ink))] hover:border-[hsl(var(--accent))] hover:text-[hsl(var(--accent))]",
  ghost: "text-[hsl(var(--ink))] hover:bg-[hsl(var(--sand-2))]",
  danger: "bg-[hsl(var(--danger))] text-white hover:bg-[hsl(var(--danger))]/90",
};

const sizes = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
  lg: "px-5 py-2.5 text-sm",
};

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: keyof typeof variants;
  size?: keyof typeof sizes;
};

export function Button({
  variant = "primary",
  size = "md",
  className,
  ...props
}: ButtonProps) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-full font-medium transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--accent))] focus-visible:ring-offset-2 focus-visible:ring-offset-[hsl(var(--sand))]",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  );
}

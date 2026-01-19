import clsx from "clsx";

type SectionHeaderProps = {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  className?: string;
};

export function SectionHeader({ title, subtitle, actions, className }: SectionHeaderProps) {
  return (
    <div className={clsx("flex flex-wrap items-start justify-between gap-4", className)}>
      <div>
        <h3 className="font-display text-lg text-[hsl(var(--ink))]">{title}</h3>
        {subtitle ? <p className="text-sm text-[hsl(var(--ink-muted))]">{subtitle}</p> : null}
      </div>
      {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
    </div>
  );
}

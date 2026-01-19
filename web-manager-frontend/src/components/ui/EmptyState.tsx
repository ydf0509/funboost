import { Card } from "./Card";

type EmptyStateProps = {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
};

export function EmptyState({ title, subtitle, action }: EmptyStateProps) {
  return (
    <Card className="flex flex-col items-start gap-3">
      <h3 className="font-display text-lg text-[hsl(var(--ink))]">{title}</h3>
      {subtitle ? <p className="text-sm text-[hsl(var(--ink-muted))]">{subtitle}</p> : null}
      {action ? <div>{action}</div> : null}
    </Card>
  );
}

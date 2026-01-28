import { Card } from "@/components/ui/Card";

export default function AboutPage() {
  return (
    <div className="space-y-8">

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <h3 className="font-display text-lg text-[hsl(var(--ink))]">任务结果与消费速率</h3>
          <p className="mt-3 text-sm text-[hsl(var(--ink-muted))]">
            这些页面依赖 MongoDB 持久化。请在后端开启函数结果持久化，才能展示队列结果与速率曲线。
          </p>
        </Card>
        <Card>
          <h3 className="font-display text-lg text-[hsl(var(--ink))]">运行消费者与队列运维</h3>
          <p className="mt-3 text-sm text-[hsl(var(--ink-muted))]">
            消费者心跳数据存储在 Redis。启用心跳上报后，可展示实时队列指标与消费者状态。
          </p>
        </Card>
      </div>
    </div>
  );
}

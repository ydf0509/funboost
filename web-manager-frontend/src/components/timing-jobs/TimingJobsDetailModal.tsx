"use client";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { TextArea } from "@/components/ui/TextArea";

import { STATUS_LABELS } from "./constants";
import type { TimingJob } from "./types";

type TimingJobsDetailModalProps = {
  job: TimingJob | null;
  funcName: string;
  onClose: () => void;
};

export function TimingJobsDetailModal({ job, funcName, onClose }: TimingJobsDetailModalProps) {
  return (
    <Modal
      open={!!job}
      title="任务详情"
      onClose={onClose}
      footer={
        <div className="flex justify-end">
          <Button onClick={onClose}>关闭</Button>
        </div>
      }
    >
      {job && (
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <div className="text-xs uppercase text-[hsl(var(--ink-muted))]">Job ID</div>
              <div className="font-mono text-sm">{job.job_id}</div>
            </div>
            <div>
              <div className="text-xs uppercase text-[hsl(var(--ink-muted))]">Queue</div>
              <div className="font-mono text-sm">{job.queue_name}</div>
            </div>
            <div>
              <div className="text-xs uppercase text-[hsl(var(--ink-muted))]">Trigger</div>
              <div className="font-mono text-sm">{job.trigger}</div>
            </div>
            <div>
              <div className="text-xs uppercase text-[hsl(var(--ink-muted))]">Next Run</div>
              <div className="font-mono text-sm">{job.next_run_time || "-"}</div>
            </div>
            <div>
              <div className="text-xs uppercase text-[hsl(var(--ink-muted))]">Status</div>
              <Badge tone={job.status === "running" ? "success" : "warning"}>
                {STATUS_LABELS[job.status]}
              </Badge>
            </div>
            <div>
              <div className="text-xs uppercase text-[hsl(var(--ink-muted))]">Wait Time</div>
              <div className="font-mono text-sm">-</div>
            </div>
          </div>
          <div>
            <div className="mb-1 text-xs uppercase text-[hsl(var(--ink-muted))]">Function Name</div>
            <div className="rounded bg-[hsl(var(--sand))] p-2 text-sm font-mono">{funcName}</div>
          </div>
          <div>
            <div className="mb-1 text-xs uppercase text-[hsl(var(--ink-muted))]">Arguments (kwargs)</div>
            <TextArea
              readOnly
              value={JSON.stringify(job.kwargs, null, 2)}
              className="h-32 text-xs font-mono"
            />
          </div>
        </div>
      )}
    </Modal>
  );
}

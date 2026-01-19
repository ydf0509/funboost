"use client";

import clsx from "clsx";
import {
  ChevronDown,
  Edit2,
  FolderOpen,
  Info,
  Pause,
  Play,
  RefreshCw,
  Trash2,
} from "lucide-react";
import type { MouseEvent } from "react";
import { Fragment, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";

import { SCHEDULER_STATUS_LABELS, STATUS_LABELS } from "./constants";
import type { SchedulerStatusInfo, TimingJob } from "./types";
import { TimingJobsPagination } from "./TimingJobsPagination";

type TimingJobsTableProps = {
  jobsByQueue: Record<string, TimingJob[]>;
  loading: boolean;
  empty: boolean;
  schedulerStatusMap: Record<string, SchedulerStatusInfo | undefined>;
  canOperate?: boolean;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onShowDetail: (job: TimingJob) => void;
  onEdit: (job: TimingJob) => void;
  onJobAction: (job: TimingJob, action: "pause" | "resume" | "delete") => void;
  onSchedulerAction: (queueName: string, action: "pause" | "resume" | "refresh") => void;
};

const schedulerTone = (status: SchedulerStatusInfo | undefined) => {
  if (!status) return "neutral";
  if (status.status === "running") return "success";
  if (status.status === "paused") return "warning";
  if (status.status === "stopped") return "danger";
  return "neutral";
};

export function TimingJobsTable({
  jobsByQueue,
  loading,
  empty,
  schedulerStatusMap,
  canOperate = true,
  page,
  totalPages,
  onPageChange,
  onShowDetail,
  onEdit,
  onJobAction,
  onSchedulerAction,
}: TimingJobsTableProps) {
  const queueNames = useMemo(() => Object.keys(jobsByQueue), [jobsByQueue]);
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});

  useEffect(() => {
    setCollapsedGroups((prev) => {
      const next = { ...prev };
      queueNames.forEach((queueName) => {
        if (!(queueName in next)) {
          next[queueName] = false;
        }
      });
      return next;
    });
  }, [queueNames]);

  const toggleGroup = (queueName: string) => {
    setCollapsedGroups((prev) => ({ ...prev, [queueName]: !prev[queueName] }));
  };

  const handleHeaderAction = (
    event: MouseEvent<HTMLButtonElement>,
    handler: () => void
  ) => {
    event.stopPropagation();
    handler();
  };

  return (
    <Card className="p-0">
      <div className="overflow-x-auto">
        {loading && empty ? (
          <div className="py-12 text-center text-sm text-[hsl(var(--ink-muted))]">
            <RefreshCw className="mx-auto mb-2 h-8 w-8 animate-spin text-[hsl(var(--accent))]" />
            正在加载任务...
          </div>
        ) : empty ? (
          <EmptyState title="暂无定时任务" subtitle="点击上方添加按钮创建新的定时任务。" />
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-[hsl(var(--sand-2))] text-left text-xs uppercase tracking-wider text-[hsl(var(--ink-muted))]">
              <tr>
                <th className="px-4 py-3 font-medium">任务ID</th>
                <th className="px-4 py-3 font-medium">触发器</th>
                <th className="px-4 py-3 font-medium">下次执行时间</th>
                <th className="px-4 py-3 font-medium">状态</th>
                <th className="px-4 py-3 text-right font-medium">操作</th>
              </tr>
            </thead>
            <tbody>
              {queueNames.map((queueName) => {
                const queueJobs = jobsByQueue[queueName] || [];
                const isCollapsed = collapsedGroups[queueName];
                const schedulerStatus = schedulerStatusMap[queueName];
                const statusValue = schedulerStatus?.status || "unknown";
                const isStatusLoading = schedulerStatus?.loading;
                const canPause = statusValue === "running" && !isStatusLoading;
                const canResume =
                  (statusValue === "paused" || statusValue === "stopped") && !isStatusLoading;
                const canSchedulerOperate = canOperate;
                const schedulerLabel = schedulerStatus?.loading
                  ? "加载中..."
                  : SCHEDULER_STATUS_LABELS[schedulerStatus?.status || "unknown"];

                return (
                  <Fragment key={queueName}>
                    <tr
                      className="cursor-pointer border-y border-[hsl(var(--line))] bg-[hsl(var(--sand))]"
                      onClick={() => toggleGroup(queueName)}
                    >
                      <td colSpan={5} className="px-4 py-2">
                        <div className="flex flex-wrap items-center gap-3">
                          <div className="flex items-center gap-3">
                            <ChevronDown
                              className={clsx(
                                "h-4 w-4 transition-transform",
                                isCollapsed ? "-rotate-90" : "rotate-0"
                              )}
                            />
                            <FolderOpen className="h-4 w-4 text-[hsl(var(--accent))]" />
                            <span className="font-semibold text-[hsl(var(--ink))]">{queueName}</span>
                            <Badge tone="neutral">{queueJobs.length} 个任务</Badge>
                          </div>
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge tone={schedulerTone(schedulerStatus)}>{schedulerLabel}</Badge>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={(event) =>
                                handleHeaderAction(event, () => onSchedulerAction(queueName, "refresh"))
                              }
                            >
                              <RefreshCw
                                className={clsx(
                                  "h-3.5 w-3.5",
                                  schedulerStatus?.loading && "animate-spin"
                                )}
                              />
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={(event) =>
                                handleHeaderAction(event, () => onSchedulerAction(queueName, "pause"))
                              }
                              disabled={!canPause || !canSchedulerOperate}
                            >
                              <Pause className="h-3.5 w-3.5" />
                              暂停
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={(event) =>
                                handleHeaderAction(event, () => onSchedulerAction(queueName, "resume"))
                              }
                              disabled={!canResume || !canSchedulerOperate}
                            >
                              <Play className="h-3.5 w-3.5" />
                              恢复
                            </Button>
                          </div>
                        </div>
                      </td>
                    </tr>
                    {!isCollapsed &&
                      queueJobs.map((job) => (
                        <tr
                          key={job.job_id}
                          className="border-b border-[hsl(var(--line))] last:border-0 hover:bg-[hsl(var(--sand-2))]/50"
                        >
                          <td className="px-4 py-3">
                            <code className="rounded bg-[hsl(var(--accent))]/10 px-2 py-1 text-xs text-[hsl(var(--accent-2))]">
                              {job.job_id}
                            </code>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              {job.trigger.startsWith("interval") ? (
                                <Badge tone="warning">间隔</Badge>
                              ) : job.trigger.startsWith("cron") ? (
                                <Badge tone="info">定时</Badge>
                              ) : (
                                <Badge tone="neutral">一次性</Badge>
                              )}
                              <span className="text-xs text-[hsl(var(--ink-muted))]">
                                {job.trigger}
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-xs text-[hsl(var(--ink))]">
                            {job.next_run_time || "-"}
                          </td>
                          <td className="px-4 py-3">
                            <Badge tone={job.status === "running" ? "success" : "warning"}>
                              {STATUS_LABELS[job.status]}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <div className="flex flex-wrap items-center justify-end gap-2">
                              <Button variant="outline" size="sm" onClick={() => onShowDetail(job)}>
                                <Info className="h-3.5 w-3.5" />
                                详情
                              </Button>
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => onEdit(job)}
                                disabled={!canOperate}
                              >
                                <Edit2 className="h-3.5 w-3.5" />
                                编辑
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                className={
                                  job.status === "running"
                                    ? "border-[hsl(var(--warning))] text-[hsl(var(--warning))] hover:border-[hsl(var(--warning))]"
                                    : "border-[hsl(var(--success))] text-[hsl(var(--success))] hover:border-[hsl(var(--success))]"
                                }
                                onClick={() =>
                                  onJobAction(job, job.status === "running" ? "pause" : "resume")
                                }
                                disabled={!canOperate}
                              >
                                {job.status === "running" ? (
                                  <>
                                    <Pause className="h-3.5 w-3.5" />
                                    暂停
                                  </>
                                ) : (
                                  <>
                                    <Play className="h-3.5 w-3.5" />
                                    恢复
                                  </>
                                )}
                              </Button>
                              <Button
                                variant="danger"
                                size="sm"
                                onClick={() => onJobAction(job, "delete")}
                                disabled={!canOperate}
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                                删除
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
      <TimingJobsPagination page={page} totalPages={totalPages} onChange={onPageChange} />
    </Card>
  );
}

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { RequirePermission } from "@/components/auth/RequirePermission";
import { Card } from "@/components/ui/Card";
import { apiFetch, funboostFetch } from "@/lib/api";

import { TimingJobsDetailModal } from "@/components/timing-jobs/TimingJobsDetailModal";
import { TimingJobsFilters } from "@/components/timing-jobs/TimingJobsFilters";
import { TimingJobsFormModal } from "@/components/timing-jobs/TimingJobsFormModal";
import { TimingJobsHeader } from "@/components/timing-jobs/TimingJobsHeader";
import { TimingJobsHelpModal } from "@/components/timing-jobs/TimingJobsHelpModal";
import { TimingJobsTable } from "@/components/timing-jobs/TimingJobsTable";
import {
  AUTO_REFRESH_INTERVAL_MS,
  DEFAULT_PAGE_SIZE,
  JOB_STORE_KIND,
} from "@/components/timing-jobs/constants";
import type {
  FuncParamsInfo,
  JobForm,
  JobResponse,
  QueueConfig,
  SchedulerStatus,
  SchedulerStatusInfo,
  TimingJob,
} from "@/components/timing-jobs/types";
import {
  buildEmptyForm,
  hasCronValue,
  hasIntervalValue,
  normalizeKwargs,
  parseJobToForm,
  validateKwargs,
} from "@/components/timing-jobs/utils";
import { useActionPermissions } from "@/hooks/useActionPermissions";
import { useProject } from "@/contexts/ProjectContext";

type Notice = {
  type: "success" | "error" | "warning";
  message: string;
};

const normalizeSchedulerStatus = (value?: string): SchedulerStatus => {
  if (value === "running" || value === "paused" || value === "stopped") {
    return value;
  }
  return "unknown";
};

export default function TimingJobsPage() {
  const [jobs, setJobs] = useState<TimingJob[]>([]);
  const [availableQueues, setAvailableQueues] = useState<string[]>([]);
  const [queueFilter, setQueueFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [notice, setNotice] = useState<Notice | null>(null);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [page, setPage] = useState(1);

  const [formOpen, setFormOpen] = useState(false);
  const [jobForm, setJobForm] = useState<JobForm>(buildEmptyForm());
  const [formError, setFormError] = useState<string | null>(null);
  const [editingJob, setEditingJob] = useState<TimingJob | null>(null);

  const [funcParamsInfo, setFuncParamsInfo] = useState<FuncParamsInfo | null>(null);
  const [loadingParams, setLoadingParams] = useState(false);

  const [detailJob, setDetailJob] = useState<TimingJob | null>(null);
  const [detailFuncName, setDetailFuncName] = useState<string>("");

  const [helpOpen, setHelpOpen] = useState(false);
  const [schedulerStatuses, setSchedulerStatuses] = useState<Record<string, SchedulerStatusInfo>>({});

  const { currentProject, careProjectName } = useProject();
  const { canExecute } = useActionPermissions("queue");
  const projectLevel = currentProject?.permission_level ?? "read";
  const canWriteProject = projectLevel === "write" || projectLevel === "admin";
  const canOperateQueue = canExecute && canWriteProject;

  const ensureOperatePermission = useCallback(() => {
    if (!canOperateQueue) {
      setNotice({ type: "warning", message: "当前项目无写权限，无法执行定时任务操作。" });
      return false;
    }
    return true;
  }, [canOperateQueue]);

  const loadSchedulerStatus = useCallback(async (queueName: string) => {
    setSchedulerStatuses((prev) => ({
      ...prev,
      [queueName]: {
        status: prev[queueName]?.status ?? "unknown",
        loading: true,
      },
    }));

    try {
      const data = await funboostFetch<{ status_str?: string }>(
        `/funboost/get_scheduler_status?queue_name=${encodeURIComponent(queueName)}&job_store_kind=${JOB_STORE_KIND}`
      );
      const status = normalizeSchedulerStatus(data?.status_str);
      setSchedulerStatuses((prev) => ({
        ...prev,
        [queueName]: {
          status,
          loading: false,
        },
      }));
    } catch {
      setSchedulerStatuses((prev) => ({
        ...prev,
        [queueName]: {
          status: "unknown",
          loading: false,
        },
      }));
    }
  }, []);

  const loadSchedulerStatuses = useCallback(
    async (queueNames: string[]) => {
      await Promise.all(queueNames.map((queueName) => loadSchedulerStatus(queueName)));
    },
    [loadSchedulerStatus]
  );

  const loadJobs = useCallback(async () => {
    setLoading(true);

    try {
      const data = await funboostFetch<JobResponse>(
        `/funboost/get_timing_jobs?job_store_kind=${JOB_STORE_KIND}`
      );
      const flattened = Object.entries(data.jobs_by_queue || {}).flatMap(([queue_name, items]) =>
        items.map((job) => ({ ...job, queue_name }))
      );
      const sorted = [...flattened].sort((a, b) => {
        if (a.queue_name !== b.queue_name) {
          return a.queue_name.localeCompare(b.queue_name);
        }
        return a.job_id.localeCompare(b.job_id);
      });
      setJobs(sorted);

      const queueNames = Object.keys(data.jobs_by_queue || {}).sort();
      if (queueNames.length > 0) {
        loadSchedulerStatuses(queueNames);
      }
    } catch (error) {
      setNotice({
        type: "error",
        message: error instanceof Error ? error.message : "加载任务失败。",
      });
    } finally {
      setLoading(false);
    }
  }, [loadSchedulerStatuses]);

  const refreshJobs = useCallback(() => {
    setNotice(null);
    loadJobs();
  }, [loadJobs]);

  const loadAvailableQueues = useCallback(async () => {
    try {
      let url = "/queue/params_and_active_consumers";
      if (currentProject?.id) {
        url += `?project_id=${currentProject.id}`;
      }
      const data = await apiFetch<Record<string, unknown>>(url);
      const queueNames = Object.keys(data).sort();
      setAvailableQueues(queueNames);
    } catch (error) {
      console.error("Failed to load queues:", error);
    }
  }, [currentProject?.id, careProjectName]);

  useEffect(() => {
    loadJobs();
    loadAvailableQueues();
  }, [loadJobs, loadAvailableQueues]);

  useEffect(() => {
    if (!autoRefresh) return;
    loadJobs();
    const interval = setInterval(loadJobs, AUTO_REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [autoRefresh, loadJobs]);

  useEffect(() => {
    setPage(1);
  }, [queueFilter, statusFilter, search]);

  const loadFuncParams = useCallback(
    async (queueName: string) => {
      if (!queueName) {
        setFuncParamsInfo(null);
        return;
      }
      setLoadingParams(true);
      try {
        const data = await funboostFetch<QueueConfig>(
          `/funboost/get_one_queue_config?queue_name=${encodeURIComponent(queueName)}`
        );
        const paramsInfo = data?.auto_generate_info?.final_func_input_params_info || null;
        setFuncParamsInfo(paramsInfo);

        if (paramsInfo) {
          setJobForm((prev) => {
            const current = normalizeKwargs(prev.kwargs);
            if (current !== "{}") {
              return prev;
            }
            const templateObj: Record<string, string> = {};
            (paramsInfo.must_arg_name_list || []).forEach((arg) => {
              templateObj[arg] = "";
            });
            (paramsInfo.optional_arg_name_list || []).forEach((arg) => {
              templateObj[arg] = "";
            });
            if (Object.keys(templateObj).length === 0) {
              return prev;
            }
            return { ...prev, kwargs: JSON.stringify(templateObj, null, 2) };
          });
        }
      } catch (error) {
        console.error("Failed to load func params:", error);
        setFuncParamsInfo(null);
      } finally {
        setLoadingParams(false);
      }
    },
    []
  );

  const queueOptions = useMemo(() => {
    const counts = jobs.reduce<Record<string, number>>((acc, job) => {
      acc[job.queue_name] = (acc[job.queue_name] || 0) + 1;
      return acc;
    }, {});
    return Object.keys(counts)
      .sort()
      .map((name) => ({ name, count: counts[name] }));
  }, [jobs]);

  const filteredJobs = useMemo(() => {
    const query = search.trim();
    return jobs.filter((job) => {
      if (queueFilter && job.queue_name !== queueFilter) return false;
      if (statusFilter !== "all" && job.status !== statusFilter) return false;
      if (query && !job.job_id.includes(query) && !job.queue_name.includes(query)) return false;
      return true;
    });
  }, [jobs, queueFilter, statusFilter, search]);

  const totalPages = Math.max(1, Math.ceil(filteredJobs.length / DEFAULT_PAGE_SIZE));

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

  const pagedJobs = useMemo(() => {
    const start = (page - 1) * DEFAULT_PAGE_SIZE;
    return filteredJobs.slice(start, start + DEFAULT_PAGE_SIZE);
  }, [filteredJobs, page]);

  const jobsByQueue = useMemo(() => {
    const grouped: Record<string, TimingJob[]> = {};
    pagedJobs.forEach((job) => {
      if (!grouped[job.queue_name]) grouped[job.queue_name] = [];
      grouped[job.queue_name].push(job);
    });
    return grouped;
  }, [pagedJobs]);

  const stats = useMemo(() => {
    const running = jobs.filter((job) => job.status === "running").length;
    return {
      queues: queueOptions.length,
      total: jobs.length,
      running,
    };
  }, [jobs, queueOptions]);

  const openForm = (job?: TimingJob) => {
    if (!ensureOperatePermission()) {
      return;
    }
    setFormError(null);

    if (job) {
      setEditingJob(job);
      setJobForm(parseJobToForm(job));
      loadFuncParams(job.queue_name);
      setFormOpen(true);
      return;
    }

    setEditingJob(null);
    setJobForm(buildEmptyForm(queueFilter || ""));
    setFuncParamsInfo(null);
    if (queueFilter) {
      loadFuncParams(queueFilter);
    }
    setFormOpen(true);
  };

  const handleQueueChange = (queueName: string) => {
    setFormError(null);
    setJobForm((prev) => ({ ...prev, queue_name: queueName, kwargs: "{}" }));
    loadFuncParams(queueName);
  };

  const closeForm = () => {
    setFormOpen(false);
    setEditingJob(null);
    setFormError(null);
  };

  const showJobDetail = async (job: TimingJob) => {
    setDetailJob(job);
    setDetailFuncName("加载中...");
    try {
      const data = await funboostFetch<QueueConfig>(
        `/funboost/get_one_queue_config?queue_name=${encodeURIComponent(job.queue_name)}`
      );
      const funcName = data?.auto_generate_info?.final_func_input_params_info?.func_name || "-";
      setDetailFuncName(funcName);
    } catch {
      setDetailFuncName("-");
    }
  };

  const handleJobAction = async (job: TimingJob, action: "pause" | "resume" | "delete") => {
    if (!ensureOperatePermission()) {
      return;
    }
    const confirmMessage =
      action === "pause"
        ? `确定要暂停任务 ${job.job_id} 吗？`
        : action === "resume"
          ? `确定要恢复任务 ${job.job_id} 吗？`
          : `确定要删除任务 ${job.job_id} 吗？\n此操作不可撤销！`;

    if (!confirm(confirmMessage)) return;

    try {
      if (action === "pause") {
        await funboostFetch(`/funboost/pause_timing_job?job_id=${job.job_id}&queue_name=${job.queue_name}`,
          { method: "POST" }
        );
        setNotice({ type: "success", message: "任务已暂停。" });
      }
      if (action === "resume") {
        await funboostFetch(`/funboost/resume_timing_job?job_id=${job.job_id}&queue_name=${job.queue_name}`,
          { method: "POST" }
        );
        setNotice({ type: "success", message: "任务已恢复。" });
      }
      if (action === "delete") {
        await funboostFetch(`/funboost/delete_timing_job?job_id=${job.job_id}&queue_name=${job.queue_name}`,
          { method: "DELETE" }
        );
        setNotice({ type: "success", message: "任务已删除。" });
      }
      loadJobs();
    } catch (error) {
      setNotice({
        type: "error",
        message: error instanceof Error ? error.message : "操作失败。",
      });
    }
  };

  const handleSchedulerAction = async (queueName: string, action: "pause" | "resume" | "refresh") => {
    if (action === "refresh") {
      loadSchedulerStatus(queueName);
      return;
    }
    if (!ensureOperatePermission()) {
      return;
    }

    const confirmMessage =
      action === "pause"
        ? `确定要暂停队列 "${queueName}" 的所有定时任务调度吗？`
        : `确定要恢复队列 "${queueName}" 的定时任务调度吗？`;

    if (!confirm(confirmMessage)) return;

    try {
      if (action === "pause") {
        await funboostFetch(
          `/funboost/pause_scheduler?queue_name=${encodeURIComponent(queueName)}&job_store_kind=${JOB_STORE_KIND}`,
          { method: "POST" }
        );
        setNotice({ type: "success", message: `队列 ${queueName} 调度器已暂停。` });
      }
      if (action === "resume") {
        await funboostFetch(
          `/funboost/resume_scheduler?queue_name=${encodeURIComponent(queueName)}&job_store_kind=${JOB_STORE_KIND}`,
          { method: "POST" }
        );
        setNotice({ type: "success", message: `队列 ${queueName} 调度器已恢复。` });
      }
      loadSchedulerStatus(queueName);
      loadJobs();
    } catch (error) {
      setNotice({
        type: "error",
        message: error instanceof Error ? error.message : "调度器操作失败。",
      });
    }
  };

  const deleteAllJobs = async () => {
    if (!ensureOperatePermission()) {
      return;
    }
    const confirmMsg = queueFilter
      ? `确定要删除队列 ${queueFilter} 的所有任务吗？\n此操作不可撤销！`
      : "确定要删除所有队列的所有任务吗？\n此操作不可撤销！";
    if (!confirm(confirmMsg)) return;

    try {
      let url = `/funboost/delete_all_timing_jobs?job_store_kind=${JOB_STORE_KIND}`;
      if (queueFilter) {
        url += `&queue_name=${encodeURIComponent(queueFilter)}`;
      }
      const data = await funboostFetch<{ deleted_count: number; failed_jobs?: string[] }>(url, {
        method: "DELETE",
      });
      const failedCount = data.failed_jobs?.length || 0;
      const message = failedCount
        ? `成功删除 ${data.deleted_count} 个任务，失败 ${failedCount} 个。`
        : `成功删除 ${data.deleted_count} 个任务。`;
      setNotice({ type: "success", message });
      loadJobs();
    } catch (error) {
      setNotice({
        type: "error",
        message: error instanceof Error ? error.message : "删除失败。",
      });
    }
  };

  const submitJob = async () => {
    if (!ensureOperatePermission()) {
      return;
    }
    setFormError(null);

    if (!jobForm.queue_name) {
      setFormError("请选择队列名称。");
      return;
    }

    const kwargsCheck = validateKwargs(jobForm.kwargs);
    if (!kwargsCheck.valid) {
      setFormError(kwargsCheck.message || "kwargs 校验失败。");
      return;
    }

    if (jobForm.triggerType === "date" && !jobForm.run_date) {
      setFormError("请选择执行时间。");
      return;
    }

    if (jobForm.triggerType === "interval" && !hasIntervalValue(jobForm.interval)) {
      setFormError("间隔执行至少填写一个时间单位。");
      return;
    }

    if (jobForm.triggerType === "cron" && !hasCronValue(jobForm.cron)) {
      setFormError("定时执行至少填写一个字段。");
      return;
    }

    const confirmMessage = editingJob ? "确定要保存修改吗？" : "确定要添加这个定时任务吗？";
    if (!confirm(confirmMessage)) return;

    try {
      const payload: Record<string, unknown> = {
        queue_name: jobForm.queue_name,
        job_id: jobForm.job_id || undefined,
        kwargs: kwargsCheck.data,
        trigger: jobForm.triggerType,
        job_store_kind: JOB_STORE_KIND,
        replace_existing: jobForm.replace_existing,
      };

      if (jobForm.triggerType === "date") {
        payload.run_date = jobForm.run_date;
      }
      if (jobForm.triggerType === "interval") {
        Object.entries(jobForm.interval).forEach(([key, value]) => {
          if (value && Number(value) > 0) payload[key] = Number(value);
        });
      }
      if (jobForm.triggerType === "cron") {
        Object.entries(jobForm.cron).forEach(([key, value]) => {
          if (value && value.trim().length > 0) payload[key] = value.trim();
        });
      }

      await funboostFetch("/funboost/add_timing_job", { method: "POST", json: payload });
      closeForm();
      setNotice({ type: "success", message: "任务保存成功！" });
      loadJobs();
    } catch (error) {
      setNotice({
        type: "error",
        message: error instanceof Error ? error.message : "保存失败。",
      });
    }
  };

  return (
    <RequirePermission permissions={["queue:read"]} projectLevel="read">
      <div className="space-y-6">
        <TimingJobsHeader stats={stats} />

        <TimingJobsFilters
          queueOptions={queueOptions}
          queueFilter={queueFilter}
          statusFilter={statusFilter}
          search={search}
          loading={loading}
          autoRefresh={autoRefresh}
          canOperate={canOperateQueue}
          onQueueChange={setQueueFilter}
          onStatusChange={setStatusFilter}
          onSearchChange={setSearch}
          onAdd={() => openForm()}
          onRefresh={refreshJobs}
          onToggleAutoRefresh={() => setAutoRefresh((prev) => !prev)}
          onDeleteAll={deleteAllJobs}
          onShowHelp={() => setHelpOpen(true)}
        />

        {notice && (
          <Card
            className={`border text-sm ${notice.type === "success"
              ? "border-[hsl(var(--success))]/30 bg-[hsl(var(--success))]/10 text-[hsl(var(--success))]"
              : notice.type === "warning"
                ? "border-[hsl(var(--warning))]/30 bg-[hsl(var(--warning))]/10 text-[hsl(var(--warning))]"
                : "border-[hsl(var(--danger))]/30 bg-[hsl(var(--danger))]/10 text-[hsl(var(--danger))]"
              }`}
            role="alert"
          >
            {notice.message}
          </Card>
        )}

        <TimingJobsTable
          jobsByQueue={jobsByQueue}
          loading={loading}
          empty={filteredJobs.length === 0}
          schedulerStatusMap={schedulerStatuses}
          canOperate={canOperateQueue}
          page={page}
          totalPages={totalPages}
          onPageChange={setPage}
          onShowDetail={showJobDetail}
          onEdit={openForm}
          onJobAction={handleJobAction}
          onSchedulerAction={handleSchedulerAction}
        />

        <TimingJobsFormModal
          open={formOpen}
          editingJobId={editingJob?.job_id || null}
          form={jobForm}
          availableQueues={availableQueues}
          funcParamsInfo={funcParamsInfo}
          loadingParams={loadingParams}
          formError={formError}
          onClose={closeForm}
          onSubmit={submitJob}
          onQueueChange={handleQueueChange}
          setForm={setJobForm}
        />

        <TimingJobsDetailModal
          job={detailJob}
          funcName={detailFuncName}
          onClose={() => setDetailJob(null)}
        />

        <TimingJobsHelpModal open={helpOpen} onClose={() => setHelpOpen(false)} />
      </div>
    </RequirePermission>
  );
}

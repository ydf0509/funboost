import type { JobForm, TimingJobStatus, SchedulerStatus } from "./types";

export const JOB_STORE_KIND = "redis";
export const AUTO_REFRESH_INTERVAL_MS = 10000;
export const DEFAULT_PAGE_SIZE = 50;

export const STATUS_LABELS: Record<TimingJobStatus, string> = {
  running: "运行中",
  paused: "已暂停",
};

export const SCHEDULER_STATUS_LABELS: Record<SchedulerStatus, string> = {
  running: "调度中",
  paused: "已暂停",
  stopped: "已停止",
  unknown: "未知",
};

export const TIME_FIELD_LABELS: Record<string, string> = {
  weeks: "周",
  days: "天",
  hours: "小时",
  minutes: "分钟",
  seconds: "秒",
  year: "年",
  month: "月",
  day: "日",
  day_of_week: "星期",
  hour: "小时",
  minute: "分钟",
  second: "秒",
};

export const EMPTY_FORM: JobForm = {
  queue_name: "",
  job_id: "",
  kwargs: "{}",
  triggerType: "interval",
  run_date: "",
  interval: { weeks: "0", days: "0", hours: "0", minutes: "0", seconds: "0" },
  cron: { year: "", month: "", day: "", day_of_week: "", hour: "", minute: "", second: "" },
  replace_existing: true,
};

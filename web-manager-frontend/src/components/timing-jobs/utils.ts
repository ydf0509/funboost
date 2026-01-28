import { EMPTY_FORM } from "./constants";
import type { JobForm, TimingJob } from "./types";

type IntervalForm = JobForm["interval"];
type CronForm = JobForm["cron"];

export const buildEmptyForm = (queueName = ""): JobForm => ({
  ...EMPTY_FORM,
  queue_name: queueName,
});

export const parseTriggerType = (trigger: string): JobForm["triggerType"] => {
  if (trigger.startsWith("cron")) return "cron";
  if (trigger.startsWith("interval")) return "interval";
  return "date";
};

const parseIntervalTrigger = (trigger: string, defaults: IntervalForm): IntervalForm => {
  const match = trigger.match(/interval\[(.*)\]/);
  if (!match) return { ...defaults };

  const body = match[1];
  const result: IntervalForm = { ...defaults };
  let hasKv = false;

  const kvRegex = /(weeks|days|hours|minutes|seconds)\s*=\s*([^,]+)/g;
  let kvMatch;
  while ((kvMatch = kvRegex.exec(body))) {
    hasKv = true;
    const key = kvMatch[1] as keyof IntervalForm;
    const value = kvMatch[2].replace(/['"]/g, "").trim();
    if (value) result[key] = value;
  }

  if (!hasKv) {
    const weekMatch = body.match(/(\d+)\s*week/);
    const dayMatch = body.match(/(\d+)\s*day/);
    const timeMatch = body.match(/(\d+):(\d+):(\d+)/);

    if (weekMatch) result.weeks = weekMatch[1];
    if (dayMatch) result.days = dayMatch[1];
    if (timeMatch) {
      result.hours = timeMatch[1];
      result.minutes = timeMatch[2];
      result.seconds = timeMatch[3];
    }
  }

  return result;
};

const parseCronTrigger = (trigger: string, defaults: CronForm): CronForm => {
  const match = trigger.match(/cron\[(.*)\]/);
  if (!match) return { ...defaults };

  const body = match[1];
  const result: CronForm = { ...defaults };
  const kvRegex = /(\w+)\s*=\s*([^,]+)/g;
  let kvMatch;

  while ((kvMatch = kvRegex.exec(body))) {
    const key = kvMatch[1] as keyof CronForm;
    const value = kvMatch[2].replace(/['"]/g, "").trim();
    if (key in result && value) {
      result[key] = value;
    }
  }

  return result;
};

export const parseJobToForm = (job: TimingJob): JobForm => {
  const triggerType = parseTriggerType(job.trigger || "");
  const form: JobForm = {
    ...EMPTY_FORM,
    queue_name: job.queue_name,
    job_id: job.job_id,
    kwargs: JSON.stringify(job.kwargs || {}, null, 2),
    triggerType,
    replace_existing: true,
  };

  if (triggerType === "interval") {
    form.interval = parseIntervalTrigger(job.trigger, form.interval);
  }
  if (triggerType === "cron") {
    form.cron = parseCronTrigger(job.trigger, form.cron);
  }

  return form;
};

export const normalizeKwargs = (value: string) => {
  const raw = value.trim();
  return raw.length === 0 ? "{}" : raw;
};

export const validateKwargs = (value: string) => {
  try {
    const parsed = JSON.parse(normalizeKwargs(value));
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return { valid: false, message: "kwargs 必须是 JSON 对象。" };
    }
    return { valid: true, data: parsed as Record<string, unknown> };
  } catch (error) {
    return { valid: false, message: "kwargs 必须是合法的 JSON 格式。" };
  }
};

export const hasIntervalValue = (interval: IntervalForm) =>
  Object.values(interval).some((value) => Number(value) > 0);

export const hasCronValue = (cron: CronForm) =>
  Object.values(cron).some((value) => value && value.trim().length > 0);

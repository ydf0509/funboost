export type TimingJobStatus = "running" | "paused";

export type TimingJob = {
  job_id: string;
  queue_name: string;
  trigger: string;
  next_run_time: string | null;
  status: TimingJobStatus;
  kwargs: Record<string, unknown>;
};

export type JobResponse = {
  jobs_by_queue: Record<string, TimingJob[]>;
  total_count: number;
};

export type FuncParamsInfo = {
  func_name?: string;
  must_arg_name_list?: string[];
  optional_arg_name_list?: string[];
};

export type QueueConfig = {
  auto_generate_info?: {
    final_func_input_params_info?: FuncParamsInfo;
  };
};

export type JobForm = {
  queue_name: string;
  job_id: string;
  kwargs: string;
  triggerType: "date" | "interval" | "cron";
  run_date: string;
  interval: {
    weeks: string;
    days: string;
    hours: string;
    minutes: string;
    seconds: string;
  };
  cron: {
    year: string;
    month: string;
    day: string;
    day_of_week: string;
    hour: string;
    minute: string;
    second: string;
  };
  replace_existing: boolean;
};

export type SchedulerStatus = "running" | "paused" | "stopped" | "unknown";

export type SchedulerStatusInfo = {
  status: SchedulerStatus;
  loading: boolean;
};

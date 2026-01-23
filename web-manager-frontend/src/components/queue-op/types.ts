export type QueueParams = {
  broker_kind?: string;
  consuming_function_name?: string;
  auto_generate_info?: Record<string, unknown>;
};

export type QueueInfo = {
  queue_params?: QueueParams;
  active_consumers?: Array<Record<string, unknown>>;
  pause_flag?: number;
  msg_num_in_broker?: number;
  history_run_count?: number;
  history_run_fail_count?: number;
  all_consumers_last_x_s_execute_count?: number;
  all_consumers_last_x_s_execute_count_fail?: number;
  all_consumers_last_x_s_avarage_function_spend_time?: number;
  all_consumers_avarage_function_spend_time_from_start?: number;
  all_consumers_last_execute_task_time?: number;
};

export type QueueRow = QueueInfo & {
  queue_name: string;
};

export type QueueTimeSeriesPoint = {
  report_data: {
    history_run_count?: number;
    history_run_fail_count?: number;
    all_consumers_last_x_s_execute_count?: number;
    all_consumers_last_x_s_execute_count_fail?: number;
    all_consumers_last_x_s_avarage_function_spend_time?: number;
    all_consumers_avarage_function_spend_time_from_start?: number;
    msg_num_in_broker?: number;
  };
  report_ts: number;
};

export type SortField = "queue_name" | "active_consumers" | "msg_num_in_broker" | "history_run_count" | "history_run_fail_count" | "all_consumers_last_x_s_execute_count" | "all_consumers_last_execute_task_time";
export type SortDirection = "asc" | "desc";

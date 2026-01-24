export type InsightTab = "overview" | "results" | "speed" | "rpc" | "consumers";

export type ResultRow = {
  function: string;
  task_id: string;
  params_str: string;
  result: string;
  publish_time_format: string;
  time_start: number;
  time_cost: number;
  run_times: number;
  run_status: string;
  success: boolean;
  exception: string;
  host_process: string;
};

export type SpeedStats = {
  success_num: number;
  fail_num: number;
  qps: number;
};

export type QueryResultResponse = {
  data: ResultRow[];
  total_count: number;
  page: number;
  page_size: number;
};

export type ParamInfo = {
  must_arg_name_list?: string[];
  optional_arg_name_list?: string[];
};

export type ConsumerInfo = {
  queue_name?: string;
  consuming_function?: string;
  computer_name?: string;
  computer_ip?: string;
  process_id?: number;
  start_datetime_str?: string;
  hearbeat_datetime_str?: string;
  last_x_s_execute_count?: number;
  last_x_s_execute_count_fail?: number;
  last_x_s_avarage_function_spend_time?: number;
  total_consume_count_from_start?: number;
  total_consume_count_from_start_fail?: number;
  avarage_function_spend_time_from_start?: number;
};

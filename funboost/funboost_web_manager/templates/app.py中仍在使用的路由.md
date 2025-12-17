

### 后续希望funboost web manager的后端都优先使用 faas 里面的接口。

### 保留的路由（前端正在使用）

| 路由 | 使用的模板 |
|------|-----------|
| `query_cols_view` | conusme_speed.html, fun_result_table.html |
| `query_result_view` | fun_result_table.html |
| `speed_stats` | fun_result_table.html |
| `consume_speed_curve` | conusme_speed.html |
| `get_msg_num_all_queues` | rpc_call.html |
| `hearbeat_info_*` | running_consumer_by_*.html |
| `get_queues_params_and_active_consumers` | queue_op.html |
| `get_time_series_data_by_queue_name` | queue_op.html (曲线图) |
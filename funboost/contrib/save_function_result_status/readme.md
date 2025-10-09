

# 用户想保存函数消费结果状态到mysql,可以建表如下

如果用户想保存funboost 消费函数结果状态,到mysql ,可以创建一个表,例如
(使用dataset,可以直接保存字典时候自动建表)

```sql
CREATE TABLE funboost_consume_results
(

    _id                       varchar(255) not null,
    `function`                varchar(255) null,
    host_name                 varchar(255) null,
    host_process              varchar(255) null,
    insert_minutes            varchar(255) null,
    insert_time               datetime     null,
    insert_time_str           varchar(255) null,
    publish_time              float        null,
    publish_time_format       varchar(255) null,
    msg_dict                  json         null,
    params                    json         null,
    params_str                varchar(255) null,
    process_id                bigint       null,
    queue_name                varchar(255) null,
    result                    text null,
    run_times                 int          null,
    script_name               varchar(255) null,
    script_name_long          varchar(255) null,
    success                   tinyint(1)   null,
    task_id                   varchar(255) null,
    thread_id                 bigint       null,
    time_cost                 float        null,
    time_end                  float        null,
    time_start                float        null,
    total_thread              int          null,
    utime                     varchar(255) null,
    exception                 mediumtext   null,
    rpc_result_expire_seconds bigint       null,
    exception_type            varchar(255) null,
    exception_msg             text         null,
    rpc_chain_error_msg_dict  text         null,
    run_status                varchar(255) null,

    primary key (_id),
    key idx_insert_time (insert_time),
    key idx_queue_name_insert_time (queue_name, insert_time),
    key idx_params_str (params_str)
)
```
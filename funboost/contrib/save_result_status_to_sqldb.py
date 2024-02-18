import copy
import functools
import json

from db_libs.sqla_lib import SqlaReflectHelper
from sqlalchemy import create_engine

from funboost import boost, FunctionResultStatus, funboost_config_deafult

"""
-- 如果用户是先保存到mysql中而非mongodb,用户自己先创建表,用于保存函数消费状态和结果.

CREATE TABLE funboost_consume_results
(
    _id              VARCHAR(255),
    `function`         VARCHAR(255),
    host_name        VARCHAR(255),
    host_process     VARCHAR(255),
    insert_minutes   VARCHAR(255),
    insert_time      datetime,
    insert_time_str  VARCHAR(255),
    msg_dict         JSON,
    params           JSON,
    params_str       VARCHAR(255),
    process_id       INT,
    publish_time     FLOAT,
    publish_time_str VARCHAR(255),
    queue_name       VARCHAR(255),
    result           VARCHAR(255),
    run_times        INT,
    script_name      VARCHAR(255),
    script_name_long VARCHAR(255),
    success          BOOLEAN,
    task_id          VARCHAR(255),
    thread_id        INT,
    time_cost        FLOAT,
    time_end         FLOAT,
    time_start       FLOAT,
    total_thread     INT,
    utime            VARCHAR(255),
    exception       MEDIUMTEXT ,
    rpc_result_expire_seconds BIGINT(20),
    primary key (_id),
    key idx_insert_time(insert_time),
    key idx_queue_name_insert_time(queue_name,insert_time),
    key idx_params_str(params_str)
)


"""


def _gen_insert_sql_and_values_by_dict(dictx: dict):
    key_list = [f'`{k}`' for k in dictx.keys()]
    fields = ", ".join(key_list)

    # 构建占位符字符串
    placeholders = ", ".join(['%s'] * len(dictx))

    # 构建插入语句
    insert_sql = f"INSERT INTO funboost_consume_results ({fields}) VALUES ({placeholders})"

    # 获取数据字典的值作为插入的值
    values = tuple(dictx.values())
    values_new = tuple([json.dumps(v) if isinstance(v, dict) else v for v in values])
    return insert_sql, values_new


def _gen_insert_sqlalchemy(dictx: dict):
    key_list = [f'`{k}`' for k in dictx.keys()]
    fields = ", ".join(key_list)

    value_list = dictx.keys()
    value_list_2 = [f':{f}' for f in value_list]
    values = ", ".join(value_list_2)

    # 构建插入语句
    insert_sql = f"INSERT INTO funboost_consume_results ({fields}) VALUES ({values})"

    return insert_sql


@functools.lru_cache()
def get_sqla_helper():
    enginex = create_engine(
        funboost_config_deafult.BrokerConnConfig.SQLACHEMY_ENGINE_URL,
        max_overflow=10,  # 超过连接池大小外最多创建的连接
        pool_size=50,  # 连接池大小
        pool_timeout=30,  # 池中没有线程最多等待的时间，否则报错
        pool_recycle=3600,  # 多久之后对线程池中的线程进行一次连接的回收（重置）
        echo=True)
    sqla_helper = SqlaReflectHelper(enginex)
    t_funboost_consume_results = sqla_helper.base_classes.funboost_consume_results
    return enginex, sqla_helper, t_funboost_consume_results


def save_result_status_to_sqlalchemy(function_result_status: FunctionResultStatus):
    """ function_result_status变量上有各种丰富的信息 ,用户可以使用其中的信息
    用户自定义记录函数消费信息的钩子函数
    """
    # print('保存到数据库', function_result_status.get_status_dict())
    enginex, sqla_helper, t_funboost_consume_results = get_sqla_helper()

    with sqla_helper.session as ss:
        status_dict = function_result_status.get_status_dict()
        status_dict_new = copy.copy(status_dict)
        for k, v in status_dict.items():
            if isinstance(v, dict):
                status_dict_new[k] = json.dumps(v)
        # sql = _gen_insert_sqlalchemy(status_dict) # 这种是sqlahemy sql方式插入.
        # ss.execute(sql, status_dict_new)
        ss.merge(t_funboost_consume_results(**status_dict_new)) # 这种是orm方式插入.

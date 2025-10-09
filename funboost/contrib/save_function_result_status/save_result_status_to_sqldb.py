
"""
一个贡献,保存函数结果状态到 mysql postgre 等等,因为默认是使用mongo保存.

可以在 @boost里面指定 user_custom_record_process_info_func= save_result_status_to_sqlalchemy
"""


import copy
import functools
import json

from db_libs.sqla_lib import SqlaReflectHelper
from sqlalchemy import create_engine

from funboost import boost, FunctionResultStatus, funboost_config_deafult




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

    例如  @boost('test_user_custom', user_custom_record_process_info_func=save_result_status_to_sqlalchemy)
    """
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

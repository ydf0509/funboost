
"""
一个贡献,保存函数结果状态到 mysql postgre 等等,因为默认是使用mongo保存.

可以在 @boost里面指定 user_custom_record_process_info_func= save_result_status_to_sqlalchemy
"""

import os
import copy
import functools
import json
import threading

import dataset

from funboost import boost, FunctionResultStatus, funboost_config_deafult,AbstractConsumer



pid__db_map = {}
_lock = threading.Lock()
def get_db(connect_url) -> dataset.Database:
    """封装一个函数，判断pid"""
    pid = os.getpid()
    key = (pid, connect_url,)
    if key not in pid__db_map:
        with _lock:
            if key not in pid__db_map:
                pid__db_map[key] =  dataset.connect(connect_url)
    return pid__db_map[key]


connect_url ='mysql+pymysql://root:123456@127.0.0.1:3306/testdb7' # dataset或 SQLAlchemy 的url连接形式

# 方式一:@boost 装饰器里面使用函数钩子,user_custom_record_process_info_func
def save_result_status_use_dataset(result_status: FunctionResultStatus):
    db = get_db(connect_url)
    table = db['funboost_consume_results']
    table.upsert(result_status.get_status_dict(), ['_id'])

# 方式二:装饰器里面使用 consumer_override_cls,重写 user_custom_record_process_info_func
class ResultStatusUseDatasetMixin(AbstractConsumer):
    def user_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus):
        # print(current_function_result_status.get_status_dict())
        db = get_db(connect_url)
        table = db['funboost_consume_results']
        table.upsert(current_function_result_status.get_status_dict(), ['_id'])
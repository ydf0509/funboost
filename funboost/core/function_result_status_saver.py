import copy
import datetime
import json
import os
import socket
import threading
import time
import uuid

import pymongo
import pymongo.errors
import sys

from pymongo import IndexModel, ReplaceOne

from funboost.core.func_params_model import FunctionResultStatusPersistanceConfig
from funboost.core.helper_funs import get_publish_time, delete_keys_and_return_new_dict, get_publish_time_format,get_func_only_params
from funboost.core.serialization import Serialization
from funboost.utils import time_util, decorators
from funboost.utils.mongo_util import MongoMixin
# from nb_log import LoggerMixin
from funboost.core.loggers import FunboostFileLoggerMixin
from funboost.constant import MongoDbName
class RunStatus:
    running = 'running'
    finish = 'finish'

class FunctionResultStatus():
    # 类级别缓存，避免每次实例化都调用系统函数
    host_name = socket.gethostname()
    _process_id = os.getpid()  # 进程ID在进程生命周期内不变
    _host_process = f'{host_name} - {_process_id}'  # 缓存 host_process

    script_name_long = sys.argv[0]
    script_name = script_name_long.split('/')[-1].split('\\')[-1]

    FUNC_RUN_ERROR = 'FUNC_RUN_ERROR'
    
    # 使用 __slots__ 可以减少内存占用和提升属性访问速度，但会影响动态属性添加
    # 这里不使用 __slots__ 以保持兼容性

    def __init__(self, queue_name: str, fucntion_name: str, msg_dict: dict, function_only_params: dict = None):
        # 优化：使用类级别缓存的 host_process，避免每次格式化
        self.host_process = self._host_process
        self.queue_name = queue_name
        self.function = fucntion_name
        self.msg_dict = msg_dict
        # 优化：直接从 msg_dict 获取 extra，避免多次 get 调用
        extra = msg_dict.get('extra', {})
        self.task_id = extra.get('task_id', '')
        self.publish_time = extra.get('publish_time')
        self.publish_time_format = extra.get('publish_time_format')
        # 优化：使用类级别缓存的 process_id
        self.process_id = self._process_id
        self.thread_id = threading.get_ident()
        # 优化：如果已经传入 function_only_params，直接使用，避免重复计算
        self.params = function_only_params if function_only_params is not None else get_func_only_params(msg_dict)
        # 优化：延迟计算 params_str，使用 _params_str 缓存
        self._params_str = None
        self.result = None
        self.run_times = 0  # 消息实际重试运行了多少次
        self.exception = None
        self.exception_type = None
        self.exception_msg = None
        self.rpc_chain_error_msg_dict: dict = None
        self.time_start = time.time()
        self.time_cost = None
        self.time_end = None
        self.success = False
        self.run_status = ''
        # 优化：延迟获取 total_thread，避免不必要的系统调用
        self._total_thread = None
        self._has_requeue = False
        self._has_to_dlx_queue = False
        self._has_kill_task = False
        self.rpc_result_expire_seconds = None
        
        # 额外的方便用户扩展，如果用户想自己放点其他的其他特殊奇葩信息，可以放在这里。而不必来这里改源码加字段。
        # 用户可以在同一个线程或者协程中通过 fct.function_result_status.user_context 获取。
        self.user_context: dict = {}
    
    @property
    def params_str(self):
        """延迟计算 params_str，只在需要时才进行 JSON 序列化"""
        if self._params_str is None:
            self._params_str = Serialization.to_json_str(self.params)
        return self._params_str
    
    @params_str.setter
    def params_str(self, value):
        self._params_str = value
    
    @property
    def total_thread(self):
        """延迟获取线程数，避免不必要的系统调用"""
        if self._total_thread is None:
            self._total_thread = threading.active_count()
        return self._total_thread
    
    @total_thread.setter
    def total_thread(self, value):
        self._total_thread = value 
      

       
    @classmethod
    def parse_status_and_result_to_obj(cls,status_dict:dict):
        obj = cls(status_dict['queue_name'],status_dict['function'],status_dict['msg_dict'])
        for k,v in status_dict.items():
            # if k.startswith('_'):
            #     continue
            setattr(obj,k,v)
        return obj

    def get_status_dict(self, without_datetime_obj=False):
        item = {}
        for k, v in self.__dict__.items():
            if not k.startswith('_'):
                item[k] = v
                
        item['params_str'] = self.params_str 
        item['total_thread'] = self.total_thread

        item['host_name'] = self.host_name
        item['host_process'] = self.host_process
        item['script_name'] = self.script_name
        item['script_name_long'] = self.script_name_long
        
        # item.pop('time_start')
        datetime_str = time_util.DatetimeConverter().datetime_str
        try:
            Serialization.to_json_str(item['result'])
            # json.dumps(item['result'])  # 不希望存不可json序列化的复杂类型。麻烦。存这种类型的结果是伪需求。
        except TypeError:
            item['result'] = str(item['result'])[:1000]
        item.update({'insert_time_str': datetime_str,
                     'insert_minutes': datetime_str[:-3],
                     })
        if not without_datetime_obj:
            item.update({'insert_time': time_util.DatetimeConverter().datetime_obj,
                         'utime': datetime.datetime.now(datetime.timezone.utc),
                         })
        else:
            item = delete_keys_and_return_new_dict(item, ['insert_time', 'utime'])

        item['_id'] = self.task_id
   
        return item

    def __str__(self):
        return f'''{self.__class__}   {Serialization.to_json_str(self.get_status_dict())}'''

    def to_pretty_json_str(self):
        return json.dumps(self.get_status_dict(),indent=4,ensure_ascii=False)


class ResultPersistenceHelper(MongoMixin, FunboostFileLoggerMixin):
 

    def __init__(self, function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig, queue_name):
        self.function_result_status_persistance_conf = function_result_status_persistance_conf
        self._bulk_list = []
        self._bulk_list_lock = threading.Lock()
        self._last_bulk_insert_time = 0
        self._has_start_bulk_insert_thread = False
        self._queue_name = queue_name
        self._table_name = self.function_result_status_persistance_conf.table_name
        if self.function_result_status_persistance_conf.is_save_status:
            self._create_indexes()
            # self._mongo_bulk_write_helper = MongoBulkWriteHelper(task_status_col, 100, 2)
            self.logger.debug(f"函数运行状态结果将保存至mongo的 {MongoDbName.TASK_STATUS_DB} 库的 {queue_name} 集合中，请确认 funboost.py文件中配置的 MONGO_CONNECT_URL")

    def _create_indexes(self):
        task_status_col = self.get_mongo_collection(MongoDbName.TASK_STATUS_DB, self._table_name)
        try:
            has_creat_index = False
            index_dict = task_status_col.index_information()
            if 'insert_time_str_-1' in index_dict:
                has_creat_index = True
            old_expire_after_seconds = None
            for index_name, v in index_dict.items():
                if index_name == 'utime_1':
                    old_expire_after_seconds = v['expireAfterSeconds']
            if has_creat_index is False:
                # params_str 如果很长，必须使用TEXt或HASHED索引。
                task_status_col.create_indexes([
                    IndexModel([("queue_name", 1)]),
                    IndexModel([("insert_time_str", -1)]), IndexModel([("insert_time", -1)]),
                                                IndexModel([("params_str", pymongo.TEXT)]), IndexModel([("success", 1)]),
                                                IndexModel([("time_cost", -1)]),  # 用于按耗时查询
                                                ], )
                task_status_col.create_index([("utime", 1)],  # 这个是过期时间索引。
                                             expireAfterSeconds=self.function_result_status_persistance_conf.expire_seconds)  # 只保留7天(用户自定义的)。
            else:
                if old_expire_after_seconds != self.function_result_status_persistance_conf.expire_seconds:
                    self.logger.warning(f'过期时间从 {old_expire_after_seconds} 修改为 {self.function_result_status_persistance_conf.expire_seconds} 。。。')
                    task_status_col.drop_index('utime_1', ),  # 这个不能也设置为True，导致修改过期时间不成功。
                    task_status_col.create_index([("utime", 1)],
                                                 expireAfterSeconds=self.function_result_status_persistance_conf.expire_seconds, background=True)  # 只保留7天(用户自定义的)。
        except pymongo.errors.PyMongoError as e:
            self.logger.warning(e)

    def save_function_result_to_mongo(self, function_result_status: FunctionResultStatus):
        if self.function_result_status_persistance_conf.is_save_status:
            task_status_col = self.get_mongo_collection(MongoDbName.TASK_STATUS_DB, self._table_name)  # type: pymongo.collection.Collection
            item = function_result_status.get_status_dict()
            item2 = copy.copy(item)
            if not self.function_result_status_persistance_conf.is_save_result:
                item2['result'] = '不保存结果'
            if item2['result'] is None:
                item2['result'] = ''
            if item2['exception'] is None:
                item2['exception'] = ''
            if self.function_result_status_persistance_conf.is_use_bulk_insert:
                # self._mongo_bulk_write_helper.add_task(InsertOne(item2))  # 自动离散批量聚合方式。
                with self._bulk_list_lock:
                    self._bulk_list.append(ReplaceOne({'_id': item2['_id']}, item2, upsert=True))
                    # if time.time() - self._last_bulk_insert_time > 0.5:
                    #     self.task_status_col.bulk_write(self._bulk_list, ordered=False)
                    #     self._bulk_list.clear()
                    #     self._last_bulk_insert_time = time.time()
                    if not self._has_start_bulk_insert_thread:
                        self._has_start_bulk_insert_thread = True
                        decorators.keep_circulating(time_sleep=0.2, is_display_detail_exception=True, block=False,
                                                    daemon=False)(self._bulk_insert)()
                        self.logger.warning(f'启动批量保存函数消费状态 结果到mongo的 线程')
            else:
                task_status_col.replace_one({'_id': item2['_id']}, item2, upsert=True)  # 立即实时插入。

    def _bulk_insert(self):
        with self._bulk_list_lock:
            if time.time() - self._last_bulk_insert_time > 0.5 and self._bulk_list:
                task_status_col = self.get_mongo_collection(MongoDbName.TASK_STATUS_DB, self._table_name)
                task_status_col.bulk_write(self._bulk_list, ordered=False)
                self._bulk_list.clear()
                self._last_bulk_insert_time = time.time()

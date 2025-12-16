"""
此模块的功能非常适合拿来开发对funboost的监控面板，或者管理后台。
    - ActiveCousumerProcessInfoGetter  获取队列的活跃消费进程信息
    - QueuesConusmerParamsGetter  获取所有队列配置参数 和 运行信息
    - SingleQueueConusmerParamsGetter  获取单个队列配置参数 和 运行信息


下面3个python文件的web接口中，funboost.faas 主要就是使用了此模块的功能。
 



care_project_name 的作用是：
    - None : 关心所有redis中存储的队列信息
    - str : 只关心指定project_name的队列信息
   
"""


import json
import threading
import time
import typing
import uuid
import os

from funboost.factories.publisher_factotry import get_publisher
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.utils.redis_manager import RedisMixin

from funboost.core.loggers import FunboostFileLoggerMixin,nb_log_config_default
from funboost.core.serialization import Serialization
from funboost.constant import RedisKeys
from funboost.core.booster import BoostersManager, Booster
from funboost.core.func_params_model import PublisherParams, BoosterParams, BaseJsonAbleModel
from funboost.core.function_result_status_saver import FunctionResultStatusPersistanceConfig
from funboost.core.consuming_func_iniput_params_check import FakeFunGenerator
from funboost.core.exceptions import QueueNameNotExists
from funboost.timing_job.timing_push import ApsJobAdder

class CareProjectNameEnv:
    env_name = 'funboost.care_project_name'
    @classmethod
    def set(cls, care_project_name: str):
        os.environ[cls.env_name] = care_project_name

    @classmethod
    def get(cls) -> typing.Optional[bool]:
        care_project_name =  os.environ.get(cls.env_name, None)
        if care_project_name in ('','all','None','null','none',None):
            return None
        return care_project_name



class RedisReportInfoGetterMixin:
    def _init(self,care_project_name:typing.Optional[str]=None,):
        """
        参数:
            care_project_name
            只关注指定project_name相关的boosters，只获取这些队列在redis中的运行信息

            避免获取redis中不相关的 boosters信息，减少信息干扰和提升性能。
        """
        if care_project_name is not None:
            self.care_project_name = care_project_name
        else:
            self.care_project_name = CareProjectNameEnv.get()
        self.project_name_queues = self.get_queue_names_by_project_name(self.care_project_name)

    def get_all_queue_names(self) ->list:
        if self.care_project_name:
            return self.project_name_queues
        return list(self.redis_db_frame.smembers(RedisKeys.FUNBOOST_ALL_QUEUE_NAMES))

    def get_queue_names_by_project_name(self,project_name:str) ->list:
        return list(self.redis_db_frame.smembers(RedisKeys.gen_funboost_project_name_key(project_name)))
    
    @property
    def all_queue_names(self):
        return self.get_all_queue_names()

    def hmget_many_by_all_queue_names(self,key):
        # if self.care_project_name is False:
        #     return self.redis_db_frame.hgetall(key)
        # ret_list = self.redis_db_frame.hmget(key,fileds)
        # return  dict(zip(fileds, ret_list))
        if len(self.all_queue_names) == 0:
            err_msg  = f"""
            care_project_name is set to {self.care_project_name},

            make sure  you have set @boost(BoosterParams(is_send_consumer_hearbeat_to_redis=True,project_name=$project_name))

            """
            self.logger.error(err_msg)
            return {}
        ret_list = self.redis_db_frame.hmget(key,self.all_queue_names)
        ret_list_exlude_none = [i for i in ret_list if i is not None]
        return  dict(zip(self.all_queue_names, ret_list_exlude_none))
    
    def get_all_project_names(self):
        return list(self.redis_db_frame.smembers(RedisKeys.FUNBOOST_ALL_PROJECT_NAMES))
    
    
    


def _cvt_int(str_value:typing.Optional[str])->typing.Optional[int]:
    if str_value is None:
        return None
    return int(str_value)


def _sum_filed_from_active_consumers(active_consumers:typing.List[dict],filed:str):
    s = 0
    for c in active_consumers:
        # print(c)
        if c[filed]:
            # print(c[filed])
            s+=c[filed]
    return s

class ActiveCousumerProcessInfoGetter(RedisMixin,RedisReportInfoGetterMixin,FunboostFileLoggerMixin):
    """

    获取分布式环境中的消费进程信息。
    使用这里面的4个方法需要相应函数的@boost装饰器设置 is_send_consumer_hearbeat_to_redis=True，这样会自动发送活跃心跳到redis。否则查询不到该函数的消费者进程信息。
    要想使用消费者进程信息统计功能，用户无论使用何种消息队列中间件类型，用户都必须安装redis，并在 funboost_config.py 中配置好redis链接信息
    """

    def __init__(self,care_project_name:typing.Optional[str]=None):
        RedisReportInfoGetterMixin._init(self,care_project_name)

        

    def _get_all_hearbeat_info_by_redis_key_name(self, redis_key):
        results = self.redis_db_frame.smembers(redis_key)
        # print(type(results))
        # print(results)
        # 如果所有机器所有进程都全部关掉了，就没办法还剩一个线程执行删除了，这里还需要判断一次15秒。
        active_consumers_processor_info_list = []
        for result in results:
            result_dict = json.loads(result)
            if  result_dict['queue_name'] not in self.get_all_queue_names():
                continue
            if self.timestamp() - result_dict['hearbeat_timestamp'] < 15:
                active_consumers_processor_info_list.append(result_dict)
                if self.timestamp() - result_dict['current_time_for_execute_task_times_every_unit_time'] > 30:
                    result_dict['last_x_s_execute_count'] = 0
                    result_dict['last_x_s_execute_count_fail'] = 0
        return active_consumers_processor_info_list

    def get_all_hearbeat_info_by_queue_name(self, queue_name) -> typing.List[typing.Dict]:
        """
        根据队列名查询有哪些活跃的消费者进程
        返回结果例子：
        [{
                "code_filename": "/codes/funboost/test_frame/my/test_consume.py",
                "computer_ip": "172.16.0.9",
                "computer_name": "VM_0_9_centos",
                "consumer_id": 140477437684048,
                "consumer_uuid": "79473629-b417-4115-b516-4365b3cdf383",
                "consuming_function": "f2",
                "hearbeat_datetime_str": "2021-12-27 19:22:04",
                "hearbeat_timestamp": 1640604124.4643965,
                "process_id": 9665,
                "queue_name": "test_queue72c",
                "start_datetime_str": "2021-12-27 19:21:24",
                "start_timestamp": 1640604084.0780013
            }, ...............]
        """
        redis_key = RedisKeys.gen_funboost_hearbeat_queue__dict_key_by_queue_name(queue_name)
        return self._get_all_hearbeat_info_by_redis_key_name(redis_key)

    def get_all_hearbeat_info_by_ip(self, ip=None) -> typing.List[typing.Dict]:
        """
        根据机器的ip查询有哪些活跃的消费者进程，ip不传参就查本机ip使用funboost框架运行了哪些消费进程，传参则查询任意机器的消费者进程信息。
        返回结果的格式和上面的 get_all_hearbeat_dict_by_queue_name 方法相同。
        """
        ip = ip or nb_log_config_default.computer_ip
        redis_key = RedisKeys.gen_funboost_hearbeat_server__dict_key_by_ip(ip)
        return self._get_all_hearbeat_info_by_redis_key_name(redis_key)

    # def _get_all_hearbeat_info_partition_by_redis_key_prefix(self, redis_key_prefix):
    #     keys = self.redis_db_frame.scan(0, f'{redis_key_prefix}*', count=10000)[1]
    #     infos_map = {}
    #     for key in keys:
    #         infos = self.redis_db_frame.smembers(key)
    #         dict_key = key.replace(redis_key_prefix, '')
    #         infos_map[dict_key] = []
    #         for info_str in infos:
    #             info_dict = json.loads(info_str)
    #             if self.timestamp() - info_dict['hearbeat_timestamp'] < 15:
    #                 infos_map[dict_key].append(info_dict)
    #                 if self.timestamp() - info_dict['current_time_for_execute_task_times_every_unit_time'] > 30:
    #                     info_dict['last_x_s_execute_count'] = 0
    #                     info_dict['last_x_s_execute_count_fail'] = 0
    #     return infos_map

    
    
    def get_all_ips(self):
        return self.redis_db_frame.smembers(RedisKeys.FUNBOOST_ALL_IPS)
    
    def _get_all_hearbeat_info_partition_by_redis_keys(self, keys):
        
        # keys = [f'{redis_key_prefix}{queue_name}' for queue_name in queue_names]
        infos_map = {}
        for key in keys:
            infos = self.redis_db_frame.smembers(key)
            dict_key = key.replace(RedisKeys.FUNBOOST_HEARTBEAT_QUEUE__DICT_PREFIX, '').replace(RedisKeys.FUNBOOST_HEARTBEAT_SERVER__DICT_PREFIX, '')
            infos_map[dict_key] = []
            for info_str in infos:
                info_dict = json.loads(info_str)
                if  info_dict['queue_name'] not in self.get_all_queue_names():
                    continue
                if self.timestamp() - info_dict['hearbeat_timestamp'] < 15:
                    infos_map[dict_key].append(info_dict)
                    if self.timestamp() - info_dict['current_time_for_execute_task_times_every_unit_time'] > 30:
                        info_dict['last_x_s_execute_count'] = 0
                        info_dict['last_x_s_execute_count_fail'] = 0
        return infos_map

    def get_all_hearbeat_info_partition_by_queue_name(self) -> typing.Dict[typing.AnyStr, typing.List[typing.Dict]]:
        """获取所有队列对应的活跃消费者进程信息，按队列名划分,不需要传入队列名，自动扫描redis键。请不要在 funboost_config.py 的redis 指定的db中放太多其他业务的缓存键值对"""
        queue_names = self.get_all_queue_names()
        infos_map = self._get_all_hearbeat_info_partition_by_redis_keys([RedisKeys.gen_funboost_hearbeat_queue__dict_key_by_queue_name(queue_name) for queue_name in queue_names])
        # self.logger.info(f'获取所有队列对应的活跃消费者进程信息，按队列名划分，结果是 {json.dumps(infos_map, indent=4)}')
        return infos_map

    def get_all_hearbeat_info_partition_by_ip(self) -> typing.Dict[typing.AnyStr, typing.List[typing.Dict]]:
        """获取所有机器ip对应的活跃消费者进程信息，按机器ip划分,不需要传入机器ip，自动扫描redis键。请不要在 funboost_config.py 的redis 指定的db中放太多其他业务的缓存键值对 """
        ips = self.get_all_ips()
        infos_map = self._get_all_hearbeat_info_partition_by_redis_keys([RedisKeys.gen_funboost_hearbeat_server__dict_key_by_ip(ip) for ip in ips])
        self.logger.info(f'获取所有机器ip对应的活跃消费者进程信息，按机器ip划分，结果是 {json.dumps(infos_map, indent=4)}')
        return infos_map





class QueuesConusmerParamsGetter(RedisMixin, RedisReportInfoGetterMixin,FunboostFileLoggerMixin):
    """
    获取所有队列的运行信息，
    方法 get_queues_params_and_active_consumers 返回信息最丰富
    """
    def __init__(self,care_project_name:typing.Optional[str]=None):
        RedisReportInfoGetterMixin._init(self,care_project_name)


    def get_queues_params(self,)->dict:
        queue__consumer_params_map = self.hmget_many_by_all_queue_names(RedisKeys.FUNBOOST_QUEUE__CONSUMER_PARAMS,)   
        return {k:Serialization.to_dict(v)  for k,v in queue__consumer_params_map.items()}

    def get_pause_flag(self):
        queue__pause_map = self.hmget_many_by_all_queue_names(RedisKeys.REDIS_KEY_PAUSE_FLAG,)
        return {k:_cvt_int(v)  for k,v in queue__pause_map.items()}

    def get_msg_num(self,ignore_report_ts=False):
        queue__msg_count_info_map = self.hmget_many_by_all_queue_names(RedisKeys.QUEUE__MSG_COUNT_MAP,)
        queue__msg_count_dict = {}
        # print(queue__msg_count_info_map)
        for queue_name,info_json in queue__msg_count_info_map.items():
            info_dict = json.loads(info_json)
            if ignore_report_ts or (info_dict['report_ts'] > time.time() - 15 and info_dict['last_get_msg_num_ts'] > time.time() - 1200):
                queue__msg_count_dict[queue_name] = info_dict['msg_num_in_broker']
        return queue__msg_count_dict

    def get_queues_history_run_count(self,):
        queue__run_count_map = self.hmget_many_by_all_queue_names(RedisKeys.FUNBOOST_QUEUE__RUN_COUNT_MAP,)
        return {k:_cvt_int(v) for k,v in queue__run_count_map.items()}
    
    def get_queues_history_run_fail_count(self,):
        queue__run_fail_count_map = self.hmget_many_by_all_queue_names(RedisKeys.FUNBOOST_QUEUE__RUN_FAIL_COUNT_MAP,)
        return {k:_cvt_int(v) for k,v in queue__run_fail_count_map.items()}
    
    def get_queues_params_and_active_consumers(self):
        """获取所有队列的参数和活跃消费者"""
        queue__active_consumers_map = ActiveCousumerProcessInfoGetter(
            care_project_name=self.care_project_name
            ).get_all_hearbeat_info_partition_by_queue_name()

        queue__history_run_count_map = self.get_queues_history_run_count()
        queue__history_run_fail_count_map = self.get_queues_history_run_fail_count()

        queue__consumer_params_map  = self.get_queues_params()
        queue__pause_map = self.get_pause_flag()
        queue__msg_count_dict = self.get_msg_num(ignore_report_ts=True)
        queue_params_and_active_consumers = {}

        for queue, consumer_params in  queue__consumer_params_map.items():
            
            active_consumers = queue__active_consumers_map.get(queue, [])
            # print(queue,active_consumers)
            all_consumers_last_x_s_execute_count = _sum_filed_from_active_consumers(active_consumers,'last_x_s_execute_count')
            all_consumers_last_x_s_execute_count_fail = _sum_filed_from_active_consumers(active_consumers, 'last_x_s_execute_count_fail')
            all_consumers_last_x_s_total_cost_time = _sum_filed_from_active_consumers(active_consumers, 'last_x_s_total_cost_time')
            all_consumers_last_x_s_avarage_function_spend_time = round( all_consumers_last_x_s_total_cost_time / all_consumers_last_x_s_execute_count,3) if all_consumers_last_x_s_execute_count else None
            
            all_consumers_total_consume_count_from_start = _sum_filed_from_active_consumers(active_consumers, 'total_consume_count_from_start')
            all_consumers_total_cost_time_from_start =_sum_filed_from_active_consumers(active_consumers, 'total_cost_time_from_start')
            all_consumers_avarage_function_spend_time_from_start = round(all_consumers_total_cost_time_from_start / all_consumers_total_consume_count_from_start,3) if all_consumers_total_consume_count_from_start else None

            queue_params_and_active_consumers[queue] = {
                'queue_params':consumer_params,
                'active_consumers':active_consumers,
                'pause_flag':queue__pause_map.get(queue,-1),
                'msg_num_in_broker':queue__msg_count_dict.get(queue,None),
                
                'history_run_count':queue__history_run_count_map.get(queue,None),
                'history_run_fail_count':queue__history_run_fail_count_map.get(queue,None),

                'all_consumers_last_x_s_execute_count':all_consumers_last_x_s_execute_count,
                'all_consumers_last_x_s_execute_count_fail':all_consumers_last_x_s_execute_count_fail,
                'all_consumers_last_x_s_avarage_function_spend_time':all_consumers_last_x_s_avarage_function_spend_time,
                'all_consumers_avarage_function_spend_time_from_start':all_consumers_avarage_function_spend_time_from_start,
                'all_consumers_total_consume_count_from_start':_sum_filed_from_active_consumers(active_consumers, 'total_consume_count_from_start'),
                'all_consumers_total_consume_count_from_start_fail':_sum_filed_from_active_consumers(active_consumers, 'total_consume_count_from_start_fail'),
            }
        return queue_params_and_active_consumers
    
    def cycle_get_queues_params_and_active_consumers_and_report(self,daemon=False):
        time_interval = 10
        report_uuid = str(uuid.uuid4()) 
        def _inner():
            while True:
                t_start = time.time()
                # 这个函数确保只有一个地方在上报数据，避免重复采集上报
                report_ts = self.timestamp()
                redis_report_uuid_ts_str = self.redis_db_frame.get(RedisKeys.FUNBOOST_LAST_GET_QUEUES_PARAMS_AND_ACTIVE_CONSUMERS_AND_REPORT__UUID_TS, )
                if redis_report_uuid_ts_str:
                    redis_report_uuid_ts = Serialization.to_dict(redis_report_uuid_ts_str)
                    if redis_report_uuid_ts['report_uuid'] != report_uuid and redis_report_uuid_ts['report_ts'] > report_ts - time_interval - 10 :
                        time.sleep(5) # 防止cpu空转
                        continue
                self.redis_db_frame.set(RedisKeys.FUNBOOST_LAST_GET_QUEUES_PARAMS_AND_ACTIVE_CONSUMERS_AND_REPORT__UUID_TS,
                                        Serialization.to_json_str({'report_uuid':report_uuid, 'report_ts':report_ts}))
                
                queue_params_and_active_consumers = self.get_queues_params_and_active_consumers()
                for queue,item in queue_params_and_active_consumers.items():
                    if len(item['active_consumers']) == 0:
                        continue
                    report_data = {k:v for k,v in item.items() if k not in ['queue_params','active_consumers']}
                    
                    report_data['report_ts'] = report_ts
                    self.redis_db_frame.zadd(RedisKeys.gen_funboost_queue_time_series_data_key_by_queue_name(queue),
                                            {Serialization.to_json_str(report_data):report_ts} )
                    # 删除过期时序数据,只保留最近1天数据
                    self.redis_db_frame.zremrangebyscore(
                        RedisKeys.gen_funboost_queue_time_series_data_key_by_queue_name(queue),
                        0, report_ts - 86400
                    )
                self.logger.info(f'采集上报时序数据耗时 {time.time() - t_start} 秒')

                time.sleep(time_interval)
        threading.Thread(target=_inner, daemon=daemon).start()

    
        



class SingleQueueConusmerParamsGetter(RedisMixin, RedisReportInfoGetterMixin,FunboostFileLoggerMixin):
    """
    获取单个队列的运行信息，
    方法 get_one_queue_params_and_active_consumers 返回信息最丰富
    """
    queue__booster_params_cache :dict= {}
    _pid_broker_kind_queue_name__booster_map = {}
    _pid_broker_kind_queue_name__publisher_map = {}
    _lock_for_generate_publisher_booster = threading.Lock()
    


    def __init__(self,queue_name:str,care_project_name:typing.Optional[str]=None):
        RedisReportInfoGetterMixin._init(self,care_project_name)
        self.queue_name = queue_name
        self._check_booster_exists()
        self._last_update_consuming_func_input_params_checker = 0
     
    
    def _check_booster_exists(self):
        if self.queue_name not in self.all_queue_names:
            err_msg = f'''
            queue_name {self.queue_name} not in all_queue_names {self.all_queue_names},  

            you have set care_project_name={self.care_project_name},

            '''
            self.logger.error(err_msg)
            raise QueueNameNotExists(err_msg,error_data={'queue_name':self.queue_name,'care_project_name':self.care_project_name})

    def get_one_queue_params(self)->dict:
        """
        类似于这样，就是booster_params的字符串json序列化

        ```json
        {
  "queue_name": "test_funboost_faas_queue2",
  "broker_kind": "REDIS",
  "project_name": "test_project1",
  "concurrent_mode": "threading",
  "concurrent_num": 50,
  "specify_concurrent_pool": null,
  "specify_async_loop": null,
  "is_auto_start_specify_async_loop_in_child_thread": true,
  "qps": null,
  "is_using_distributed_frequency_control": false,
  "is_send_consumer_hearbeat_to_redis": true,
  "max_retry_times": 3,
  "retry_interval": 0,
  "is_push_to_dlx_queue_when_retry_max_times": false,
  "consumin_function_decorator": null,
  "function_timeout": null,
  "is_support_remote_kill_task": false,
  "log_level": 10,
  "logger_prefix": "",
  "create_logger_file": true,
  "logger_name": "",
  "log_filename": null,
  "is_show_message_get_from_broker": false,
  "is_print_detail_exception": true,
  "publish_msg_log_use_full_msg": false,
  "msg_expire_senconds": null,
  "do_task_filtering": false,
  "task_filtering_expire_seconds": 0,
  "function_result_status_persistance_conf": {
    "is_save_status": false,
    "is_save_result": false,
    "expire_seconds": 604800,
    "is_use_bulk_insert": false
  },
  "user_custom_record_process_info_func": null,
  "is_using_rpc_mode": true,
  "rpc_result_expire_seconds": 1800,
  "rpc_timeout": 1800,
  "delay_task_apscheduler_jobstores_kind": "redis",
  "is_do_not_run_by_specify_time_effect": false,
  "do_not_run_by_specify_time": [
    "10:00:00",
    "22:00:00"
  ],
  "schedule_tasks_on_main_thread": false,
  "is_auto_start_consuming_message": false,
  "booster_group": "test_group1",
  "consuming_function": "<function sub at 0x00000272649BBA60>",
  "consuming_function_raw": "<function sub at 0x00000272649BBA60>",
  "consuming_function_name": "sub",
  "broker_exclusive_config": {
    "redis_bulk_push": 1,
    "pull_msg_batch_size": 100
  },
  "should_check_publish_func_params": true,
  "manual_func_input_params": {
    "is_manual_func_input_params": false,
    "must_arg_name_list": [],
    "optional_arg_name_list": []
  },
  "consumer_override_cls": null,
  "publisher_override_cls": null,
  "consuming_function_kind": "COMMON_FUNCTION",
  "user_options": {
    
  },
  "auto_generate_info": {
    "where_to_instantiate": "D:\\codes\\funboost\\examples\\example_faas\\task_funs_dir\\sub.py:5",
    "final_func_input_params_info": {
      "func_name": "sub",
      "func_position": "<function sub at 0x00000272649BBA60>",
      "is_manual_func_input_params": false,
      "all_arg_name_list": [
        "a",
        "b"
      ],
      "must_arg_name_list": [
        "a",
        "b"
      ],
      "optional_arg_name_list": []
    }
  }
}


        ```
        """
        one_queue_params =  self.redis_db_frame.hget('funboost_queue__consumer_parmas',self.queue_name)
        return Serialization.to_dict(one_queue_params)

    def get_one_queue_params_use_cache(self)->dict:
        if self.queue_name not in self.queue__booster_params_cache or time.time() - self.queue__booster_params_cache[self.queue_name]['get_from_redis_ts'] > 60:
            booster_params = self.get_one_queue_params()
            get_from_redis_ts = time.time()
            self.queue__booster_params_cache[self.queue_name] = {'booster_params':booster_params,'get_from_redis_ts':get_from_redis_ts}
        return self.queue__booster_params_cache[self.queue_name]['booster_params']

    def generate_publisher_by_funboost_redis_info(self)-> AbstractPublisher:
        booster_params = self.get_one_queue_params_use_cache()
        key = (os.getpid(), booster_params['broker_kind'], booster_params['queue_name'])
        with self._lock_for_generate_publisher_booster:
            if key not in self._pid_broker_kind_queue_name__publisher_map:
                redis_final_func_input_params_info = booster_params['auto_generate_info']['final_func_input_params_info']
                fake_fun = FakeFunGenerator.gen_fake_fun_by_params(redis_final_func_input_params_info)
                booster_params['consuming_function'] = fake_fun
                booster_params['consuming_function_raw'] = fake_fun
                
                booster_params['is_fake_booster'] = True # 重要，不要注册到BoostersManager，防止干扰用户的真实booster的消费函数逻辑。由此类的 _pid_broker_kind_queue_name__publisher_map 管理
                # 发布消息时候会立即校验入参是否正确，你使用了redis中的 booster配置的 auto_generate_info.final_func_input_params_info 信息来校验入参名字和个数是否正确
                # booster_params['should_check_publish_func_params'] = False # 
                booster_params_model = BoosterParams(**booster_params)
                publisher_params_model = BaseJsonAbleModel.init_by_another_model(PublisherParams, booster_params_model)
                publisher = get_publisher(publisher_params_model)
                self._pid_broker_kind_queue_name__publisher_map[key] = publisher
            publisher:AbstractPublisher = self._pid_broker_kind_queue_name__publisher_map[key]
            self._update_publisher_params_checker(publisher,booster_params)
            return publisher

    def generate_booster_by_funboost_redis_info_for_timing_push(self)-> Booster:
        booster_params= self.get_one_queue_params_use_cache()
        key = (os.getpid(), booster_params['broker_kind'],booster_params['queue_name'])
        with self._lock_for_generate_publisher_booster:
            if key not in self._pid_broker_kind_queue_name__booster_map:
                # 只是为了生成一个能发送定时的booster,不需要那么多配置，很多redis中的配置是不可序列化的用字符串替代了，有些字符串不能直接拿来使用，因为pydantic有类型校验。
                redis_final_func_input_params_info = booster_params['auto_generate_info']['final_func_input_params_info']
                fake_fun = FakeFunGenerator.gen_fake_fun_by_params(redis_final_func_input_params_info)
                booster_params['consuming_function'] = fake_fun
                booster_params['consuming_function_raw'] = fake_fun

                # booster_params['should_check_publish_func_params'] = False
                booster_params['specify_concurrent_pool'] = None
                booster_params['specify_async_loop'] = None
                booster_params['consumin_function_decorator'] = None
                booster_params['function_result_status_persistance_conf'] = FunctionResultStatusPersistanceConfig(is_save_status=False,is_save_result=False)
                booster_params['user_custom_record_process_info_func'] = None
                booster_params['consumer_override_cls'] = None
                booster_params['publisher_override_cls'] = None

                booster_params['is_fake_booster'] = True # 重要，不要注册到BoostersManager，防止干扰用户的真实booster的消费函数逻辑。由此类的 _pid_broker_kind_queue_name__booster_map 管理
                booster_params_model = BoosterParams(**booster_params)
                booster = Booster(booster_params_model)(booster_params_model.consuming_function)
                self._pid_broker_kind_queue_name__booster_map[key] = booster
            booster:Booster = self._pid_broker_kind_queue_name__booster_map[key]
            self._update_publisher_params_checker(booster.publisher,booster_params)
            return booster

    def generate_aps_job_adder(self,job_store_kind='redis',is_auto_start=True,is_auto_paused=True) -> ApsJobAdder:
        booster = self.generate_booster_by_funboost_redis_info_for_timing_push()
        job_adder = ApsJobAdder(booster, job_store_kind=job_store_kind, is_auto_start=is_auto_start,is_auto_paused=is_auto_paused)
        return job_adder


    def _update_publisher_params_checker(self,publisher:AbstractPublisher,booster_params:dict):
        """ 
        如果函数上线后，中途又修改函数入参定义，所以任然需要更新 publish_params_checker， 这样才能持续正确校验发布消息时候的入参是否合法
        """
        if  self._last_update_consuming_func_input_params_checker < time.time() - 60:
            self._last_update_consuming_func_input_params_checker = time.time()
            final_func_input_params_info = booster_params['auto_generate_info'].get('final_func_input_params_info',None)
            if final_func_input_params_info:
                publisher.publish_params_checker.update_check_params(final_func_input_params_info)



    def get_one_queue_pause_flag(self) ->int:
        """
        返回队列的暂停状态，-1 表示队列不存在，0 表示队列未暂停，1 表示队列已暂停
        """
        pause_flag = self.redis_db_frame.hget(RedisKeys.REDIS_KEY_PAUSE_FLAG,self.queue_name)
        if pause_flag is None:
            return -1
        return int(pause_flag)

    def get_one_queue_history_run_count(self,) ->int:
        return _cvt_int(self.redis_db_frame.hget(RedisKeys.FUNBOOST_QUEUE__RUN_COUNT_MAP,self.queue_name))
    
    def get_one_queue_history_run_fail_count(self,) ->int:
        return _cvt_int(self.redis_db_frame.hget(RedisKeys.FUNBOOST_QUEUE__RUN_FAIL_COUNT_MAP,self.queue_name))

    def get_one_queue_msg_num(self,ignore_report_ts=False) ->int:
        """
        从上报到redis的心跳信息中获取的消息数量，
        如果 ignore_report_ts 为 True 并且最近一次上报时间是很久之前的，消息数量就不准
        上报线程是随着消费一起自动运行的，如果没有启动消息，就会停止心跳信息上报。
        """
        msg_count_info = self.redis_db_frame.hget(RedisKeys.QUEUE__MSG_COUNT_MAP,self.queue_name)
        info_dict = json.loads(msg_count_info)
        if ignore_report_ts or (info_dict['report_ts'] > time.time() - 15 and info_dict['last_get_msg_num_ts'] > time.time() - 1200):
            return info_dict['msg_num_in_broker']
        return -1

    def get_one_queue_msg_num_realtime(self,) ->int:   
        """
        实时从broker获取的消息数量，
        """
        try:
            consumer_params = self.get_one_queue_params()
            publisher = BoostersManager.get_cross_project_publisher(
                PublisherParams(queue_name=self.queue_name, 
                                broker_kind=consumer_params['broker_kind'],
                                broker_exclusive_config=consumer_params['broker_exclusive_config'],
                                publish_msg_log_use_full_msg=True))
            return publisher.get_message_count()
        except Exception as e:
            self.logger.exception(f'实时获取队列消息数失败 {e}')
            return -1



    def get_one_queue_params_and_active_consumers(self)->dict:
        active_consumers = ActiveCousumerProcessInfoGetter(
            care_project_name=self.care_project_name
            ).get_all_hearbeat_info_by_queue_name(self.queue_name)

        history_run_count = self.get_one_queue_history_run_count()
        history_run_fail_count = self.get_one_queue_history_run_fail_count()

        consumer_params  = self.get_one_queue_params()
        pause_flag = self.get_one_queue_pause_flag()
        # msg_num = self.get_one_queue_msg_num(ignore_report_ts=True)
        msg_num = self.get_one_queue_msg_num_realtime()

        # print(queue,active_consumers)
        all_consumers_last_x_s_execute_count = _sum_filed_from_active_consumers(active_consumers,'last_x_s_execute_count')
        all_consumers_last_x_s_execute_count_fail = _sum_filed_from_active_consumers(active_consumers, 'last_x_s_execute_count_fail')
        all_consumers_last_x_s_total_cost_time = _sum_filed_from_active_consumers(active_consumers, 'last_x_s_total_cost_time')
        all_consumers_last_x_s_avarage_function_spend_time = round( all_consumers_last_x_s_total_cost_time / all_consumers_last_x_s_execute_count,3) if all_consumers_last_x_s_execute_count else None
        
        all_consumers_total_consume_count_from_start = _sum_filed_from_active_consumers(active_consumers, 'total_consume_count_from_start')
        all_consumers_total_cost_time_from_start =_sum_filed_from_active_consumers(active_consumers, 'total_cost_time_from_start')
        all_consumers_avarage_function_spend_time_from_start = round(all_consumers_total_cost_time_from_start / all_consumers_total_consume_count_from_start,3) if all_consumers_total_consume_count_from_start else None

        params_and_active_consumers = {
            'queue_params':consumer_params,
            'active_consumers':active_consumers,
            'pause_flag':pause_flag,
            'msg_num_in_broker':msg_num,
            
            'history_run_count':history_run_count,
            'history_run_fail_count':history_run_fail_count,

            'all_consumers_last_x_s_execute_count':all_consumers_last_x_s_execute_count,
            'all_consumers_last_x_s_execute_count_fail':all_consumers_last_x_s_execute_count_fail,
            'all_consumers_last_x_s_avarage_function_spend_time':all_consumers_last_x_s_avarage_function_spend_time,
            'all_consumers_avarage_function_spend_time_from_start':all_consumers_avarage_function_spend_time_from_start,
            'all_consumers_total_consume_count_from_start':_sum_filed_from_active_consumers(active_consumers, 'total_consume_count_from_start'),
            'all_consumers_total_consume_count_from_start_fail':_sum_filed_from_active_consumers(active_consumers, 'total_consume_count_from_start_fail'),
        }
        return params_and_active_consumers

    
    def get_one_queue_time_series_data(self,start_ts=None,end_ts=None,curve_samples_count=None):
        res = self.redis_db_frame.zrangebyscore(
            RedisKeys.gen_funboost_queue_time_series_data_key_by_queue_name(self.queue_name),
            max(float(start_ts or 0),self.timestamp() - 86400) ,float(end_ts or -1),withscores=True)
        # print(res)
        series_data_all= [{'report_data':Serialization.to_dict(item[0]),'report_ts':item[1]} for item in res]
        if curve_samples_count is None:
            return series_data_all
        
        # 曲线采样数量
        total_count = len(series_data_all)
        if total_count <= curve_samples_count:
            # 如果原始数据量小于等于需要的样本数，直接返回全部数据
            return series_data_all
        
        # 计算采样步长
        step = total_count / curve_samples_count
        sampled_data = []
        
        # 按照步长进行采样
        for i in range(curve_samples_count):
            index = int(i * step)
            if index < total_count:
                sampled_data.append(series_data_all[index])
        
        return sampled_data

    def deprecate_queue(self):
        """
        废弃队列 - 从 Redis 中移除队列名
        1. 从 funboost_all_queue_names set 中移除
        2. 从 funboost.project_name:{project_name} set 中移除
        """
        # 从所有队列名 set 中移除
        self.redis_db_frame.srem(RedisKeys.FUNBOOST_ALL_QUEUE_NAMES, self.queue_name)
        # 从项目队列名 set 中移除
        self.redis_db_frame.srem(RedisKeys.gen_funboost_project_name_key(self.care_project_name), self.queue_name)

    
 

       


if __name__ == '__main__':
    CareProjectNameEnv.set('test_project1')
    print(Serialization.to_json_str(QueuesConusmerParamsGetter().get_queues_params_and_active_consumers()))
    print(Serialization.to_json_str(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name()))
    # QueuesConusmerParamsGetter().cycle_get_queues_params_and_active_consumers_and_report()
    print(SingleQueueConusmerParamsGetter('queue_test_g03t').get_one_queue_time_series_data(1749617883,1749621483))
   


    print(SingleQueueConusmerParamsGetter('test_funboost_faas_queue').get_one_queue_params_and_active_consumers())
    
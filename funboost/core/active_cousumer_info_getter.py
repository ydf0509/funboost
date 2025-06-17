import json
import threading
import time
import typing
import uuid

from pydantic import main

from funboost.utils.redis_manager import RedisMixin

from funboost.core.loggers import FunboostFileLoggerMixin,nb_log_config_default
from funboost.core.serialization import Serialization
from funboost.constant import RedisKeys

class ActiveCousumerProcessInfoGetter(RedisMixin, FunboostFileLoggerMixin):
    """

    获取分布式环境中的消费进程信息。
    使用这里面的4个方法需要相应函数的@boost装饰器设置 is_send_consumer_hearbeat_to_redis=True，这样会自动发送活跃心跳到redis。否则查询不到该函数的消费者进程信息。
    要想使用消费者进程信息统计功能，用户无论使用何种消息队列中间件类型，用户都必须安装redis，并在 funboost_config.py 中配置好redis链接信息
    """

    def _get_all_hearbeat_info_by_redis_key_name(self, redis_key):
        results = self.redis_db_frame.smembers(redis_key)
        # print(type(results))
        # print(results)
        # 如果所有机器所有进程都全部关掉了，就没办法还剩一个线程执行删除了，这里还需要判断一次15秒。
        active_consumers_processor_info_list = []
        for result in results:
            result_dict = json.loads(result)
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

    def get_all_queue_names(self):
        return self.redis_db_frame.smembers(RedisKeys.FUNBOOST_ALL_QUEUE_NAMES)
    
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



class QueueConusmerParamsGetter(RedisMixin, FunboostFileLoggerMixin):

    def get_queue_params(self):
        queue__consumer_params_map  = self.redis_db_frame.hgetall('funboost_queue__consumer_parmas')
        return {k:Serialization.to_dict(v)  for k,v in queue__consumer_params_map.items()}

    def get_pause_flag(self):
        queue__pause_map = self.redis_db_frame.hgetall(RedisKeys.REDIS_KEY_PAUSE_FLAG)
        return {k:int(v)  for k,v in queue__pause_map.items()}

    def get_msg_num(self,ignore_report_ts=False):
        queue__msg_count_info_map = self.redis_db_frame.hgetall(RedisKeys.QUEUE__MSG_COUNT_MAP)
        queue__msg_count_dict = {}
        for queue_name,info_json in queue__msg_count_info_map.items():
            info_dict = json.loads(info_json)
            if ignore_report_ts or (info_dict['report_ts'] > time.time() - 15 and info_dict['last_get_msg_num_ts'] > time.time() - 1200):
                queue__msg_count_dict[queue_name] = info_dict['msg_num_in_broker']
        return queue__msg_count_dict

    @staticmethod
    def _sum_filed_from_active_consumers(active_consumers:typing.List[dict],filed:str):
        s = 0
        for c in active_consumers:
            # print(c)
            if c[filed]:
                # print(c[filed])
                s+=c[filed]
        return s
    
    def get_queues_history_run_count(self,):
        return self.redis_db_frame.hgetall(RedisKeys.FUNBOOST_QUEUE__RUN_COUNT_MAP)
    
    def get_queues_history_run_fail_count(self,):
        return self.redis_db_frame.hgetall(RedisKeys.FUNBOOST_QUEUE__RUN_FAIL_COUNT_MAP)
    
    def get_queue_params_and_active_consumers(self):
        queue__active_consumers_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name()

        # queue_name_list = list(queue__active_consumers_map.keys())
        queue__history_run_count_map = self.get_queues_history_run_count()
        queue__history_run_fail_count_map = self.get_queues_history_run_fail_count()

        queue__consumer_params_map  = self.get_queue_params()
        queue__pause_map = self.get_pause_flag()
        queue__msg_count_dict = self.get_msg_num(ignore_report_ts=True)
        queue_params_and_active_consumers = {}

        for queue, consumer_params in  queue__consumer_params_map.items():
            
            active_consumers = queue__active_consumers_map.get(queue, [])
            # print(queue,active_consumers)
            all_consumers_last_x_s_execute_count = self._sum_filed_from_active_consumers(active_consumers,'last_x_s_execute_count')
            all_consumers_last_x_s_execute_count_fail = self._sum_filed_from_active_consumers(active_consumers, 'last_x_s_execute_count_fail')
            all_consumers_last_x_s_total_cost_time = self._sum_filed_from_active_consumers(active_consumers, 'last_x_s_total_cost_time')
            all_consumers_last_x_s_avarage_function_spend_time = round( all_consumers_last_x_s_total_cost_time / all_consumers_last_x_s_execute_count,3) if all_consumers_last_x_s_execute_count else None
            
            all_consumers_total_consume_count_from_start = self._sum_filed_from_active_consumers(active_consumers, 'total_consume_count_from_start')
            all_consumers_total_cost_time_from_start =self._sum_filed_from_active_consumers(active_consumers, 'total_cost_time_from_start')
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
                'all_consumers_total_consume_count_from_start':self._sum_filed_from_active_consumers(active_consumers, 'total_consume_count_from_start'),
                'all_consumers_total_consume_count_from_start_fail':self._sum_filed_from_active_consumers(active_consumers, 'total_consume_count_from_start_fail'),
            }
        return queue_params_and_active_consumers
    
    def cycle_get_queue_params_and_active_consumers_and_report(self,daemon=False):
        time_interval = 10
        report_uuid = str(uuid.uuid4()) 
        def _inner():
            while True:
                t_start = time.time()
                # 这个函数确保只有一个地方在上报数据，避免重复上报
                report_ts = self.timestamp()
                redis_report_uuid_ts_str = self.redis_db_frame.get(RedisKeys.FUNBOOST_LAST_GET_QUEUE_PARAMS_AND_ACTIVE_CONSUMERS_AND_REPORT__UUID_TS, )
                if redis_report_uuid_ts_str:
                    redis_report_uuid_ts = Serialization.to_dict(redis_report_uuid_ts_str)
                    if redis_report_uuid_ts['report_uuid'] != report_uuid and redis_report_uuid_ts['report_ts'] > report_ts - time_interval - 10 :
                        continue
                self.redis_db_frame.set(RedisKeys.FUNBOOST_LAST_GET_QUEUE_PARAMS_AND_ACTIVE_CONSUMERS_AND_REPORT__UUID_TS,
                                        Serialization.to_json_str({'report_uuid':report_uuid, 'report_ts':report_ts}))
                
                queue_params_and_active_consumers = self.get_queue_params_and_active_consumers()
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
                self.logger.info(f'上报时序数据耗时 {time.time() - t_start} 秒')

                time.sleep(time_interval)
        threading.Thread(target=_inner, daemon=daemon).start()

    def get_time_series_data_by_queue_name(self,queue_name,start_ts=None,end_ts=None):
        res = self.redis_db_frame.zrangebyscore(
            RedisKeys.gen_funboost_queue_time_series_data_key_by_queue_name(queue_name),
            max(float(start_ts or 0),self.timestamp() - 86400) ,float(end_ts or -1),withscores=True)
        # print(res)
        return [{'report_data':Serialization.to_dict(item[0]),'report_ts':item[1]} for item in res]

if __name__ == '__main__':
    # print(Serialization.to_json_str(QueueConusmerParamsGetter().get_queue_params_and_active_consumers()))
    # QueueConusmerParamsGetter().cycle_get_queue_params_and_active_consumers_and_report()
    print(QueueConusmerParamsGetter().get_time_series_data_by_queue_name('queue_test_g03t',1749617883,1749621483))
    # print(QueueConusmerParamsGetter().get_time_series_data_by_queue_name('queue_test_g03t',))
    
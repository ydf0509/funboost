import json
import typing

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
        redis_key = f'funboost_hearbeat_queue__dict:{queue_name}'
        return self._get_all_hearbeat_info_by_redis_key_name(redis_key)

    def get_all_hearbeat_info_by_ip(self, ip=None) -> typing.List[typing.Dict]:
        """
        根据机器的ip查询有哪些活跃的消费者进程，ip不传参就查本机ip使用funboost框架运行了哪些消费进程，传参则查询任意机器的消费者进程信息。
        返回结果的格式和上面的 get_all_hearbeat_dict_by_queue_name 方法相同。
        """
        ip = ip or nb_log_config_default.computer_ip
        redis_key = f'funboost_hearbeat_server__dict:{ip}'
        return self._get_all_hearbeat_info_by_redis_key_name(redis_key)

    def _get_all_hearbeat_info_partition_by_redis_key_prefix(self, redis_key_prefix):
        keys = self.redis_db_frame.scan(0, f'{redis_key_prefix}*', count=10000)[1]
        infos_map = {}
        for key in keys:
            infos = self.redis_db_frame.smembers(key)
            dict_key = key.replace(redis_key_prefix, '')
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
        infos_map = self._get_all_hearbeat_info_partition_by_redis_key_prefix('funboost_hearbeat_queue__dict:')
        self.logger.info(f'获取所有队列对应的活跃消费者进程信息，按队列名划分，结果是 {json.dumps(infos_map, indent=4)}')
        return infos_map

    def get_all_hearbeat_info_partition_by_ip(self) -> typing.Dict[typing.AnyStr, typing.List[typing.Dict]]:
        """获取所有机器ip对应的活跃消费者进程信息，按机器ip划分,不需要传入机器ip，自动扫描redis键。请不要在 funboost_config.py 的redis 指定的db中放太多其他业务的缓存键值对 """
        infos_map = self._get_all_hearbeat_info_partition_by_redis_key_prefix('funboost_hearbeat_server__dict:')
        self.logger.info(f'获取所有机器ip对应的活跃消费者进程信息，按机器ip划分，结果是 {json.dumps(infos_map, indent=4)}')
        return infos_map



class QueueConusmerParamsGetter(RedisMixin, FunboostFileLoggerMixin):

    def get_queue_params(self):
        queue__consumer_params_map  = self.redis_db_frame.hgetall('funboost_queue__consumer_parmas')
        return {k:Serialization.to_dict(v)  for k,v in queue__consumer_params_map.items()}

    def get_pause_flag(self):
        queue__pause_map = self.redis_db_frame.hgetall(RedisKeys.REDIS_KEY_PAUSE_FLAG)
        return {k:int(v)  for k,v in queue__pause_map.items()}
    
    def get_queue_params_and_active_consumers(self):
        queue__active_consumers_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name()
        queue__consumer_params_map  = self.get_queue_params()
        queue__pause_map = self.get_pause_flag()
        queue_params_and_active_consumers = {}
        for queue, consumer_params in  queue__consumer_params_map.items():
            queue_params_and_active_consumers[queue] = {
            'queue_params':consumer_params,
            'active_consumers':queue__active_consumers_map.get(queue,[]),
            'pause_flag':queue__pause_map.get(queue,-1),
            }
        return queue_params_and_active_consumers


if __name__ == '__main__':
    print(Serialization.to_json_str(QueueConusmerParamsGetter().get_queue_params_and_active_consumers()))

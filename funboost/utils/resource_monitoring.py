# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/9/18 0018 10:29
import datetime
import json
import socket
import sys
import threading
import time
import psutil
from funboost.utils import LoggerLevelSetterMixin, LoggerMixin, decorators
from funboost.utils.mongo_util import MongoMixin

"""
# psutil.virtual_memory()
svmem = namedtuple(
    'svmem', ['total', 'available', 'percent', 'used', 'free',
              'active', 'inactive', 'buffers', 'cached', 'shared', 'slab'])
# psutil.disk_io_counters()
sdiskio = namedtuple(
    'sdiskio', ['read_count', 'write_count',
                'read_bytes', 'write_bytes',
                'read_time', 'write_time',
                'read_merged_count', 'write_merged_count',
                'busy_time'])
# psutil.Process().open_files()
popenfile = namedtuple(
    'popenfile', ['path', 'fd', 'position', 'mode', 'flags'])
# psutil.Process().memory_info()
pmem = namedtuple('pmem', 'rss vms shared text lib data dirty')
# psutil.Process().memory_full_info()
pfullmem = namedtuple('pfullmem', pmem._fields + ('uss', 'pss', 'swap'))
# psutil.Process().memory_maps(grouped=True)
pmmap_grouped = namedtuple(
    'pmmap_grouped',
    ['path', 'rss', 'size', 'pss', 'shared_clean', 'shared_dirty',
     'private_clean', 'private_dirty', 'referenced', 'anonymous', 'swap'])
# psutil.Process().memory_maps(grouped=False)
pmmap_ext = namedtuple(
    'pmmap_ext', 'addr perms ' + ' '.join(pmmap_grouped._fields))
# psutil.Process.io_counters()
pio = namedtuple('pio', ['read_count', 'write_count',
                         'read_bytes', 'write_bytes',
                         'read_chars', 'write_chars'])


p = psutil.Process()
print(p)
print(p.memory_info()[0])

print(p.cpu_percent(interval=1))
print(p.cpu_percent(interval=1))

print(psutil.cpu_percent(1,percpu=True))
print(psutil.virtual_memory())

"""


class ResourceMonitor(LoggerMixin, LoggerLevelSetterMixin, MongoMixin):
    # ResourceMonitor(is_save_info_to_mongo=True).set_log_level(20).start_build_info_loop_on_daemon_thread(60)
    cpu_count = psutil.cpu_count()
    host_name = socket.gethostname()

    def __init__(self, process=psutil.Process(), is_save_info_to_mongo=False, mongo_col='default'):
        self.process = process
        self.logger.setLevel(20)
        self.all_info = {}
        self._is_save_info_to_mongo = is_save_info_to_mongo
        self._mongo_col = mongo_col

    @staticmethod
    def divide_1m(value):
        return round(value / (1024 * 1024), 2)

    def get_current_process_memory(self) -> float:
        result = self.process.memory_info()
        self.logger.debug(result)
        return self.divide_1m(result[0])

    def get_current_process_cpu(self):
        result = self.process.cpu_percent(interval=1)
        self.logger.debug(result)
        return result

    def get_os_cpu_percpu(self):
        result = psutil.cpu_percent(1, percpu=True)
        self.logger.debug(result)
        return result

    def get_os_cpu_totalcpu(self):
        result = round(psutil.cpu_percent(1, percpu=False) * self.cpu_count, 2)
        self.logger.debug(result)
        return result

    def get_os_cpu_avaragecpu(self):
        result = psutil.cpu_percent(1, percpu=False)
        self.logger.debug(result)
        return result

    def get_os_virtual_memory(self) -> dict:
        memory_tuple = psutil.virtual_memory()
        self.logger.debug(memory_tuple)
        return {
            'total': self.divide_1m(memory_tuple[0]),
            'available': self.divide_1m(memory_tuple[1]),
            'used': self.divide_1m(memory_tuple[3]),
        }

    def get_os_net_info(self):
        result1 = psutil.net_io_counters(pernic=False)
        time.sleep(1)
        result2 = psutil.net_io_counters(pernic=False)
        speed_dict = dict()
        speed_dict['up_speed'] = self.divide_1m(result2[0] - result1[0])
        speed_dict['down_speed'] = self.divide_1m(result2[1] - result1[1])
        speed_dict['packet_sent_speed'] = result2[2] - result1[2]
        speed_dict['packet_recv_speed'] = result2[3] - result1[3]
        self.logger.debug(result1)
        return speed_dict

    def get_all_info(self):
        self.all_info = {
            'host_name': self.host_name,
            'process_id': self.process.pid,
            'process_name': self.process.name(),
            'process_script': sys.argv[0],
            'memory': self.get_current_process_memory(),
            'cpu': self.get_current_process_cpu(),
            'os_memory': self.get_os_virtual_memory(),
            'os_cpu': {'cpu_count': self.cpu_count, 'total_cpu': self.get_os_cpu_totalcpu(), 'avarage_cpu': self.get_os_cpu_avaragecpu()},
            'net_info': self.get_os_net_info()
        }
        # nb_print(json.dumps(self.all_info,indent=4))
        self.logger.info(json.dumps(self.all_info, indent=4))
        if self._is_save_info_to_mongo:
            self.all_info.update({'update_time': datetime.datetime.now()})
            self.mongo_client.get_database('process_info').get_collection(self._mongo_col).insert_one(self.all_info)
        return self.all_info

    def start_build_info_loop(self, interval=60, ):
        decorators.keep_circulating(interval)(self.get_all_info)()

    def start_build_info_loop_on_daemon_thread(self, interval=60, ):
        threading.Thread(target=self.start_build_info_loop, args=(interval,), daemon=True).start()

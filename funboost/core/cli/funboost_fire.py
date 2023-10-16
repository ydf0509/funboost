import copy
import importlib
import sys
import typing
from os import PathLike

from funboost import get_booster
from funboost.core.cli.discovery_boosters import BoosterDiscovery
from funboost.core.global_boosters import get_all_queues
from funboost.utils.ctrl_c_end import ctrl_c_recv

env_dict = {'project_root_path': None}


# noinspection PyMethodMayBeStatic
class BoosterFire(object):
    def __init__(self, import_modules_str: str = None,
                 booster_dirs_str: str = None, max_depth=1, py_file_re_str: str = None, project_root_path=None):
        """
        :param project_root_path : 用户项目根目录
        :param import_modules_str:
        :param booster_dirs_str: 扫描@boost函数所在的目录，多个目录用,隔开
        :param max_depth: 扫描目录代码层级
        :param py_file_re_str: python文件的正则， 例如  tasks.py那么就不自动import其他名字的python模块
        """
        project_root_path = env_dict['project_root_path']
        print(f'project_root_path is :{project_root_path} ,请确认')
        if project_root_path is None:
            raise Exception('project_root_path is none')
        loc = copy.copy(locals())
        for k, v in loc.items():
            print(f'{k} : {v}')
        sys.path.insert(1, str(project_root_path))
        self.import_modules_str = import_modules_str
        if import_modules_str:
            for m in self.import_modules_str.split(','):
                importlib.import_module(m)  # 发现@boost函数
        if booster_dirs_str and project_root_path:
            boost_dirs = booster_dirs_str.split(',')
            BoosterDiscovery(project_root_path=str(project_root_path), booster_dirs=boost_dirs,
                             max_depth=max_depth, py_file_re_str=py_file_re_str).auto_discovery()  # 发现@boost函数

    def show_all_queues(self):
        """显示扫描到的所有queue name"""
        print(f'get_all_queues: {get_all_queues()}')

    def clear(self, *queue_names: str):
        """
        清空多个queue ; 例子: clear test_cli1_queue1  test_cli1_queue2   # 清空2个消息队列消息队列
        """

        for queue_anme in queue_names:
            get_booster(queue_anme).clear()

    def push(self, queue_anme, *args, **kwargs):
        """push发布消息到消息队列 ;
        例子: 假设函数是 def  add(x,y)  队列名是 add_queue , 发布 1 + 2求和;
        push add_queue 1 2;
        或者 push add_queue --x=1 --y=2;
        或者 push add_queue -x 1 -y 2;
        """
        get_booster(queue_anme).push(*args, **kwargs)

    def publish(self, queue_anme, msg):
        """publish发布消息到消息队列;
           假设函数是 def  add(x,y)  队列名是 add_queue , 发布 1 + 2求和;
           publish add_queue "{'x':1,'y':2}"
        """

        get_booster(queue_anme).publish(msg)

    def consume(self, *queue_names: str):
        """
        启动多个消息队列名的消费;
        例子: consume queue1 queue2
        """
        for queue_anme in queue_names:
            get_booster(queue_anme).consume()
        ctrl_c_recv()

    def multi_process_consume(self, **queue_name__process_num):
        """
        使用多进程启动消费,每个队列开启多个单独的进程消费;
        例子:  m_consume --queue1=2 --queue2=3    # queue1启动两个单独进程消费  queue2 启动3个单独进程消费
        """
        for queue_anme, process_num in queue_name__process_num.items():
            get_booster(queue_anme).multi_process_consume(process_num)
        ctrl_c_recv()

    m_consume = multi_process_consume

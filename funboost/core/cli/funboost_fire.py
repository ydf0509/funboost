import copy
import importlib
import sys
import typing
from os import PathLike

from funboost.core.booster import BoostersManager
from funboost.core.cli.discovery_boosters import BoosterDiscovery
from funboost.utils.ctrl_c_end import ctrl_c_recv

env_dict = {'project_root_path': None}


# noinspection PyMethodMayBeStatic
class BoosterFire(object):
    def __init__(self, import_modules_str: str = None,
                 booster_dirs_str: str = None, max_depth=1, py_file_re_str: str = None, project_root_path=None):
        """
        :param project_root_path : 用户项目根目录
        :param import_modules_str:
        :param booster_dirs_str: 扫描@boost函数所在的目录，如果多个目录用,隔开
        :param max_depth: 扫描目录代码层级
        :param py_file_re_str: python文件的正则， 例如  tasks.py那么就不自动import其他名字的python模块
        """
        project_root_path = env_dict['project_root_path'] or project_root_path
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
        print(f'get_all_queues: {BoostersManager.get_all_queues()}')
        return self

    def clear(self, *queue_names: str):
        """
        清空多个queue ; 例子: clear test_cli1_queue1  test_cli1_queue2   # 清空2个消息队列消息队列
        """

        for queue_name in queue_names:
            BoostersManager.get_booster(queue_name).clear()
        return self

    def push(self, queue_name, *args, **kwargs):
        """push发布消息到消息队列 ;
        例子: 假设函数是 def  add(x,y)  队列名是 add_queue , 发布 1 + 2求和;
        push add_queue 1 2;
        或者 push add_queue --x=1 --y=2;
        或者 push add_queue -x 1 -y 2;
        """
        BoostersManager.push(queue_name,*args, **kwargs)
        return self

    def __str__(self):
        # print('over')  # 这行重要,否则命令行链式调用无法自动结束
        return ''

    def publish(self, queue_name, msg):
        """publish发布消息到消息队列;
           假设函数是 def  add(x,y)  队列名是 add_queue , 发布 1 + 2求和;
           publish add_queue "{'x':1,'y':2}"
        """

        BoostersManager.publish(queue_name,msg)
        return self

    def consume_queues(self, *queue_names: str):
        """
        启动多个消息队列名的消费;
        例子: consume queue1 queue2
        """
        BoostersManager.consume_queues(*queue_names)

    consume = consume_queues

    def consume_all_queues(self, ):
        """
        启动所有消息队列名的消费,无需指定队列名;
        例子: consume_all_queues
        """
        BoostersManager.consume_all_queues()

    consume_all = consume_all_queues

    def multi_process_consume_queues(self, **queue_name__process_num):
        """
        使用多进程启动消费,每个队列开启多个单独的进程消费;
        例子:  mp_consume --queue1=2 --queue2=3    # queue1启动两个单独进程消费  queue2 启动3个单独进程消费
        """
        BoostersManager.multi_process_consume_queues(**queue_name__process_num)

    mp_consume = multi_process_consume_queues

    def multi_process_consume_all_queues(self, process_num=1):
        """
        启动所有消息队列名的消费,无需指定队列名,每个队列启动n个单独的消费进程;
        例子: multi_process_consume_all_queues 2
        """
        BoostersManager.multi_process_consume_all_queues(process_num)

    mp_consume_all = multi_process_consume_all_queues

    def pause(self, *queue_names: str):
        """
        暂停多个消息队列名的消费;
        例子: pause queue1 queue2
        """
        for queue_name in queue_names:
            BoostersManager.get_booster(queue_name).pause()

    def continue_consume(self, *queue_names: str):
        """
        继续多个消息队列名的消费;
        例子: continue_consume queue1 queue2
        """
        for queue_name in queue_names:
            BoostersManager.get_booster(queue_name).continue_consume()
    
    def start_funboost_web_manager(self):
        """
        启动funboost web管理器;
        例子: start_funboost_web_manager
        """
        from funboost.funboost_web_manager.app import start_funboost_web_manager
        start_funboost_web_manager()

    start_web = start_funboost_web_manager

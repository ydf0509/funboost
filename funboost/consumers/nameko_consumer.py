# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/8 0008 13:32
from multiprocessing import Process

import threading

import typing
from funboost.constant import BrokerEnum


from nameko.containers import ServiceContainer
from nameko.rpc import rpc
from nameko.runners import ServiceRunner

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers.nameko_publisher import get_nameko_config

all_queue_name__nameko_service_cls_map = {}


class NamekoConsumer(AbstractConsumer, ):
    """
    nameko作为中间件实现的。
    """


    def custom_init(self):
        try:
            from funboost.concurrent_pool.custom_evenlet_pool_executor import check_evenlet_monkey_patch
            check_evenlet_monkey_patch()
        except Exception as e:
            self.logger.critical('nameko 必须使用eventlet 并发，并且eventlet包打猴子补丁')
            raise e

        class MyService:
            name = self.queue_name

            @rpc
            def call(this, *args, **kwargs):
                return self.consuming_function(*args, **kwargs)

        all_queue_name__nameko_service_cls_map[self.queue_name] = MyService

    def _shedual_task(self):
        container = ServiceContainer(all_queue_name__nameko_service_cls_map[self.queue_name], config=get_nameko_config())
        container.start()
        container.wait()

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        pass



def batch_start_nameko_consumers(boost_fun_list: typing.List):
    runner = ServiceRunner(config=get_nameko_config())
    for boost_fun in boost_fun_list:
        runner.add_service(all_queue_name__nameko_service_cls_map[boost_fun.queue_name])
    runner.start()
    runner.wait()


def batch_start_nameko_service_in_new_thread(boost_fun_list: typing.List):
    threading.Thread(target=batch_start_nameko_consumers, args=(boost_fun_list,)).start()


def batch_start_nameko_service_in_new_process(boost_fun_list: typing.List, process_num=1):
    for i in range(process_num):
        Process(target=batch_start_nameko_consumers, args=(boost_fun_list,)).start()

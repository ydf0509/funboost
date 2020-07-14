from multiprocessing import Process
# noinspection PyUnresolvedReferences
from typing import List

import apscheduler
from function_scheduling_distributed_framework.set_frame_config import patch_frame_config, show_frame_config

# import frame_config
from function_scheduling_distributed_framework.consumers.base_consumer import ExceptionForRequeue, ExceptionForRetry, \
    AbstractConsumer, ConsumersManager, FunctionResultStatusPersistanceConfig
from function_scheduling_distributed_framework.publishers.base_publisher import PriorityConsumingControlConfig
from function_scheduling_distributed_framework.factories.publisher_factotry import get_publisher
from function_scheduling_distributed_framework.factories.consumer_factory import get_consumer
# noinspection PyUnresolvedReferences
from function_scheduling_distributed_framework.utils import nb_print, patch_print, LogManager


def run_many_consumer_by_init_params(consumer_init_params_list: List[dict]):
    for consumer_init_params in consumer_init_params_list:
        get_consumer(**consumer_init_params).start_consuming_message()
    ConsumersManager.join_all_consumer_shedual_task_thread()


def run_many_consumer_with_multi_process(consumer_init_params_list: List[dict], process_num=1):
    """
     此处传init参数而不是conusmer对象本身，是由于一些属性的类型不可以被picke序列化，在windows中开多进程会出错。
     run_many_consumer_with_multi_process([consumer1.init_params,consumer2.init_params],4)
    """
    [Process(target=run_many_consumer_by_init_params, args=(consumer_init_params_list,)).start() for _ in range(process_num)]

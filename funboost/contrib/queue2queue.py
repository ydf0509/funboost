import os
import time
import typing
from multiprocessing import Process
import logging
import threading

from funboost import get_publisher, get_consumer, BrokerEnum, wait_for_possible_has_finish_all_tasks_by_conusmer_list
from funboost.core.func_params_model import PublisherParams, BoosterParams

""" 将队列中的消息移到另一个队列名中，例如把死信队列的消息移到正常队列。"""


def consume_and_push_to_another_queue(source_queue_name: str, source_broker_kind: str,
                                      target_queue_name: str, target_broker_kind: str,
                                      log_level: int = logging.DEBUG,
                                      exit_script_when_finish=False):
    """ 将队列中的消息移到另一个队列名中，例如把死信队列的消息移到正常队列。"""
    if source_queue_name == target_queue_name and source_broker_kind == target_broker_kind:
        raise ValueError('不能转移消息到当前队列名，否则死循环')

    target_publisher = get_publisher(publisher_params=PublisherParams(queue_name=target_queue_name, broker_kind=target_broker_kind, log_level=log_level))
    msg_cnt = 0
    msg_cnt_lock = threading.Lock()

    def _task_fun(**kwargs):
        # print(kwargs)
        nonlocal msg_cnt
        target_publisher.publish(kwargs)
        with msg_cnt_lock:
            msg_cnt += 1

    source_consumer = get_consumer(boost_params=BoosterParams(queue_name=source_queue_name, broker_kind=source_broker_kind, consuming_function=_task_fun, log_level=log_level))
    source_consumer._set_do_not_delete_extra_from_msg()
    source_consumer.start_consuming_message()
    if exit_script_when_finish:
        source_consumer.wait_for_possible_has_finish_all_tasks(2)
        print(f'消息转移完成，结束脚本,累计从 {source_queue_name} 转移消息到 {target_queue_name} 队列 总数是 {msg_cnt}')
        os._exit(888)  # 结束脚本


def _consume_and_push_to_another_queue_for_multi_process(source_queue_name: str, source_broker_kind: str,
                                                         target_queue_name: str, target_broker_kind: str,
                                                         log_level: int = logging.DEBUG,
                                                         ):
    consume_and_push_to_another_queue(source_queue_name, source_broker_kind, target_queue_name, target_broker_kind, log_level, False)
    while 1:
        time.sleep(3600)


def multi_prcocess_queue2queue(source_target_list: typing.List[typing.List],
                               log_level: int = logging.DEBUG, exit_script_when_finish=False, n=1):
    """
    转移多个队列，并使用多进程。
    :param source_target_list:  入参例如  [['test_queue77h5', BrokerEnum.RABBITMQ_AMQPSTORM, 'test_queue77h4', BrokerEnum.RABBITMQ_AMQPSTORM],['test_queue77h6', BrokerEnum.RABBITMQ_AMQPSTORM, 'test_queue77h7', BrokerEnum.REDIS]]
    :param log_level:
    :param exit_script_when_finish:
    :param n:
    :return:
    """
    source_consumer_list = []
    for (source_queue_name, source_broker_kind, target_queue_name, target_broker_kind) in source_target_list:
        for i in range(n):
            Process(target=_consume_and_push_to_another_queue_for_multi_process,
                    args=(source_queue_name, source_broker_kind, target_queue_name, target_broker_kind, log_level)).start()
        if exit_script_when_finish:
            def _fun():
                pass

            source_consumer = get_consumer(boost_params=BoosterParams(queue_name=source_queue_name, broker_kind=source_broker_kind, consuming_function=_fun,
                                                                      log_level=log_level))
            source_consumer_list.append(source_consumer)
    if exit_script_when_finish:
        wait_for_possible_has_finish_all_tasks_by_conusmer_list(consumer_list=source_consumer_list, minutes=2)
        for (source_queue_name, source_broker_kind, target_queue_name, target_broker_kind) in source_target_list:
            print(f'{source_queue_name}  转移到 {target_queue_name} 消息转移完成，结束脚本')
        os._exit(999)  #


if __name__ == '__main__':
    # 一次转移一个队列，使用单进程
    consume_and_push_to_another_queue('test_queue77h3_dlx', BrokerEnum.REDIS_PRIORITY,
                                      'test_queue77h3', BrokerEnum.REDIS_PRIORITY,
                                      log_level=logging.INFO, exit_script_when_finish=True)

    # 转移多个队列，并使用多进程。
    multi_prcocess_queue2queue([['test_queue77h5', BrokerEnum.RABBITMQ_AMQPSTORM, 'test_queue77h4', BrokerEnum.RABBITMQ_AMQPSTORM]],
                               log_level=logging.INFO, exit_script_when_finish=True, n=6)

import os
import logging
import threading

from funboost import get_publisher, get_consumer,BrokerEnum


def consume_and_push_to_another_queue(source_queue_name: str, source_broker_kind: int,
                                      target_queue_name: str, target_broker_kind: int,
                                      log_level_int: int = logging.DEBUG,
                                      exit_script_when_finish=False):
    """ 将队列中的消息移到另一个队列名中，例如把死信队列的消息移到正常队列。"""
    if source_queue_name == target_queue_name and source_broker_kind == target_broker_kind:
        raise ValueError('不能转移消息到当前队列名，否则死循环')

    target_publisher = get_publisher(target_queue_name, broker_kind=target_broker_kind, log_level_int=log_level_int)
    msg_cnt = 0
    msg_cnt_lock = threading.Lock()

    def _task_fun(**kwargs):
        # print(kwargs)
        nonlocal msg_cnt
        target_publisher.publish(kwargs)
        with msg_cnt_lock:
            msg_cnt += 1

    source_consumer = get_consumer(source_queue_name, broker_kind=source_broker_kind, consuming_function=_task_fun, log_level=log_level_int)
    source_consumer.set_do_not_delete_extra_from_msg()
    source_consumer.start_consuming_message()
    source_consumer.wait_for_possible_has_finish_all_tasks(2)
    if exit_script_when_finish:
        print(f'消息转移完成，结束脚本,累计从 {source_queue_name} 转移消息到 {target_queue_name} 队列 总数是 {msg_cnt}')
        os._exit(888)  # 结束脚本


if __name__ == '__main__':
    consume_and_push_to_another_queue('test_queue77h3_dlx2', BrokerEnum.RABBITMQ_AMQPSTORM,
                                      'test_queue77h3_dlx3', BrokerEnum.RABBITMQ_AMQPSTORM,
                                      log_level_int=logging.INFO, exit_script_when_finish=True)

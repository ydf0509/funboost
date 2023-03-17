import logging
from funboost import get_publisher, get_consumer, wait_for_possible_has_finish_all_tasks_by_conusmer_list


def consume_and_push_to_another_queue(source_queue_name: str, source_broker_kind: int, target_queue_name: str, target_broker_kind: int, log_level_int: int = logging.DEBUG):
    """ 将队列中的消息移到另一个队列名中，例如把死信队列的消息移到正常队列。"""
    target_publisher = get_publisher(target_queue_name, broker_kind=target_broker_kind, log_level_int=log_level_int)

    def _task_fun(**kwargs):
        # print(kwargs)
        target_publisher.publish(kwargs)

    source_consumer = get_consumer(source_queue_name, broker_kind=source_broker_kind, consuming_function=_task_fun, log_level=log_level_int)
    source_consumer.set_do_not_delete_extra_from_msg()
    source_consumer.start_consuming_message()
    source_consumer.wait_for_possible_has_finish_all_tasks()


if __name__ == '__main__':
    consume_and_push_to_another_queue('test_queue77h3_dlx2', 0, 'test_queue77h3_dlx3', 0, log_level_int=logging.INFO)

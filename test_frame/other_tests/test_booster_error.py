import time

from funboost import boost, BrokerEnum, PriorityConsumingControlConfig


@boost('ticket_query', broker_kind=BrokerEnum.REDIS_ACK_ABLE, concurrent_num=5)
def ticket_query(task_id, url: str, times):
    time.sleep(10)
    print('tick_query')

@boost('task', broker_kind=BrokerEnum.REDIS_ACK_ABLE, concurrent_num=5)
def task(task_id, url: str, times):
    time.sleep(10)
    print('task')

if __name__ == "__main__":
    ticket_query.publish({'task_id':111,'url':'url222','times':33}, priority_control_config=PriorityConsumingControlConfig(countdown=50))
    task.multi_process_consume(process_num=2)
    ticket_query.consume()
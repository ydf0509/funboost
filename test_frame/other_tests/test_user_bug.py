
from funboost import BoosterParams, boost,run_forever,PriorityConsumingControlConfig,BrokerEnum,Booster


@BoosterParams(
    queue_name="aaa_queue2",
    concurrent_num=1,
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    log_level=20,
    should_check_publish_func_params=False,
# delay_task_apscheduler_jobstores_kind='memory',
)
def aaa(msg):
    print(f'aaaa: {msg}')


@Booster(BoosterParams(
        queue_name="bbb_queue2",
        concurrent_num=1,
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        log_level=20,
        should_check_publish_func_params=False,
# delay_task_apscheduler_jobstores_kind='memory',
    ))
def bbb(msg):
    print(f'bbbb:  {msg}')


@BoosterParams(
        queue_name="ccc_queue2",
        concurrent_num=1,
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        log_level=20,
        should_check_publish_func_params=False,
        # delay_task_apscheduler_jobstores_kind='memory',
    )
def ccc(msg):
    print(f'ccc:  {msg}')


if __name__ == '__main__':

    aaa.publish({'msg':'a队列的消息'},priority_control_config=PriorityConsumingControlConfig(countdown=10))
    bbb.publish({'msg':'b队列的消息'},priority_control_config=PriorityConsumingControlConfig(countdown=15))
    ccc.publish({'msg':'c队列的消息'},priority_control_config=PriorityConsumingControlConfig(countdown=20))

    aaa.consume()
    aaa.multi_process_consume(2)
    bbb.consume()
    ccc.consume()
    run_forever()













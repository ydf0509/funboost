
from funboost import BoosterParams, boost,run_forever,PriorityConsumingControlConfig,BrokerEnum


@BoosterParams(
    queue_name="aaa_queue",
    concurrent_num=1,
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    log_level=20,
    should_check_publish_func_params=False,
)
def aaa(msg):
    print(f'aaaa: {msg}')


@BoosterParams(
        queue_name="bbb_queue",
        concurrent_num=1,
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        log_level=20,
        should_check_publish_func_params=False,
    )
def bbb(msg):
    print(f'bbbb:  {msg}')


aaa.publish({'msg':'a队列的消息'},priority_control_config=PriorityConsumingControlConfig(countdown=10))
bbb.publish({'msg':'b队列的消息'},priority_control_config=PriorityConsumingControlConfig(countdown=20))

aaa.consume()
bbb.consume()
run_forever()

import asyncio

from funboost import boost, BrokerEnum, ConcurrentModeEnum, BoosterParams, ExceptionForRequeue, run_forever, ctrl_c_recv,fct

from PauseConsumer import PauseConsumer


# @boost(BoosterParams(queue_name='task_list', concurrent_mode=ConcurrentModeEnum.ASYNC, concurrent_num=100, qps=10,
#                      broker_kind=BrokerEnum.REDIS_ACK_ABLE, max_retry_times=0, consumer_override_cls=PauseConsumer))

@boost(BoosterParams(queue_name='task_list5', concurrent_mode=ConcurrentModeEnum.ASYNC, concurrent_num=100, qps=10,
                     broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM, max_retry_times=0, consumer_override_cls=PauseConsumer,
                     is_show_message_get_from_broker=True))
async def task_list(params):
    print("消费flag")

    
    

    print("让本机暂停消费")

    await asyncio.sleep(3)

    PauseConsumer.pause.set()

    # task_list.consumer._rp.channel.stop_consuming()
    # task_list.consumer._rp.channel.close()
    raise ExceptionForRequeue("重回队列")
    



async def main():
    for i in range(1):
        task_list.push(77)
    task_list.consume()


if __name__ == '__main__':
    asyncio.run(main())
    # run_forever()
    ctrl_c_recv()



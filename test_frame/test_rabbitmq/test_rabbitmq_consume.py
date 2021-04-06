from function_scheduling_distributed_framework import task_deco,BrokerEnum,run_consumer_with_multi_process

@task_deco('test_rabbit_queue',broker_kind=BrokerEnum.RABBITMQ_PIKA,qps=100,is_using_distributed_frequency_control=True)
def test_fun(x):
    print(x)

if __name__ == '__main__':
    run_consumer_with_multi_process(test_fun,4)
from function_scheduling_distributed_framework import task_deco,BrokerEnum

@task_deco('test_delay',broker_kind=BrokerEnum.REDIS_ACK_ABLE)
def f(x):
    print(x)

if __name__ == '__main__':
    f.consume()
import time
from function_scheduling_distributed_framework import task_deco,BrokerEnum

@task_deco('test_confirm_queue',broker_kind=BrokerEnum.REDIS_ACK_ABLE,qps=10,)
def f(x):
    print(f' 待消费 {x}')
    time.sleep(30)
    print(f'消费完成 {x}')


if __name__ == '__main__':
    f.consume()
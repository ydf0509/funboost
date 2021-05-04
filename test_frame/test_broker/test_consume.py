import time
import random
from function_scheduling_distributed_framework import task_deco,BrokerEnum,run_consumer_with_multi_process,ConcurrentModeEnum

@task_deco('test_queue_10',broker_kind=BrokerEnum.REDIS,qps=0,log_level=20,is_print_detail_exception=False)
def f(x,y):
    # if random.randint(1,110) == 10:
    #     raise ValueError('测试出错')
    print(f''' {x} + {y} = {x + y}''')
    return x + y


if __name__ == '__main__':
    # f.consume()
    run_consumer_with_multi_process(f,4)
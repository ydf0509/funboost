import time
import random
from function_scheduling_distributed_framework import task_deco,BrokerEnum,run_consumer_with_multi_process,ConcurrentModeEnum

@task_deco('20010',broker_kind=BrokerEnum.MQTT,qps=2,log_level=10,is_print_detail_exception=False,is_show_message_get_from_broker=False)
def f(x,y):
    # if random.randint(1,110) == 10:
    #     raise ValueError('测试出错')
    print(f''' {x} + {y} = {x + y}''')
    return x + y


if __name__ == '__main__':
    # f.consume()
    run_consumer_with_multi_process(f,1)
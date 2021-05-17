import time
import random
from function_scheduling_distributed_framework import task_deco,BrokerEnum,run_consumer_with_multi_process,ConcurrentModeEnum

@task_deco('test_queue66',broker_kind=BrokerEnum.HTTPSQS,qps=2,log_level=10,is_print_detail_exception=False,is_show_message_get_from_broker=False)
def f(x,y):
    print(f''' {x} + {y} = {x + y}''')
    return x + y


if __name__ == '__main__':
    # f.consume()
    run_consumer_with_multi_process(f,1)
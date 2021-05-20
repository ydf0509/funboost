import time
import random
from function_scheduling_distributed_framework import task_deco,BrokerEnum,run_consumer_with_multi_process

@task_deco('test_rabbit_queue7',broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM,qps=100,log_level=20)
def test_fun(x):
    # time.sleep(2.9)
    # sleep时间随机从0.1毫秒到5秒任意徘徊,最小耗时和最大耗时差距达到了5万倍。
    # 传统的恒定并发数量的线程池对未知的耗时任务且波动达到了5万倍，持续100次每秒的精确控频无能为力，
    # 但此框架只要简单设置一个qps就自动达到了这个目的。
    random_sleep = random.randrange(1,50000) / 10000
    time.sleep(random_sleep)
    print(x,random_sleep)

if __name__ == '__main__':
    run_consumer_with_multi_process(test_fun,1)
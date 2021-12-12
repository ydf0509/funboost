import time
import random
from function_scheduling_distributed_framework import task_deco,BrokerEnum

@task_deco('test_rabbit_queue7f',broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM,)
def test_fun(x):
    # time.sleep(2.9)
    # sleep时间随机从0.1毫秒到5秒任意徘徊,最小耗时和最大耗时差距达到了5万倍。
    # 传统的恒定并发数量的线程池对未知的耗时任务且波动达到了5万倍，持续100次每秒的精确控频无能为力，
    # 但此框架只要简单设置一个qps就自动达到了这个目的。
    # random_sleep = random.randrange(1,50000) / 10000
    # time.sleep(random_sleep)
    # print(x,random_sleep)
    time.sleep(40000)
    print(x * 2)
    return x*2


if __name__ == '__main__':
    test_fun.consume()
import time
import random
from funboost import boost, BrokerEnum
from funboost.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAble

pool = ThreadPoolExecutorShrinkAble(200)


@boost('test_rabbit_queue7', broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM, is_show_message_get_from_broker=True, specify_concurrent_pool=pool)
def test_fun(x):
    # time.sleep(2.9)
    # sleep时间随机从0.1毫秒到5秒任意徘徊,最小耗时和最大耗时差距达到了5万倍。
    # 传统的恒定并发数量的线程池对未知的耗时任务且波动达到了5万倍，持续100次每秒的精确控频无能为力，
    # 但此框架只要简单设置一个qps就自动达到了这个目的。
    # random_sleep = random.randrange(1,50000) / 10000
    # time.sleep(random_sleep)
    # print(x,random_sleep)
    # time.sleep(20000)
    rd= random.random()
    time_sleep = 0
    if 0 < rd < 0.3:
        time_sleep = 500
    if 0.3 < rd < 0.6 :
        time_sleep = 1700
    if 0.6 < rd < 1 :
        time_sleep = 1900
    time_sleep=1900
    time.sleep(time_sleep)
    print(time_sleep)
    print(x * 2)
    return x * 2


@boost('test_rabbit_queue8g', broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM, is_show_message_get_from_broker=True, qps=400, specify_concurrent_pool=pool,
       broker_exclusive_config={'x-max-priority':4})
def test_fun2(x):
    # time.sleep(2.9)
    # sleep时间随机从0.1毫秒到5秒任意徘徊,最小耗时和最大耗时差距达到了5万倍。
    # 传统的恒定并发数量的线程池对未知的耗时任务且波动达到了5万倍，持续100次每秒的精确控频无能为力，
    # 但此框架只要简单设置一个qps就自动达到了这个目的。
    # random_sleep = random.randrange(1,50000) / 10000
    # time.sleep(random_sleep)
    # print(x,random_sleep)
    time.sleep(20)
    print(x )
    return x


if __name__ == '__main__':
    # test_fun.consume()
    test_fun2.push(1)
    test_fun2.consume()

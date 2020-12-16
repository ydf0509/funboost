# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
from multiprocessing import Process
import time
from function_scheduling_distributed_framework import get_consumer, get_publisher, AbstractConsumer
from function_scheduling_distributed_framework.consumers.redis_consumer import RedisConsumer
from function_scheduling_distributed_framework.utils import LogManager

logger = LogManager('complex_example').get_logger_and_add_handlers()
pb2 = get_publisher('task2_queue', broker_kind=2)


def task1(x, y):
    logger.info(f'消费此消息 {x} - {y} ,结果是  {x - y}')
    for i in range(10):
        pb2.publish({'n': x * 100 + i})  # 消费时候发布任务到别的队列或自己的队列。可以边消费边推送。
    time.sleep(10)  # 模拟做某事需要阻塞10秒种，必须用并发绕过此阻塞。


def task2(n):
    logger.info(n)
    time.sleep(3)


def multi_processing_consume():
    get_consumer('task1_queue', consuming_function=task1, broker_kind=2).start_consuming_message()
    RedisConsumer('task2_queue', consuming_function=task2, threads_num=100).start_consuming_message()
    AbstractConsumer.join_shedual_task_thread()  # linux多进程启动时候一定要加这一句,否则即使是while 1 的线程如果不join，子进程也会迅速退出。windows下可以不需要这一句。


if __name__ == '__main__':
    [Process(target=multi_processing_consume).start() for _ in range(4)]

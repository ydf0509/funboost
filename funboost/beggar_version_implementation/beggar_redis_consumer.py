# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/12/18 0018 10:06
"""
这里是最精简的乞丐版的基于redis的分布式函数执行的实现。相对于完整版，砍掉所有功能，只是演示框架的最精简最本质的实现。
主要是砍掉很多功能，大大简化代码行数，演示框架思路是如何分布式执行python
函数的，这个只做精简演示，不要亲自去使用这里，功能太弱。

完整版支持3种并发类型，乞丐版只支持多线程并发。完整版的线程池是有界队列，线程大小动态伸缩，乞丐版线程池的线程数量只会增加不能主动主动缩小。

完整版支持15种函数辅助控制，包括控频、超时杀死、消费确认 等15种功能，
乞丐版为了简化代码演示，全部不支持。

完整版支持10种消息队列中间件，这里只演示大家喜欢的redis作为中间件。
"""
import json
import redis
from concurrent.futures import ThreadPoolExecutor
from funboost import patch_print, funboost_config_deafult



redis_db_frame = redis.Redis(host=funboost_config_deafult.REDIS_HOST, password=funboost_config_deafult.REDIS_PASSWORD, port=funboost_config_deafult.REDIS_PORT, db=funboost_config_deafult.REDIS_DB)


class BeggarRedisConsumer:
    """保持和完整版差不多的代码形态。如果仅仅是像这里的十分简化的版本，一个函数实现也可以了。例如下面的函数。"""

    def __init__(self, queue_name, consume_function, threads_num):
        self.pool = ThreadPoolExecutor(threads_num)  # 最好是使用BoundedThreadpoolexecutor或customThreadpoolexecutor。无界队列会迅速取完redis消息。
        self.consume_function = consume_function
        self.queue_name = queue_name

    def start_consuming_message(self):
        while True:
            try:
                redis_task = redis_db_frame.blpop(self.queue_name, timeout=60)
                if redis_task:
                    task_str = redis_task[1].decode()
                    print(f'从redis的 [{self.queue_name}] 队列中 取出的消息是： {task_str}  ')
                    task_dict = json.loads(task_str)
                    self.pool.submit(self.consume_function, **task_dict)
                else:
                    print(f'redis的 {self.queue_name} 队列中没有任务')
            except redis.RedisError as e:
                print(e)


def start_consuming_message(queue_name, consume_function, threads_num=50):
    """
    本例子实现的功能和中间件过于简单，单一函数最好了。
    看不懂有类的代码，不用看上面那个类，看这个函数就可以，使用一个10行代码的函数实现乞丐版分布式函数执行框架。

    """
    pool = ThreadPoolExecutor(threads_num)
    while True:
        try:
            redis_task = redis_db_frame.brpop(queue_name, timeout=60)
            if redis_task:
                task_str = redis_task[1].decode()
                print(f'从redis的 {queue_name} 队列中 取出的消息是： {task_str}')
                pool.submit(consume_function, **json.loads(task_str))
            else:
                print(f'redis的 {queue_name} 队列中没有任务')
        except redis.RedisError as e:
            print(e)


if __name__ == '__main__':
    import time


    def add(x, y):
        time.sleep(5)
        print(f'{x} + {y} 的结果是 {x + y}')

    # 推送任务
    for i in range(100):
        print(i)
        redis_db_frame.lpush('test_beggar_redis_consumer_queue', json.dumps(dict(x=i, y=i * 2)))

    # 消费任务
    # consumer = BeggarRedisConsumer('test_beggar_redis_consumer_queue', consume_function=add, threads_num=100)
    # consumer.start_consuming_message()

    start_consuming_message('test_beggar_redis_consumer_queue', consume_function=add, threads_num=10)

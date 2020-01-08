# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
import gevent.monkey;gevent.monkey.patch_all()
import time
import random

from function_scheduling_distributed_framework import get_consumer, AbstractConsumer
from function_scheduling_distributed_framework.consumers.base_consumer import ConsumersManager, FunctionResultStatusPersistanceConfig
from function_scheduling_distributed_framework.utils import LogManager

from test_frame.my_patch_frame_config import do_patch_frame_config

do_patch_frame_config()

logger = LogManager('test_consume').get_logger_and_add_handlers()


class RandomError(Exception):
    pass


def add(a, b):
    logger.info(f'消费此消息 {a} + {b} 中。。。。。')
    time.sleep(random.randint(1, 3))  # 模拟做某事需要阻塞10秒种，必须用并发绕过此阻塞。
    # if random.randint(4, 6) == 5:
    #     raise RandomError('演示随机出错')
    logger.info(f'计算 {a} + {b} 得到的结果是  {a + b}')
    return a + b


def sub(x, y):
    logger.info(f'消费此消息 {x} - {y} 中。。。。。')
    time.sleep(4)  # 模拟做某事需要阻塞10秒种，必须用并发绕过此阻塞。
    if random.randint(1, 10) == 4000:
        raise ValueError('4444')
    result = x - y
    logger.info(f'计算 {x} - {y} 得到的结果是  {result}')
    return result


# 把消费的函数名传给consuming_function，就这么简单。
consumer_add = get_consumer('queue_test569', consuming_function=add, concurrent_num=5000, max_retry_times=2,
                            qps=2, log_level=10, logger_prefix='zz平台消费',
                            function_timeout=0, is_print_detail_exception=False,
                            msg_expire_senconds=3600,
                            function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(False, False, 7 * 24 * 3600),
                            broker_kind=2, concurrent_mode=2, )  # 通过设置broker_kind，一键切换中间件为rabbitmq或redis等9种中间件或包。

consumer_sub = get_consumer('queue_test57', consuming_function=sub, concurrent_num=500, qps=108, log_level=10, logger_prefix='xxxxx平台消费',
                            function_timeout=80, is_print_detail_exception=True,
                            broker_kind=2, concurrent_mode=2)  # 通过设置

if __name__ == '__main__':
    ConsumersManager.show_all_consumer_info()
    # consumer_add.start_consuming_message()
    consumer_sub.start_consuming_message()


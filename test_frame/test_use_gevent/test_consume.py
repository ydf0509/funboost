# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
# import gevent.monkey;gevent.monkey.patch_all()   # 需要打猴子补丁。
import eventlet;eventlet.monkey_patch(all=True)
import time

from function_scheduling_distributed_framework import get_consumer,ConcurrentModeEnum
from function_scheduling_distributed_framework.utils import LogManager



logger = LogManager('f2').get_logger_and_add_handlers()


def f2(a, b):
    logger.info(f'消费此消息 {a} + {b} 中。。。。。')
    time.sleep(10)  # 模拟做某事需要阻塞10秒种，必须用并发绕过此阻塞。
    logger.info(f'计算 {a} + {b} 得到的结果是  {a + b}')


# 把消费的函数名传给consuming_function，就这么简单。
consumer = get_consumer('queue_test62', consuming_function=f2, concurrent_num=200, msg_schedule_time_intercal=0.1, log_level=10, logger_prefix='zz平台消费',
                        function_timeout=20, is_print_detail_exception=True,
                        msg_expire_senconds=500, broker_kind=6, concurrent_mode=ConcurrentModeEnum.EVENTLET)  # 通过设置broker_kind，一键切换中间件为mq或redis等7种中间件或包。

if __name__ == '__main__':
    consumer.start_consuming_message()
    
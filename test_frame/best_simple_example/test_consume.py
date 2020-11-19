# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
import time

from function_scheduling_distributed_framework import task_deco, LogManager

logger = LogManager('test.f2').get_logger_and_add_handlers(formatter_template=7)


@task_deco('queue_test2', qps=3, broker_kind=6)  # 通过设置broker_kind，一键切换中间件为mq或redis等13种中间件或包。
def f2(a, b):
    print(f'消费此消息 {a} + {b} 中。。。。。')
    time.sleep(10)  # 模拟做某事需要阻塞10秒种，必须用并发绕过此阻塞。
    logger.info(f'计算 {a} + {b} 得到的结果是  {a + b}')


if __name__ == '__main__':
    f2.clear()
    for i in range(1000):
        f2.push(i, i * 2)
    f2.consume()

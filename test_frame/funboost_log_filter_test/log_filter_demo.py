

import logging
import time
from nb_log import LogManager

# 在funboost 导入之前就提前锁定好相关命名空间的级别,可以屏蔽你所谓的烦人的日志提示
# funboost 框架的funboost_config.py的配置设置和logo打印等可以通过设置 funboost.prompt 命名空间的日志级别来 屏蔽显示
LogManager('funboost.prompt').preset_log_level(logging.INFO)
# funboost 作者研发的按需扩大,可自动缩小的python线程池,会debug打印线程的创建和摧毁,更直观了解背后的线程是什么时候创建和销毁的,对这个线程池非凡之处完全不感兴趣的人,可以设置提高_KeepAliveTimeThread的日志级别.
LogManager('_KeepAliveTimeThread').preset_log_level(logging.INFO)

from funboost import boost, BrokerEnum, BoosterParams

@boost( boost_params=BoosterParams(queue_name='task_queue_n10', max_retry_times=4, qps=3,
                                     log_level=10,log_filename='自定义.log'))
def task_fun(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(3)  # 框架会自动并发绕开这个阻塞，无论函数内部随机耗时多久都能自动调节并发达到每秒运行 5 次 这个 task_fun 函数的目的。


if __name__ == "__main__":
    pass
    task_fun.consume()  # 消费者启动循环调度并发消费任务
    for i in range(10):
        task_fun.push(i, y=i * 2)  # 发布者发布任务




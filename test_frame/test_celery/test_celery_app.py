"""
主要用用来测试相同基准下的celery和此框架的性能对比。
"""

import time
from datetime import timedelta

import celery
from celery import platforms

import celery_helper

platforms.C_FORCE_ROOT = True
# celery_app = celery.Celery('test_frame.test_celery.test_celery_app')
celery_app = celery.Celery()
class Config2:
    broker_url = f'redis://:@127.0.0.1:6379/10'  # 使用redis
    # result_backend = f'redis://:@127.0.0.1:6379/11'  # 使用redis
    broker_connection_max_retries = 150  # 默认是100
    # result_serializer = 'json'
    # task_default_queue = 'default'  # 默认celery
    # # task_default_rate_limit = '101/s'
    # task_default_routing_key = 'default'
    # task_eager_propagates = False  # 默认disable
    # task_ignore_result = False
    # task_serializer = 'json'
    # task_time_limit = 70
    # task_soft_time_limit = 60
    # worker_concurrency = 32
    # worker_enable_remote_control = True
    # worker_prefetch_multiplier = 3  # 默认4
    # worker_redirect_stdouts_level = 'WARNING'
    # worker_timer_precision = 0.1  # 默认1秒
    task_routes = {
        '求和啊': {"queue": "queue_add2", },
        'sub啊': {"queue": 'queue_sub2'},
        'f1': {"queue": 'queue_f1'},
    }

    # task_reject_on_worker_lost = True #配置这两项可以随意停止
    # task_acks_late = True


celery_app.config_from_object(Config2)


@celery_app.task(name='求和啊',rate_limit='100/s' )  # REMIND rate_limit在这里写，也可以在调用时候写test_task.apply_async(args=(1,2),expires=3)
def add(a, b):
    # print(f'消费此消息 {a} + {b} 中。。。。。')
    # time.sleep(100, )  # 模拟做某事需要阻塞10秒种，必须用并发绕过此阻塞。
    print(f'{int(time.time())} 计算 {a} + {b} 得到的结果是  {a + b}')
    time.sleep(1)
    return a + b


@celery_app.task(name='sub啊')
def sub(x, y):
    print(f'消费此消息 {x} - {y} 中。。。。。')
    time.sleep(30, )  # 模拟做某事需要阻塞10秒种，必须用并发绕过此阻塞。
    print(f'计算 {x} - {y} 得到的结果是  {x - y}')
    return x - y

@celery_app.task(name='sub啊')
def print_hello(x):
    print(f'hello {x}')


@celery.shared_task(name='无apptask')
def test_shere_deco(x):
    print(x)




print(sub)

def patch_celery_console(celery_instance:celery.Celery):
    import logging
    from nb_log.handlers import ColorHandler
    logging.StreamHandler = ColorHandler  # 解决celery的颜色不好看的问题

    #设置celery的conf配置项，解决日志可点击跳转问题。
    # print(celery_app.conf)
    celery_instance.conf.worker_task_log_format = '%(asctime)s - %(name)s - "%(pathname)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(message)s'
    celery_instance.conf.worker_log_format = '%(asctime)s - %(name)s - "%(pathname)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(message)s'

    #禁止print重定向，不希望print被转化成celery日志。配置这个。
    celery_instance.conf.worker_redirect_stdouts = False

celery_app.conf.beat_schedule = {
    'add-every-30-seconds': {
        'task': '求和啊',
        'schedule': timedelta(seconds=2),
        'args': (10000, 20000)
    }}
celery_helper.auto_register_tasks_and_set_routes()
if __name__ == '__main__':
    """
    celery是可以在python脚本直接启动消费的。直接运行此脚本就行。本人非常反感cmd 命令行敲字母。
    """

    """
    celery multi start
     Pool implementation: prefork (default), eventlet,
                        gevent or solo.
    """
    """
    celery_app.worker_main(
        argv=['worker', '--pool=prefork', '--concurrency=100', '-n', 'worker1@%h', '--loglevel=debug',
              '--queues=queue_add', '--detach','--logfile=/pythonlogs/celery_add.log'])
    """
    # queue_add,queue_sub,queue_f1
    patch_celery_console(celery_app)
    celery_app.worker_main(
        argv=['worker', '--pool=gevent','--concurrency=500', '-n', 'worker1@%h', '--loglevel=DEBUG',
              '--queues=queue_f1,queue_add2,queue_sub2'])
    import threading

    print(777777777777777)
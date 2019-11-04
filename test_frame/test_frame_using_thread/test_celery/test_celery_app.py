import time
import celery
from celery import platforms
from function_scheduling_distributed_framework import frame_config
from test_frame.my_patch_frame_config import do_patch_frame_config
do_patch_frame_config()
platforms.C_FORCE_ROOT = True
celery_app = celery.Celery()

class Config2:
    broker_url = f'redis://:{frame_config.REDIS_PASSWORD}@{frame_config.REDIS_HOST}:{frame_config.REDIS_PORT}/7' # 使用redis
    result_backend  = f'redis://:{frame_config.REDIS_PASSWORD}@{frame_config.REDIS_HOST}:{frame_config.REDIS_PORT}/14'  # 使用redis
    broker_connection_max_retries = 150  # 默认是100
    # result_serializer = 'json'
    task_default_queue = 'default'  # 默认celery
    # task_default_rate_limit = '101/s'
    task_default_routing_key = 'default'
    task_eager_propagates = False  # 默认disable
    task_ignore_result = False
    # task_serializer = 'json'
    # task_time_limit = 70
    # task_soft_time_limit = 60
    # worker_concurrency = 32
    # worker_enable_remote_control = True
    # worker_prefetch_multiplier = 3  # 默认4
    # worker_redirect_stdouts_level = 'WARNING'
    # worker_timer_precision = 0.1  # 默认1秒
    task_routes = {
        '求和啊': {"queue": "queue_add", },
    }


celery_app.config_from_object(Config2)

@celery_app.task(name='求和啊',)  # REMIND rate_limit在这里写，也可以在调用时候写test_task.apply_async(args=(1,2),expires=3)
def add(a, b):
    print(f'消费此消息 {a} + {b} 中。。。。。')
    time.sleep(10,) # 模拟做某事需要阻塞10秒种，必须用并发绕过此阻塞。
    print(f'计算 {a} + {b} 得到的结果是  {a + b}')
    return a + b


if __name__ == '__main__':
    """
    celery_app.worker_main(
        argv=['worker', '--pool=gevent', '--concurrency=100', '-n', 'worker1@%h', '--loglevel=debug',
              '--queues=queue_add', '--detach','--logfile=/pythonlogs/celery_add.log'])
    """
    celery_app.worker_main(
        argv=['worker', '--pool=gevent', '--concurrency=5000', '-n', 'worker1@%h', '--loglevel=debug',
              '--queues=queue_add', '--detach',])



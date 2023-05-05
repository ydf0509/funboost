
from celery.schedules import crontab
from datetime import timedelta
import time

from funboost import boost, BrokerEnum
from funboost.consumers.celery_consumer import CeleryHelper


queue_1 = 'celery_beat_queue_7a2'
queue_2 = 'celery_beat_queueb_8a2'


@boost(queue_1, broker_kind=BrokerEnum.CELERY, qps=5)
def f_beat(x, y):
    time.sleep(3)
    print(1111, x, y)
    return x + y



@boost(queue_2, broker_kind=BrokerEnum.CELERY, qps=1, broker_exclusive_config={'celery_task_config': {'default_retry_delay':60*5}})
def f_beat2(a, b):
    time.sleep(2)
    print(2222, a, b)
    return a - b


beat_schedule = {  # 这是100% 原汁原味的celery 定时任务配置方式
    'add-every-10-seconds_job': {
        'task': queue_1,
        'schedule': timedelta(seconds=10),
        'args': (10000, 20000)
    },
    'celery_beat_queueb_8_jobxx': {
        'task': queue_2,
        'schedule': timedelta(seconds=20),
        # 'schedule': crontab(minute=30, hour=16),
        'kwargs': {'a': 20, 'b': 30}
    }

}

if __name__ == '__main__':
    CeleryHelper.start_flower(5556)  # 启动flower 网页，这个函数也可以单独的脚本中启动
    CeleryHelper.celery_start_beat(beat_schedule) # 配置和启动定时任务，这个函数也可以在单独的脚本中启动，但脚本中需要 先import 导入@boost装饰器函数所在的脚本，因为@boost时候consumer的custom_init中注册celery任务路由，之后才能使定时任务发送到正确的消息队列。
    print(CeleryHelper.celery_app.conf)
    CeleryHelper.show_celery_app_conf()
    f_beat.consume()  # 启动f_beat消费，这个是登记celery worker要启动消费的函数，真正的启动worker消费需要运行 realy_start_celery_worker，realy_start_celery_worker是一次性启动所有登记的需要运行的函数
    f_beat2.consume() # 启动f_beat2消费，这个是登记celery worker要启动消费的函数，真正的启动worker消费需要运行 realy_start_celery_worker，realy_start_celery_worker是一次性启动所有登记的需要运行的函数
    CeleryHelper.realy_start_celery_worker(worker_name='test_worker啊')  # 这个是真正的启动celery worker 函数消费。
    print('batch_start_celery_consumers()  之后的代码不会被运行')

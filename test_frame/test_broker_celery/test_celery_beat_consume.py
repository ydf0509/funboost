import json

from celery.schedules import crontab
from datetime import timedelta
import time

from funboost import boost, BrokerEnum
from funboost.consumers.celery_consumer import celery_start_beat, batch_start_celery_consumers, start_flower
from funboost.assist.user_custom_broker_register import register_celery_broker
from funboost.publishers.celery_publisher import celery_app

'''
目前没有加到 funboost/factories/consumer_factory.py的 broker_kind__consumer_type_map 字典中，防止用户安装celery报错和funboost瘦身，
如果想要使用celery作为funboost的消息中间件，需要先调用 register_celery_broker() 函数，目的是把类注册到funboost框架中。看文档4.21自由扩展中间件文档。
'''
register_celery_broker()

queue_1 = 'celery_beat_queue_7a2'
queue_2 = 'celery_beat_queueb_8a2'


@boost(queue_1, broker_kind=BrokerEnum.CELERY, qps=0)
def f_beat(x, y):
    time.sleep(3)
    print(1111, x, y)
    return x + y


@boost(queue_2, broker_kind=BrokerEnum.CELERY, qps=1, broker_exclusive_config={'celery_task_config': {}})
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
    start_flower()
    celery_start_beat(beat_schedule)
    #
    for i in range(100):
        f_beat.push(i, i + 1)
        f_beat2.push(i, i * 2)

    print(celery_app.conf)
    batch_start_celery_consumers([f_beat, f_beat2])
    print('batch_start_celery_consumers()  之后的代码不会被运行')

import time

from funboost import boost, BrokerEnum
from funboost.assist.user_custom_broker_register import register_celery_broker

register_celery_broker()


@boost('celery_beat_queue_7', broker_kind=BrokerEnum.CELERY, concurrent_num=10,
       broker_exclusive_config={'celery_app_config':
                                    {'task_default_rate_limit': '1/s', }}
       )
def f_beat(x, y):
    time.sleep(3)
    print(1111, x, y)


@boost('celery_beat_queueb_8', broker_kind=BrokerEnum.CELERY, concurrent_num=10,
       broker_exclusive_config={'celery_app_config':
                                    {'task_default_rate_limit': '3/s', }}
       )
def f_beat2(x, y):
    time.sleep(2)
    print(2222, x, y)


if __name__ == '__main__':
    for i in range(1000):
        f_beat.push(i, i + 1)
        f_beat2.push(i, i * 2)
    f_beat.consume()
    f_beat2.consume()

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
    print(6666, x, y)

if __name__ == '__main__':
    f_beat.consume()
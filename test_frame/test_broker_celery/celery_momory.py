import time

from funboost import boost, BrokerEnum, ConcurrentModeEnum, BrokerConnConfig
from funboost.assist.celery_helper import celery_app, CeleryHelper

# BrokerConnConfig.CELERY_BROKER_URL = 'redis://'


@boost('test_list_queue', broker_kind=BrokerEnum.CELERY, qps=2, log_level=20, concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD, concurrent_num=1,
       )
def f(x):
    time.sleep(1)
    print(x)


if __name__ == '__main__':
    f.consume()

    for i in range(1000):
        f.push(i)
    print(f.publisher.get_message_count())
    CeleryHelper.start_flower()
    CeleryHelper.realy_start_celery_worker()

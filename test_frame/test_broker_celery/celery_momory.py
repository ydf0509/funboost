import time

from funboost import boost, BrokerEnum, ConcurrentModeEnum, BrokerConnConfig
from funboost.assist.celery_helper import celery_app, CeleryHelper


@boost('test_list_queue', broker_kind=BrokerEnum.CELERY, qps=0, log_level=20, concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD, concurrent_num=1,
       )
def f(x):
    # time.sleep(1)
    print(x)
    return x*2


if __name__ == '__main__':
    CeleryHelper.use_nb_log_instead_celery_log()
    f.consume()
    f.clear()
    for i in range(5000):
        f.push(i)
    print(f.publisher.get_message_count())
    CeleryHelper.start_flower()

    CeleryHelper.realy_start_celery_worker()


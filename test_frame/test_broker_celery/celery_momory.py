from funboost import boost, BrokerEnum, ConcurrentModeEnum, BrokerConnConfig
from funboost.assist.celery_helper import celery_app, CeleryHelper

BrokerConnConfig.CELERY_BROKER_URL = 'meomory://'


@boost('test_list_queue', broker_kind=BrokerEnum.CELERY, qps=0, log_level=20, concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD, concurrent_num=1,
       )
def f(x):
    print(x)


if __name__ == '__main__':
    for i in range(100000):
        f.push(i)
    print(f.publisher.get_message_count())
    f.consume()
    CeleryHelper.realy_start_celery_worker()

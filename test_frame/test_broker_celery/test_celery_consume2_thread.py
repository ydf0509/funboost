import logging
import threading
import time
import nb_log
from funboost import boost, BrokerEnum, ConcurrentModeEnum
from funboost.consumers.celery_consumer import CeleryHelper, celery_app
import requests
queue_1 = 'celery_qq3b'
queue_2 = 'celery_qq4b'

logger = nb_log.get_logger('test_funboost_celery', log_filename='test_funboost_celery.log')

lock = threading.Lock()

@boost(queue_1, broker_kind=BrokerEnum.CELERY, qps=0.2, )
def f1(x, y):
    with lock:
        print('start', x, y)
        # time.sleep(10)

        print('over', x, y)
        logger.info(['hahaha', x, y])
        return x + y


@boost(queue_2, broker_kind=BrokerEnum.CELERY, qps=0.5, )
def f2(a, b):
    time.sleep(2)
    print('嘻嘻', a, b)
    return a - b


if __name__ == '__main__':
    # for i in range(200):
    #     f1.push(i, i * 2)
    #     f2.push(a=i, b=i * 10)

    f1.consume()
    f2.consume()
    CeleryHelper.use_nb_log_instead_celery_log(logging.INFO, 'celery_run.log')
    CeleryHelper.realy_start_celery_worker()

    '''
    $env:PYTHONPATH="D:/codes/funboost" 
    python -m celery -A test_celery_consume2 status
    '''

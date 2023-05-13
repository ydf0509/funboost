
import time
import nb_log
from funboost import boost, BrokerEnum,ConcurrentModeEnum
from funboost.consumers.celery_consumer import CeleryHelper,celery_app


queue_1 = 'celery_qq3'
queue_2 = 'celery_qq4'

nb_log.get_logger('celery')

@boost(queue_1, broker_kind=BrokerEnum.CELERY, qps=0.2,)
def f1(x, y):
    time.sleep(3)
    print('哈哈哈', x, y)
    return x + y


@boost(queue_2, broker_kind=BrokerEnum.CELERY, qps=0.5,)
def f2(a, b):
    time.sleep(2)
    print('嘻嘻', a, b)
    return a - b


if __name__ == '__main__':
    for i in range(200):
        f1.push(i,i*2)
        f2.push(a=i,b=i*10)

    f1.consume()
    f2.consume()
    CeleryHelper.realy_start_celery_worker()

    '''
    $env:PYTHONPATH="D:/codes/funboost" 
    python -m celery -A test_celery_consume2 status
    '''

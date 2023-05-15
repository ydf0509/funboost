import time

from funboost import boost, BrokerEnum
from funboost.consumers.celery_consumer import CeleryHelper


@boost('celery_q1', broker_kind=BrokerEnum.CELERY, qps=5)
def f1(x, y):
    time.sleep(3)
    print('哈哈哈', x, y)
    return x + y


@boost('celery_q2', broker_kind=BrokerEnum.CELERY, qps=1, )
def f2(a, b):
    time.sleep(2)
    print('嘻嘻', a, b)
    return a - b


if __name__ == '__main__':
    for i in range(200):
        f1.push(i, i * 2)
        f2.push(a=i, b=i * 10)

    f1.consume()  # 登记celery worker命令需要启动的--queues
    f2.consume()  # 登记celery worker命令需要启动的--queues
    CeleryHelper.realy_start_celery_worker(worker_name='测试celery worker2') # 正正的启动celery worker

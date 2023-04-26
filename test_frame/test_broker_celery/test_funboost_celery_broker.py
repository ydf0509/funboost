import time
import nb_log
from funboost import register_custom_broker, boost
from funboost.consumers.celery_consumer import CeleryConsumer
from funboost.publishers.celery_publisher import CeleryPublisher

register_custom_broker(30, CeleryPublisher, CeleryConsumer)

celery_config = {'broker_url': 'redis://192.168.64.151:6378/11'}


@boost('tets_funboost_celery_queue26a', broker_kind=30, concurrent_num=10,
       broker_exclusive_config={'task_default_rate_limit': '1/s', 'worker_prefetch_multiplier': 10}
       )
def fa(x, y):
    time.sleep(3)
    print(6666, x, y)


@boost('tets_funboost_celery_queue26b', broker_kind=30, concurrent_num=10,
       broker_exclusive_config={'task_default_rate_limit': '2/s', 'worker_prefetch_multiplier': 10}
       )
def fb(a, b):
    time.sleep(2)
    print(7777, a, b)


if __name__ == '__main__':
    for i in range(1000):
        fa.push(i, i + 1)
        fb.push(i, i * 2)

    # fa.multi_process_consume(1)
    # fb.multi_process_consume(1)

    fa.consume()
    fb.consume()

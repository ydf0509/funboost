

from funboost import boost,BoosterParams,BrokerEnum,ConcurrentModeEnum
from funboost.assist.celery_helper import CeleryHelper

@boost(BoosterParams(queue_name='tets_performance',broker_kind=BrokerEnum.MEMORY_QUEUE,concurrent_mode=ConcurrentModeEnum.SOLO,log_level=20))
# @boost(BoosterParams(queue_name='tets_performance',broker_kind=BrokerEnum.KOMBU,concurrent_mode=ConcurrentModeEnum.SOLO,log_level=20,
#                      broker_exclusive_config={'kombu_url': 'memory://',
#                                        'transport_options': {},
#                                        'prefetch_count': 500
#                                        }))
# @boost(BoosterParams(queue_name='tets_performance',broker_kind=BrokerEnum.CELERY,concurrent_mode=ConcurrentModeEnum.SOLO,log_level=20))
def f(x):
    if x % 10000 == 0:
        print(x)


if __name__ == '__main__':
    for i in range(1000000):
        f.push(i)
    f.consume()
    # CeleryHelper.realy_start_celery_worker(loglevel='WARNING')



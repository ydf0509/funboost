

from funboost import boost,BoosterParams,BrokerEnum,ConcurrentModeEnum
from funboost.assist.celery_helper import CeleryHelper

@boost(BoosterParams(queue_name='tets_performance',broker_kind=BrokerEnum.REDIS,concurrent_mode=ConcurrentModeEnum.SOLO
    ,log_level=20,
                     broker_exclusive_config={'pull_msg_batch_size':2000}))
# @boost(BoosterParams(queue_name='tets_performance',broker_kind=BrokerEnum.KOMBU,concurrent_mode=ConcurrentModeEnum.SOLO,log_level=20,
#                      broker_exclusive_config={
#                          # 'kombu_url': 'memory://',
#                           'kombu_url':'redis://127.0.0.1:6379/14',
#                                        'transport_options': {},
#                                        'prefetch_count': 500
#                                        }))
# @boost(BoosterParams(queue_name='tets_performance',broker_kind=BrokerEnum.CELERY,concurrent_mode=ConcurrentModeEnum.SOLO,log_level=20))
def f(x):
    if x % 10000 == 0:
        print(x)


if __name__ == '__main__':
    for i in range(500000):
        f.push(i)
    f.consume()
    CeleryHelper.realy_start_celery_worker(loglevel='WARNING')



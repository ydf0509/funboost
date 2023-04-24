import time

from funboost import BrokerEnum, boost


queue_name = 'test_kombu5'


@boost(queue_name, broker_kind=BrokerEnum.KOMBU, qps=0.1,
       broker_exclusive_config={
           'kombu_url': 'filesystem://',
           'transport_options': {
               'data_folder_in': f'/data/kombu_queue/{queue_name}',
               'data_folder_out': f'/data/kombu_queue/{queue_name}',
               'store_processed': True,
               'processed_folder': f'/data/kombu_processed/{queue_name}'
           },
           'prefetch_count': 10})
def f2(x, y):
    print(f'start {x} {y} 。。。')
    time.sleep(60)
    print(f'{x} + {y} = {x + y}')
    print(f'over {x} {y}')


if __name__ == '__main__':
    for i in range(100):
        f2.push(i, i + 1)
    f2.consume()

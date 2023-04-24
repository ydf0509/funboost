import time
import kombu
from pymongo import MongoClient,collection,cursor
collection.Collection.ensure_index =    collection.Collection.create_index

import celery
# collection.Collection.count_documents()
# cursor.Cursor.
# MongoClient.get_database().list_collection_names()


from funboost import BrokerEnum, boost


queue_name = 'test_kombu_mongo4'


@boost(queue_name, broker_kind=BrokerEnum.KOMBU, qps=0.1,
       broker_exclusive_config={
           'kombu_url': 'mongodb://root:123456@192.168.64.151:27017/my_db?authSource=admin',
           'transport_options': {
               'default_database':'my_db',
               'messages_collection':queue_name,

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
    # f2.consume()

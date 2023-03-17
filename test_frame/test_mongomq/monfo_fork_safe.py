import time

import pymongo
import os
from pymongo.collection import Collection
# from funboost import funboost_config_deafult

print(pymongo)
client = pymongo.MongoClient(f'mongodb://192.168.6.133:27017', connect=False)

col = client.get_database('db2').get_collection('col23')



print((col.database.client.__dict__))
print(col.insert_one)


#
# if __name__ == '__main__':
#     ForkSafeCollection(col)

t1= time.perf_counter()
for  i in range(1000000):
    os.getpid()

print(time.perf_counter()-t1)
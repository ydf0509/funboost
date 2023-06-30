import time
from concurrent.futures import ThreadPoolExecutor

import redis
import nb_log

r = redis.Redis(max_connections=10)
# # from funboost.utils.time_util import DatetimeConverter
# print()
# r.set('k1', 1)
# print()
# print()
# r.set('k1', 1)
# print()
# print(time.time())
# with r.pipeline() as pipe:
#     print(time.time())
#     # pipe.watch('abc4')
#     v2 = pipe.get('abc')
#     print(v2)
#     # pipe.unwatch()
#     # pipe.set('abc',int(v2)+3)
#     pipe.execute()
#     print(time.time())
#
# print(time.time())
r.ping()
print()
with ThreadPoolExecutor(50) as pool:
    for i in range(20000):
        r.lpush('list1',i)
        # pool.submit(r.lpush,i)
print()


# print()
# for i in range(200000):
#     r.lpush('list1',i)
#     # pool.submit(r.lpush, i)
# print()

import tomorrow3
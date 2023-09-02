import time

import redis
from funboost import funboost_config_deafult

from test_frame.test_speed.speed_test_consume import f_test_speed

redis_db_frame = redis.Redis(host=funboost_config_deafult.REDIS_HOST, password=funboost_config_deafult.REDIS_PASSWORD, port=funboost_config_deafult.REDIS_PORT, db=funboost_config_deafult.REDIS_DB)

# f_test_speed.clear()
for i in range(500000):

    f_test_speed.push(i)
    # redis_db_frame.lpush('no_frame_queue',f'{{"x":{i}}}')

# from funboost.utils.redis_manager import RedisMixin
#
#
#
# r = RedisMixin().redis_db_frame
#
# for _ in range(30):
#     # r.lpush('speed_test_queue',*[f'{{"x":{i}}}'  for i in  range (200000)])
#     pass
#
# t1 = time.time()
# # with r.pipeline() as p:
# #     for i in range(10000):
# #         p.lpushx('test567',i)
# #     p.execute()
#
#
# # for i in range(10000):
# #     r.lpushx('test568',i)
#
#
# r.lpush('stest569',*[i  for i in  range (10000)])
# print(time.time()-t1)
import time

from test_frame.test_speed.speed_test_consume import f_test_speed

f_test_speed.clear()
for i in range(500000):
    f_test_speed.push(i)

# from function_scheduling_distributed_framework.utils.redis_manager import RedisMixin
#
#
#
# r = RedisMixin().redis_db_frame_version3
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
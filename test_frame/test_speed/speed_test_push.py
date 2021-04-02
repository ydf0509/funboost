from test_frame.test_speed.speed_test_consume import f_test_speed

f_test_speed.clear()
# for i in range(500000):
#     f_test_speed.push(i)

from function_scheduling_distributed_framework.utils.redis_manager import RedisMixin




for _ in range(3):
    RedisMixin().redis_db_frame_version3.lpush('speed_test_queue',*[f'{{"x":{i}}}'  for i in  range (500000)])
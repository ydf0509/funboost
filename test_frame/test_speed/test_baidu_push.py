from function_scheduling_distributed_framework.utils.redis_manager import RedisMixin



r = RedisMixin().redis_db_frame_version3

for i in range(100):
    r.lpush('speed_baidu',*[f'{{"x":{i}}}' for i in range(10000)])
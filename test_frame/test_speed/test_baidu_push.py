from funboost.utils.redis_manager import RedisMixin



r = RedisMixin().redis_db_frame

for i in range(100):
    r.lpush('speed_baidu',*[f'{{"x":{i}}}' for i in range(10000)])
from funboost.utils.redis_manager import RedisMixin

print(RedisMixin().redis_db_frame.xinfo_groups('queue_test_f01'))

print(RedisMixin().redis_db_frame.xinfo_stream('queue_test_f01'))

print(RedisMixin().redis_db_frame.xinfo_consumers('queue_test_f01', 'distributed_frame_group'))

print(RedisMixin().redis_db_frame.xpending('queue_test_f01', 'distributed_frame_group'))


RedisMixin().redis_db_frame
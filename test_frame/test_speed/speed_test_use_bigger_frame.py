import json
from funboost.beggar_version_implementation.beggar_redis_consumer import start_consuming_message, redis_db_frame

queue_name = 'no_frame_queue'

def f(x):
    if x % 5000 == 0:
        print(x)

for i in range(100000):
    if i % 5000 == 0:
        print(i)
    redis_db_frame.lpush(queue_name, json.dumps(dict(x=i, )))

start_consuming_message(queue_name,consume_function=f,threads_num=1)

from test_frame.test_redis_ack_able.test_redis_ack_able_consumer import cost_long_time_fun

for i in range(500):
    cost_long_time_fun.push(i)

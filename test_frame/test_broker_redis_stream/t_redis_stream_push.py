import time

from test_frame.test_broker_redis_stream.t_redis_stream_consume import test_fun

if __name__ == '__main__':

    test_fun.push(60)
    time.sleep(1)
    test_fun.push(30)

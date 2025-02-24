


from test_frame.test_redis_ack_able.test_load_balancing_consume import test_load_balancing


if __name__ == '__main__':

    for i in range(100):
        test_load_balancing.push(i)

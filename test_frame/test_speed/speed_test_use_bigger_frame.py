from funboost.beggar_version_implementation.beggar_redis_consumer import start_consuming_message


def f(x):
    print(x)

start_consuming_message('no_frame_queue',consume_function=f)
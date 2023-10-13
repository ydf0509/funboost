from funboost.utils import RedisMixin


def f(x,y,runonce_uuid):
    if RedisMixin().redis_db_frame.sadd('k6',runonce_uuid):
        print(x,y)
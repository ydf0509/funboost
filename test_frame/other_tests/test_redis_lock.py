import threading
import time

from funboost.utils.decorators import RedisDistributedLockContextManager
from funboost.utils.redis_manager import RedisMixin

lock_key = 'redis_locka2'


def f(x):
    with RedisDistributedLockContextManager(RedisMixin().redis_db_frame_version3, lock_key, ).set_log_level(30) as lock:
        if lock:
            print(f'获得锁 {x}')
            time.sleep(60)
        else:
            print(f'没有获得锁 {x}')


if __name__ == '__main__':
    threading.Thread(target=f, args=[1]).start()
    threading.Thread(target=f, args=[2]).start()

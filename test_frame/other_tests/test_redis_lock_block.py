import random

import time
import threading

from funboost.utils.redis_manager import RedisMixin

from funboost.utils.decorators import RedisDistributedBlockLockContextManager


def f():
    x = random.random()
    with RedisDistributedBlockLockContextManager(RedisMixin().redis_db_frame,'lock_key1'):
        print(f'start {x} {threading.get_ident()}')
        time.sleep(5)
        print(f'over {x} {threading.get_ident()}')


for i in range(10):
    threading.Thread(target=f).start()
import time
from multiprocessing import Process
import uuid
from redis import Redis
import nb_log

r = Redis()


class MyProcessPool:
    def __init__(self, max_workers=10):
        self.max_workers = max_workers
        self._redis_incr_key = f'pool_cnt:{uuid.uuid4()}'

    def get_now_running_cnt(self):
        res:str = r.get(self._redis_incr_key)
        if res:
            return int(res)
        return 0

    def _run(self, fn, *args, **kwargs):
        fn(*args, **kwargs)
        r.set(self._redis_incr_key, self.get_now_running_cnt() - 1)

    def submit(self, fn, *args, **kwargs):
        while 1:
            if self.get_now_running_cnt() < self.max_workers:
                r.incr(self._redis_incr_key, )
                args_new = [fn]
                args_new.extend(list(args))
                Process(target=self._run, args=args_new, kwargs=kwargs).start()
                break
            else:
                time.sleep(1)


def test_f(x):
    time.sleep(10)
    print(x)


if __name__ == '__main__':
    pool = MyProcessPool(3)
    for i in range(10):
        pool.submit(test_f, i)

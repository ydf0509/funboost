import threading
import time

from decorator_libs import synchronized
from concurrent.futures import ThreadPoolExecutor

# @synchronized
def f(x):
    # time.sleep(3)
    # print(f'hi {x}')
    pass

if __name__ == '__main__':
    pool = ThreadPoolExecutor(100)
    t1 = time.time()
    for i in range(100000):
        # pool.submit(f,i)
        f(i)
    pool.shutdown()
    print(time.time()-t1)

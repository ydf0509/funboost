import time
from concurrent.futures import ThreadPoolExecutor
from funboost.concurrent_pool.bounded_threadpoolexcutor import BoundedThreadPoolExecutor


# pool = ThreadPoolExecutor(10)
pool = BoundedThreadPoolExecutor(10)

def print_long_str(long_str):
    print(long_str[:10])
    time.sleep(5)


for i in range(10000000):
    pool.submit(print_long_str,'很长的字符串很占内存'*100000)


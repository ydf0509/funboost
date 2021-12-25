from funboost.concurrent_pool.custom_threadpool_executor import CustomThreadpoolExecutor

import time

import threading
from concurrent.futures import ThreadPoolExecutor


pool = CustomThreadpoolExecutor(10)
pool2 = ThreadPoolExecutor(10)
t1 = time.time()

lock = threading.Lock()
def f(x):
    with lock:
        print(x)

for i in range(10000):
    # pool.submit(f,i)
    pool2.submit(f,i)
    # threading.Thread(target=f,args=(i,)).start()
    # f(i)

print("&&&",time.time() -t1)
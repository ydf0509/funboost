
from concurrent.futures import ThreadPoolExecutor
import time
from threading import Thread
from funboost.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAbleNonDaemon,ThreadPoolExecutorShrinkAble


pool = ThreadPoolExecutorShrinkAble(10)

def f(x):
    time.sleep(10)
    print(x)

def thread_fun():
    while 1:
        time.sleep(10)
        print('sleep 10 seconds')
        pool.submit(f,666)


if __name__ == '__main__':
    Thread(target=thread_fun).start()

    # time.sleep(1000)

    

    
import time
from concurrent.futures import ThreadPoolExecutor


def f(x):
    time.sleep(3)
    print(x)


pool = ThreadPoolExecutor(10)

if __name__ == '__main__':
    for i in range(100):
        pool.submit(f, i)
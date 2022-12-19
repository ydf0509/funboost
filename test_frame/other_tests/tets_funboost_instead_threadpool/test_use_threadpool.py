import time
from concurrent.futures import ThreadPoolExecutor


def f(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(10)


if __name__ == '__main__':

    pool = ThreadPoolExecutor(5)

    for i in range(100):
        pool.submit(f, i, i * 2)

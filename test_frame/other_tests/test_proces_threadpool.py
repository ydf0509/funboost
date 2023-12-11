import time
from concurrent.futures import ThreadPoolExecutor

from multiprocessing import Process


def f(x):
    try:
        print(f'hi {x}')
        time.sleep(1)
    except Exception as e:
        print(e)



def tf():
    for i  in range(100):
        pool.submit(f,i)
    time.sleep(11000)


if __name__ == '__main__':
    pool = ThreadPoolExecutor(5)
    for j in range(2):
        Process(target=tf).start()
    time.sleep(100000)
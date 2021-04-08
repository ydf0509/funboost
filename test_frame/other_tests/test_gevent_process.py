import time

from gevent import monkey

monkey.patch_all()
from multiprocessing import Process

print(6666)
def f(x):
    print(x)
    time.sleep(10000)

if __name__ == '__main__':
    [Process(target=f,args=(2,)).start() for i in range(2)]
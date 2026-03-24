
from multiprocessing import Process


def f():
    while 1:
        pass


if __name__ =="__main__":
    for i in range(16):
        Process(target=f).start()

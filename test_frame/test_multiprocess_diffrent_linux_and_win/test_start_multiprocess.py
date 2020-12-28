from multiprocessing import Process
import threading


def f(xx):
    print(xx)


# x = threading.Lock()
x = 2



# if __name__ == '__main__':
#     Process(target=f, args=(x,)).start()

Process(target=f, args=(x,)).start()
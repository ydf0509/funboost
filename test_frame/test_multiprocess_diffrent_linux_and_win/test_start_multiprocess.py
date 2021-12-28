from multiprocessing import Process
import threading


def f(xx):
    print(xx)

x = 2
x = threading.Lock()
x = (i for i in range(5))




if __name__ == '__main__':
    Process(target=f, args=(x,)).start()

# Process(target=f, args=(x,)).start()
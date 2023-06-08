
import multiprocessing

def f():
    print(multiprocessing.current_process().name)


if __name__ == '__main__':
    print(multiprocessing.current_process().name)
    multiprocessing.Process(target=f).start()



import threading
import time


def my_thread():
    # 定义一个互斥锁
    lock = threading.Lock()
    # 获取互斥锁
    lock.acquire()

    # 定义一个事件对象
    event = threading.Event()
    # 设置事件对象
    event.set()

    # 定义一个信号量
    semaphore = threading.Semaphore(2)
    # 获取两个信号量
    semaphore.acquire()
    semaphore.acquire()

    # 定义一个条件变量
    condition = threading.Condition()
    # 获取条件变量
    condition.acquire()

    # 定义一个递归锁
    rlock = threading.RLock()
    # 获取递归锁
    rlock.acquire()

    # 等待被杀死
    event.wait()

def acquire_all_locks():
    for lock in threading.enumerate():
        print(lock,type(lock))
        if isinstance(lock, (threading.Lock, threading.RLock, threading.Semaphore)):
            lock.release()
        elif isinstance(lock, threading.Condition):
            lock.acquire()
            lock.notify_all()
            lock.release()




import threading
import ctypes
import nb_log

lock2 = threading.Lock()

def my_thread2():
    with lock2:
        while 1:
            time.sleep(2)
            print(666)

def main():
    print(lock2.locked())

    # 创建需要杀死的线程
    t = threading.Thread(target=my_thread2)
    t.start()

    # 在杀死线程之前，先释放线程持有的所有锁
    # acquire_all_locks()

    # 获取线程的标识符 ID
    thread_id = t.ident
    time.sleep(1)
    print(lock2.locked())
    time.sleep(6.1)
    # 使用 ctypes 杀死线程
    print(lock2.locked())
    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.py_object(SystemExit))
    print(lock2.locked())
    with lock2:
        print(2222)


if __name__ == '__main__':
    main()
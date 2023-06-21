#
# __version__ = '0.1.0'
# __author__ = 'fx-kirin <fx.kirin@gmail.com>'
# __all__ = ['Lock']
#
# import threading
# import time
#
# """
# Thread-safe lock mechanism with timeout support module.
# """
#
# from queue import Empty, Full, Queue
# from threading import ThreadError, current_thread
#
# import nb_log
#
# logger = nb_log.get_logger(__name__)
#
#
# class Lock(object):
#     """
#     Thread-safe lock mechanism with timeout support.
#     """
#
#     def __init__(self, timeout=None):
#         self._queue = Queue(maxsize=1)
#         self._owner = None
#         if timeout:
#             self._timeout = timeout
#         else:
#             self._timeout = 0
#
#     def acquire(self, timeout=None):
#         if timeout:
#             # timeout = self._timeout
#             timeout = 100 # todo
#         th = current_thread()
#         try:
#             logger.debug('Acquiring Lock')
#             self._queue.put(
#                 th, block=(timeout != 0),
#                 # timeout=(None if timeout < 0 else timeout # todo
#                 timeout=self._timeout,
#                  )
#
#             logger.debug('Acquired Lock')
#         except Full:
#             raise ThreadError('Lock Timed Out')
#
#         self._owner = th
#         return True
#
#     def release(self):
#         th = current_thread()
#         if th != self._owner:
#             raise ThreadError('This lock isn\'t owned by this thread.')
#
#         self._owner = None
#         try:
#             logger.debug('Releasing Lock')
#             self._queue.get(False)
#             return True
#         except Empty:
#             raise ThreadError('This lock was released already.')
#
#     def __enter__(self, *args, **kwargs):
#         if 'timeout' in kwargs:
#             self.acquire(timeout=kwargs['timeout'])
#         else:
#             self.acquire(self._timeout)
#
#     def __exit__(self, *args, **kwargs):
#         self.release()
#
#
# if __name__ == '__main__':
#     lock = Lock(1)
#
#     def f1(x):
#         with lock:
#             print(f' start {x}')
#             time.sleep(2)
#             print(f' over {x}')
#
#     def f2(y):
#         with lock:
#             print(f' start {y}')
#             time.sleep(2)
#             print(f' over {y}')
#
#
#     def f3(z):
#         with lock:
#             print(f' start {z}')
#             time.sleep(2)
#             print(f' over {z}')
#
#     threading.Thread(target=f1,args=[1]).start()
#     threading.Thread(target=f2,args=[2]).start()
#     threading.Thread(target=f3,args=[3]).start()

'''
import threading
import time

lock = threading.Lock()

def acquire_lock_with_timeout(timeout):
    acquire_result = lock.acquire(blocking=True, timeout=timeout)
    if acquire_result:
        # 获取锁成功,启动定时器
        timer = threading.Timer(timeout, release_lock, ())
        timer.start()
    return acquire_result

def release_lock():
    # 释放锁
    lock.release()

# 获取锁,定时5s后自动释放
acquire_lock_with_timeout(5)

'''
import uuid

import nb_log
import threading
from threading import current_thread
import time


class ThreadLockExpireAble:
    lock_lock = threading.Lock()
    lock_lock2 = threading.Lock()

    def __init__(self, lock: threading.Lock, timeout):
        self.lock = lock
        self.timeout = timeout

    def release_lock(self):
        # 释放锁
        # print(self.lock_uuid)
        # if self.lock_uuid != '没超时' and self.lock.locked():
        #     self.lock.release()
        #     print('释放成功')
        # if time.time() - self.start_time > self.timeout:
        #     self.lock.release()
        #     print('释放成功')
        with self.lock_lock:
            if self.lock.locked():
                self.lock.release()
                print('运行超时释放成功')

    # def __enter__(self):
    #     with self.lock_lock:
    #         boolx = self.lock.acquire(blocking=True)
    #         print('获得锁')
    #         self.start_time = time.time()
    #         self.lock_uuid = uuid.uuid4().hex
    #
    #     timer = threading.Timer(self.timeout, self.release_lock, args=[])
    #     timer.start()
    #     return boolx
    #
    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     print([exc_type, exc_val, exc_tb])
    #     with self.lock_lock:
    #         if self.lock.locked():
    #             self.lock.release()
    #             print('运行没有超时释放成功')

    def __enter__(self):
        with self.lock_lock2:
            boolx = self.lock.acquire(blocking=True)
            print('获得锁')
            self.start_time = time.time()
            self.lock_uuid = uuid.uuid4().hex

        timer = threading.Timer(self.timeout, self.release_lock, args=[])
        timer.start()
        return boolx

    def __exit__(self, exc_type, exc_val, exc_tb):
        print([exc_type, exc_val, exc_tb])
        with self.lock_lock2:
            with self.lock_lock:
                if self.lock.locked():
                    self.lock.release()
                    print('运行没有超时释放成功')


if __name__ == '__main__':
    lockx = threading.Lock()
    lock_expire = ThreadLockExpireAble(lockx, 5)


    def f(x):
        with lock_expire:
            print(f'start {x}')
            time.sleep(10)
            print(f'over {x}')


    def f2(x):

        lockx.acquire(timeout=5)
        print(f'start {x}')
        time.sleep(2)
        lockx.release()
        print(f'over {x}')




    for i in range(100):
        threading.Thread(target=f, args=[i]).start()

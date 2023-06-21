import copy
import threading
import time
import uuid
import sys

from nb_log import LoggerMixin, LoggerLevelSetterMixin

# cond = threading.Condition()
event = threading.Event()
event.set()

class LockStore:
    lock0 = threading.Lock()

    lock_key__info_map = {}

    has_start_delete_expire_lock_key_thread = False

    @classmethod
    def _delete_expire_lock_key_thread(cls):
        while 1:
            lock_key__info_map_copy = copy.copy(cls.lock_key__info_map)
            for lock_key, info in lock_key__info_map_copy.items():
                if time.time() - info['set_time'] > info['ex']:
                    cls.lock_key__info_map.pop(lock_key)
                    # with cond:
                    #     cond.notify_all()
                    event.set()
            time.sleep(0.1)

    @classmethod
    def set(cls, lock_key, value, ex):
        with cls.lock0:
            if cls.has_start_delete_expire_lock_key_thread is False:
                cls.has_start_delete_expire_lock_key_thread = True
                threading.Thread(target=cls._delete_expire_lock_key_thread).start()
            print(cls.lock_key__info_map)
            if lock_key not in cls.lock_key__info_map:
                cls.lock_key__info_map[lock_key] = {'value': value, 'ex': ex, 'set_time': time.time()}
                return True

            return False

    @classmethod
    def delete(cls, lock_key, value):
        with cls.lock0:
            if lock_key in cls.lock_key__info_map:
                if cls.lock_key__info_map[lock_key]['value'] == value:
                    cls.lock_key__info_map.pop(lock_key)
                    # with cond:
                        # cond.notify_all()
                    event.set()
                    print('expire delete')
                    return True
            return False


threading.Thread(target=LockStore._delete_expire_lock_key_thread).start()

class ThreadLockAutoExpire(LoggerMixin, LoggerLevelSetterMixin):
    """
    分布式redis锁上下文管理.
    """



    def __init__(self, lock_key, expire_seconds=30, ):
        self.lock_key = lock_key
        self._expire_seconds = expire_seconds
        self.identifier = str(uuid.uuid4())
        self.has_aquire_lock = False

    # def __enter__(self):
    #     self._line = sys._getframe().f_back.f_lineno  # noqa 调用此方法的代码的函数
    #     self._file_name = sys._getframe(1).f_code.co_filename  # noqa 哪个文件调了用此方法
    #     # ret = self.redis_client.set(self.redis_lock_key, value=self.identifier, ex=self._expire_seconds, nx=True)
    #     ret = LockStore.set(self.lock_key, value=self.identifier, ex=self._expire_seconds)
    #     self.has_aquire_lock = ret
    #     if self.has_aquire_lock:
    #         log_msg = f'\n"{self._file_name}:{self._line}" 这行代码获得了锁 {self.lock_key}'
    #     else:
    #         log_msg = f'\n"{self._file_name}:{self._line}" 这行代码此次没有获得锁 {self.lock_key}'
    #     # print(self.logger.level,log_msg)
    #     self.logger.debug(log_msg)
    #     return self

    def __enter__(self):
        self._line = sys._getframe().f_back.f_lineno  # noqa 调用此方法的代码的函数
        self._file_name = sys._getframe(1).f_code.co_filename  # noqa 哪个文件调了用此方法
        # ret = self.redis_client.set(self.redis_lock_key, value=self.identifier, ex=self._expire_seconds, nx=True)

        while 1:
            ret = LockStore.set(self.lock_key, value=self.identifier, ex=self._expire_seconds)
            self.has_aquire_lock = ret
            print(self.has_aquire_lock)
            print(event.is_set())
            if not self.has_aquire_lock:
                event.wait()
                continue
            else:
                event.clear()
                break




    def __bool__(self):
        return self.has_aquire_lock

    def __exit__(self, exc_type, exc_val, exc_tb):
        # self.redis_client.delete(self.redis_lock_key)
        # unlock = self.redis_client.register_script(self.unlock_script)
        # result = unlock(keys=[self.redis_lock_key], args=[self.identifier])

        result = LockStore.delete(self.lock_key, self.identifier)
        # with cond:
        #     cond.notify_all()
        event.set()
        if result:
            return True
        else:
            return False


if __name__ == '__main__':
    def f(x):
        with ThreadLockAutoExpire('test_lock_name', expire_seconds=2) :
            print(x)
            time.sleep(5)



    threading.Thread(target=f, args=[1]).start()
    # time.sleep(1)
    threading.Thread(target=f, args=[2]).start()

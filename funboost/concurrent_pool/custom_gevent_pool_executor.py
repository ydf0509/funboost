# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/7/2 14:11
import atexit
import time
import warnings
# from collections import Callable
from typing import Callable
import threading
import gevent
from gevent import pool as gevent_pool
from gevent import monkey
from gevent.queue import JoinableQueue

from nb_log import LoggerMixin, nb_print, LogManager


def check_gevent_monkey_patch(raise_exc=True):
    if not monkey.is_module_patched('socket'):  # 随便选一个检测标志
        if raise_exc:
            warnings.warn(f'检测到 你还没有打gevent包的猴子补丁，请在所运行的起始脚本第一行写上  【import gevent.monkey;gevent.monkey.patch_all()】  这句话。')
            raise Exception(f'检测到 你还没有打gevent包的猴子补丁，请在所运行的起始脚本第一行写上  【import gevent.monkey;gevent.monkey.patch_all()】  这句话。')
    else:
        return 1


logger_gevent_timeout_deco = LogManager('gevent_timeout_deco').get_logger_and_add_handlers()


def gevent_timeout_deco(timeout_t):
    def _gevent_timeout_deco(f):
        def __gevent_timeout_deceo(*args, **kwargs):
            timeout = gevent.Timeout(timeout_t, )
            timeout.start()
            result = None
            try:
                result = f(*args, **kwargs)
            except gevent.Timeout as t:
                logger_gevent_timeout_deco.error(f'函数 {f} 运行超过了 {timeout_t} 秒')
                if t is not timeout:
                    nb_print(t)
                    # raise  # not my timeout
            finally:
                timeout.close()
                return result

        return __gevent_timeout_deceo

    return _gevent_timeout_deco


class GeventPoolExecutor(gevent_pool.Pool):
    def __init__(self, size=None, greenlet_class=None):
        check_gevent_monkey_patch() # basecomer.py中检查。
        super().__init__(size, greenlet_class)
        atexit.register(self.shutdown)

    def submit(self, *args, **kwargs):
        self.spawn(*args, **kwargs)

    def shutdown(self):
        self.join()


class GeventPoolExecutor2(LoggerMixin):
    def __init__(self, max_works, ):
        self._q = JoinableQueue(maxsize=max_works)
        # self._q = Queue(maxsize=max_works)
        for _ in range(max_works):
            gevent.spawn(self.__worker)
        # atexit.register(self.__atexit)
        self._q.join(timeout=100)

    def __worker(self):
        while True:
            fn, args, kwargs = self._q.get()
            try:
                fn(*args, **kwargs)
            except Exception as exc:
                self.logger.exception(f'函数 {fn.__name__} 中发生错误，错误原因是 {type(exc)} {exc} ')
            finally:
                pass
                self._q.task_done()

    def submit(self, fn: Callable, *args, **kwargs):
        self._q.put((fn, args, kwargs))

    def __atexit(self):
        self.logger.critical('想即将退出程序。')
        self._q.join()


class GeventPoolExecutor3(LoggerMixin):
    def __init__(self, max_works, ):
        self._q = gevent.queue.Queue(max_works)
        self.g_list = []
        for _ in range(max_works):
            self.g_list.append(gevent.spawn(self.__worker))
        atexit.register(self.__atexit)

    def __worker(self):
        while True:
            fn, args, kwargs = self._q.get()
            try:
                fn(*args, **kwargs)
            except Exception as exc:
                self.logger.exception(f'函数 {fn.__name__} 中发生错误，错误原因是 {type(exc)} {exc} ')

    def submit(self, fn: Callable, *args, **kwargs):
        self._q.put((fn, args, kwargs))

    def joinall(self):
        gevent.joinall(self.g_list)

    def joinall_in_new_thread(self):
        threading.Thread(target=self.joinall)

    def __atexit(self):
        self.logger.critical('想即将退出程序。')
        self.joinall()


if __name__ == '__main__':
    monkey.patch_all(thread=False)


    def f2(x):

        time.sleep(3)
        nb_print(x * 10)


    pool = GeventPoolExecutor3(40)

    for i in range(20):
        time.sleep(0.1)
        nb_print(f'放入{i}')
        pool.submit(gevent_timeout_deco(8)(f2), i)
    # pool.joinall_in_new_thread()
    nb_print(66666666)

import ctypes
import threading
import time


def kill_thread(threadx:threading.Thread):
    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(threadx.ident), ctypes.py_object(SystemExit))


def kill_fun_deco(fun,*a,**k):
    def _inner(f):
        def __inner(*args,**kwargs):
            return f(*args,**kwargs)
        return __inner
    return _inner


def get_stop_flag():
    time.sleep(5)
    return True

def my_fun(x):
    print('start')
    time.sleep(10)
    print('over')


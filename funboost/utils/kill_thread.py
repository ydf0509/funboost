import ctypes
import threading
import time


def kill_thread(threadx:threading.Thread):
    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(threadx.ident), ctypes.py_object(SystemExit))


def kill_fun_deco(fun,*a,**k):
    def _inner(f):
        def _new_func(oldfunc, result, oldfunc_args, oldfunc_kwargs):
            result.append(oldfunc(*oldfunc_args, **oldfunc_kwargs))

        def __inner(*args, **kwargs):
            result = []
            new_kwargs = {
                'oldfunc': f,
                'result': result,
                'oldfunc_args': args,
                'oldfunc_kwargs': kwargs
            }

            thd = threading.Thread(target=_new_func, args=(), kwargs=new_kwargs)
            thd.start()
            return result[0]



        return __inner
    return _inner


def get_stop_flag():
    time.sleep(5)
    return True

def my_fun(x):
    print('start')
    time.sleep(10)
    print('over')


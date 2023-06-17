import ctypes
import threading
import time

import requests


class ThreadKillAble(threading.Thread):
    task_id = None
    killed = False
    event_kill = threading.Event()


def kill_thread(thread_id):
    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.py_object(SystemExit))


class ThreadHasKilled(Exception):
    pass


def kill_thread_by_task_id(task_id):
    for t in threading.enumerate():
        if isinstance(t, ThreadKillAble):
            thread_task_id = getattr(t, 'task_id', None)
            if thread_task_id == task_id:
                t.killed = True
                t.event_kill.set()
                kill_thread(t.ident)


def kill_fun_deco(task_id):
    def _inner(f):
        def __inner(*args, **kwargs):
            def _new_func(oldfunc, result, oldfunc_args, oldfunc_kwargs):
                result.append(oldfunc(*oldfunc_args, **oldfunc_kwargs))
                threading.current_thread().event_kill.set()   # noqa

            result = []
            new_kwargs = {
                'oldfunc': f,
                'result': result,
                'oldfunc_args': args,
                'oldfunc_kwargs': kwargs
            }

            thd = ThreadKillAble(target=_new_func, args=(), kwargs=new_kwargs)
            thd.task_id = task_id
            thd.event_kill = threading.Event()
            thd.start()
            thd.event_kill.wait()
            if not result and thd.killed is True:
                raise ThreadHasKilled(f'线程已被杀死 {thd.task_id}')
            return result[0]

        return __inner

    return _inner


if __name__ == '__main__':
    import nb_log
    test_lock = threading.Lock()
    @kill_fun_deco(task_id='task1234')
    def my_fun(x):
        test_lock.acquire()
        print(f'start {x}')
        resp = requests.get('http://127.0.0.1:5000') # flask接口里面sleep30秒，
        print(resp.text)
        # for i in range(10):
        #     time.sleep(2)
        test_lock.release()
        print(f'over {x}')
        return 666


    @kill_fun_deco(task_id='task5678')
    def my_fun2(x):
        test_lock.acquire()
        print(f'start {x}')
        resp = requests.get('http://127.0.0.1:5000')
        print(resp.text)
        # for i in range(10):
        #     time.sleep(2)
        test_lock.release()
        print(f'over {x}')
        return 666


    def kill_thread_by_task(task_id):
        time.sleep(5)
        kill_thread_by_task_id(task_id)


    threading.Thread(target=kill_thread_by_task,args=('task1234',)).start()
    threading.Thread(target=my_fun, args=(777,)).start()
    threading.Thread(target=my_fun2, args=(888,)).start()

    """
    强行杀死线程，会导致锁一直不能释放
    """



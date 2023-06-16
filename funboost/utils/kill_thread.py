import ctypes
import threading
import time


class ThreadKillAble(threading.Thread):
    task_id = None
    killed = False
    ev = threading.Event()


def kill_thread(thread_id):
    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.py_object(SystemExit))


class ThreadHasKilled(Exception):
    pass


def kill_thread_by_task_id(task_id):
    for t in threading.enumerate():
        if isinstance(t, ThreadKillAble):
            if t.task_id == task_id:
                t.killed = True
                t.ev.set()
                kill_thread(t.ident)


def kill_fun_deco(task_id):
    def _inner(f):
        def __inner(*args, **kwargs):
            def _new_func(oldfunc, result, oldfunc_args, oldfunc_kwargs):
                result.append(oldfunc(*oldfunc_args, **oldfunc_kwargs))
                current_thread = threading.currentThread()  # type:ThreadKillAble
                current_thread.ev.set()

            result = []
            new_kwargs = {
                'oldfunc': f,
                'result': result,
                'oldfunc_args': args,
                'oldfunc_kwargs': kwargs
            }

            thd = ThreadKillAble(target=_new_func, args=(), kwargs=new_kwargs)
            thd.task_id = task_id
            thd.ev = threading.Event()
            thd.start()
            thd.ev.wait()
            print(thd.ev)
            # thd.join(timeout=0.1)
            if not result and thd.killed is True:
                raise ThreadHasKilled(f'线程已被杀死 {thd.task_id}')
            return result[0]

        return __inner

    return _inner


if __name__ == '__main__':
    import nb_log

    test_lock = threading.Lock()


    def my_fun(x):
        with test_lock:
            print(f'start {x}')
            time.sleep(10)
            print(f'over {x}')
            return 666


    def kill_thread_by_task(task_id):
        time.sleep(5)
        kill_thread_by_task_id('task1234')

    print(111)
    threading.Thread(target=kill_thread_by_task,args=('task1234',)).start()
    # threading.Thread(target=kill_thread_by_task, args=('task5678',)).start()
    threading.Thread(target=kill_fun_deco(task_id='task1234')(my_fun),args=(29,)).start()
    threading.Thread(target=kill_fun_deco(task_id='task5678')(my_fun), args=(30,)).start()

    print(222)

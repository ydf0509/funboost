import ctypes
import threading
import time


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
            print(thread_task_id)
            if thread_task_id == task_id:
                t.killed = True
                t.event_kill.set()
                kill_thread(t.ident)


def kill_fun_deco(task_id):
    def _inner(f):
        def __inner(*args, **kwargs):
            def _new_func(oldfunc, result, oldfunc_args, oldfunc_kwargs):
                result.append(oldfunc(*oldfunc_args, **oldfunc_kwargs))

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
    @kill_fun_deco(task_id='task1234')
    def my_fun(x):
        print('start')
        print(x)
        time.sleep(10)
        print('over')
        return 666


    def kill_thread_by_task_1234():
        time.sleep(5)
        kill_thread_by_task_id('task1234')


    threading.Thread(target=kill_thread_by_task_1234).start()

    print(111)
    try:
        print(my_fun(29))
    except Exception as e:
        print(e)
    print(222)

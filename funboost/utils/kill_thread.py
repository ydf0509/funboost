import ctypes
import threading
import time

import requests


class ThreadKillAble(threading.Thread):
    task_id = None
    killed = False
<<<<<<< HEAD
    ev = threading.Event()
=======
    event_kill = threading.Event()
>>>>>>> f2307ea1366ff218d2f6736b9de793b3fd8cfdd5


def kill_thread(thread_id):
    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.py_object(SystemExit))


class ThreadHasKilled(Exception):
    pass


def kill_thread_by_task_id(task_id):
    for t in threading.enumerate():
        print(t)
        if isinstance(t, ThreadKillAble):
<<<<<<< HEAD
            if t.task_id == task_id:
=======
            thread_task_id = getattr(t, 'task_id', None)
            if thread_task_id == task_id:
>>>>>>> f2307ea1366ff218d2f6736b9de793b3fd8cfdd5
                t.killed = True
                t.event_kill.set()
                kill_thread(t.ident)


def kill_fun_deco(task_id):
    def _inner(f):
        def __inner(*args, **kwargs):
            def _new_func(oldfunc, result, oldfunc_args, oldfunc_kwargs):
                result.append(oldfunc(*oldfunc_args, **oldfunc_kwargs))
<<<<<<< HEAD
                current_thread = threading.currentThread()  # type:ThreadKillAble
                current_thread.ev.set()
=======
                threading.current_thread().event_kill.set()   # noqa
>>>>>>> f2307ea1366ff218d2f6736b9de793b3fd8cfdd5

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
<<<<<<< HEAD
            thd.ev.wait()
            print(thd.ev)
            # thd.join(timeout=0.1)
=======
            thd.event_kill.wait()
>>>>>>> f2307ea1366ff218d2f6736b9de793b3fd8cfdd5
            if not result and thd.killed is True:
                raise ThreadHasKilled(f'线程已被杀死 {thd.task_id}')
            return result[0]

        return __inner

    return _inner


if __name__ == '__main__':
    import nb_log
<<<<<<< HEAD

    test_lock = threading.Lock()


    def my_fun(x):
        with test_lock:
            print(f'start {x}')
            time.sleep(10)
            print(f'over {x}')
            return 666


=======
    test_lock = threading.Lock()
    @kill_fun_deco(task_id='task1234')
    def my_fun(x):
        test_lock.acquire()
        print(f'start {x}')
        resp = requests.get('http://127.0.0.1:5000')
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


>>>>>>> f2307ea1366ff218d2f6736b9de793b3fd8cfdd5
    def kill_thread_by_task(task_id):
        time.sleep(5)
        kill_thread_by_task_id(task_id)

<<<<<<< HEAD
    print(111)
    threading.Thread(target=kill_thread_by_task,args=('task1234',)).start()
    # threading.Thread(target=kill_thread_by_task, args=('task5678',)).start()
    threading.Thread(target=kill_fun_deco(task_id='task1234')(my_fun),args=(29,)).start()
    threading.Thread(target=kill_fun_deco(task_id='task5678')(my_fun), args=(30,)).start()

    print(222)
=======

    threading.Thread(target=kill_thread_by_task,args=('task1234',)).start()
    threading.Thread(target=my_fun, args=(777,)).start()
    threading.Thread(target=my_fun2, args=(888,)).start()


>>>>>>> f2307ea1366ff218d2f6736b9de793b3fd8cfdd5

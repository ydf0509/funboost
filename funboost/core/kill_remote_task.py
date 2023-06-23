import ctypes
import threading
import time
from funboost.utils.time_util import DatetimeConverter
from funboost.utils.redis_manager import RedisMixin
import nb_log


class ThreadKillAble(threading.Thread):
    task_id = None
    killed = False
    event_kill = threading.Event()


def kill_thread(thread_id):
    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.py_object(SystemExit))


class TaskHasKilledError(Exception):
    pass


def kill_fun_deco(task_id):
    def _inner(f):
        def __inner(*args, **kwargs):
            def _new_func(oldfunc, result, oldfunc_args, oldfunc_kwargs):
                result.append(oldfunc(*oldfunc_args, **oldfunc_kwargs))
                threading.current_thread().event_kill.set()  # noqa

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
                raise TaskHasKilledError(f'{DatetimeConverter()} 线程已被杀死 {thd.task_id}')
            return result[0]

        return __inner

    return _inner


def kill_thread_by_task_id(task_id):
    for t in threading.enumerate():
        if isinstance(t, ThreadKillAble):
            thread_task_id = getattr(t, 'task_id', None)
            if thread_task_id == task_id:
                t.killed = True
                t.event_kill.set()
                kill_thread(t.ident)


kill_task = kill_thread_by_task_id


class RemoteTaskKillerZset(RedisMixin, nb_log.LoggerMixin):
    """
    zset实现的，需要zrank 并发数次。
    """

    def __init__(self, queue_name, task_id):
        self.queue_name = queue_name
        self.task_id = task_id
        self._redis_zset_key = f'funboost_kill_task:{queue_name}'
        self._lsat_kill_task_ts = time.time()

    def send_remote_task_comd(self):
        self.redis_db_frame_version3.zadd(self._redis_zset_key, {self.task_id: time.time()})

    def judge_need_revoke_run(self):
        if self.redis_db_frame_version3.zrank(self._redis_zset_key, self.task_id) is not None:
            self.redis_db_frame_version3.zrem(self._redis_zset_key, self.task_id)
            return True
        return False

    def kill_local_task(self):
        kill_task(self.task_id)

    def start_cycle_kill_task(self):
        def _start_cycle_kill_task():
            while 1:
                for t in threading.enumerate():
                    if isinstance(t, ThreadKillAble):
                        thread_task_id = getattr(t, 'task_id', None)
                        if self.redis_db_frame_version3.zrank(self._redis_zset_key, thread_task_id) is not None:
                            self.redis_db_frame_version3.zrem(self._redis_zset_key, thread_task_id)
                            t.killed = True
                            t.event_kill.set()
                            kill_thread(t.ident)
                            self._lsat_kill_task_ts = time.time()
                            self.logger.warning(f'队列 {self.queue_name} 的 任务 {thread_task_id} 被杀死')
                if time.time() - self._lsat_kill_task_ts < 2:
                    time.sleep(0.001)
                else:
                    time.sleep(5)

        threading.Thread(target=_start_cycle_kill_task).start()


class RemoteTaskKiller(RedisMixin, nb_log.LoggerMixin):
    """
    hash实现的，只需要 hmget 一次
    """

    def __init__(self, queue_name, task_id):
        self.queue_name = queue_name
        self.task_id = task_id
        # self.redis_zset_key = f'funboost_kill_task:{queue_name}'
        self._redis_hash_key = f'funboost_kill_task_hash:{queue_name}'
        self._lsat_kill_task_ts = 0  # time.time()

    def send_remote_task_comd(self):
        # self.redis_db_frame_version3.zadd(self.redis_zset_key, {self.task_id: time.time()})
        self.redis_db_frame_version3.hset(self._redis_hash_key, key=self.task_id, value=time.time())

    def judge_need_revoke_run(self):
        if self.redis_db_frame_version3.hexists(self._redis_hash_key, self.task_id):
            self.redis_db_frame_version3.hdel(self._redis_hash_key, self.task_id)
            return True
        return False

    def kill_local_task(self):
        kill_task(self.task_id)

    def start_cycle_kill_task(self):
        def _start_cycle_kill_task():
            while 1:
                if time.time() - self._lsat_kill_task_ts < 2:
                    time.sleep(0.01)
                else:
                    time.sleep(5)

                thread_task_id_list = []
                task_id__thread_map = {}
                for t in threading.enumerate():
                    if isinstance(t, ThreadKillAble):
                        thread_task_id = getattr(t, 'task_id', None)
                        thread_task_id_list.append(thread_task_id)
                        task_id__thread_map[thread_task_id] = t
                if thread_task_id_list:
                    values = self.redis_db_frame_version3.hmget(self._redis_hash_key, keys=thread_task_id_list)
                    for idx, thread_task_id in enumerate(thread_task_id_list):
                        if values[idx] is not None:
                            self.redis_db_frame_version3.hdel(self._redis_hash_key, thread_task_id)
                            t = task_id__thread_map[thread_task_id]
                            t.killed = True
                            t.event_kill.set()
                            kill_thread(t.ident)
                            self._lsat_kill_task_ts = time.time()
                            self.logger.warning(f'队列 {self.queue_name} 的 任务 {thread_task_id} 被杀死')

        threading.Thread(target=_start_cycle_kill_task).start()


if __name__ == '__main__':

    test_lock = threading.Lock()


    def my_fun(x):
        """
        使用lock.acquire(),强行杀死会一直无法释放锁
        """
        test_lock.acquire()
        print(f'start {x}')
        # resp = requests.get('http://127.0.0.1:5000')  # flask接口里面sleep30秒，
        # print(resp.text)
        for i in range(10):
            time.sleep(2)
        test_lock.release()
        print(f'over {x}')
        return 666


    def my_fun2(x):
        """
        使用with lock,强行杀死会不会出现一直无法释放锁
        """
        with test_lock:
            print(f'start {x}')
            # resp = requests.get('http://127.0.0.1:5000')  # flask接口里面sleep30秒，
            # print(resp.text)
            for i in range(10):
                time.sleep(2)
            print(f'over {x}')
            return 666


    threading.Thread(target=kill_fun_deco(task_id='task1234')(my_fun2), args=(777,)).start()
    threading.Thread(target=kill_fun_deco(task_id='task5678')(my_fun2), args=(888,)).start()
    time.sleep(5)
    # kill_thread_by_task_id('task1234')

    k = RemoteTaskKiller('test_kill_queue', 'task1234')
    k.start_cycle_kill_task()
    k.send_remote_task_comd()

    """
    第一种代码：
    test_lock.acquire()
    执行io耗时代码
    test_lock.release()
    如果使用lock.acquire()获得锁以后，执行耗时代码时候，还没有执行lock.release() 强行杀死线程，会导致锁一直不能释放
    
    第二种代码
    with test_lock:
        执行io耗时代码
    使用with lock 获得锁以后，执行耗时代码时候，强行杀死线程，则不会导致锁一直不能释放
    
    """

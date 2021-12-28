"""
可自动实时调节线程数量的线程池。
比官方ThreadpoolExecutor的改进是
1.有界队列
2.实时调节线程数量，指的是当任务很少时候会去关闭很多线程。官方ThreadpoolExecurot只能做到忙时候开启很多线程，但不忙时候线程没有关闭线程，
此线程池实现了java ThreadpoolExecutor线程池的keppaliveTime参数的功能，linux系统能承受的线程总数有限，一般不到2万。
3.能非常智能节制的开启多线程。比如设置线程池大小为500，线程池的运行函数消耗时间是只需要0.1秒，如果每隔2秒钟来一个任务。1个线程足够了，官方线程池是一直增长到500，然后不增长，官方的太不智能了。

这个线程池是框架的默认线程方式的线程池，如果不设置并发方式就用的这里。

此实现了submit，但没实现future相关的内容。
"""

import atexit
import queue
import sys
import threading
import time
import weakref

from nb_log import LoggerMixin, nb_print, LoggerLevelSetterMixin, LogManager
from funboost.concurrent_pool.custom_evenlet_pool_executor import check_evenlet_monkey_patch
from funboost.concurrent_pool.custom_gevent_pool_executor import check_gevent_monkey_patch

_shutdown = False
_threads_queues = weakref.WeakKeyDictionary()


def _python_exit():
    global _shutdown
    _shutdown = True
    items = list(_threads_queues.items())
    for t, q in items:
        q.put(None)
    for t, q in items:
        t.join()


atexit.register(_python_exit)


class _WorkItem(LoggerMixin):
    def __init__(self, fn, args, kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        # noinspection PyBroadException
        try:
            self.fn(*self.args, **self.kwargs)
        except BaseException as exc:
            self.logger.exception(f'函数 {self.fn.__name__} 中发生错误，错误原因是 {type(exc)} {exc} ')

    def __str__(self):
        return f'{(self.fn.__name__, self.args, self.kwargs)}'


def check_not_monkey():
    if check_gevent_monkey_patch(raise_exc=False):
        raise Exception('请不要打gevent包的补丁')
    if check_evenlet_monkey_patch(raise_exc=False):
        raise Exception('请不要打evenlet包的补丁')


class CustomThreadPoolExecutor(LoggerMixin, LoggerLevelSetterMixin):
    def __init__(self, max_workers=None, thread_name_prefix=''):
        """
        最好需要兼容官方concurren.futures.ThreadPoolExecutor 和改版的BoundedThreadPoolExecutor，入参名字和个数保持了一致。
        :param max_workers:
        :param thread_name_prefix:
        """
        self._max_workers = max_workers or 4
        self._min_workers = 5  # 这是对应的 java Threadpoolexecutor的corePoolSize，为了保持线程池公有方法和与py官方内置的concurren.futures.ThreadPoolExecutor一致，不增加更多的实例化时候入参，这里写死为5.
        self._thread_name_prefix = thread_name_prefix
        self.work_queue = queue.Queue(max_workers)
        # self._threads = set()
        self._threads = weakref.WeakSet()
        self._lock_compute_threads_free_count = threading.Lock()
        self.threads_free_count = 0
        self._shutdown = False
        self._shutdown_lock = threading.Lock()
        # self.logger.setLevel(20)

    def set_min_workers(self, min_workers=10):
        self._min_workers = min_workers
        return self

    def change_threads_free_count(self, change_num):
        with self._lock_compute_threads_free_count:
            self.threads_free_count += change_num

    def submit(self, func, *args, **kwargs):
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('不能添加新的任务到线程池')
        self.work_queue.put(_WorkItem(func, args, kwargs))
        self._adjust_thread_count()

    def _adjust_thread_count(self):
        # if len(self._threads) < self._threads_num:
        # self.logger.debug((self.threads_free_count, len(self._threads), len(_threads_queues), get_current_threads_num()))
        if self.threads_free_count < self._min_workers and len(self._threads) < self._max_workers:
            # t = threading.Thread(target=_work,
            #                      args=(self._work_queue,self))
            t = _CustomThread(self).set_log_level(self.logger.level)
            t.setDaemon(True)
            t.start()
            self._threads.add(t)
            _threads_queues[t] = self.work_queue

    def shutdown(self, wait=True):
        with self._shutdown_lock:
            self._shutdown = True
            self.work_queue.put(None)
        if wait:
            for t in self._threads:
                t.join()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown(wait=True)
        return False


class _CustomThread(threading.Thread, LoggerMixin, LoggerLevelSetterMixin):
    _lock_for_judge_threads_free_count = threading.Lock()

    def __init__(self, executorx: CustomThreadPoolExecutor):
        super().__init__()
        self._executorx = executorx
        self._run_times = 0

    # noinspection PyProtectedMember
    def _remove_thread(self, stop_resson=''):
        # noinspection PyUnresolvedReferences
        self.logger.debug(f'停止线程 {self._ident}, 触发条件是 {stop_resson} ')
        self._executorx.change_threads_free_count(-1)
        self._executorx._threads.remove(self)
        _threads_queues.pop(self)

    # noinspection PyProtectedMember
    def run(self):
        # noinspection PyUnresolvedReferences
        self.logger.debug(f'新启动线程 {self._ident} ')
        self._executorx.change_threads_free_count(1)
        while True:
            try:
                work_item = self._executorx.work_queue.get(block=True, timeout=60)
            except queue.Empty:
                with self._lock_for_judge_threads_free_count:
                    if self._executorx.threads_free_count > self._executorx._min_workers:
                        self._remove_thread(f'当前线程超过60秒没有任务，线程池中不在工作状态中的线程数量是 {self._executorx.threads_free_count}，超过了指定的数量 {self._executorx._min_workers}')
                        break  # 退出while 1，即是结束。这里才是决定线程结束销毁，_remove_thread只是个名字而已，不是由那个来销毁线程。
                    else:
                        continue

            # nb_print(work_item)
            if work_item is not None:
                self._executorx.change_threads_free_count(-1)
                work_item.run()
                del work_item
                self._executorx.change_threads_free_count(1)
                continue
            if _shutdown or self._executorx._shutdown:
                self._executorx.work_queue.put(None)
                break


process_name_set = set()
logger_show_current_threads_num = LogManager('show_current_threads_num').get_logger_and_add_handlers(
    formatter_template=5, log_filename='show_current_threads_num.log', do_not_use_color_handler=True)


def show_current_threads_num(sleep_time=60, process_name='', block=False):
    process_name = sys.argv[0] if process_name == '' else process_name

    def _show_current_threads_num():
        while True:
            # logger_show_current_threads_num.info(f'{process_name} 进程 的 并发数量是 -->  {threading.active_count()}')
            nb_print(f'{process_name} 进程 的 线程数量是 -->  {threading.active_count()}')
            time.sleep(sleep_time)

    if process_name not in process_name_set:
        if block:
            _show_current_threads_num()
        else:
            t = threading.Thread(target=_show_current_threads_num, daemon=True)
            t.start()
        process_name_set.add(process_name)


def get_current_threads_num():
    return threading.active_count()


if __name__ == '__main__':
    from funboost.utils import decorators
    from funboost.concurrent_pool.bounded_threadpoolexcutor import BoundedThreadPoolExecutor


    # @decorators.keep_circulating(1)
    def f1(a):
        time.sleep(0.2)
        nb_print(f'{a} 。。。。。。。')
        # raise Exception('抛个错误测试')


    # show_current_threads_num()
    pool = CustomThreadPoolExecutor(200).set_log_level(10).set_min_workers()
    # pool = BoundedThreadPoolExecutor(200)   # 测试对比原来写的BoundedThreadPoolExecutor
    show_current_threads_num(sleep_time=5)
    for i in range(300):
        time.sleep(0.3)  # 这里的间隔时间模拟，当任务来临不密集，只需要少量线程就能搞定f1了，因为f1的消耗时间短，不需要开那么多线程，CustomThreadPoolExecutor比BoundedThreadPoolExecutor 优势之一。
        pool.submit(f1, str(i))

    nb_print(6666)
    # pool.shutdown(wait=True)
    pool.submit(f1, 'yyyy')

    # 下面测试阻塞主线程退出的情况。注释掉可以测主线程退出的情况。
    while True:
        time.sleep(10)

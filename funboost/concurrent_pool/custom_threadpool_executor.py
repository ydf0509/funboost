"""
史上最强的python线程池。

最智能的可自动实时调节线程数量的线程池。此线程池和官方concurrent.futures的线程池 是鸭子类关系，所以可以一键替换类名 或者 import as来替换类名。
对比官方线程池，有4个创新功能或改进。

1、主要是不仅能扩大，还可自动缩小(官方内置的ThreadpoolExecutor不具备此功能，此概念是什么意思和目的，可以百度java ThreadpoolExecutor的KeepAliveTime参数的介绍)，
   例如实例化一个1000线程的线程池，上一分钟疯狂高频率的对线程池submit任务，线程池会扩张到最大线程数量火力全开运行，
   但之后的七八个小时平均每分钟只submit一两个任务，官方线程池会一直维持在1000线程，而此线程池会自动缩小，靠什么来识别预测啥时机可以自动缩小呢，就是KeepAliveTime。

2、非常节制的开启多线程，例如实例化一个最大100线程数目的pool，每隔2秒submit一个函数任务，而函数每次只需要1秒就能完成，实际上只需要调节增加到1个线程就可以，不需要慢慢增加到100个线程
官方的线程池不够智能，会一直增加到最大线程数目，此线程池则不会。

3、线程池任务的queue队列，修改为有界队列

4、此线程池运行函数出错时候，直接显示线程错误，官方的线程池则不会显示错误，例如函数中写1/0,任然不现实错误。

此实现了submit，还实现future相关的内容，真正的和内置的ThreadpoolExecutor 完全替代。

可以在各种地方加入 time.sleep 来验证 第1条和第2条的自动智能缩放功能。
"""
import os
import atexit
import queue
import sys
import threading
import time
import weakref
from nb_log import LoggerMixin, nb_print, LoggerLevelSetterMixin, LogManager
from concurrent.futures import Executor, Future

from funboost.concurrent_pool.custom_evenlet_pool_executor import check_evenlet_monkey_patch
from funboost.concurrent_pool.custom_gevent_pool_executor import check_gevent_monkey_patch

_shutdown = False
_threads_queues = weakref.WeakKeyDictionary()


def check_not_monkey():
    if check_gevent_monkey_patch(raise_exc=False):
        raise Exception('指定使用多线程模式时候，请不要打gevent包的补丁')
    if check_evenlet_monkey_patch(raise_exc=False):
        raise Exception('指定使用多线程模式时候，请不要打evenlet包的补丁')


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
    def __init__(self, future, fn, args, kwargs):
        self.future = future
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        # noinspection PyBroadException
        if not self.future.set_running_or_notify_cancel():
            return
        try:
            result = self.fn(*self.args, **self.kwargs)
        except BaseException as exc:
            self.logger.exception(f'函数 {self.fn.__name__} 中发生错误，错误原因是 {type(exc)} {exc} ')
            self.future.set_exception(exc)
            # Break a reference cycle with the exception 'exc'
            self = None  # noqa
        else:
            self.future.set_result(result)

    def __str__(self):
        return f'{(self.fn.__name__, self.args, self.kwargs)}'


def set_threadpool_executor_shrinkable(min_works=1, keep_alive_time=5):
    ThreadPoolExecutorShrinkAble.MIN_WORKERS = min_works
    ThreadPoolExecutorShrinkAble.KEEP_ALIVE_TIME = keep_alive_time


class ThreadPoolExecutorShrinkAble(Executor, LoggerMixin, LoggerLevelSetterMixin):
    # 为了和官方自带的THredpoolexecutor保持完全一致的鸭子类，参数设置成死的，不让用户传参了。
    # 建议用猴子补丁修改这两个参数，为了保持入参api和内置的concurrent.futures 相同。
    # MIN_WORKERS = 5   # 最小值可以设置为0，代表线程池无论多久没有任务最少要保持多少个线程待命。
    # KEEP_ALIVE_TIME = 60  # 这个参数表名，当前线程从queue.get(block=True, timeout=KEEP_ALIVE_TIME)多久没任务，就线程结束。

    MIN_WORKERS = 5
    KEEP_ALIVE_TIME = 60

    def __init__(self, max_workers: int = None, thread_name_prefix=''):
        """
        最好需要兼容官方concurren.futures.ThreadPoolExecutor 和改版的BoundedThreadPoolExecutor，入参名字和个数保持了一致。
        :param max_workers:
        :param thread_name_prefix:
        """
        # print(max_workers)
        self._max_workers = max_workers or (os.cpu_count() or 1) * 5
        self._thread_name_prefix = thread_name_prefix
        # print(self._max_workers)
        # self.work_queue = self._work_queue = queue.Queue(self._max_workers or 10)
        self.work_queue = self._work_queue = queue.Queue(10)
        # self._threads = set()
        self._threads = weakref.WeakSet()
        self._lock_compute_threads_free_count = threading.Lock()
        self.threads_free_count = 0
        self._shutdown = False
        self._shutdown_lock = threading.Lock()
        self.pool_ident = id(self)

    def _change_threads_free_count(self, change_num):
        with self._lock_compute_threads_free_count:
            self.threads_free_count += change_num

    def submit(self, func, *args, **kwargs):
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('不能添加新的任务到线程池')
            f = Future()
            w = _WorkItem(f, func, args, kwargs)
            self.work_queue.put(w)
            self._adjust_thread_count()
            return f

    def _adjust_thread_count(self):
        # print(self.threads_free_count, self.MIN_WORKERS, len(self._threads), self._max_workers)
        if self.threads_free_count <= self.MIN_WORKERS and len(self._threads) < self._max_workers:
            t = _CustomThread(self).set_log_level(self.logger.level)
            t.daemon = True
            t.start()
            self._threads.add(t)
            _threads_queues[t] = self._work_queue

    def shutdown(self, wait=True):  # noqa
        with self._shutdown_lock:
            self._shutdown = True
            self.work_queue.put(None)
        if wait:
            for t in self._threads:
                t.join()


# 两个名字都可以，兼容以前的老名字（中文意思是 自定义线程池），但新名字更能表达意思（可缩小线程池）。
CustomThreadpoolExecutor = CustomThreadPoolExecutor = ThreadPoolExecutorShrinkAble


# noinspection PyProtectedMember
class _CustomThread(threading.Thread, LoggerMixin, LoggerLevelSetterMixin):
    _lock_for_judge_threads_free_count = threading.Lock()

    def __init__(self, executorx: ThreadPoolExecutorShrinkAble):
        super().__init__()
        self._executorx = executorx

    def _remove_thread(self, stop_resson=''):
        # noinspection PyUnresolvedReferences
        self.logger.debug(f'停止线程 {self._ident}, 触发条件是 {stop_resson} ')
        self._executorx._change_threads_free_count(-1)
        self._executorx._threads.remove(self)
        _threads_queues.pop(self)

    # noinspection PyProtectedMember
    def run(self):
        # noinspection PyUnresolvedReferences
        self.logger.debug(f'新启动线程 {self._ident} ')
        self._executorx._change_threads_free_count(1)
        while True:
            try:
                work_item = self._executorx.work_queue.get(block=True, timeout=self._executorx.KEEP_ALIVE_TIME)
            except queue.Empty:
                # continue
                # self._remove_thread()
                with self._lock_for_judge_threads_free_count:
                    if self._executorx.threads_free_count > self._executorx.MIN_WORKERS:
                        self._remove_thread(
                            f'{self._executorx.pool_ident} 线程池中的 {self.ident} 线程 超过 {self._executorx.KEEP_ALIVE_TIME} 秒没有任务，线程池中不在工作状态中的线程数量是 '
                            f'{self._executorx.threads_free_count}，超过了指定的最小核心数量 {self._executorx.MIN_WORKERS}')
                        break  # 退出while 1，即是结束。这里才是决定线程结束销毁，_remove_thread只是个名字而已，不是由那个来销毁线程。
                    else:
                        continue

            if work_item is not None:
                self._executorx._change_threads_free_count(-1)
                work_item.run()
                del work_item
                self._executorx._change_threads_free_count(1)
                continue
            if _shutdown or self._executorx._shutdown:
                self._executorx.work_queue.put(None)
                break


process_name_set = set()
logger_show_current_threads_num = LogManager('show_current_threads_num').get_logger_and_add_handlers(
    formatter_template=5, log_filename='show_current_threads_num.log', do_not_use_color_handler=False)


def show_current_threads_num(sleep_time=600, process_name='', block=False, daemon=True):
    """另起一个线程每隔多少秒打印有多少线程，这个和可缩小线程池的实现没有关系"""
    process_name = sys.argv[0] if process_name == '' else process_name

    def _show_current_threads_num():
        while True:
            # logger_show_current_threads_num.info(f'{process_name} 进程 的 并发数量是 -->  {threading.active_count()}')
            # nb_print(f'  {process_name} {os.getpid()} 进程 的 线程数量是 -->  {threading.active_count()}')
            logger_show_current_threads_num.info(
                f'  {process_name} {os.getpid()} 进程 的 线程数量是 -->  {threading.active_count()}')
            time.sleep(sleep_time)

    if process_name not in process_name_set:
        if block:
            _show_current_threads_num()
        else:
            t = threading.Thread(target=_show_current_threads_num, daemon=daemon)
            t.start()
        process_name_set.add(process_name)


def get_current_threads_num():
    return threading.active_count()


if __name__ == '__main__':
    show_current_threads_num(sleep_time=5)


    def f1(a):
        time.sleep(0.2)  # 可修改这个数字测试多线程数量调节功能。
        nb_print(f'{a} 。。。。。。。')
        return a * 10
        # raise Exception('抛个错误测试')  # 官方的不会显示函数出错你，你还以为你写的代码没毛病呢。


    pool = ThreadPoolExecutorShrinkAble(1)
    # pool = ThreadPoolExecutor(200)  # 测试对比官方自带

    for i in range(30):
        time.sleep(0.1)  # 这里的间隔时间模拟，当任务来临不密集，只需要少量线程就能搞定f1了，因为f1的消耗时间短，
        # 不需要开那么多线程，CustomThreadPoolExecutor比ThreadPoolExecutor 优势之一。
        futurex = pool.submit(f1, i)
        # print(futurex.result())

    # 1/下面测试阻塞主线程退出的情况。注释掉可以测主线程退出的情况。
    # 2/此代码可以证明，在一段时间后，连续长时间没任务，官方线程池的线程数目还是保持在最大数量了。而此线程池会自动缩小，实现了java线程池的keppalivetime功能。
    time.sleep(1000000)

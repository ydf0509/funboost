# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/7/3 10:35
import atexit
import time
import warnings
# from eventlet import greenpool, monkey_patch, patcher, Timeout

from funboost.concurrent_pool import FunboostBaseConcurrentPool
from funboost.core.loggers import get_funboost_file_logger
# print('eventlet 导入')
from funboost.core.lazy_impoter import EventletImporter


def check_evenlet_monkey_patch(raise_exc=True):
    try:
        if not EventletImporter().patcher.is_monkey_patched('socket'):  # 随便选一个检测标志
            if raise_exc:
                warnings.warn(f'检测到没有打 evenlet 包的猴子补丁 ,请在起始脚本文件首行加上     import eventlet;eventlet.monkey_patch(all=True) ')
                raise Exception('检测到没有打 evenlet 包的猴子补丁 ,请在起始脚本文件首行加上    import eventlet;eventlet.monkey_patch(all=True)')
        else:
            return 1
    except ModuleNotFoundError:
        if raise_exc:
            warnings.warn(f'检测到没有打 evenlet 包的猴子补丁 ,请在起始脚本文件首行加上     import eventlet;eventlet.monkey_patch(all=True) ')
            raise Exception('检测到没有打 evenlet 包的猴子补丁 ,请在起始脚本文件首行加上    import eventlet;eventlet.monkey_patch(all=True)')


logger_evenlet_timeout_deco = get_funboost_file_logger('evenlet_timeout_deco')


def evenlet_timeout_deco(timeout_t):
    def _evenlet_timeout_deco(f):
        def __evenlet_timeout_deco(*args, **kwargs):
            timeout = EventletImporter().Timeout(timeout_t, )
            # timeout.start()  # 与gevent不一样,直接start了。
            result = None
            try:
                result = f(*args, **kwargs)
            except EventletImporter().Timeout as t:
                logger_evenlet_timeout_deco.error(f'函数 {f} 运行超过了 {timeout_t} 秒')
                if t is not timeout:
                    print(t)
                    # raise  # not my timeout
            finally:
                timeout.cancel()
                return result

        return __evenlet_timeout_deco

    return _evenlet_timeout_deco


def get_eventlet_pool_executor(*args2, **kwargs2):
    class CustomEventletPoolExecutor(EventletImporter().greenpool.GreenPool, FunboostBaseConcurrentPool):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            check_evenlet_monkey_patch()  # basecomer.py中检查。
            atexit.register(self.shutdown)

        def submit(self, *args, **kwargs):  # 保持为一直的公有用法。
            # nb_print(args)
            self.spawn_n(*args, **kwargs)
            # self.spawn_n(*args, **kwargs)

        def shutdown(self):
            self.waitall()

    return CustomEventletPoolExecutor(*args2, **kwargs2)


if __name__ == '__main__':
    # greenpool.GreenPool.waitall()
    EventletImporter().monkey_patch(all=True)


    def f2(x):

        time.sleep(2)
        print(x)


    pool = get_eventlet_pool_executor(4)

    for i in range(15):
        print(f'放入{i}')
        pool.submit(evenlet_timeout_deco(8)(f2), i)

# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/7/3 10:35
import atexit
import time
import warnings
from eventlet import greenpool, monkey_patch, patcher, Timeout

from nb_log import LogManager, nb_print


def check_evenlet_monkey_patch(raise_exc=True):
    if not patcher.is_monkey_patched('socket'):  # 随便选一个检测标志
        if raise_exc:
            warnings.warn(f'检测到没有打 evenlet 包的猴子补丁 ,请在起始脚本文件首行加上     import eventlet;eventlet.monkey_patch(all=True) ')
            raise Exception('检测到没有打 evenlet 包的猴子补丁 ,请在起始脚本文件首行加上    import eventlet;eventlet.monkey_patch(all=True)')
    else:
        return 1


logger_evenlet_timeout_deco = LogManager('evenlet_timeout_deco').get_logger_and_add_handlers()


def evenlet_timeout_deco(timeout_t):
    def _evenlet_timeout_deco(f):
        def __evenlet_timeout_deco(*args, **kwargs):
            timeout = Timeout(timeout_t, )
            # timeout.start()  # 与gevent不一样,直接start了。
            result = None
            try:
                result = f(*args, **kwargs)
            except Timeout as t:
                logger_evenlet_timeout_deco.error(f'函数 {f} 运行超过了 {timeout_t} 秒')
                if t is not timeout:
                    nb_print(t)
                    # raise  # not my timeout
            finally:
                timeout.cancel()
                return result

        return __evenlet_timeout_deco

    return _evenlet_timeout_deco


class CustomEventletPoolExecutor(greenpool.GreenPool):
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


if __name__ == '__main__':
    # greenpool.GreenPool.waitall()
    monkey_patch(all=True)


    def f2(x):

        time.sleep(2)
        nb_print(x)


    pool = CustomEventletPoolExecutor(4)

    for i in range(15):
        nb_print(f'放入{i}')
        pool.submit(evenlet_timeout_deco(8)(f2), i)

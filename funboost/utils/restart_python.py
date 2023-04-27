import datetime
import os
import sys
import threading
import time

import nb_log

# print(sys.path)

logger = nb_log.get_logger('restart_program')

""" 这个只能在 win cmd 或者 linux下测试重启功能，
   不能在pycharm中观察有无打印来判断是否重启了，因为重启后python进程变化了，pycharm控制台不能捕捉到新进程的打印输出，所以不要在pycharm下运行python来验证重启功能。

"""


def restart_program(seconds):
    '''
    间隔n秒重启脚本
    :param seconds:
    :return:
    '''
    """ 
    这个只能在 win cmd 或者 linux下测试重启功能，
    不能在pycharm中观察有无打印来判断是否重启了，因为重启后python进程变化了，pycharm控制台不能捕捉到新进程的打印输出，所以不要在pycharm下运行python来验证重启功能。
    """

    def _restart_program():
        time.sleep(seconds)
        python = sys.executable
        logger.warning(f'重启当前python程序 {python} , {sys.argv}')
        os.execl(python, python, *sys.argv)

    threading.Thread(target=_restart_program).start()


def _run():
    print(datetime.datetime.now(),'开始运行程序')
    for i in range(1000):
        time.sleep(0.5)
        print(datetime.datetime.now(),i)

if __name__ == '__main__':
    restart_program(10)  # 每隔10秒重启。
    _run()

import threading
import os
import requests
import time

from  loguru  import logger
import nb_log
g_x = 666


def heavy_task2(x, y):
    print(f"[{threading.get_ident()}] heavy_task: {x} + {y}")
    print('pid:', os.getpid(), g_x)
    # nb_log.warning('wwwwwwww')
    print('fffffffffff')
    logger.debug('hhhhhhhhhhhh')
    print(requests.get('https://www.baidu.com/').content)
    # simulate work
    while True:
        pass
    time.sleep(10)
    return x + y


if __name__ == '__main__':
    heavy_task2(1, 2)

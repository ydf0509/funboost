import os
import sys
import time


def ctrl_c_recv():
    while 1:
        try:
            time.sleep(5)
        except (KeyboardInterrupt) as e:
            # time.sleep(2)
            print(f'{e} 你按了ctrl c ,程序退出')
            time.sleep(1)
            break
    # sys.exit(4)
    os._exit(44)

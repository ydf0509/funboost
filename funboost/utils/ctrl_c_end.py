import os
import sys
import time


def ctrl_c_recv():
    for i in range(4):
        while 1:
            try:
                time.sleep(2)
            except (KeyboardInterrupt,) as e:
                # time.sleep(2)
                print(f'{type(e)} 你按了ctrl c ,程序退出, 第 {i + 1} 次', flush=True)
                # time.sleep(2)
                break
    # sys.exit(4)

    os._exit(44)
    # exit(444)

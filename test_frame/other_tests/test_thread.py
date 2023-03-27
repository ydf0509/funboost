# import threading
# from time import sleep
# import nb_log
#
# def test():
#     while 1:
#         print(123123)
#         sleep(1)
#
# if __name__ == '__main__':
#     threading.Thread(target=test).start()
#     # threading._start_new_thread(test, ())
#     print(111111111)

import os
import signal
import sys
import time
import threading

# def signal_handler(signal, frame):
#     print('You pressed Ctrl+C!')
#     # sys.exit(0)
#     os._exit(4444)
#
# signal.signal(signal.SIGINT, signal_handler)
# print('Press Ctrl+C')
# # forever = threading.Event()
# # forever.wait()
#
# while 1:
#     time.sleep(10)
from auto_run_on_remote import run_current_script_on_remote
run_current_script_on_remote()
from multiprocessing import Process
import threading

def f():
    def _f():
        while 1:
            print('hello')
            time.sleep(10)
    threading.Thread(target=_f).start()

if __name__ == '__main__':

    Process(target=f).start()
    print('start')




import multiprocessing

import threading
from multiprocessing import Process
from auto_run_on_remote import run_current_script_on_remote
run_current_script_on_remote()
import time

import os
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor

print('启动')

tp = ThreadPoolExecutor(2)

def thread_fun(x):
    # print('aaaa')
    time.sleep(10)
    print(os.getpid(),multiprocessing.current_process().pid,threading.currentThread().ident, id(tp),x,)


pp = ProcessPoolExecutor(max_workers=2)
def process_fun(pid_name):
    for i in range(100):
        tp.submit(thread_fun,f'{pid_name}-{i}')
    time.sleep(10000)

if __name__ == '__main__':

    # tp.submit(ft,666)
    # for j in range(2):
    #     pp.submit(pf,f'pidname---{j}')
    Process(target=process_fun, args=('pid111',)).start()
    Process(target=process_fun, args=('pid222',)).start()
    Process(target=process_fun, args=('pid333',)).start()




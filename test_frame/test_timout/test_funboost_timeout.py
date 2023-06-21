from auto_run_on_remote import run_current_script_on_remote
# run_current_script_on_remote()
import time

from funboost import boost

import threading

lock = threading.Lock()

@boost('test_timeout_queue',function_timeout=10,)
def f(x):
    # t1 =time.perf_counter()
    # sum =0
    # for i in range(1,10000*10000):
    #     sum+=i
    # print(time.perf_counter()-t1)
    time.sleep(x)
    lock.acquire()
    print(f'start {x}')
    time.sleep(60)
    print(f'release lock {x}')
    lock.release()
    print(f'over {x}')

if __name__ == '__main__':
    f.push(7)
    f.push(20)

    f.consume()
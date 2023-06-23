import threading


import time

from funboost.utils.decorators import timeout
from func_timeout import func_set_timeout



lock = threading.Lock()
lock2 = threading.Lock()

@timeout(2)
# @func_set_timeout(2,)
def f(x):
   lock.acquire()
   print(f'start {x}')
   time.sleep(5)
   print(f'over {x}')
   lock.release()

   # with lock:
   #     print(f'start {x}')
   #     time.sleep(5)
   #     print(f'over {x}')



@timeout(20)
# @func_set_timeout(20, )
def f2(y):
    lock.acquire()
    print(f'start {y}')
    time.sleep(5)
    print(f'over {y}')
    lock.release()

threading.Thread(target=f,args=[1]).start()
time.sleep(0.2)
threading.Thread(target=f2,args=[2]).start()


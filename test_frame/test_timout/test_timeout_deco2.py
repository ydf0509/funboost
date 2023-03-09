
import funboost
from auto_run_on_remote import run_current_script_on_remote
run_current_script_on_remote()

import time
# from funboost.utils.decorators import timeout
from func_timeout import func_set_timeout



# @timeout(100)
@func_set_timeout(2)
def f():
    sum =0
    for i in range(10000 * 10000 ):
        sum+=i
    print(sum)

t1 =time.perf_counter()

try:
    print('start')
    f()
except BaseException as e:
    print("错误:",e)

print('over')
print(time.perf_counter()-t1)




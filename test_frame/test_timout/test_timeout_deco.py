import funboost
import time
from func_timeout import func_set_timeout

from funboost.utils.decorators import timeout

# @timeout(100)
@func_set_timeout(2,allowOverride=True)
def f():
    sum =0
    for i in range(10000 * 10000 ):
        sum+=i
    print(sum)

t1 =time.perf_counter()
try:
    print('start')
    f()
except Exception as e:
    print("错误:",e)
print('over')
print(time.perf_counter()-t1)




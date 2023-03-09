from auto_run_on_remote import run_current_script_on_remote
# run_current_script_on_remote()
import time

from funboost import boost

@boost('test_timeout_queue',function_timeout=2)
def f(x):
    t1 =time.perf_counter()
    sum =0
    for i in range(1,10000*10000):
        sum+=i
    print(time.perf_counter()-t1)

if __name__ == '__main__':
    for i in range(1):
        f.push(1)
    f.consume()
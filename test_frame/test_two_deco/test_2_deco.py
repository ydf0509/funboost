import time
from functools import wraps
from function_scheduling_distributed_framework import task_deco

def my_deco(f):
    wraps(f)
    def _inner(y):
        print('开始执行',y)
        f(y)
        print('结束执行',y)
    return _inner


@task_deco('test2deco')
@my_deco
def fun(x):
    time.sleep(10)
    print(x)

if __name__ == '__main__':
    fun.push(5)
    fun.consume()



    # for i in range(10):
    #     fun.push(i)
    # fun.consume()
    # fun.multi_process_consume(2)
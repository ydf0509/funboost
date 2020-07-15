"""
测试装饰器版本方式,注意对比非装饰器版本 test_common_no_decorator_example.py
"""

from function_scheduling_distributed_framework import task_deco


@task_deco('queue_test_f01', qps=2, broker_kind=0)
def f(a, b):
    print(f'{a} + {b} = {a + b}')


if __name__ == '__main__':
    f(1000, 2000)
    for i in range(100, 200):
        f.pub(dict(a=i, b=i * 2))
    # f.clear()
    f.consume()

"""
测试装饰器版本方式,注意对比非装饰器版本 test_common_no_decorator_example.py
"""

from function_scheduling_distributed_framework import task_deco


@task_deco('queue_test_f01', qps=0.2, broker_kind=2)
def f(a, b):
    print(a + b)


for i in range(10, 20):
    f.pub(dict(a=i, b=i * 2))

f.consume()

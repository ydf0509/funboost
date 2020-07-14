"""

测试装饰器版本方式,注意对比非装饰器版本 test_common_no_decorator_example.py
"""

from function_scheduling_distributed_framework import task_deco


@task_deco('queue_test_f01', qps=0.2, broker_kind=2)
def f(a, b):
    print(a + b)


print(f)  # 可以发现函数签名被保留住了，f还是原来的f。
print(dir(f))
print(f.__dict__)

f(5, 6)  # 可以直接调用

for i in range(10, 20):
    f.pub(dict(a=i, b=i * 2))

f.consume()

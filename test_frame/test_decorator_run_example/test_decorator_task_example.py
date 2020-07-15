"""
测试装饰器版本方式,注意对比非装饰器版本 test_common_no_decorator_example.py
"""

from function_scheduling_distributed_framework import task_deco, IdeAutoCompleteHelper


@task_deco('queue_test_f01', qps=2, broker_kind=3)
def f(a, b):
    print(f'{a} + {b} = {a + b}')


if __name__ == '__main__':
    f(1000, 2000)
    f.clear()
    for i in range(100, 200):
        f.pub(dict(a=i, b=i * 2))
        IdeAutoCompleteHelper(f).pub({'a': i * 3, 'b': i * 4})  # 和上面等效，但可以自动补全方法名字和入参。

    IdeAutoCompleteHelper(f).start_consuming_message()  # f.consume() 等效


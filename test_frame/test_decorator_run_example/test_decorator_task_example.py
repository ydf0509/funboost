"""
测试装饰器版本方式,注意对比非装饰器版本 test_common_no_decorator_example.py
"""
import time

from function_scheduling_distributed_framework import task_deco, IdeAutoCompleteHelper,BrokerEnum


@task_deco('queue_test_f01', qps=1, broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE)
def f(a, b):
    print(f'{a} + {b} = {a + b}')
    # f.pub(dict(a=a + 10, b=b + 10))


if __name__ == '__main__':
    f(1000, 2000)
    f.clear()
    for i in range(100, 200):
        f.pub(dict(a=i, b=i * 2))
        f.push(i * 10, i * 20,)
        f.delay(i * 100, b=i * 200,)
        IdeAutoCompleteHelper(f).pub({'a': i * 1000, 'b': i * 2000})  # 和上面等效，但可以自动补全方法名字和入参。

    IdeAutoCompleteHelper(f).start_consuming_message()  # f.consume() 等效

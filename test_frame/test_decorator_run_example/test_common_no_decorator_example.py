"""
测试非装饰器版本方式，注意对比装饰器版本test_decorator_task_example.py
"""

from funboost import get_consumer


def f(a, b):
    print(a + b)


consumer = get_consumer('queue_test_f01', consuming_function=f, qps=0.2, broker_kind=0)

for i in range(10, 20):
    consumer.publisher_of_same_queue.publish(dict(a=i, b=i * 2))

consumer.start_consuming_message()

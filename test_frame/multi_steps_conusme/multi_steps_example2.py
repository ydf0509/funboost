from function_scheduling_distributed_framework import get_consumer, task_deco


def step1(x):
    print(f'x 的值是 {x}')
    if x == 0:
        for i in range(1, 10):
            consumer1.publisher_of_same_queue.publish(dict(x=x + i))
    for j in range(10):
        consumer2.publisher_of_same_queue.publish(dict(y=x * 100 + j))


def step2(y):
    print(f'y 的值是 {y}')


consumer1 = get_consumer('queue_test_step1', consuming_function=step1)
consumer2 = get_consumer('queue_test_step2', consuming_function=step2)
consumer1.publisher_of_same_queue.clear()

consumer1.publisher_of_same_queue.publish({'x': 0})

consumer1.start_consuming_message()
consumer2.start_consuming_message()

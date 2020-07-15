from function_scheduling_distributed_framework import get_consumer, task_deco


@task_deco('queue_test_step1')
def step1(x):
    print(f'x 的值是 {x}')
    if x == 0:
        for i in range(1, 10):
            step1.pub(dict(x=x + i))
    for j in range(10):
        step2.pub(dict(y=x * 100 + j))


@task_deco('queue_test_step2')
def step2(y):
    print(f'y 的值是 {y}')


step1.clear()
step1.pub({'x': 0})

step1.consume()
step2.consume()

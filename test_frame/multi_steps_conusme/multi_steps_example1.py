from function_scheduling_distributed_framework import  task_deco


@task_deco('queue_test_step1',qps=0.5)
def step1(x):
    print(f'x 的值是 {x}')
    if x == 0:
        for i in range(1, 30):
            step2.pub(dict(y=x + i))
    for j in range(10):
        step1.pub(dict(x=x * 100 + j))


@task_deco('queue_test_step2',qps=3)
def step2(y):
    print(f'y 的值是 {y}')


step1.clear()
step1.pub({'x': 0})

step1.consume()
step2.consume()

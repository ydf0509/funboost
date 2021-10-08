from function_scheduling_distributed_framework import task_deco,BrokerEnum


@task_deco('127.0.0.1:5690',broker_kind=BrokerEnum.TCP,log_level=20)
def f(x):
    print(x)


if __name__ == '__main__':
    f.consume()
    for i in range(10):
        f.push(f'hello {i}')

from function_scheduling_distributed_framework import task_deco,BrokerEnum


@task_deco('127.0.0.1:5689',broker_kind=BrokerEnum.UDP)
def f(x):
    print(x)


if __name__ == '__main__':
    f.consume()
    f.push('hello')

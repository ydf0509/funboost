from function_scheduling_distributed_framework import task_deco, BrokerEnum
from auto_run_on_remote import run_current_script_on_remote



@task_deco('10.0.126.147:5691', broker_kind=BrokerEnum.HTTP, log_level=10)
def f(x):
    print(x)


if __name__ == '__main__':
    # run_current_script_on_remote()
    f.consume()
    for i in range(10):
        f.push(f'hello {i}')

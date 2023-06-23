import time

from funboost import boost,BrokerEnum

@boost('test_kill_fun_queue',broker_kind=BrokerEnum.REDIS,is_support_remote_kill_task=True)
def test_kill_fun(x):
    print(f'start {x}')
    time.sleep(60)
    print(f'over {x}')


if __name__ == '__main__':
    test_kill_fun.consume()
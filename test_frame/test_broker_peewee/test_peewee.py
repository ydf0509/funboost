



import time

from funboost import BrokerEnum, boost, FunctionResultStatusPersistanceConfig, funboost_config_deafult

@boost('test_kombu2b', broker_kind=BrokerEnum.PEEWEE, qps=0.1,)
def f1(x, y):
    print(f'start {x} {y} 。。。')
    time.sleep(60)
    print(f'{x} + {y} = {x + y}')
    print(f'over {x} {y}')


if __name__ == '__main__':
    for i in range(100):
        f1.push(i, i*2)
    f1.consume()
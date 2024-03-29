

import time
import kombu
from funboost import BrokerEnum, boost,FunctionResultStatusPersistanceConfig


@boost('test_kombu_pyro', broker_kind=BrokerEnum.KOMBU, qps=0.1,
       function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(True,True),
       broker_exclusive_config={
           'kombu_url': 'pyro://',
           'transport_options': {

           },
           'prefetch_count': 1000})
def f1(x, y):
    print(f'start {x} {y} 。。。')
    time.sleep(60)
    print(f'{x} + {y} = {x + y}')
    print(f'over {x} {y}')


if __name__ == '__main__':
    f1.push(3,4)
    f1.consume()



import time,os
from funboost import boost, BrokerEnum

@boost('test_rabbit_queue2',broker_exclusive_config={'x-max-priority':5},
       broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM, qps=200,is_using_distributed_frequency_control=True)
def test_fun(x):
    print(x)

def _push():
    for i in range(1000):
        test_fun.push(x=i)

if __name__ == '__main__':
    test_fun.clear()
    test_fun.multi_process_consume(3)

    _push()
    # test_fun.consume()
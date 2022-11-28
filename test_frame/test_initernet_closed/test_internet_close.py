

from funboost import boost,BrokerEnum


@boost('test_internet_close_queue',broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM,qps=0.5,concurrent_num=5)
def add(x,y):
    print(f'{x} + {y} = {x+y}')


if __name__ == '__main__':
    add.consume()



from funboost import BrokerEnum,boost
from funboost.assist.user_custom_broker_register import register_kombu_broker

register_kombu_broker()


@boost('test_kombu',broker_kind=BrokerEnum.KOMBU)
def f1(x,y):
    print(f'{x} + {y} = {x  + y}')


if __name__ == '__main__':
    f1.push(1,2)
    f1.consume()
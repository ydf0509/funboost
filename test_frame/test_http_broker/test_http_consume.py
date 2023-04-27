import time

from funboost import boost,BrokerEnum

@boost('127.0.0.1:6789',broker_kind=BrokerEnum.HTTP)
def f(x):
    time.sleep(2)
    print(x)

if __name__ == '__main__':
    f.consume()
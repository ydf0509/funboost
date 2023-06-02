from funboost import boost, BrokerEnum

"""
定时的语法和入参与本框架无关系，不是本框架发明的定时语法，具体的需要学习 apscheduler包。
"""


@boost('queue_test_666', broker_kind=BrokerEnum.REDIS)
def consume_func(x, y):
    print(f'{x} + {y} = {x + y}')


if __name__ == '__main__':
    consume_func.consume()

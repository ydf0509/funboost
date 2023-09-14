


from funboost import boost,BrokerEnum

@boost('test_sqlite_queue',broker_kind=BrokerEnum.SQLITE_QUEUE)
def f(x):
    print(x)

if __name__ == '__main__':
    print(type(f))
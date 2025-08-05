from funboost import boost, BrokerEnum, BoosterParams


@boost(BoosterParams(
    queue_name='test_http_queue', broker_kind=BrokerEnum.HTTP,
    broker_exclusive_config={'host': '127.0.0.1', 'port': 7102},
))
def f(x):
    print(x)


if __name__ == '__main__':
    f.consume()

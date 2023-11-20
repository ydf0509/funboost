from funboost import Booster, BoostersManager,BrokerEnum


def add(a, b):
    print(a + b)


def my_push(quue_name, a, b):
    booster = BoostersManager.build_booster(queue_name=quue_name, qps=0.2, consuming_function=add, broker_kind=BrokerEnum.REDIS)  # type: Booster
    # get_or_create_booster 这种就不会无数次去创建 消息队列连接了。
    booster.push(a, b)


if __name__ == '__main__':
    for i in range(1000):
        queue_namx = f'queue_{i % 10}'
        my_push(queue_namx, i, i * 2)

    for j in range(10):
        booster = BoostersManager.build_booster(queue_name=f'queue_{j}', qps=0.2, consuming_function=add)  # type: Booster
        booster.multi_process_consume(2)


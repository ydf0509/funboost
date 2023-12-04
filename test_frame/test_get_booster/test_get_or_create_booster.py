from funboost import Booster, BoostersManager,BrokerEnum,BoosterParams


def add(a, b):
    print(a + b)


def my_push(quue_name, a, b):
    booster = BoostersManager.build_booster(BoosterParams(queue_name=quue_name, qps=0.2, consuming_function=add, broker_kind=BrokerEnum.REDIS))  # type: Booster
    # get_or_create_booster 这种就不会无数次去创建 消息队列连接了。
    booster.push(a, b)

for i in range(1000):
    queue_namx = f'queue_{i % 10}'
    my_push(queue_namx, i, i * 2)

print(BoostersManager.pid_queue_name__booster_map)
print(BoostersManager.queue_name__boost_params_map)
if __name__ == '__main__':


    for j in range(1):
        booster = BoostersManager.build_booster(BoosterParams(queue_name=f'queue_{j}', qps=0.2, consuming_function=add))  # type: Booster
        # booster.consume()
        booster.multi_process_consume(2)


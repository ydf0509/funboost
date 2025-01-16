from funboost import boost, FunctionResultStatusPersistanceConfig, BoosterParams


class MyBoosterParams(BoosterParams):
    function_result_status_persistance_conf:FunctionResultStatusPersistanceConfig = FunctionResultStatusPersistanceConfig(
        is_save_status=True, is_save_result=True, expire_seconds=7 * 24 * 3600)


@boost(MyBoosterParams(queue_name='queue_test_f01t',
                       function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
                           is_save_status=True, is_save_result=True, expire_seconds=7 * 24 * 3600)))
def f(x):
    print(f'hello: {x}')
    return x + 1


if __name__ == '__main__':
    # for i in range(0, 10):
    #     f.push(i)

    f.consume()

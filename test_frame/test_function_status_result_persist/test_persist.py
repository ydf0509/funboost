from funboost import boost, FunctionResultStatusPersistanceConfig


@boost('queue_test_f01', qps=2,
       function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
           is_save_status=True, is_save_result=True, expire_seconds=7 * 24 * 3600))
def f(a, b):
    return a + b


if __name__ == '__main__':
    f(5, 6)  # 可以直接调用

    for i in range(0, 200):
        f.push(i, b=i * 2)

    f.consume()
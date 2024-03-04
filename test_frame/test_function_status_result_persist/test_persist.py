import random
import time

from funboost import boost, FunctionResultStatusPersistanceConfig,BoosterParams


@boost(BoosterParams(queue_name='queue_test_f01', qps=2,concurrent_num=5,
       function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
           is_save_status=True, is_save_result=True, expire_seconds=7 * 24 * 3600)))
def f(a, b):
    time.sleep(20)
    if random.random() > 0.5:
        raise Exception(f'{a} {b} 模拟出错啦')
    print(a+b)
    return a + b


if __name__ == '__main__':
    # f(5, 6)  # 可以直接调用

    for i in range(0, 2000):
        f.push(i, b=i * 2)

    f.consume()
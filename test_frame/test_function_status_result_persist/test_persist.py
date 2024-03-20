import logging
import random
import time

import nb_log
from funboost import boost, FunctionResultStatusPersistanceConfig,BoosterParams
from funboost.core.current_task import funboost_current_task
from funboost.funboost_config_deafult import FunboostCommonConfig

logger = nb_log.get_logger('my_log',formatter_template=FunboostCommonConfig.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER)

@boost(BoosterParams(queue_name='queue_test_f01', qps=2,concurrent_num=5,
       function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
           is_save_status=True, is_save_result=True, expire_seconds=7 * 24 * 3600)))
def f(a, b):
    fct = funboost_current_task()
    print(fct.function_result_status.get_status_dict())
    print(fct.function_result_status.task_id)
    print(fct.function_result_status.run_times)
    print(fct.full_msg)
    print(fct.function_result_status.publish_time)
    logger.debug('cdf')

    time.sleep(20)
    if random.random() > 0.9999:
        raise Exception(f'{a} {b} 模拟出错啦')
    print(a+b)

    return a + b


if __name__ == '__main__':
    # f(5, 6)  # 可以直接调用

    for i in range(0, 200):
        f.push(i, b=i * 2)

    f.consume()


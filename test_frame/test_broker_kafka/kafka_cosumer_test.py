import time
import random
from function_scheduling_distributed_framework import task_deco, BrokerEnum, FunctionResultStatusPersistanceConfig


@task_deco('test_kafka12', broker_kind=BrokerEnum.KAFKA_CONFLUENT, qps=3,
           function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(True, True, 3600, is_use_bulk_insert=False))
def f(x):
    print(f'开始 {x}')
    time.sleep(random.randint(1, 50))
    print(f'结束 {x}')
    return x*10


if __name__ == '__main__':
    # for i in range(200):
    #     f.push(i)
    # f.publisher.get_message_count()
    f.consume()

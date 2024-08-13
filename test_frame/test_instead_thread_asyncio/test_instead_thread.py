import time
from funboost import BoosterParams, BrokerEnum


@BoosterParams(queue_name="test_insteda_thread_queue", broker_kind=BrokerEnum.MEMORY_QUEUE, concurrent_num=10, is_auto_start_consuming_message=True)
def f(x):
    time.sleep(3)
    print(x)


if __name__ == '__main__':
    for i in range(20):
        f.push(i)

import random
import time

from funboost import boost, PriorityConsumingControlConfig, BrokerEnum



@boost('test_redis_priority_queue4b', broker_kind=BrokerEnum.REDIS_PRIORITY, qps=5,broker_exclusive_config={'x-max-priority':4})
def f(x):
    # time.sleep(60)
    print(x)
    time.sleep(random.randint(1,5))



if __name__ == '__main__':

    f.clear()

    print(f.get_message_count())
      
    for i in range(100):
        randx = random.randint(1, 6)
        if randx > 10:
            randx = None
        print(randx)
        f.publish({'x': randx}, priority_control_config=PriorityConsumingControlConfig(other_extra_params={'priroty': randx}))
    print(f.get_message_count())
      
    # f.consume()
      
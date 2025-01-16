import random
import time

from test_frame.test_broker_rabbitmq.test_rabbitmq_consume import test_fun,test_fun2
from funboost import  PriorityConsumingControlConfig

test_fun.clear()
for i in range(2000):
    test_fun.push(i)
    # test_fun2.push(i)
    randx = random.randint(1,10)
    if randx > 4:
        randx = None
    print(randx)
    test_fun2.publish({'x':randx},priority_control_config=PriorityConsumingControlConfig(other_extra_params={'priroty':randx}))

time.sleep(10000)

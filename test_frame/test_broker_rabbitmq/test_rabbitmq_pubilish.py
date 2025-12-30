import random
import time

from test_frame.test_broker_rabbitmq.test_rabbitmq_consume import test_fun,test_fun2
from funboost import  TaskOptions

test_fun.clear()
for i in range(2000):
    test_fun.push(i)
    # test_fun2.push(i)
    randx = random.randint(1,10)
    if randx > 4:
        randx = None
    print(randx)
    test_fun2.publish({'x':randx},task_options=TaskOptions(other_extra_params={'priroty':randx}))

time.sleep(10000)

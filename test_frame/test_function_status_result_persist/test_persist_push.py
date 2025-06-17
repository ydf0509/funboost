import random
from test_persist import my_consuming_function,f2,time,aio_f3,f4,f5
from funboost import PriorityConsumingControlConfig,ApsJobAdder


def interval_push_f5(x):
    f5.publish({'x':x},priority_control_config=PriorityConsumingControlConfig(other_extra_params={'priroty': 4}))

ApsJobAdder(f5,job_store_kind='redis').aps_obj.add_job(
    interval_push_f5,trigger='interval',seconds=5,kwargs={'x':10},id='id_interval_push_f5',
    replace_existing=True)


for i in range(0, 1000):
    my_consuming_function.push(i)
    f2.push(i,i*2)
    aio_f3.push(i)
    f4.push(i)
    f5.publish({'x':i},priority_control_config=PriorityConsumingControlConfig(other_extra_params={'priroty': random.randint(0,5)}))
    time.sleep(0.01)




import time

from funboost import boost,BoosterParams
import queue_names

@boost(BoosterParams(queue_name=queue_names.q_test_queue_manager1, qps=0.5, ))
def fun1(x):
    print(f'fun1 x 的值是 {x}')

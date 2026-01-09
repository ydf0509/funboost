from .base_booster_params import Project1BoosterParams
from funboost import boost, BoosterParams, BrokerEnum
import time

@boost(Project1BoosterParams(queue_name="test_funboost_faas_queue", ))
def add(x:int, y:int=10,):
    time.sleep(1)
    print(f"add {x} + {y} = {x + y}")
    return x + y


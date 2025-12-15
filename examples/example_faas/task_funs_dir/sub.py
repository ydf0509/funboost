from .base_booster_params import Project1BoosterParams
from funboost import boost, BoosterParams, BrokerEnum
import time

@boost(Project1BoosterParams(queue_name="test_funboost_faas_queue2", ))
def sub(a, b):
    time.sleep(1)
    print(f"sub {a} - {b} = {a - b}")
    return a - b

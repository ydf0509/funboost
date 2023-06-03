import os
import typing

from funboost.core.booster import Booster
from funboost.core.global_boosters import pid_queue_name__booster_map


def get_booster(queue_name:str) -> Booster:
    return pid_queue_name__booster_map[(os.getpid(), queue_name)]


def get_boost_params_and_conusming_function(queue_name:str) :
    for k,v in pid_queue_name__booster_map.items():
        if k[1] == queue_name:
            booster = pid_queue_name__booster_map[k] # type: Booster
            return booster.boost_params,booster.consuming_function
import os

from funboost.core.booster import Booster
from funboost.core.global_boosters import pid_queue_name__booster_map


def get_booster(queue_name) -> Booster:
    return pid_queue_name__booster_map[(os.getpid(), queue_name)]
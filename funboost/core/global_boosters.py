import os

pid_queue_name__booster_map = {}


def regist_booster(queue_name: str, booster):
    pid_queue_name__booster_map[(os.getpid(), queue_name)] = booster

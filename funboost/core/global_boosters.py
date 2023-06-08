import os

pid_queue_name__booster_map = {}
queue_name__boost_params_consuming_function_map = {}


def regist_booster(queue_name: str, booster):
    pid_queue_name__booster_map[(os.getpid(), queue_name)] = booster
    queue_name__boost_params_consuming_function_map[queue_name] = (booster.boost_params, booster.consuming_function)

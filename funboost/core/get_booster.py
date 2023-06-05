import os

import typing

from funboost.core.booster import Booster
from funboost.core.global_boosters import pid_queue_name__booster_map


def get_booster(queue_name: str) -> Booster:
    pid = os.getpid()
    if (pid, queue_name) not in pid_queue_name__booster_map:
        err_msg = f'进程 {pid} ，没有 {queue_name} 对应的 booster'
        raise ValueError(err_msg)
    return pid_queue_name__booster_map[(pid, queue_name)]


def get_booster_ignore_current_pid(queue_name: str) -> Booster:
    """
    _booster = get_booster_ignore_current_pid(queue_name)
    booster_current_pid = boost(**_booster.boost_params)(_booster.consuming_function)

    这个函数是为了在别的进程实例化 booster，consumer和publisher,是为了获取queue_name队列对应的booster的当时的入参。
    有些中间件python包的对中间件连接对象不是多进程安全的，不要在进程2中去操作进程1中生成的booster consumer publisher等对象。
    """
    for k, v in pid_queue_name__booster_map.items():
        if k[1] == queue_name:
            booster = pid_queue_name__booster_map[k]  # type: Booster
            return booster
    err_msg = f'，没有 {queue_name} 对应的 booster'
    raise ValueError(err_msg)

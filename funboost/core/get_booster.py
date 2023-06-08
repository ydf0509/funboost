import os
import typing
from funboost.core.booster import Booster
from funboost.core.global_boosters import pid_queue_name__booster_map, queue_name__boost_params_consuming_function_map


def get_booster(queue_name: str) -> Booster:
    pid = os.getpid()
    if (pid, queue_name) not in pid_queue_name__booster_map:
        err_msg = f'进程 {pid} ，没有 {queue_name} 对应的 booster'
        raise ValueError(err_msg)
    return pid_queue_name__booster_map[(pid, queue_name)]


def get_boost_params_and_consuming_function(queue_name: str) -> (dict, typing.Callable):
    """
    这个函数是为了在别的进程实例化 booster，consumer和publisher,获取queue_name队列对应的booster的当时的入参。
    有些中间件python包的对中间件连接对象不是多进程安全的，不要在进程2中去操作进程1中生成的booster consumer publisher等对象。
    """

    """
    boost_params,consuming_function = get_boost_params_and_consuming_function(queue_name)
    booster_current_pid = boost(**boost_params)(consuming_function)
    """
    return queue_name__boost_params_consuming_function_map[queue_name]

import importlib
import os
import time

import fire
from funboost import get_booster
from funboost.core.discovery_boosters import BoosterDiscovery
from funboost.utils.ctrl_c_end import ctrl_c_recv


class BoosterFire(object):
    def __init__(self, import_modules_str: str = None, boost_dirs=None):
        self.import_modules_str = import_modules_str
        if import_modules_str:
            for m in self.import_modules_str.split(','):
                importlib.import_module(m)
        if boost_dirs:
            BoosterDiscovery(boost_dirs,
                             max_depth=2, py_file_re_str='task').auto_discovery()

    def clear(self, *queue_names: str):
        """清空queue"""
        for queue_anme in queue_names:
            get_booster(queue_anme).clear()

    fq = clear
    cl = clear

    def push(self, queue_anme, *args, **kwargs):
        get_booster(queue_anme).push(*args, **kwargs)

    p = push

    def publish(self, queue_anme, msg):
        get_booster(queue_anme).publish(msg)

    pb = publish

    def consume(self, *queue_names: str):
        for queue_anme in queue_names:
            get_booster(queue_anme).consume()
        ctrl_c_recv()

    c = consume

    def multi_process_consume(self, **queue_name__process_num):
        for queue_anme, process_num in queue_name__process_num.items():
            get_booster(queue_anme).multi_process_consume(process_num)
        ctrl_c_recv()

    mc = multi_process_consume
    m_consume = multi_process_consume


def funboost_fire():
    fire.Fire(BoosterFire)


if __name__ == '__main__':
    funboost_fire()

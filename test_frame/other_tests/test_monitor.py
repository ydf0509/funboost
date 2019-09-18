# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/9/18 0018 12:15
import time

from function_scheduling_distributed_framework import nb_print
from function_scheduling_distributed_framework.utils.resource_monitoring import ResourceMonitor
from test_frame.my_patch_frame_config import do_patch_frame_config

do_patch_frame_config()


def test_monitor():
    while 1:
        monitor = ResourceMonitor().set_log_level(10)
        nb_print(monitor.cpu_count)
        nb_print(monitor.get_current_process_memory())
        nb_print(monitor.get_current_process_cpu())
        nb_print(monitor.get_os_cpu_percpu())
        nb_print(monitor.get_os_cpu_avaragecpu())
        nb_print(monitor.get_os_cpu_totalcpu())
        nb_print(monitor.get_os_virtual_memory())
        nb_print(monitor.get_os_net_info())
        time.sleep(1)
        nb_print(monitor.get_os_net_info())
        nb_print(monitor.get_all_info())


if __name__ == '__main__':
    # test_monitor()
    monitorx = ResourceMonitor(is_save_info_to_mongo=True).set_log_level(10)
    # monitorx.start_build_info_loop(5)

    monitorx.start_build_info_loop_on_daemon_thread(5)
    while True:
        time.sleep(10)


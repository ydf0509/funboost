import time

from test_funboost_kill_consume import test_kill_fun
from funboost import RemoteTaskKiller


if __name__ == '__main__':
    async_result = test_kill_fun.push(555)
    # time.sleep(10)
    RemoteTaskKiller(test_kill_fun.queue_name,async_result.task_id).send_remote_task_comd()
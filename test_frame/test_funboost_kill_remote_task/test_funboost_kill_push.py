import time

from test_funboost_kill_consume import test_kill_add
from funboost import RemoteTaskKiller


if __name__ == '__main__':
    async_result = test_kill_add.push(3,4)
    # time.sleep(10)
    RemoteTaskKiller(test_kill_add.queue_name,async_result.task_id).send_remote_task_comd()
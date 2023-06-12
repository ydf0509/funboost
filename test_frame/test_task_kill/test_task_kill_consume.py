import time

from funboost import boost
from funboost.utils.kill_thread import kill_thread_by_task_id
@boost('test_kill_queue')
def f(x):
    print('start')
    time.sleep(10)
    print(x)
    print('over')

if __name__ == '__main__':

    f.consume()
    task = f.push(0)
    time.sleep(5)
    kill_thread_by_task_id(task.task_id)
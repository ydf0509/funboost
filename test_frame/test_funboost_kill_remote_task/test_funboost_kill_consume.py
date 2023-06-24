import threading
import time

from funboost import boost, BrokerEnum

test_lock= threading.Lock()

@boost('test_kill_fun_queue', broker_kind=BrokerEnum.REDIS, is_support_remote_kill_task=True,is_show_message_get_from_broker=True)
def test_kill_add(x, y):
    with test_lock:
        print(f'start {x} + {y} ....')
        time.sleep(60)
        print(f'over {x} + {y} = {x + y}')


if __name__ == '__main__':
    test_kill_add.consume()

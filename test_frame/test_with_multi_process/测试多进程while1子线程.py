import time
from threading import Thread
from multiprocessing import Process
from auto_run_on_remote import run_current_script_on_remote
run_current_script_on_remote()


def while1_thread():
    while 1:
        time.sleep(5)
        print('hello')


def run_in_thread():
    t = Thread(target=while1_thread)
    t.start()
    # t.join()  # linux + py3.6 + 多进程运行  如果不join 代码会迅速结束。


if __name__ == '__main__':
    Process(target=run_in_thread).start()

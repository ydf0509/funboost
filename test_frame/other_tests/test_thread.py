import threading
from time import sleep
import nb_log

def test():
    while 1:
        print(123123)
        sleep(1)

if __name__ == '__main__':
    threading.Thread(target=test).start()
    # threading._start_new_thread(test, ())
    print(111111111)
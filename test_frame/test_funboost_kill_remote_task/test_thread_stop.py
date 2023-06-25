import time
import threading

def f():
    print('start')
    time.sleep(5)
    print('hi')

t = threading.Thread(target=f)
t.start()
t._stop()
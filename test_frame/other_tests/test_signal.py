


# import signal
#
# def f(signal, frame):
#     print(6666)
#
# signal.signal(signal.SIG_DFL,f)
import time
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

def f():
    print('heelo')


class MyBackgroundScheduler(BackgroundScheduler):
    def start(self, *args, **kwargs):
        def _when_exit():
            while 1:
                print('阻止退出')
                time.sleep(10)
        atexit.register(_when_exit)

sc  = MyBackgroundScheduler(daemon=False)

sc.add_job(f,'interval', id='3_second_job', seconds=3)

sc.start()
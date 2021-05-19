from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import time
from apscheduler.schedulers . blocking import BlockingScheduler


def func(x,y):
    print(f' {x} + {y} = {x + y}')

scheduler = BackgroundScheduler()
scheduler.add_job(func,'date', run_date=datetime.datetime(2021, 5, 19, 10, 53, 20), args=(5, 6,))


scheduler.start()


for i in range(10000):
    scheduler.add_job(func,'date', run_date=datetime.datetime(2021, 5, 19, 10, 53, 30) + datetime.timedelta(seconds=i), args=(i, i,))


print(datetime.datetime.now())
print('over')


while 1:
    time.sleep(10)
import time

from test_frame.test_broker.test_consume import f

f.clear()
for i in range(100000):
    # time.sleep(0.5)
    if i == 0:
        print(time.strftime("%H:%M:%S"), '发布第一条')
    if i == 99999:
        print(time.strftime("%H:%M:%S"), '发布第100000条')
    f.push(i,i*2)


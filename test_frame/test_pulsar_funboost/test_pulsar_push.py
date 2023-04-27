import time

from test_pulsar_consume import add

for i in range(10000000):
    # time.sleep(0.01)
    add.push(i , i *2)
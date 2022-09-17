import time

from queuelib import FifoDiskQueue
q = FifoDiskQueue("queuefile")

for i in range(1000):
    q.push(f'{i}'.encode())


while 1:
    time.sleep(1)
    print(q.pop())
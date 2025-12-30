import os
import time

t1 = time.time()
for i in range(10000000):
    1+1
    os.getpid()

print(time.time() - t1)
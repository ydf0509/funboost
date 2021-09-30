import time
from test_udp_consumer import f

for i in range(100000):
    time.sleep(2)
    f.push(i)

import time
from test_udp_consumer import f

for i in range(1000000):
    # time.sleep(0.1)
    # print(i)
    f.push(i)



from test_frame.test_broker.test_consume import f


for i in range(10000):
    f.push(i)
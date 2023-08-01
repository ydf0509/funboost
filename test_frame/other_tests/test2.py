
import time

from funboost import boost, BrokerEnum
from funboost.concurrent_pool.flexible_thread_pool import BoundedSimpleQueue

q = BoundedSimpleQueue()

for i in range(1000):
    print(i)
    q.put(i,block=True)

print(q.qsize())
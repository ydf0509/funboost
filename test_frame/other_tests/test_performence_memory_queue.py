from queue import Queue
import nb_log
q = Queue()

print()
for i in range(1000000):
    q.put(i)
print()
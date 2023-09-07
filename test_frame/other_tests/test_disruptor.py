import time

import nb_log
# from disruptor import Disruptor, Consumer
# import time, random
#
# class MyConsumer(Consumer):
#     def __init__(self, name):
#         self.name = name
#     def consume(self, elements):
#         # simulate some random processing delay
#         # time.sleep(random.random())
#         time.sleep(2)
#         print("{} consumed {}".format(self.name,elements))
#
# # Construct a couple of consumer instances
# consumer_one = MyConsumer(name = 'consumer one')
# consumer_two = MyConsumer(name = 'consumer two')
#
# # Construct a disruptor named example
# disruptor = Disruptor(name = 'Example', size = 3)
# try:
#     # Register consumers
#     disruptor.register_consumer(consumer_one)
#     disruptor.register_consumer(consumer_one)
#     disruptor.register_consumer(consumer_two)
#
#     for i in range(10):
#         # Produce a bunch of elements
#         element = 'element {}'.format(i)
#         disruptor.produce([element])
#         print("produced {}".format(element))
# finally:
#     # Shut down the disruptor
#     disruptor.close()











import pyring
import queue
import threading
# create ring buffer
ring_buffer = pyring.BlockingRingBuffer(size=1000000)

queue = queue.Queue(1000000)
# add to ring

for i in range(500000):

    # ring_buffer.put(f"Something new!{i}")
    # ring_buffer.put(i)
    queue.put(i)


def f():
    while 1:

        # time.sleep(1)
        try:
            # r = ring_buffer.next()
            # r= r[1]
            r = queue.get()
        except Exception as e:
            print(type(e))
            break

        # print(r)
        if r %1000 == 0:
            print(r) # 0 Something new!

for j in range(100):
    t = threading.Thread(target=f)
    t.start()




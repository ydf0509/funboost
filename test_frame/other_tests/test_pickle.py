import queue

import threading

import pickle


import fastapi

import uvicorn
class A:
    def __init__(self,x):
        # self.lock = threading.Lock()
        self.q = queue.Queue()
        print('12323')
        self.x =x

a = A(1)

dumpa = pickle.dumps(a)
print(dumpa)

print(pickle.loads(dumpa))


msg
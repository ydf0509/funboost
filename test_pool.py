from copyreg import pickle

from function_scheduling_distributed_framework.concurrent_pool import CustomThreadPoolExecutor

import pickle
import threading
import requests

class CannotPickleObject:
    def __init__(self):
        self._lock = threading.Lock()
        
class CannotPickleObject2:
    def __init__(self):
        self._session = requests

pickle.dumps(CannotPickleObject)
pickle.dumps(CannotPickleObject2)
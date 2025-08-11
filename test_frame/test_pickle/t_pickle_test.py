

class MyClass:
    def __init__(self,x,y):
        self.x = x
        self.y = y
    def __str__(self):
        return f'MyClass(x={self.x},y={self.y})'
    

import datetime
import json



dic1 = {
    # 'a':MyClass(1,2),
        'b':datetime.datetime.now(),
        'c':[1,2]
        }



print(json.dumps(dic1))








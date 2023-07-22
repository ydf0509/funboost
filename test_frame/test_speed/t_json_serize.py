import json
import time

import nb_log

msg = '''
{
  "x": 5,
  "extra": {
    "task_id": "test_cost_long_time_fun_queue2d2_result:cddd1f8d-46c3-4c56-bd1d-8818edef6d2c",
    "publish_time": 1689867092.9808,
    "publish_time_format": "2023-07-20 23:31:32"
  }
}
'''

dict2 = {
  "x": 5,
  "extra": {
    "task_id": "test_cost_long_time_fun_queue2d2_result:cddd1f8d-46c3-4c56-bd1d-8818edef6d2c",
    "publish_time": 1689867092.9808,
    "publish_time_format": "2023-07-20 23:31:32"
  }
}

t1 = time.time()
print(t1)
for i in range(100000):
    json.loads(msg)
    json.dumps(dict2)

print(time.time() -t1)
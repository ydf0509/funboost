from function_scheduling_distributed_framework.utils import RedisMixin
from function_scheduling_distributed_framework.utils.bulk_operation import RedisOperation,RedisBulkWriteHelper
from test_frame.test_with_multi_process.test_consume import fff
import json
fff.clear()

helper = RedisBulkWriteHelper(RedisMixin().redis_db_frame,10000)
for i in range(0,1000000):
    helper.add_task(RedisOperation('rpush', fff.consumer.queue_name, json.dumps({"x":i})))

if __name__ == '__main__':
    pass

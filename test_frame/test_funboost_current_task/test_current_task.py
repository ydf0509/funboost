
import random
import time

from funboost import boost, FunctionResultStatusPersistanceConfig,BoosterParams
from funboost.core.current_task import funboost_current_task

# print(f)
@boost(BoosterParams(queue_name='queue_test_fct', qps=2,concurrent_num=5,))
def f(a, b):
    fct = funboost_current_task() # 线程/协程隔离级别的上下文
    print(fct.function_result_status.task_id) # 获取消息的任务id
    print(fct.function_result_status.run_times) # 获取消息是第几次重试运行
    print(fct.full_msg) # 获取消息的完全体。出了a和b的值意外，还有发布时间 task_id等。
    print(fct.function_result_status.publish_time) # 获取消息的发布时间
    print(fct.function_result_status.get_status_dict()) # 获取任务的信息，可以转成字典看。

    time.sleep(2)
    if random.random() > 0.99:
        raise Exception(f'{a} {b} 模拟出错啦')
    print(a+b)

    return a + b


if __name__ == '__main__':
    # f(5, 6)  # 可以直接调用

    for i in range(0, 200):
        f.push(i, b=i * 2)

    f.consume()
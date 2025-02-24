import random
import time

from funboost import boost, BoosterParams, fct


@boost(BoosterParams(queue_name='queue_test_fct', qps=2, concurrent_num=5, ))
def f(a, b):
    print(fct.task_id)  # 获取消息的任务id
    print(fct.function_result_status.run_times)  # 获取消息是第几次重试运行
    print(fct.full_msg)  # 获取消息的完全体。出了a和b的值意外，还有发布时间 task_id等。
    print(fct.function_result_status.publish_time)  # 获取消息的发布时间
    print(fct.function_result_status.get_status_dict())  # 获取任务的信息，可以转成字典看。

    time.sleep(20)
    if random.random() > 0.5:
        raise Exception(f'{a} {b} 模拟出错啦')
    print(a + b)
    common_fun()
    return a + b


def common_fun():
    """ common_fun 函数中也能自动通过上下文知道当前是在消费什么消息内容，无需让f函数调用 common_fun 时候吧taskid full_msg作为入参传过来 """
    print(f'common_fun函数也能自动知道消息的taskid，无需在f消费函数中把taskid作为common_fun函数的入参传过来,taskid: {fct.task_id}, full_msg: {fct.full_msg}')


if __name__ == '__main__':
    # f(5, 6)  # 可以直接调用

    for i in range(0, 200):
        f.push(i, b=i * 2)

    f.consume()

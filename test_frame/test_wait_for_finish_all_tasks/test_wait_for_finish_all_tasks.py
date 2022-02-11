import time
import os

from funboost import boost


@boost('test_f1_queue', qps=0.5)
def f1(x):
    time.sleep(3)
    print(f'x: {x}')
    for j in range(1, 5):
        f2.push(x * j)


@boost('test_f2_queue', qps=2)
def f2(y):
    time.sleep(5)
    print(f'y: {y}')


if __name__ == '__main__':
    f1.clear()
    f2.clear()
    for i in range(30):
        f1.push(i)
    f1.consume()
    f2.consume()
    f1.wait_for_possible_has_finish_all_tasks(4)
    print('f1函数的队列中4分钟内没有需要执行的任务')
    f2.wait_for_possible_has_finish_all_tasks(3)
    print('f2函数的队列中3分钟内没有需要执行的任务')
    print('f1 和f2任务都运行完了，。。。')
    print('马上 os._exit(444) 结束脚本')
    os._exit(444)  # 结束脚本

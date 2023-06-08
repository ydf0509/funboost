
import time

from funboost import boost, BrokerEnum


@boost('queue_test_step1g', qps=0.5, broker_kind=BrokerEnum.MONGOMQ)
def step1(x):
    print(f'x 的值是 {x}')
    if x == 0:
        for i in range(1, 300):
            step1.pub(dict(x=x + i))
    for j in range(10):
        step2.push(x * 100 + j)  # push是直接发送多个参数，pub是发布一个字典
    time.sleep(10)


@boost('queue_test_step2g', qps=3, broker_kind=BrokerEnum.MONGOMQ)
def step2(y):
    print(f'y 的值是 {y}')
    time.sleep(10)


if __name__ == '__main__':
    # step1.clear()
    step1.push(0)  # 给step1的队列推送任务。

    step1.consume()  # 可以连续启动两个消费者，因为conusme是启动独立线程里面while 1调度的，不会阻塞主线程，所以可以连续运行多个启动消费。
    step2.consume()
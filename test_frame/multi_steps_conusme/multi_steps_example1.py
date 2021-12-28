import time

from funboost import boost, BrokerEnum,ConcurrentModeEnum
import gevent.monkey;gevent.monkey.patch_all()

@boost('queue_test_step1', qps=0.5, broker_kind=BrokerEnum.REDIS_ACK_ABLE, concurrent_mode=ConcurrentModeEnum.GEVENT)
def step1(x):
    print(f'x 的值是 {x}')
    if x == 0:
        for i in range(1, 3):
            step1.pub(dict(x=x + i))
    for j in range(10):
        step2.push(y=x * 100 + j)  # push是直接发送多个参数，pub是发布一个字典
    time.sleep(10)


@boost('queue_test_step2', qps=3, broker_kind=BrokerEnum.REDIS_ACK_ABLE)
def step2(y):
    print(f'y 的值是 {y}')
    time.sleep(10)


if __name__ == '__main__':
    # step1.clear()
    step1.push(0)

    step1.consume()  # 可以连续启动两个消费者，sonusme是启动独立线程里面while 1调度的，所以可以连续运行多个启动消费。
    step2.consume()
